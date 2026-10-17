# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 196.689 | 557.889 | 0.056 | 3.965 |
| baseline | code | 197.280 | 753.842 | 0.044 | 3.967 |
| baseline | reason | 197.260 | 906.696 | 0.048 | 4.003 |
| baseline | story | 197.320 | 761.391 | 0.046 | 3.988 |
| baseline | long-context | 141.866 | 4522.670 | 0.517 | 4.644 |
| sort-always | explain | 191.185 | 553.264 | 0.056 | 3.965 |
| sort-always | code | 191.491 | 760.925 | 0.044 | 3.967 |
| sort-always | reason | 191.117 | 896.699 | 0.048 | 4.003 |
| sort-always | story | 189.635 | 753.494 | 0.047 | 3.988 |
| sort-always | long-context | 138.696 | 4480.712 | 0.522 | 4.644 |
| sort-never | explain | 197.108 | 354.599 | 0.088 | 3.951 |
| sort-never | code | 193.938 | 352.883 | 0.094 | 3.952 |
| sort-never | reason | 196.639 | 353.286 | 0.122 | 4.007 |
| sort-never | story | 196.972 | 336.008 | 0.104 | 3.989 |
| sort-never | long-context | 142.588 | 395.120 | 5.896 | 4.592 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
