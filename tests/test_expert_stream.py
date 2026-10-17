"""Opt-in numerical and eviction checks on actual Metal execution."""
import os
from pathlib import Path
import tempfile
import unittest

@unittest.skipUnless(os.environ.get('COLIBRI_GPU_TESTS') == '1', 'opt-in Metal test')
class ExpertStreamTests(unittest.TestCase):
    def test_original_bytes_and_bounded_eviction(self):
        import json
        import struct
        import mlx.core as mx
        from mlx_lm.models.switch_layers import QuantizedSwitchLinear
        from pocs import expert_stream as poc
        mx.set_default_device(mx.gpu)
        mx.random.seed(19)
        layer = QuantizedSwitchLinear(64, 128, 8, bias=False)
        original = QuantizedSwitchLinear.__call__
        x = mx.random.normal((1, 1, 1, 64))
        cases = [mx.array([[0, 1]]), mx.array([[2, 3]]), mx.array([[0, 1]])]
        expected = [original(layer, x, idx) for idx in cases]
        mx.eval(expected)
        tensors = {f'experts.{e}.up_proj.{suffix}':layer[suffix][e]
                   for e in range(8) for suffix in ('weight', 'scales', 'biases')}
        fd = None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'experts.safetensors'
                mx.save_safetensors(str(path), tensors)
                fd = os.open(path, os.O_RDONLY)
                size = struct.unpack('<Q', os.pread(fd, 8, 0))[0]
                poc.states[id(layer)] = dict(cache=poc.OrderedDict(), capacity=2,
                    frequency={}, policy='lru', fd=fd, offset=8+size,
                    header=json.loads(os.pread(fd, size, 8)),
                    projection='up_proj', prefix='experts.')
                for suffix in ('weight', 'scales', 'biases'):
                    del layer[suffix]
                poc.install({})
                for idx, reference in zip(cases, expected):
                    actual = layer(x, idx)
                    mx.eval(actual)
                    self.assertTrue(mx.allclose(actual, reference, atol=1e-4, rtol=1e-4).item())
                    self.assertLessEqual(len(poc.states[id(layer)]['cache']), 2)
                self.assertEqual(poc.stats['misses'], 6)
                self.assertGreater(poc.stats['read_bytes'], 0)
        finally:
            QuantizedSwitchLinear.__call__ = original
            poc.states.clear()
            if fd is not None:
                os.close(fd)
