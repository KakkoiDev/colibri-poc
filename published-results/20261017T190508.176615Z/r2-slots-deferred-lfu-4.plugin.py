"""Bounded expert GPU banks with exact original bytes and explicit I/O policies.
SwitchGLU structure adapted from MLX-LM (Apple, MIT); see licenses/.
"""
import json
import os
import struct
import time
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

load_options = {'lazy': os.environ.get('SLOTS_LAZY','1') == '1'}
cache_description = 'OS file cache uncontrolled; lazy startup; fixed retained expert banks; bounded prefill partitions; prefetch scratch separate'
states = {}
stats = dict(read_bytes=0,read_calls=0,read_seconds=0.0,hits=0,misses=0,
             upload_seconds=0.0,compute_seconds=0.0,prefetch_useful=0,prefetch_submitted=0,
             prefetch_discarded=0,bank_updates=0)
lock = threading.Lock()
config = {}
executor = None


def install(variant):
    import mlx.core as mx
    from mlx_lm.models import switch_layers as layers
    original=layers.SwitchGLU.__call__
    def forward(self,x,indices):
        state=states.get(id(self))
        if state is None:return original(self,x,indices)
        x=mx.expand_dims(x,(-2,-3))
        indices=mx.stop_gradient(indices)
        grouped=indices.size>=64
        idx=indices;inverse=None
        if grouped:x,idx,inverse=layers._gather_sort(x,indices)
        flat=idx.flatten().tolist()  # One routing synchronization per complete GLU.
        if grouped:
            # Sorted expert IDs: partition before banks overflow, preserving original order.
            pieces=[];begin=0
            while begin<len(flat):
                seen=set();end=begin
                while end<len(flat) and (flat[end] in seen or len(seen)<state['capacity']):
                    seen.add(flat[end]);end+=1
                pieces.append(compute(state,self,x[begin:end],idx[begin:end],flat[begin:end]))
                mx.eval(pieces[-1])  # Release old-bank graphs before replacing slots.
                begin=end
            y=mx.concatenate(pieces,axis=0) if len(pieces)>1 else pieces[0]
            y=layers._scatter_unsort(y,inverse,indices.shape)
        else:
            y=compute(state,self,x,idx,flat)
        return y.squeeze(-2)
    layers.SwitchGLU.__call__=forward


def source_meta(state,expert):
    prefix=f'model.layers.{state["layer"]}.mlp.experts.{expert}.'
    return [(projection,suffix,state['header'][prefix+projection+'.'+suffix])
            for projection in ('up_proj','gate_proj','down_proj')
            for suffix in ('weight','scales','biases')]


def raw_read(state, experts):
    records=[]
    for e in experts:
        for projection,suffix,meta in source_meta(state,e):
            a,b=meta['data_offsets']
            records.append((a,b,e,projection,suffix,meta))
    records.sort()
    groups=[]
    for rec in records:
        if config['group_reads'] and groups and rec[0]==groups[-1][-1][1]:groups[-1].append(rec)
        else:groups.append([rec])
    result={e:{} for e in experts}
    for group in groups:
        a=group[0][0];b=group[-1][1];start=time.perf_counter()
        raw=os.pread(state['fd'],b-a,state['offset']+a)
        elapsed=time.perf_counter()-start
        if len(raw)!=b-a:raise IOError('Short expert read')
        with lock:
            stats['read_bytes']+=len(raw);stats['read_calls']+=1;stats['read_seconds']+=elapsed
        for c,d,e,projection,suffix,meta in group:
            result[e][projection,suffix]=(memoryview(raw)[c-a:d-a],meta)
    return result


def read_missing(state,missing):
    result={};pending=[]
    for e in missing:
        if e in state['prefetch']:
            result.update(state['prefetch'].pop(e).result());stats['prefetch_useful']+=1
        else:pending.append(e)
    if pending:
        if config['workers']==1 or len(pending)==1:
            result.update(raw_read(state,pending))
        else:
            # Group into adjacent runs first; workers divide those runs.
            jobs=[]
            for e in sorted(pending):
                if config['group_reads'] and jobs and e==jobs[-1][-1]+1:jobs[-1].append(e)
                else:jobs.append([e])
            futures=[executor.submit(raw_read,state,job) for job in jobs]
            for f in futures:result.update(f.result())
    return result


def compute(state,module,x,indices,flat):
    import mlx.core as mx
    import numpy as np
    unique=sorted(set(flat));protected=set(unique)
    if len(unique)>state['capacity']:raise RuntimeError('Active expert set exceeds bank capacity')
    state['clock']+=1
    for e in unique:
        state['frequency'][e]=state['frequency'].get(e,0)+1
        state['last'][e]=state['clock']
    missing=[e for e in unique if e not in state['slots']]
    stats['hits']+=len(unique)-len(missing);stats['misses']+=len(missing)
    state['hits']+=len(unique)-len(missing);state['misses']+=len(missing)
    payload=read_missing(state,missing)
    targets=[]
    for e in unique:
        if e in state['slots']:state['slots'].move_to_end(e)
    for e in missing:
        if len(state['slots'])<state['capacity']:
            slot=next(s for s in range(state['capacity']) if s not in state['slots'].values())
        else:
            eligible=[v for v in state['slots'] if v not in protected]
            if config['policy']=='lru':victim=eligible[0]
            elif config['policy']=='lfu':victim=min(eligible,key=lambda v:state['frequency'][v])
            else:victim=min(eligible,key=lambda v:state['frequency'][v]/(1+(state['clock']-state['last'][v])/64))
            slot=state['slots'].pop(victim)
            state.get('rows', {}).pop(victim, None)
        state['slots'][e]=slot;targets.append(slot)
    if missing:
        start=time.perf_counter()
        for projection in ('up_proj','gate_proj','down_proj'):
            for suffix in ('weight','scales','biases'):
                arrays=[]
                for e in missing:
                    raw,meta=payload[e][projection,suffix]
                    dtype={'U32':np.uint32,'BF16':np.uint16,'F16':np.float16,'F32':np.float32}[meta['dtype']]
                    a=mx.array(np.frombuffer(raw,dtype=dtype).reshape(meta['shape']).copy())
                    if meta['dtype']=='BF16':a=a.view(mx.bfloat16)
                    arrays.append(a)
                key=projection,suffix
                if config.get('compact'):
                    for e, array in zip(missing, arrays):
                        state['rows'].setdefault(e,{})[key]=array
                    continue
                if key not in state['banks']:
                    state['banks'][key]=mx.zeros((state['capacity'],*arrays[0].shape),dtype=arrays[0].dtype)
                bank=state['banks'][key]
                bank[mx.array(targets)]=mx.stack(arrays)
                state['banks'][key]=bank
        if not config.get('deferred'):
            mx.eval([a for rows in state.get('rows',{}).values() for a in rows.values()] if config.get('compact') else list(state['banks'].values()))
        stats['upload_seconds']+=time.perf_counter()-start;stats['bank_updates']+=1
    mapping={e:i for i,e in enumerate(unique)} if config.get('compact') else state['slots']
    remapped=mx.array([mapping[e] for e in flat],dtype=mx.uint32).reshape(indices.shape)
    def project(name,value):
        m=getattr(module,name)
        weights=[mx.stack([state['rows'][e][name,s] for e in unique]) for s in ('weight','scales','biases')] if config.get('compact') else [state['banks'][name,s] for s in ('weight','scales','biases')]
        return mx.gather_qmm(value,*weights,
            rhs_indices=remapped,transpose=True,group_size=m.group_size,bits=m.bits,mode=m.mode,
            sorted_indices=False)
    start=time.perf_counter()
    up=project('up_proj',x);gate=project('gate_proj',x)
    y=project('down_proj',module.activation(up,gate))
    if not config.get('deferred'):
        mx.eval(y)
    stats['compute_seconds']+=time.perf_counter()-start
    if config['prefetch']:
        # Temporal predictor: most frequently used absent expert, one in-flight record/layer.
        for e,future in list(state['prefetch'].items()):
            if future.done():
                future.result();del state['prefetch'][e];stats['prefetch_discarded']+=1
        if not state['prefetch']:
            choices=[e for e in state['frequency'] if e not in state['slots']]
            if choices:
                e=max(choices,key=lambda e:state['frequency'][e])
                state['prefetch'][e]=executor.submit(raw_read,state,[e]);stats['prefetch_submitted']+=1
    return y


def after_load(model,tokenizer,root):
    import mlx.core as mx
    global executor,config
    capacity=int(os.environ.get('SLOTS_CAPACITY','32'))
    capacities=json.loads(os.environ.get('SLOTS_CAPACITIES',json.dumps([capacity]*16)))
    if len(capacities)!=16 or any(not 8<=n<=64 for n in capacities):raise ValueError('Capacity must be 8..64 for all 16 layers')
    config=dict(workers=int(os.environ.get('SLOTS_WORKERS','1')),
        group_reads=os.environ.get('SLOTS_GROUP_READS','0')=='1',
        policy=os.environ.get('SLOTS_POLICY','lru'),prefetch=os.environ.get('SLOTS_PREFETCH','0')=='1',
        layout=os.environ.get('SLOTS_LAYOUT','original'),capacities=capacities,deferred=os.environ.get('SLOTS_DEFERRED','0')=='1',compact=os.environ.get('SLOTS_COMPACT','0')=='1')
    if config['workers'] not in (1,2,4,8) or config['policy'] not in ('lru','lfu','hybrid'):raise ValueError('Invalid streaming configuration')
    executor=ThreadPoolExecutor(max_workers=max(1,config['workers']))
    folder=root/'models/olmoe-1b-7b-4bit'
    if config['layout']=='packed':
        index=json.loads((folder/'experts-contiguous.json').read_text())
        header=index['tensors'];offset=0;fd=os.open(folder/'experts-contiguous.bin',os.O_RDONLY)
        config['layout_sha256']=index['packed_sha256']
    else:
        fd=os.open(folder/'model.safetensors',os.O_RDONLY)
        size=struct.unpack('<Q',os.pread(fd,8,0))[0];header=json.loads(os.pread(fd,size,8));offset=8+size
    for i,layer in enumerate(model.model.layers):
        module=layer.mlp.switch_mlp
        for projection in ('up_proj','gate_proj','down_proj'):
            p=getattr(module,projection)
            if p.bits!=4 or p.mode!='affine' or p.global_scale is not None or 'bias' in p:raise ValueError('Only original affine 4bit OLMoE supported')
            for suffix in ('weight','scales','biases'):del p[suffix]
        states[id(module)]=dict(capacity=capacities[i],layer=i,header=header,fd=fd,offset=offset,
            banks={},rows={},slots=OrderedDict(),frequency={},last={},clock=0,prefetch={},hits=0,misses=0)
    mx.eval(model.parameters())  # Dense weights only; expert graphs were removed before evaluation.
    mx.clear_cache()


def telemetry():
    retained=sum(t.nbytes for s in states.values() for t in s['banks'].values())
    retained+=sum(t.nbytes for s in states.values() for rows in s.get('rows',{}).values() for t in rows.values())
    layers=[dict(layer=s['layer'],capacity=s['capacity'],hits=s['hits'],misses=s['misses']) for s in states.values()]
    return dict(stats,retained_expert_bytes=retained,configuration=config,layers=layers,
        timing_scope='enqueue-only upload/compute timers when deferred=true; read timers are CPU syscall time',
        prefetch_record_limit=16 if config['prefetch'] else 0,
        counters='cumulative since worker start, including warmup; read seconds sum across threads')
