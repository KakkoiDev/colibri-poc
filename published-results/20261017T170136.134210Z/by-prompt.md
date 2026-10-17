# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 194.301 | 543.729 | 0.057 | 3.965 |
| baseline | code | 196.399 | 745.209 | 0.045 | 3.967 |
| baseline | reason | 195.492 | 890.588 | 0.049 | 4.003 |
| baseline | story | 196.638 | 752.264 | 0.047 | 3.988 |
| baseline | long-context | 141.065 | 4496.935 | 0.520 | 4.644 |
| stream-packed-64 | explain | 70.484 | 253.460 | 0.123 | 3.965 |
| stream-packed-64 | code | 76.459 | 258.267 | 0.128 | 3.980 |
| stream-packed-64 | reason | 86.385 | 353.434 | 0.122 | 4.073 |
| stream-packed-64 | story | 119.866 | 302.865 | 0.116 | 4.124 |
| stream-packed-64 | long-context | 142.278 | 4182.043 | 0.559 | 4.644 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
