# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 201.0030523413969 | 1.0 | True | 0 |
| prefill-1024 | 200.7086476671779 | 0.9998032728573708 | False | 0 |
| prefill-256 | 200.90141419638317 | 0.9994943452657569 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
