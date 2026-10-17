# Extended experiment measurements

OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.
Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.
Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.

| Variant | Decode tok/s | Paired ratio | TTFT s | Load s | Load + first token s | Startup GPU GB | Worst request GPU GB | Requested bytes/output token | Exact tokens |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 202.8493 | 1.0000 | 0.0480 | 0.2749 | 0.3473 | 4.1146 | 4.6441 | None | True |
| stream-lru-32 | 47.7647 | 0.2398 | 0.3400 | 0.2805 | 0.7428 | 4.1104 | 2.7702 | 271016755.2000 | True |
| compact-packed-grouped | 41.6465 | 0.2057 | 0.3741 | 0.1098 | 0.6417 | 0.2684 | 2.5569 | 239387443.2000 | False |
| slots-capacity-16 | 28.5147 | 0.1422 | 0.5206 | 0.1084 | 0.6656 | 0.2684 | 1.6420 | 395255808.0000 | False |
| slots-capacity-48 | 68.6252 | 0.3429 | 0.2485 | 0.1079 | 0.6332 | 0.2684 | 3.4209 | 92543385.6000 | False |
| slots-capacity-8 | 23.7258 | 0.1179 | 0.5581 | 0.1107 | 0.6848 | 0.2684 | 1.1347 | 465747148.8000 | False |
| slots-eager-original | 45.0968 | 0.2274 | 0.4319 | 0.2826 | 0.8516 | 4.1104 | 2.6259 | 239387443.2000 | False |
| slots-hybrid | 51.1064 | 0.2790 | 0.4146 | 0.1094 | 0.6485 | 0.2684 | 2.6259 | 221980262.4000 | False |
| slots-lazy-original | 45.5686 | 0.2268 | 0.4302 | 0.1086 | 0.6631 | 0.2684 | 2.6259 | 239387443.2000 | False |
| slots-lfu | 51.1524 | 0.2774 | 0.4110 | 0.1102 | 0.6487 | 0.2684 | 2.6259 | 222511104.0000 | False |
| slots-packed-grouped | 46.1126 | 0.2305 | 0.4173 | 0.1118 | 0.6498 | 0.2684 | 2.6259 | 239387443.2000 | False |
| slots-packed-separate | 45.1908 | 0.2292 | 0.4213 | 0.1093 | 0.6547 | 0.2684 | 2.6259 | 239387443.2000 | False |
| slots-prefetch | 46.2115 | 0.2305 | 0.3761 | 0.1100 | 0.6045 | 0.2684 | 2.6259 | 293046681.6000 | False |
| slots-workers-2 | 48.1650 | 0.2395 | 0.3827 | 0.1092 | 0.6111 | 0.2684 | 2.6259 | 239387443.2000 | False |
| slots-workers-4 | 48.4632 | 0.2400 | 0.3727 | 0.1103 | 0.5986 | 0.2684 | 2.6259 | 239387443.2000 | False |
| slots-workers-8 | 48.4587 | 0.2398 | 0.3762 | 0.1124 | 0.6008 | 0.2684 | 2.6259 | 239387443.2000 | False |
