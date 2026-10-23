# Extended experiment measurements

OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.
Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.
Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.

| Variant | Decode tok/s | Paired ratio | TTFT s | Load s | Load + first token s | Startup GPU GB | Worst request GPU GB | Requested bytes/output token | Exact tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 204.3168 | 1.0000 | 0.0474 | 0.2780 | 0.3509 | 4.1104 | 4.6441 | None | True |
| stream-lru-32 | 47.8446 | 0.2375 | 0.3627 | 0.2805 | 0.7471 | 4.1104 | 2.7702 | 271016755.2000 | True |
| slots-deferred-packed | 54.9650 | 0.2779 | 0.3974 | 0.1143 | 0.6171 | 0.2684 | 2.6324 | 239387443.2000 | False |
| compact-deferred-packed | 47.6354 | 0.2387 | 0.3671 | 0.1095 | 0.6347 | 0.2684 | 2.5540 | 239387443.2000 | False |
| slots-unequal-packed | 46.5819 | 0.2350 | 0.4154 | 0.1080 | 0.6537 | 0.2684 | 2.6308 | 237839155.2000 | False |
| compact-deferred-unequal-packed | 47.1382 | 0.2440 | 0.3789 | 0.1081 | 0.6482 | 0.2684 | 2.5496 | 237839155.2000 | False |
| slots-deferred-lfu-4 | 66.4830 | 0.3518 | 0.3607 | 0.1078 | 0.5673 | 0.2684 | 2.6324 | 222511104.0000 | False |
