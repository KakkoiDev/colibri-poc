# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 211.05789564744438 | 1.0 | True | 0 |
| slots-lazy-original | 42.92674550880946 | 0.20445823955188228 | False | 0 |
| slots-packed-grouped | 43.710417945641446 | 0.20980970681601968 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
