# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 189.33322972071417 | 1.0 | True | 0 |
| stream-lru-32 | 44.28061194594355 | 0.2450596061642936 | False | 0 |
| slots-packed-grouped | 41.450344309069536 | 0.23954420756214687 | False | 0 |
| slots-lfu | 39.16009998827115 | 0.24172220503870542 | False | 0 |
| slots-deferred-packed | 48.09922869676682 | 0.26930012834941147 | False | 0 |
| slots-unequal-packed | 43.83599549960932 | 0.2378047870711086 | False | 0 |
| slots-deferred-lfu-4 | 58.1622578179724 | 0.3360449463089915 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
