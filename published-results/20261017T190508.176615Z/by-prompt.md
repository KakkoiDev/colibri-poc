# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 189.333 | 547.590 | 0.057 | 3.965 |
| baseline | code | 190.380 | 735.376 | 0.045 | 3.967 |
| baseline | reason | 190.779 | 838.343 | 0.052 | 4.003 |
| baseline | story | 189.989 | 724.833 | 0.049 | 3.988 |
| baseline | long-context | 137.937 | 4429.499 | 0.528 | 4.644 |
| stream-lru-32 | explain | 46.210 | 91.559 | 0.339 | 2.392 |
| stream-lru-32 | code | 47.140 | 95.348 | 0.347 | 2.398 |
| stream-lru-32 | reason | 41.696 | 118.364 | 0.364 | 2.426 |
| stream-lru-32 | story | 45.509 | 96.907 | 0.362 | 2.410 |
| stream-lru-32 | long-context | 38.587 | 1188.555 | 1.962 | 2.770 |
| slots-packed-grouped | explain | 46.147 | 74.304 | 0.417 | 2.279 |
| slots-packed-grouped | code | 44.817 | 86.360 | 0.382 | 2.283 |
| slots-packed-grouped | reason | 46.388 | 95.385 | 0.451 | 2.304 |
| slots-packed-grouped | story | 38.524 | 62.484 | 0.560 | 2.289 |
| slots-packed-grouped | long-context | 41.096 | 517.252 | 4.505 | 2.626 |
| slots-lfu | explain | 51.705 | 69.479 | 0.446 | 2.279 |
| slots-lfu | code | 49.494 | 82.926 | 0.398 | 2.283 |
| slots-lfu | reason | 39.160 | 98.672 | 0.436 | 2.304 |
| slots-lfu | story | 37.528 | 61.819 | 0.566 | 2.289 |
| slots-lfu | long-context | 34.091 | 521.623 | 4.467 | 2.610 |
| slots-deferred-packed | explain | 48.029 | 63.761 | 0.486 | 2.280 |
| slots-deferred-packed | code | 53.926 | 70.722 | 0.467 | 2.284 |
| slots-deferred-packed | reason | 52.150 | 96.186 | 0.447 | 2.305 |
| slots-deferred-packed | story | 46.656 | 80.904 | 0.433 | 2.290 |
| slots-deferred-packed | long-context | 44.534 | 524.068 | 4.446 | 2.632 |
| slots-unequal-packed | explain | 43.818 | 66.828 | 0.464 | 2.286 |
| slots-unequal-packed | code | 45.220 | 65.339 | 0.505 | 2.278 |
| slots-unequal-packed | reason | 44.062 | 79.309 | 0.543 | 2.304 |
| slots-unequal-packed | story | 45.415 | 81.688 | 0.429 | 2.289 |
| slots-unequal-packed | long-context | 36.065 | 515.530 | 4.520 | 2.631 |
| slots-deferred-lfu-4 | explain | 70.801 | 98.571 | 0.315 | 2.280 |
| slots-deferred-lfu-4 | code | 61.132 | 104.830 | 0.315 | 2.284 |
| slots-deferred-lfu-4 | reason | 60.537 | 105.841 | 0.407 | 2.305 |
| slots-deferred-lfu-4 | story | 51.302 | 97.855 | 0.358 | 2.290 |
| slots-deferred-lfu-4 | long-context | 48.364 | 550.209 | 4.235 | 2.618 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
