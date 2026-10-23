# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 188.46126360687649 | 1.0 | True | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
