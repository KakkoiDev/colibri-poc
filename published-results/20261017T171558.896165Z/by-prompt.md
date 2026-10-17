# Per-prompt results

2 rounds; up to 32 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 203.168 | 561.346 | 0.055 | 3.965 |
| baseline | code | 204.242 | 762.430 | 0.044 | 3.967 |
| baseline | reason | 203.631 | 901.263 | 0.048 | 4.003 |
| baseline | story | 203.393 | 754.654 | 0.047 | 3.988 |
| baseline | long-context | 148.220 | 4540.198 | 0.515 | 4.644 |
| stream-lru-32 | explain | 46.638 | 97.150 | 0.320 | 2.391 |
| stream-lru-32 | code | 51.530 | 103.637 | 0.319 | 2.398 |
| stream-lru-32 | reason | 48.692 | 126.652 | 0.340 | 2.428 |
| stream-lru-32 | story | 47.965 | 100.671 | 0.348 | 2.413 |
| stream-lru-32 | long-context | 43.849 | 1261.549 | 1.849 | 2.770 |
| compact-packed-grouped | explain | 40.803 | 89.735 | 0.346 | 2.230 |
| compact-packed-grouped | code | 43.078 | 96.484 | 0.343 | 2.231 |
| compact-packed-grouped | reason | 42.174 | 112.193 | 0.384 | 2.231 |
| compact-packed-grouped | story | 41.672 | 93.692 | 0.374 | 2.231 |
| compact-packed-grouped | long-context | 36.892 | 557.686 | 4.178 | 2.557 |
| slots-capacity-16 | explain | 28.211 | 64.180 | 0.483 | 1.323 |
| slots-capacity-16 | code | 33.177 | 66.812 | 0.496 | 1.324 |
| slots-capacity-16 | reason | 28.881 | 81.016 | 0.531 | 1.324 |
| slots-capacity-16 | story | 28.455 | 67.924 | 0.516 | 1.324 |
| slots-capacity-16 | long-context | 24.815 | 487.020 | 4.784 | 1.642 |
| slots-capacity-48 | explain | 69.420 | 153.748 | 0.202 | 3.103 |
| slots-capacity-48 | code | 72.243 | 166.996 | 0.198 | 3.106 |
| slots-capacity-48 | reason | 69.109 | 167.983 | 0.256 | 3.113 |
| slots-capacity-48 | story | 68.014 | 141.003 | 0.248 | 3.105 |
| slots-capacity-48 | long-context | 58.143 | 673.085 | 3.462 | 3.421 |
| slots-capacity-8 | explain | 23.329 | 57.585 | 0.539 | 0.814 |
| slots-capacity-8 | code | 26.268 | 63.204 | 0.522 | 0.814 |
| slots-capacity-8 | reason | 24.016 | 73.826 | 0.583 | 0.815 |
| slots-capacity-8 | story | 23.726 | 62.747 | 0.558 | 0.814 |
| slots-capacity-8 | long-context | 19.728 | 462.086 | 5.042 | 1.135 |
| slots-eager-original | explain | 43.305 | 77.674 | 0.400 | 2.279 |
| slots-eager-original | code | 49.973 | 86.480 | 0.382 | 2.283 |
| slots-eager-original | reason | 46.300 | 98.173 | 0.438 | 2.304 |
| slots-eager-original | story | 45.097 | 81.101 | 0.432 | 2.289 |
| slots-eager-original | long-context | 38.382 | 520.653 | 4.475 | 2.626 |
| slots-hybrid | explain | 57.004 | 84.874 | 0.365 | 2.279 |
| slots-hybrid | code | 57.291 | 89.671 | 0.368 | 2.283 |
| slots-hybrid | reason | 51.106 | 101.916 | 0.422 | 2.304 |
| slots-hybrid | story | 43.468 | 84.493 | 0.415 | 2.289 |
| slots-hybrid | long-context | 41.580 | 525.720 | 4.432 | 2.626 |
| slots-lazy-original | explain | 43.231 | 78.851 | 0.394 | 2.279 |
| slots-lazy-original | code | 49.440 | 86.036 | 0.384 | 2.283 |
| slots-lazy-original | reason | 46.183 | 99.155 | 0.434 | 2.304 |
| slots-lazy-original | story | 45.569 | 81.418 | 0.430 | 2.289 |
| slots-lazy-original | long-context | 38.201 | 520.322 | 4.478 | 2.626 |
| slots-lfu | explain | 57.138 | 85.271 | 0.364 | 2.279 |
| slots-lfu | code | 57.491 | 90.234 | 0.366 | 2.290 |
| slots-lfu | reason | 51.152 | 103.284 | 0.417 | 2.304 |
| slots-lfu | story | 42.887 | 85.211 | 0.411 | 2.297 |
| slots-lfu | long-context | 41.115 | 528.558 | 4.408 | 2.626 |
| slots-packed-grouped | explain | 44.510 | 82.323 | 0.377 | 2.279 |
| slots-packed-grouped | code | 50.560 | 88.360 | 0.374 | 2.283 |
| slots-packed-grouped | reason | 46.936 | 103.119 | 0.417 | 2.304 |
| slots-packed-grouped | story | 46.113 | 83.394 | 0.420 | 2.289 |
| slots-packed-grouped | long-context | 39.072 | 526.299 | 4.427 | 2.626 |
| slots-packed-separate | explain | 44.338 | 81.341 | 0.381 | 2.279 |
| slots-packed-separate | code | 50.556 | 85.733 | 0.385 | 2.283 |
| slots-packed-separate | reason | 45.501 | 101.266 | 0.425 | 2.304 |
| slots-packed-separate | story | 45.920 | 82.769 | 0.423 | 2.289 |
| slots-packed-separate | long-context | 38.954 | 523.559 | 4.450 | 2.626 |
| slots-prefetch | explain | 44.224 | 89.076 | 0.348 | 2.279 |
| slots-prefetch | code | 50.148 | 95.578 | 0.346 | 2.283 |
| slots-prefetch | reason | 46.937 | 110.461 | 0.390 | 2.304 |
| slots-prefetch | story | 46.212 | 93.151 | 0.376 | 2.289 |
| slots-prefetch | long-context | 39.348 | 547.700 | 4.254 | 2.626 |
| slots-workers-2 | explain | 46.013 | 87.930 | 0.353 | 2.279 |
| slots-workers-2 | code | 51.994 | 96.870 | 0.341 | 2.283 |
| slots-workers-2 | reason | 48.763 | 110.308 | 0.390 | 2.304 |
| slots-workers-2 | story | 48.165 | 90.520 | 0.387 | 2.289 |
| slots-workers-2 | long-context | 40.550 | 545.708 | 4.270 | 2.626 |
| slots-workers-4 | explain | 46.550 | 91.133 | 0.340 | 2.279 |
| slots-workers-4 | code | 52.444 | 98.761 | 0.334 | 2.283 |
| slots-workers-4 | reason | 48.877 | 112.048 | 0.384 | 2.304 |
| slots-workers-4 | story | 48.463 | 93.978 | 0.373 | 2.289 |
| slots-workers-4 | long-context | 40.616 | 547.424 | 4.256 | 2.626 |
| slots-workers-8 | explain | 46.320 | 91.210 | 0.340 | 2.279 |
| slots-workers-8 | code | 52.590 | 98.573 | 0.335 | 2.283 |
| slots-workers-8 | reason | 48.719 | 110.813 | 0.388 | 2.304 |
| slots-workers-8 | story | 48.521 | 93.105 | 0.376 | 2.289 |
| slots-workers-8 | long-context | 40.586 | 547.970 | 4.252 | 2.626 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
