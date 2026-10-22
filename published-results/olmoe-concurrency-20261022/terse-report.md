# OLMoE concurrency (terse, 128 tokens max)

| Requests at once | Total tok/s | Per request tok/s | p50 latency s | p95 latency s | Peak server memory GB | Same as single | Correct |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 147.28 | 119.58 | 0.236 | 0.722 | 3.95 | 24/24, 24/24, 24/24 | 12/24, 12/24, 12/24 |
| 4 | 204.58 | 44.76 | 0.682 | 1.858 | 4.58 | 89/96, 90/96, 90/96 | 49/96, 49/96, 48/96 |
| 10 | 278.34 | 22.4 | 1.244 | 3.753 | 6.09 | 223/240, 224/240, 222/240 | 122/240, 122/240, 124/240 |

Median over repeats. total_tok_s = generated tokens of all requests / wall time of the level. Each client sends every prompt once, in a rotated order; one warm-up request discarded. Connections reset before a request started (server backlog of 5) are retried and counted; latency is the successful attempt.
