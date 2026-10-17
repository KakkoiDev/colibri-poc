# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 191.40672280404954 | 1.0 | True | 0 |
| resident-fused | 194.2230036663093 | 1.0089513225173181 | True | 0 |
| resident-compiled | 192.46571284621817 | 1.005532669002712 | True | 0 |
| resident-compiled-fused | 192.3925408579791 | 1.0083315004432019 | True | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
