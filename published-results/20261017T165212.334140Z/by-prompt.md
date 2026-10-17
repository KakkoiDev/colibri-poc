# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 197.601 | 551.406 | 0.056 | 3.965 |
| baseline | code | 197.574 | 767.719 | 0.043 | 3.967 |
| baseline | reason | 197.114 | 901.249 | 0.048 | 4.003 |
| baseline | story | 197.243 | 759.224 | 0.046 | 3.988 |
| baseline | long-context | 142.187 | 4516.471 | 0.518 | 4.644 |
| fused-gate-up-compact | explain | 199.614 | 560.804 | 0.056 | 3.988 |
| fused-gate-up-compact | code | 199.848 | 791.766 | 0.042 | 3.992 |
| fused-gate-up-compact | reason | 198.831 | 937.877 | 0.046 | 4.007 |
| fused-gate-up-compact | story | 199.004 | 778.587 | 0.045 | 3.992 |
| fused-gate-up-compact | long-context | 143.906 | 4475.710 | 0.522 | 4.737 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
