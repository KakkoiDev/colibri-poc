# Extended experiment measurements

OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.
Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.
Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.

| Variant | Decode tok/s | Paired ratio | TTFT s | Load s | Load + first token s | Startup GPU GB | Worst request GPU GB | Requested bytes/output token | Exact tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 211.0579 | 1.0000 | 0.0497 | 0.2742 | 0.3471 | 4.1104 | 4.6441 | None | True |
| slots-lazy-original | 42.9267 | 0.2045 | 0.4243 | 0.1068 | 0.7437 | 0.2684 | 2.6259 | 394813440.0000 | False |
| slots-packed-grouped | 43.7104 | 0.2098 | 0.4093 | 0.1118 | 0.7556 | 0.2684 | 2.6259 | 394813440.0000 | False |
