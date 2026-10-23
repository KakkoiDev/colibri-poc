"""Sweep expert grouping threshold in MLX-LM's SwitchGLU.

Adapted from mlx_lm/models/switch_layers.py, Copyright (c) 2023 Apple Inc.,
MIT license: https://github.com/ml-explore/mlx-lm/blob/main/LICENSE
Routing, weights, and original output order are preserved.
"""
import os


def install(variant):
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
