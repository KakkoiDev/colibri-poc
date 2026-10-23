# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 36.62921549157305 | 1.0 | True | 0 |
| prefill-1024 | 37.18776075302251 | 0.9749340932518785 | False | 0 |
| prefill-256 | 37.13974088650476 | 1.000641420406473 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
