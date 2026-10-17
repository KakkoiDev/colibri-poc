"""Read original expert tensors on demand; bounded retained LRU per projection.
No weight conversion. Temporary active-expert batches can exceed retained capacity.
"""
import json
import os
import struct
import time
from collections import OrderedDict

states = {}
stats = dict(read_bytes=0, read_calls=0, hits=0, misses=0, read_seconds=0.0)
cache_description = 'OS page cache uncontrolled; fresh KV; bounded retained expert LRU; temporary active batches may exceed cache'


def install(variant):
    import mlx.core as mx
    import numpy as np
    from mlx_lm.models.switch_layers import QuantizedSwitchLinear
    original = QuantizedSwitchLinear.__call__

    def forward(self, x, indices, sorted_indices=False):
        state = states.get(id(self))
        if state is None:
            return original(self, x, indices, sorted_indices)
        flat = indices.flatten().tolist()
        unique = sorted(set(flat))
        active = []
        for expert in unique:
            if expert in state['cache']:
                stats['hits'] += 1
                tensors = state['cache'].pop(expert)
            else:
                stats['misses'] += 1
                tensors = []
                for suffix in ('weight', 'scales', 'biases'):
                    meta = state['header'][state['prefix'] + str(expert) + '.' + state['projection'] + '.' + suffix]
                    start, end = meta['data_offsets']
                    begin = time.perf_counter()
                    raw = os.pread(state['fd'], end-start, state['offset']+start)
                    stats['read_seconds'] += time.perf_counter()-begin
                    if len(raw) != end-start:
                        raise IOError('Short expert read')
                    stats['read_bytes'] += len(raw)
                    stats['read_calls'] += 1
                    dtype = {'U32':np.uint32, 'BF16':np.uint16, 'F16':np.float16, 'F32':np.float32}[meta['dtype']]
                    tensor = mx.array(np.frombuffer(raw, dtype=dtype).reshape(meta['shape']).copy())
                    if meta['dtype'] == 'BF16':
                        tensor = tensor.view(mx.bfloat16)
                    tensors.append(tensor)
                mx.eval(tensors)
            state['cache'][expert] = tensors
            while len(state['cache']) > state['capacity']:
                state['cache'].popitem(last=False)
            active.append(tensors)
        packed = [mx.stack([t[i] for t in active]) for i in range(3)]
        mapping = {e:i for i,e in enumerate(unique)}
        remapped = mx.array([mapping[e] for e in flat], dtype=mx.uint32).reshape(indices.shape)
        return mx.gather_qmm(x, *packed, rhs_indices=remapped, transpose=True,
                             group_size=self.group_size, bits=self.bits, mode=self.mode,
                             sorted_indices=sorted_indices)

    QuantizedSwitchLinear.__call__ = forward


def after_load(model, tokenizer, root):
    import mlx.core as mx
    capacity = int(os.environ['COLIBRI_EXPERT_CACHE'])
    if not 1 <= capacity <= 64:
        raise ValueError('Expert capacity must be 1..64')
    path = root/'models/olmoe-1b-7b-4bit/model.safetensors'
    fd = os.open(path, os.O_RDONLY)
    size = struct.unpack('<Q', os.pread(fd, 8, 0))[0]
    header = json.loads(os.pread(fd, size, 8))
    for layer_id, layer in enumerate(model.model.layers):
        for projection in ('up_proj', 'gate_proj', 'down_proj'):
            module = getattr(layer.mlp.switch_mlp, projection)
            if module.bits != 4 or module.mode != 'affine' or module.global_scale is not None or 'bias' in module:
                raise ValueError('Only original affine 4bit OLMoE supported')
            states[id(module)] = dict(cache=OrderedDict(), capacity=capacity,
                fd=fd, offset=8+size, header=header, projection=projection,
                prefix=f'model.layers.{layer_id}.mlp.experts.')
            for suffix in ('weight', 'scales', 'biases'):
                del module[suffix]
    mx.clear_cache()


def telemetry():
    retained = sum(t.nbytes for s in states.values() for ts in s['cache'].values() for t in ts)
    return dict(stats, retained_expert_bytes=retained,
                capacity_per_projection=int(os.environ['COLIBRI_EXPERT_CACHE']),
                counters='cumulative since worker start, including warmup')
