# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 203.60967114885716 | 1.0 | True | 0 |
| stream-lru-8 | 29.026520773715486 | 0.14359186037490643 | False | 0 |
| stream-lru-32 | 48.87052145997233 | 0.24537644433674236 | False | 0 |
| stream-lru-64 | 71.28754128069247 | 0.35150029969514207 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
