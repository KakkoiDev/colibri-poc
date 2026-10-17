"""Opt-in real Metal numerical checks: COLIBRI_GPU_TESTS=1 make test."""
import os
import unittest


@unittest.skipUnless(os.environ.get('COLIBRI_GPU_TESTS') == '1', 'opt-in Metal test')
class ExpertSortTests(unittest.TestCase):
    def test_always_grouping_preserves_quantized_expert_results(self):
        from pocs.expert_sort import install
        self.check_projection(install)

    def test_fused_projection_preserves_quantized_expert_results(self):
        from pocs.fused_gate_up import install
        self.check_projection(install)

    def test_compact_fused_projection_preserves_results(self):
        from pocs.fused_gate_up import install
        old = os.environ.get('COLIBRI_FUSED_RELEASE_ORIGINALS')
        os.environ['COLIBRI_FUSED_RELEASE_ORIGINALS'] = '1'
        try:
            self.check_projection(install)
        finally:
            if old is None:
                os.environ.pop('COLIBRI_FUSED_RELEASE_ORIGINALS', None)
            else:
                os.environ['COLIBRI_FUSED_RELEASE_ORIGINALS'] = old

    def check_projection(self, install):
        import mlx.core as mx
        import mlx.nn as nn
        from mlx_lm.models import switch_layers
        mx.set_default_device(mx.gpu)
        mx.random.seed(7)
        original = switch_layers.SwitchGLU.__call__
        old = os.environ.get('COLIBRI_SORT_THRESHOLD')
        try:
            layer = switch_layers.SwitchGLU(64, 128, 8)
            nn.quantize(layer, group_size=64, bits=4)
            for rows in (1, 64):
                x = mx.random.normal((rows, 64))
                indices = mx.random.randint(0, 8, (rows, 2))
                expected = original(layer, x, indices)
                mx.eval(expected)
                for threshold in (0,):
                    os.environ['COLIBRI_SORT_THRESHOLD'] = str(threshold)
                    install({})
                    actual = layer(x, indices)
                    mx.eval(actual)
                    self.assertTrue(mx.allclose(actual, expected, atol=1e-4, rtol=1e-4).item(),
                                    f'rows={rows}, threshold={threshold}')
        finally:
            switch_layers.SwitchGLU.__call__ = original
            if old is None:
                os.environ.pop('COLIBRI_SORT_THRESHOLD', None)
            else:
                os.environ['COLIBRI_SORT_THRESHOLD'] = old
