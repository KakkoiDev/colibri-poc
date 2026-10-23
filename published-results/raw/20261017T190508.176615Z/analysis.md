# Extended experiment measurements

OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.
Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.
Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.

| Variant | Decode tok/s | Paired ratio | TTFT s | Load s | Load + first token s | Startup GPU GB | Worst request GPU GB | Requested bytes/output token | Exact tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 189.3332 | 1.0000 | 0.0517 | 0.2914 | 0.3642 | 4.1104 | 4.6441 | None | True |
| stream-lru-32 | 44.2806 | 0.2451 | 0.3617 | 0.3312 | 0.8583 | 4.1104 | 2.7702 | 129796300.8000 | False |
| slots-packed-grouped | 41.4503 | 0.2395 | 0.5473 | 0.1162 | 0.8635 | 0.2684 | 2.6259 | 118549094.4000 | False |
| slots-lfu | 39.1601 | 0.2417 | 0.4695 | 0.1228 | 0.6689 | 0.2684 | 2.6241 | 123741388.8000 | False |
| slots-deferred-packed | 48.0992 | 0.2693 | 0.4849 | 0.1191 | 0.6994 | 0.2684 | 2.6324 | 118549094.4000 | False |
| slots-unequal-packed | 43.8360 | 0.2378 | 0.5071 | 0.1116 | 0.6738 | 0.2684 | 2.6326 | 117520588.8000 | False |
| slots-deferred-lfu-4 | 58.1623 | 0.3360 | 0.3656 | 0.1170 | 0.6295 | 0.2684 | 2.6177 | 123741388.8000 | False |
