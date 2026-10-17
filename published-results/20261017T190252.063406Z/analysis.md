# Extended experiment measurements

OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.
Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.
Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.

| Variant | Decode tok/s | Paired ratio | TTFT s | Load s | Load + first token s | Startup GPU GB | Worst request GPU GB | Requested bytes/output token | Exact tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 191.4067 | 1.0000 | 0.0501 | 0.2879 | 0.3610 | 4.1104 | 4.6441 | None | True |
| resident-fused | 194.2230 | 1.0090 | 0.0475 | 0.2842 | 0.4594 | 4.1104 | 4.7365 | None | True |
| resident-compiled | 192.4657 | 1.0055 | 0.0503 | 0.2861 | 0.3601 | 4.1104 | 4.6441 | None | True |
| resident-compiled-fused | 192.3925 | 1.0083 | 0.0490 | 0.2892 | 0.4429 | 4.1104 | 4.7365 | None | True |
