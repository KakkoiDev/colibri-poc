# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 196.71134742085786 | 1.0 | True | 0 |
| sort-always | 189.68577408961332 | 0.9716510162621345 | True | 0 |
| sort-never | 196.59003314302612 | 0.9974669352808773 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
