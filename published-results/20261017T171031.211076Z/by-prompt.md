# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 200.015 | 560.300 | 0.056 | 3.965 |
| baseline | code | 199.269 | 774.008 | 0.043 | 3.967 |
| baseline | reason | 197.948 | 899.020 | 0.048 | 4.003 |
| baseline | story | 197.515 | 758.721 | 0.046 | 3.988 |
| baseline | long-context | 142.866 | 4523.991 | 0.517 | 4.644 |
| allocator-256mb | explain | 197.967 | 553.469 | 0.056 | 3.965 |
| allocator-256mb | code | 197.618 | 768.098 | 0.043 | 3.967 |
| allocator-256mb | reason | 198.143 | 897.756 | 0.048 | 4.003 |
| allocator-256mb | story | 198.072 | 762.860 | 0.046 | 3.988 |
| allocator-256mb | long-context | 142.911 | 4564.377 | 0.512 | 4.644 |
| allocator-off | explain | 197.178 | 557.738 | 0.056 | 3.965 |
| allocator-off | code | 198.097 | 768.256 | 0.043 | 3.967 |
| allocator-off | reason | 194.750 | 885.260 | 0.049 | 4.003 |
| allocator-off | story | 197.143 | 746.688 | 0.047 | 3.988 |
| allocator-off | long-context | 142.329 | 4434.246 | 0.527 | 4.644 |
| group-0 | explain | 191.709 | 562.985 | 0.055 | 3.965 |
| group-0 | code | 191.615 | 768.372 | 0.043 | 3.967 |
| group-0 | reason | 190.966 | 899.012 | 0.048 | 4.003 |
| group-0 | story | 191.003 | 748.254 | 0.047 | 3.988 |
| group-0 | long-context | 140.891 | 4539.781 | 0.515 | 4.644 |
| group-128 | explain | 199.583 | 558.381 | 0.056 | 3.965 |
| group-128 | code | 199.357 | 768.196 | 0.043 | 3.967 |
| group-128 | reason | 198.493 | 897.822 | 0.048 | 4.003 |
| group-128 | story | 194.960 | 759.351 | 0.046 | 3.988 |
| group-128 | long-context | 144.224 | 4557.484 | 0.513 | 4.644 |
| group-256 | explain | 200.443 | 353.111 | 0.088 | 3.951 |
| group-256 | code | 200.007 | 773.545 | 0.043 | 3.967 |
| group-256 | reason | 196.319 | 905.518 | 0.048 | 4.003 |
| group-256 | story | 197.188 | 759.808 | 0.046 | 3.988 |
| group-256 | long-context | 142.725 | 4544.700 | 0.514 | 4.644 |
| group-32 | explain | 199.549 | 561.900 | 0.055 | 3.965 |
| group-32 | code | 198.514 | 768.474 | 0.043 | 3.967 |
| group-32 | reason | 199.164 | 908.084 | 0.048 | 4.003 |
| group-32 | story | 198.141 | 766.852 | 0.046 | 3.988 |
| group-32 | long-context | 142.957 | 4543.639 | 0.514 | 4.644 |
| resident-compiled-fused | explain | 199.148 | 561.855 | 0.055 | 3.988 |
| resident-compiled-fused | code | 201.795 | 785.195 | 0.042 | 3.992 |
| resident-compiled-fused | reason | 201.194 | 929.174 | 0.047 | 4.007 |
| resident-compiled-fused | story | 201.225 | 777.985 | 0.045 | 3.992 |
| resident-compiled-fused | long-context | 145.790 | 4488.144 | 0.521 | 4.737 |
| resident-compiled | explain | 199.619 | 561.268 | 0.055 | 3.965 |
| resident-compiled | code | 198.015 | 768.487 | 0.043 | 3.967 |
| resident-compiled | reason | 198.870 | 885.547 | 0.049 | 4.003 |
| resident-compiled | story | 199.886 | 757.604 | 0.046 | 3.988 |
| resident-compiled | long-context | 144.276 | 4557.570 | 0.513 | 4.644 |
| resident-fused | explain | 196.222 | 555.126 | 0.056 | 3.988 |
| resident-fused | code | 199.190 | 768.681 | 0.043 | 3.992 |
| resident-fused | reason | 198.561 | 914.772 | 0.047 | 4.007 |
| resident-fused | story | 195.550 | 776.569 | 0.045 | 3.992 |
| resident-fused | long-context | 144.232 | 4504.548 | 0.519 | 4.737 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
