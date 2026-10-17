"""Opt-in real GPU tests of fixed slots, partitioning, raw bytes and eviction."""
import os
import unittest

@unittest.skipUnless(os.environ.get('COLIBRI_GPU_TESTS')=='1','opt-in Metal test')
class SlotTests(unittest.TestCase):
    def test_fixed_slots_partition_and_eviction(self):
        self.check_slots(False, False)

    def test_compact_partition_and_eviction(self):
        self.check_slots(True, False)

    def test_deferred_fixed_slots(self):
        self.check_slots(False, True)

    def test_deferred_compact_slots(self):
        self.check_slots(True, True)

    def check_slots(self, compact, deferred):
        import json
        import struct
        import tempfile
        from pathlib import Path
        import mlx.core as mx
        import mlx.nn as nn
        from mlx_lm.models import switch_layers as layers
        from pocs import stream_slots as poc
        mx.set_default_device(mx.gpu);mx.random.seed(27)
        module=layers.SwitchGLU(64,128,64)
        nn.quantize(module,group_size=64,bits=4)
        original=layers.SwitchGLU.__call__
        cases=[(mx.random.normal((1,64)),mx.array([[0,1,2,3,4,5,6,7]])),
               (mx.random.normal((12,64)),mx.random.randint(0,64,(12,8))),
               (mx.random.normal((1,64)),mx.array([[0,1,2,3,4,5,6,7]]))]
        expected=[original(module,x,i) for x,i in cases];mx.eval(expected)
        tensors={f'model.layers.0.mlp.experts.{e}.{p}.{s}':getattr(module,p)[s][e]
            for e in range(64) for p in ('up_proj','gate_proj','down_proj') for s in ('weight','scales','biases')}
        fd=None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'test.safetensors';mx.save_safetensors(str(path),tensors)
                fd=os.open(path,os.O_RDONLY);size=struct.unpack('<Q',os.pread(fd,8,0))[0]
                for p in ('up_proj','gate_proj','down_proj'):
                    for s in ('weight','scales','biases'):del getattr(module,p)[s]
                state=dict(capacity=8,layer=0,header=json.loads(os.pread(fd,size,8)),fd=fd,offset=8+size,
                    banks={},rows={},slots=poc.OrderedDict(),frequency={},last={},clock=0,prefetch={},hits=0,misses=0)
                poc.states[id(module)]=state
                poc.config.update(workers=1,group_reads=True,policy='hybrid',prefetch=False,compact=compact,deferred=deferred)
                poc.install({})
                for (x,i),ref in zip(cases,expected):
                    actual=module(x,i);mx.eval(actual)
                    self.assertTrue(mx.allclose(actual,ref,atol=1e-4,rtol=1e-4).item())
                    self.assertLessEqual(len(state['slots']),8)
                    self.assertLessEqual(len(state['rows']),8)
                    self.assertTrue(all(bank.shape[0]==8 for bank in state['banks'].values()))
                self.assertGreater(state['misses'],8)
                self.assertGreater(poc.stats['read_bytes'],0)
        finally:
            layers.SwitchGLU.__call__=original;poc.states.clear()
            if fd is not None:os.close(fd)
