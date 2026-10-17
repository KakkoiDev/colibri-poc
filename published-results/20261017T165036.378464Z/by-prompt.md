# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 195.978 | 556.752 | 0.056 | 3.965 |
| baseline | code | 197.759 | 767.018 | 0.043 | 3.967 |
| baseline | reason | 196.347 | 885.444 | 0.049 | 4.003 |
| baseline | story | 197.016 | 756.925 | 0.047 | 3.988 |
| baseline | long-context | 142.154 | 4527.985 | 0.516 | 4.644 |
| fused-gate-up | explain | 199.860 | 559.227 | 0.056 | 6.404 |
| fused-gate-up | code | 198.646 | 786.309 | 0.042 | 6.408 |
| fused-gate-up | reason | 196.867 | 920.017 | 0.047 | 6.423 |
| fused-gate-up | story | 198.779 | 777.858 | 0.045 | 6.407 |
| fused-gate-up | long-context | 143.684 | 4486.775 | 0.521 | 7.152 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
