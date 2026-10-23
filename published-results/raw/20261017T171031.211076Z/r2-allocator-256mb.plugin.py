"""Fuse two selected-expert projections into one gather_qmm call.

SwitchGLU skeleton adapted from MLX-LM, Copyright (c) 2023 Apple Inc., MIT.
See licenses/mlx-lm-LICENSE. Original weights retained by default; compact mode replaces them with views.
"""
def install_fused(variant):
    import os
    import mlx.core as mx
    from mlx_lm.models import switch_layers as layers

    def forward(self, x, indices):
        up, gate = self.up_proj, self.gate_proj
        if not hasattr(self, '_poc_fused_weights'):
            if not isinstance(up, layers.QuantizedSwitchLinear) or not isinstance(gate, layers.QuantizedSwitchLinear):
                raise ValueError('Fused PoC requires quantized experts')
            if (up.bits,up.group_size,up.mode)!=(gate.bits,gate.group_size,gate.mode) or up.global_scale is not None or gate.global_scale is not None:
                raise ValueError('Incompatible expert quantization')
            if 'bias' in up or 'bias' in gate:
                raise ValueError('Biased expert projections are unsupported')
            self._poc_fused_weights = (
                mx.concatenate([up.weight,gate.weight],axis=1),
                mx.concatenate([up.scales,gate.scales],axis=1),
                mx.concatenate([up.biases,gate.biases],axis=1))
            mx.eval(self._poc_fused_weights)
            if os.environ.get('COLIBRI_FUSED_RELEASE_ORIGINALS') == '1':
                for attr, combined in zip(('weight','scales','biases'), self._poc_fused_weights):
                    u, g = mx.split(combined, 2, axis=1)
                    setattr(up, attr, u)
                    setattr(gate, attr, g)
                mx.eval(up.parameters(), gate.parameters())
        x = mx.expand_dims(x, (-2,-3))
        indices = mx.stop_gradient(indices)
        grouped = indices.size >= 64
        idx = indices
        inverse = None
        if grouped:
            x,idx,inverse = layers._gather_sort(x,indices)
        w,s,b = self._poc_fused_weights
        combined = mx.gather_qmm(x,w,s,b,rhs_indices=idx,transpose=True,
                                 group_size=up.group_size,bits=up.bits,mode=up.mode,
                                 sorted_indices=grouped)
        projected_up,projected_gate = mx.split(combined,2,axis=-1)
        x = self.down_proj(self.activation(projected_up,projected_gate),idx,sorted_indices=grouped)
        if grouped:
            x = layers._scatter_unsort(x,inverse,indices.shape)
        return x.squeeze(-2)

    layers.SwitchGLU.__call__ = forward

"""Sweep expert grouping threshold in MLX-LM's SwitchGLU.

Adapted from mlx_lm/models/switch_layers.py, Copyright (c) 2023 Apple Inc.,
MIT license: https://github.com/ml-explore/mlx-lm/blob/main/LICENSE
Routing, weights, and original output order are preserved.
"""
import os


def install_sort(variant):
    import mlx.core as mx
    from mlx_lm.models import switch_layers as layers
    threshold = int(os.environ['COLIBRI_SORT_THRESHOLD'])

    def forward(self, x, indices):
        x = mx.expand_dims(x, (-2, -3))
        indices = mx.stop_gradient(indices)
        do_sort = indices.size >= threshold
        idx = indices
        inverse = None
        if do_sort:
            x, idx, inverse = layers._gather_sort(x, indices)
        up = self.up_proj(x, idx, sorted_indices=do_sort)
        gate = self.gate_proj(x, idx, sorted_indices=do_sort)
        x = self.down_proj(self.activation(up, gate), idx, sorted_indices=do_sort)
        if do_sort:
            x = layers._scatter_unsort(x, inverse, indices.shape)
        return x.squeeze(-2)

    layers.SwitchGLU.__call__ = forward


def install(variant):
    import os
    import mlx.core as mx
    from mlx_lm.models.switch_layers import SwitchGLU
    if os.environ.get('POC_FUSED') == '1':
        os.environ['COLIBRI_FUSED_RELEASE_ORIGINALS'] = '1'
        install_fused(variant)
    elif 'COLIBRI_SORT_THRESHOLD' in os.environ:
        install_sort(variant)
    if 'POC_ALLOCATOR_MB' in os.environ:
        mx.set_cache_limit(int(os.environ['POC_ALLOCATOR_MB']) * 1024**2)
    if os.environ.get('POC_COMPILE') == '1':
        original = SwitchGLU.__call__
        compiled = {}
        def forward(self, x, indices):
            if id(self) not in compiled:
                # Eager initialization first: fused packing must not mutate a compiled graph.
                original(self, x, indices)
                mx.eval(self.parameters())
                compiled[id(self)] = mx.compile(lambda a, b: original(self, a, b))
            return compiled[id(self)](x, indices)
        SwitchGLU.__call__ = forward
