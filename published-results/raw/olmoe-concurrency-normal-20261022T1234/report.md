# OLMoE concurrency (normal, 128 tokens max)

| Requests at once | Total tok/s | Per request tok/s | p50 latency s | p95 latency s | Peak server memory GB | Same as single | Correct |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 166.5 | 166.16 | 0.759 | 0.772 | 4.17 | 24/24, 24/24, 24/24 | 17/24, 17/24, 17/24 |
| 4 | 239.81 | 61.44 | 2.016 | 2.441 | 4.61 | 76/96, 74/96, 72/96 | 68/96, 68/96, 68/96 |
| 10 | 326.34 | 33.03 | 3.69 | 4.131 | 5.71 | 176/240, 178/240, 176/240 | 170/240, 170/240, 170/240 |

Median over repeats. total_tok_s = generated tokens of all requests / wall time of the level. Each client sends every prompt once, in a rotated order; one warm-up request discarded. Connections reset before a request started (server backlog of 5) are retried and counted; latency is the successful attempt.
