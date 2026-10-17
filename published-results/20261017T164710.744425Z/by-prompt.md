# Per-prompt results

3 rounds; up to 128 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 198.205 | 556.107 | 0.056 | 3.965 |
| baseline | code | 190.719 | 756.562 | 0.044 | 3.967 |
| baseline | reason | 195.145 | 881.212 | 0.049 | 4.003 |
| baseline | story | 197.359 | 758.111 | 0.046 | 3.988 |
| baseline | long-context | 141.355 | 4452.042 | 0.525 | 4.644 |
| kv-8bit | explain | 194.823 | 545.387 | 0.057 | 3.979 |
| kv-8bit | code | 192.056 | 733.547 | 0.045 | 3.981 |
| kv-8bit | reason | 192.716 | 842.596 | 0.051 | 4.011 |
| kv-8bit | story | 194.993 | 726.455 | 0.048 | 3.997 |
| kv-8bit | long-context | 160.643 | 4086.569 | 0.572 | 4.589 |
| kv-4bit | explain | 193.698 | 543.939 | 0.057 | 3.972 |
| kv-4bit | code | 196.088 | 744.144 | 0.045 | 3.974 |
| kv-4bit | reason | 195.491 | 878.198 | 0.049 | 4.006 |
| kv-4bit | story | 195.729 | 735.099 | 0.048 | 3.992 |
| kv-4bit | long-context | 172.785 | 4107.697 | 0.569 | 4.502 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
