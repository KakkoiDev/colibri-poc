# Per-prompt results

1 rounds; up to 16 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 214.470 | 565.697 | 0.055 | 3.965 |
| baseline | code | 209.828 | 775.299 | 0.043 | 3.967 |
| baseline | reason | 211.058 | 870.496 | 0.050 | 4.003 |
| baseline | story | 212.763 | 757.891 | 0.046 | 3.988 |
| baseline | long-context | 154.026 | 4526.882 | 0.516 | 4.644 |
| slots-lazy-original | explain | 42.081 | 80.073 | 0.387 | 2.279 |
| slots-lazy-original | code | 45.430 | 85.439 | 0.387 | 2.283 |
| slots-lazy-original | reason | 43.153 | 99.595 | 0.432 | 2.304 |
| slots-lazy-original | story | 42.927 | 82.539 | 0.424 | 2.289 |
| slots-lazy-original | long-context | 39.443 | 522.626 | 4.459 | 2.626 |
| slots-packed-grouped | explain | 42.552 | 82.879 | 0.374 | 2.279 |
| slots-packed-grouped | code | 46.277 | 87.338 | 0.378 | 2.290 |
| slots-packed-grouped | reason | 44.282 | 101.774 | 0.423 | 2.304 |
| slots-packed-grouped | story | 43.710 | 85.580 | 0.409 | 2.290 |
| slots-packed-grouped | long-context | 40.116 | 529.591 | 4.400 | 2.626 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
