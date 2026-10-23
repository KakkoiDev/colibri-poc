# gemma4:26b-mlx concurrency (terse, 4096 tokens max)

| Requests at once | Total tok/s | Per request tok/s | p50 latency s | p95 latency s | Peak server memory GB | Same as single | Correct |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 49.63 | 46.89 | 4.37 | 57.767 | 27.02 | 22/24, 21/24, 20/24 | 23/24, 23/24, 21/24 |
| 4 | 46.54 | 12.11 | 35.342 | 101.24 | 27.02 | 83/96, 82/96, 86/96 | 93/96, 92/96, 93/96 |
| 10 | 46.68 | 5.26 | 114.726 | 195.914 | 27.02 | 206/240, 209/240, 210/240 | 227/240, 232/240, 231/240 |

Median over repeats. total_tok_s = generated tokens of all requests / wall time of the level. Each client sends every prompt once, in a rotated order; one warm-up request discarded. Connections reset before a request started (server backlog of 5) are retried and counted; latency is the successful attempt.

Existing Ollama settings; no parallelism reconfiguration. One model at a time. Native keeps model default thinking with temperature zero. Footprint sums daemon and descendants; shared pages may be counted more than once. Requests in flight are not proof of GPU batching.
