# Per-prompt results

3 rounds; up to 64 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 200.669 | 558.167 | 0.056 | 3.965 |
| baseline | code | 200.437 | 764.306 | 0.043 | 3.967 |
| baseline | reason | 197.252 | 895.329 | 0.048 | 4.003 |
| baseline | story | 198.996 | 749.151 | 0.047 | 3.988 |
| baseline | long-context | 142.211 | 4435.676 | 0.527 | 4.644 |
| stream-lru-8 | explain | 28.381 | 80.180 | 0.387 | 1.119 |
| stream-lru-8 | code | 30.513 | 84.185 | 0.392 | 1.123 |
| stream-lru-8 | reason | 28.650 | 105.604 | 0.408 | 1.152 |
| stream-lru-8 | story | 28.085 | 85.926 | 0.408 | 1.139 |
| stream-lru-8 | long-context | 25.925 | 1210.819 | 1.926 | 1.495 |
| stream-lru-32 | explain | 50.223 | 98.350 | 0.316 | 2.393 |
| stream-lru-32 | code | 51.584 | 105.745 | 0.313 | 2.398 |
| stream-lru-32 | reason | 47.581 | 125.521 | 0.343 | 2.426 |
| stream-lru-32 | story | 48.825 | 98.493 | 0.356 | 2.414 |
| stream-lru-32 | long-context | 43.436 | 1265.452 | 1.843 | 2.770 |
| stream-lfu-32 | explain | 55.480 | 124.276 | 0.250 | 2.396 |
| stream-lfu-32 | code | 49.783 | 132.679 | 0.249 | 2.405 |
| stream-lfu-32 | reason | 48.084 | 168.384 | 0.256 | 2.426 |
| stream-lfu-32 | story | 42.197 | 130.024 | 0.270 | 2.415 |
| stream-lfu-32 | long-context | 42.014 | 1655.863 | 1.409 | 2.779 |
| stream-lru-64 | explain | 70.043 | 245.545 | 0.127 | 3.905 |
| stream-lru-64 | code | 69.199 | 246.497 | 0.135 | 3.930 |
| stream-lru-64 | reason | 69.565 | 307.091 | 0.141 | 4.029 |
| stream-lru-64 | story | 69.681 | 245.770 | 0.143 | 4.100 |
| stream-lru-64 | long-context | 61.179 | 2683.008 | 0.870 | 4.499 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
