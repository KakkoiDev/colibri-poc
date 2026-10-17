# Extended experiment measurements

OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.
Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.
Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.

| Variant | Decode tok/s | Paired ratio | TTFT s | Load s | Load + first token s | Startup GPU GB | Worst request GPU GB | Requested bytes/output token | Exact tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 197.9477 | 1.0000 | 0.0481 | 0.2729 | 0.3449 | 4.1104 | 4.6441 | None | True |
| allocator-256mb | 197.6177 | 0.9939 | 0.0482 | 0.2744 | 0.3465 | 4.1104 | 4.6441 | None | True |
| allocator-off | 194.7501 | 0.9902 | 0.0488 | 0.2932 | 0.3617 | 4.1159 | 4.6441 | None | True |
| group-0 | 190.9658 | 0.9647 | 0.0481 | 0.2763 | 0.3502 | 4.1104 | 4.6441 | None | True |
| group-128 | 198.3754 | 0.9977 | 0.0482 | 0.2738 | 0.3464 | 4.1104 | 4.6441 | None | True |
| group-256 | 197.1880 | 0.9986 | 0.0477 | 0.2776 | 0.3782 | 4.1104 | 4.6441 | None | True |
| group-32 | 198.4883 | 0.9986 | 0.0476 | 0.2723 | 0.3445 | 4.1104 | 4.6441 | None | True |
| resident-compiled-fused | 199.6504 | 1.0086 | 0.0467 | 0.2709 | 0.4799 | 4.1104 | 4.7365 | None | True |
| resident-compiled | 198.1495 | 0.9981 | 0.0488 | 0.2712 | 0.3509 | 4.1104 | 4.6441 | None | True |
| resident-fused | 195.5503 | 0.9938 | 0.0488 | 0.2750 | 0.4292 | 4.1187 | 4.7365 | None | True |
