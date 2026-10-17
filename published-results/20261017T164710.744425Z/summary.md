# Benchmark results

OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.

| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |
|---|---:|---:|---|---:|
| baseline | 190.71889360727607 | 1.0 | True | 0 |
| kv-8bit | 192.71569801988144 | 0.9956777946867055 | False | 0 |
| kv-4bit | 195.2425021548153 | 1.0256570383813237 | False | 0 |

Output mismatches need quality investigation; they are not automatically a quality regression.
Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.
