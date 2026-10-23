# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 67.07489044972107 | 1.0 | True | 0 |
| prefill-1024 | 50.55501958528299 | 0.9524561250551575 | False | 0 |
| prefill-256 | 64.60334717813228 | 0.9119663923462746 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
