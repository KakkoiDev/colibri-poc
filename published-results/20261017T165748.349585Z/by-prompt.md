# Per-prompt results

1 rounds; up to 32 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 204.066 | 563.397 | 0.055 | 3.965 |
| baseline | code | 205.331 | 770.702 | 0.043 | 3.967 |
| baseline | reason | 203.582 | 901.676 | 0.048 | 4.003 |
| baseline | story | 203.610 | 745.701 | 0.047 | 3.988 |
| baseline | long-context | 146.945 | 4495.265 | 0.520 | 4.644 |
| stream-lru-8 | explain | 28.283 | 81.147 | 0.382 | 1.118 |
| stream-lru-8 | code | 30.821 | 85.519 | 0.386 | 1.124 |
| stream-lru-8 | reason | 29.233 | 106.817 | 0.403 | 1.152 |
| stream-lru-8 | story | 29.027 | 86.041 | 0.407 | 1.139 |
| stream-lru-8 | long-context | 26.852 | 693.871 | 3.359 | 1.460 |
| stream-lru-32 | explain | 47.726 | 99.613 | 0.312 | 2.390 |
| stream-lru-32 | code | 52.393 | 105.183 | 0.314 | 2.398 |
| stream-lru-32 | reason | 49.954 | 129.133 | 0.333 | 2.426 |
| stream-lru-32 | story | 48.871 | 103.401 | 0.339 | 2.414 |
| stream-lru-32 | long-context | 43.878 | 726.848 | 3.206 | 2.737 |
| stream-lru-64 | explain | 71.729 | 246.291 | 0.127 | 3.816 |
| stream-lru-64 | code | 71.288 | 239.223 | 0.139 | 3.873 |
| stream-lru-64 | reason | 71.573 | 303.490 | 0.142 | 4.008 |
| stream-lru-64 | story | 71.199 | 244.219 | 0.144 | 4.093 |
| stream-lru-64 | long-context | 63.130 | 1730.778 | 1.348 | 4.464 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
