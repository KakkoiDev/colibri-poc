# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 201.393 | 566.316 | 0.055 | 3.965 |
| baseline | code | 200.850 | 789.221 | 0.042 | 3.967 |
| baseline | reason | 201.003 | 919.191 | 0.047 | 4.003 |
| baseline | story | 201.097 | 780.957 | 0.045 | 3.988 |
| baseline | long-context | 145.187 | 4621.078 | 0.506 | 4.644 |
| prefill-1024 | explain | 201.871 | 565.674 | 0.055 | 3.965 |
| prefill-1024 | code | 200.709 | 787.307 | 0.042 | 3.967 |
| prefill-1024 | reason | 200.580 | 926.757 | 0.047 | 4.003 |
| prefill-1024 | story | 201.122 | 779.643 | 0.045 | 3.988 |
| prefill-1024 | long-context | 145.393 | 5146.935 | 0.454 | 4.644 |
| prefill-256 | explain | 202.085 | 569.358 | 0.055 | 3.965 |
| prefill-256 | code | 201.223 | 787.826 | 0.042 | 3.967 |
| prefill-256 | reason | 200.901 | 931.851 | 0.046 | 4.003 |
| prefill-256 | story | 200.452 | 783.263 | 0.045 | 3.988 |
| prefill-256 | long-context | 145.398 | 3496.268 | 0.668 | 4.580 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
