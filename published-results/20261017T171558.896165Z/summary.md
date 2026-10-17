# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 202.84934386102768 | 1.0 | True | 0 |
| stream-lru-32 | 47.76468859894109 | 0.2397819391787117 | True | 0 |
| compact-packed-grouped | 41.646475043366216 | 0.20572780605688645 | False | 0 |
| slots-capacity-16 | 28.514663435216193 | 0.14217469871049954 | False | 0 |
| slots-capacity-48 | 68.62520613298375 | 0.3428923911576722 | False | 0 |
| slots-capacity-8 | 23.725791283807197 | 0.11793699783450043 | False | 0 |
| slots-eager-original | 45.09675863731381 | 0.22737425338579692 | False | 0 |
| slots-hybrid | 51.106387676210545 | 0.27904141119675574 | False | 0 |
| slots-lazy-original | 45.56863289085922 | 0.22679931911887558 | False | 0 |
| slots-lfu | 51.15239697479598 | 0.277351506601622 | False | 0 |
| slots-packed-grouped | 46.11256402644046 | 0.23049588785150404 | False | 0 |
| slots-packed-separate | 45.19075635539351 | 0.22924083618749036 | False | 0 |
| slots-prefetch | 46.211517293554046 | 0.230503700689001 | False | 0 |
| slots-workers-2 | 48.16500649301848 | 0.23946817461157738 | False | 0 |
| slots-workers-4 | 48.46322019987425 | 0.2400276107436003 | False | 0 |
| slots-workers-8 | 48.45869841315277 | 0.2398077913030292 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
