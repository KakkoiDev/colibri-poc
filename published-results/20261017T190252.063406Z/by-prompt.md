# Per-prompt results

3 rounds; up to 256 output tokens. Medians below exclude warmup.
OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.

| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |
|---|---|---:|---:|---:|---:|
| baseline | explain | 193.455 | 549.775 | 0.057 | 3.994 |
| baseline | code | 191.687 | 745.812 | 0.045 | 3.994 |
| baseline | reason | 192.234 | 870.993 | 0.050 | 4.003 |
| baseline | story | 189.587 | 730.240 | 0.048 | 3.994 |
| baseline | long-context | 138.746 | 4400.153 | 0.531 | 4.644 |
| resident-fused | explain | 194.223 | 553.802 | 0.056 | 4.007 |
| resident-fused | code | 194.467 | 771.667 | 0.043 | 4.007 |
| resident-fused | reason | 193.940 | 910.593 | 0.048 | 4.007 |
| resident-fused | story | 195.652 | 762.636 | 0.046 | 4.007 |
| resident-fused | long-context | 140.650 | 4477.812 | 0.522 | 4.737 |
| resident-compiled | explain | 193.851 | 556.568 | 0.056 | 3.994 |
| resident-compiled | code | 192.450 | 738.484 | 0.045 | 3.994 |
| resident-compiled | reason | 192.466 | 861.294 | 0.050 | 4.003 |
| resident-compiled | story | 193.570 | 733.575 | 0.048 | 3.994 |
| resident-compiled | long-context | 139.151 | 4495.879 | 0.520 | 4.644 |
| resident-compiled-fused | explain | 191.804 | 549.476 | 0.057 | 4.007 |
| resident-compiled-fused | code | 193.151 | 759.051 | 0.044 | 4.007 |
| resident-compiled-fused | reason | 193.600 | 892.269 | 0.049 | 4.007 |
| resident-compiled-fused | story | 193.663 | 753.567 | 0.047 | 4.007 |
| resident-compiled-fused | long-context | 139.617 | 4443.488 | 0.526 | 4.737 |

See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.
Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.
