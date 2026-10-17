# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 204.316831556691 | 1.0 | True | 0 |
| stream-lru-32 | 47.84455302330067 | 0.23748657471907017 | True | 0 |
| slots-deferred-packed | 54.96504715969133 | 0.2778947637844398 | False | 0 |
| compact-deferred-packed | 47.63540456785429 | 0.23868933699405548 | False | 0 |
| slots-unequal-packed | 46.581901376948906 | 0.23503057975195182 | False | 0 |
| compact-deferred-unequal-packed | 47.13817857340091 | 0.2440112744972449 | False | 0 |
| slots-deferred-lfu-4 | 66.4830188231828 | 0.3518241120698588 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
