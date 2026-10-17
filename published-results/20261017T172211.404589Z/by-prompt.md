# Per-prompt results

1 rounds; up to 32 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 204.317 | 562.736 | 0.055 | 3.965 |
| baseline | code | 206.473 | 761.728 | 0.044 | 3.967 |
| baseline | reason | 204.687 | 912.728 | 0.047 | 4.003 |
| baseline | story | 203.605 | 747.749 | 0.047 | 3.988 |
| baseline | long-context | 149.753 | 4529.425 | 0.516 | 4.644 |
| stream-lru-32 | explain | 47.190 | 97.177 | 0.320 | 2.392 |
| stream-lru-32 | code | 49.615 | 88.474 | 0.373 | 2.397 |
| stream-lru-32 | reason | 47.845 | 118.721 | 0.363 | 2.425 |
| stream-lru-32 | story | 48.354 | 100.750 | 0.348 | 2.414 |
| stream-lru-32 | long-context | 43.759 | 1268.382 | 1.838 | 2.770 |
| slots-deferred-packed | explain | 54.965 | 86.849 | 0.357 | 2.280 |
| slots-deferred-packed | code | 63.010 | 93.230 | 0.354 | 2.284 |
| slots-deferred-packed | reason | 54.868 | 107.280 | 0.401 | 2.305 |
| slots-deferred-packed | story | 56.581 | 88.124 | 0.397 | 2.290 |
| slots-deferred-packed | long-context | 47.688 | 537.280 | 4.337 | 2.632 |
| compact-deferred-packed | explain | 47.635 | 93.148 | 0.333 | 2.230 |
| compact-deferred-packed | code | 52.312 | 99.820 | 0.331 | 2.230 |
| compact-deferred-packed | reason | 46.917 | 115.322 | 0.373 | 2.231 |
| compact-deferred-packed | story | 48.598 | 95.461 | 0.367 | 2.230 |
| compact-deferred-packed | long-context | 42.742 | 560.597 | 4.157 | 2.554 |
| slots-unequal-packed | explain | 44.430 | 80.542 | 0.385 | 2.286 |
| slots-unequal-packed | code | 51.279 | 89.961 | 0.367 | 2.278 |
| slots-unequal-packed | reason | 48.108 | 102.754 | 0.419 | 2.304 |
| slots-unequal-packed | story | 46.582 | 84.312 | 0.415 | 2.289 |
| slots-unequal-packed | long-context | 39.070 | 527.770 | 4.415 | 2.631 |
| compact-deferred-unequal-packed | explain | 47.138 | 90.060 | 0.345 | 2.230 |
| compact-deferred-unequal-packed | code | 52.296 | 97.463 | 0.339 | 2.230 |
| compact-deferred-unequal-packed | reason | 49.946 | 112.749 | 0.382 | 2.231 |
| compact-deferred-unequal-packed | story | 46.831 | 92.507 | 0.379 | 2.230 |
| compact-deferred-unequal-packed | long-context | 42.287 | 555.498 | 4.195 | 2.550 |
| slots-deferred-lfu-4 | explain | 74.221 | 98.182 | 0.316 | 2.280 |
| slots-deferred-lfu-4 | code | 73.811 | 104.508 | 0.316 | 2.284 |
| slots-deferred-lfu-4 | reason | 66.483 | 119.317 | 0.361 | 2.305 |
| slots-deferred-lfu-4 | story | 55.916 | 96.892 | 0.362 | 2.290 |
| slots-deferred-lfu-4 | long-context | 52.687 | 558.254 | 4.174 | 2.632 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
