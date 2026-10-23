# gemma4:26b concurrency (terse, 4096 tokens max)

| Requests at once | Total tok/s | Per request tok/s | p50 latency s | p95 latency s | Peak server memory GB | Same as single | Correct |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 71.87 | 70.07 | 3.071 | 23.874 | 24.03 | 21/24, 22/24, 22/24 | 23/24, 23/24, 23/24 |
| 4 | 72.96 | 18.73 | 28.438 | 76.516 | 24.03 | 88/96, 88/96, 88/96 | 92/96, 92/96, 92/96 |
| 10 | 73.31 | 7.99 | 82.6 | 132.57 | 24.03 | 219/240, 220/240, 220/240 | 226/240, 226/240, 226/240 |

Median over repeats. total_tok_s = generated tokens of all requests / wall time of the level. Each client sends every prompt once, in a rotated order; one warm-up request discarded. Connections reset before a request started (server backlog of 5) are retried and counted; latency is the successful attempt.

Existing Ollama settings; no parallelism reconfiguration. One model at a time. Native keeps model default thinking with temperature zero. Footprint sums daemon and descendants; shared pages may be counted more than once. Requests in flight are not proof of GPU batching.
