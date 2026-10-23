# Quiet-machine GLM rerun 20261021T174236Z

Free RAM before/after: 27.2 / 26.5 GB (busy runs: 10-17.5 GB). Swap used before: 521.62 MB. Processes: 449. Repeats: 2.

| Case | Busy tok/s | Quiet tok/s (each repeat) | Quiet mean | Change | Same text as busy |
|---|---:|---|---:|---:|---|
| exact-sky-24 | 0.43 | 0.42, 0.42 | 0.42 | -2% | 2/2 |
| skip030-sky-48 | 0.91 | 0.88, 0.87 | 0.88 | -4% | 2/2 |
| skip050-sky-48 | 1.57 | 1.57, 1.56 | 1.56 | -0% | 2/2 |
| exact-code-48 | 0.42 | 0.40, 0.40 | 0.40 | -5% | 2/2 |
| skip050-code-48 | 1.46 | 1.47, 1.47 | 1.47 | +1% | 2/2 |
| exact-sky-24-t12 | 0.44 | 0.41, 0.40 | 0.41 | -8% | 2/2 |
| skip050-sky-48-t12 | 1.91 | 1.91, 1.91 | 1.91 | +0% | 2/2 |

| RAM budget GB | tok/s | Expert hit rate % | Result |
|---:|---:|---:|---|
| 22 | 0.42 | 2.8 | ok |
| 26 | 0.42 | 3.6 | ok |
