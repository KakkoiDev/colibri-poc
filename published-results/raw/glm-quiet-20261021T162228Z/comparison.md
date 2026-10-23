# Quiet-machine GLM rerun 20261021T162228Z

Free RAM before/after: 28.3 / 28.0 GB (busy runs: 10-17.5 GB). Swap used before: 1169.44 MB. Processes: 568. Repeats: 2.

| Case | Busy tok/s | Quiet tok/s (each repeat) | Quiet mean | Change | Same text as busy |
|---|---:|---|---:|---:|---|
| exact-sky-24 | 0.43 | 0.41, 0.42 | 0.41 | -3% | 2/2 |
| skip030-sky-48 | 0.91 | 0.86, 0.88 | 0.87 | -4% | 2/2 |
| skip050-sky-48 | 1.57 | 1.55, 1.56 | 1.56 | -1% | 2/2 |
| exact-code-48 | 0.42 | 0.40, 0.40 | 0.40 | -5% | 2/2 |
| skip050-code-48 | 1.46 | 1.46, 1.46 | 1.46 | +0% | 2/2 |
| exact-sky-24-t12 | 0.44 | 0.41, 0.40 | 0.41 | -8% | 2/2 |
| skip050-sky-48-t12 | 1.91 | 1.90, 1.90 | 1.90 | -1% | 2/2 |

## Original engine (the user-reported 0.10 tok/s start)

| Run | RAM / context | tok/s | Prompt reading s | Result |
|---|---|---:|---:|---|
| original-defaults | automatic (24.3 GB) / default | 0.06 | 273.08 | ok |
| original-r18-c1k | 18 GB / 1024 | 0.07 | 267.92 | ok |
