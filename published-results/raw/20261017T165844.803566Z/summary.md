# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 198.99561626649623 | 1.0 | True | 0 |
| stream-lru-8 | 28.380654194035124 | 0.14512548586543955 | False | 0 |
| stream-lru-32 | 48.57529542734005 | 0.25027556217938784 | False | 0 |
| stream-lfu-32 | 48.083956077915175 | 0.24933279403374298 | False | 0 |
| stream-lru-64 | 69.53033258748263 | 0.34955674833373135 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
