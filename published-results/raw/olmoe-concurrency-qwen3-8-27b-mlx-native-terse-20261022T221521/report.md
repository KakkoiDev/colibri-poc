# qwen3.8:27b-mlx concurrency (terse, 4096 tokens max)

| Requests at once | Total tok/s | Per request tok/s | p50 latency s | p95 latency s | Peak server memory GB | Same as single | Correct |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 20.8 | 20.81 | 2.788 | 2.788 | 19.03 | 1/1 | 1/1 |
| 4 | 21.49 | 11.34 | 5.36 | 10.791 | 19.03 | 4/4 | 4/4 |

Median over repeats. total_tok_s = generated tokens of all requests / wall time of the level. Each client sends every prompt once, in a rotated order; one warm-up request discarded. Connections reset before a request started (server backlog of 5) are retried and counted; latency is the successful attempt.

Existing Ollama settings; no parallelism reconfiguration. One model at a time. Native keeps model default thinking with temperature zero. Footprint sums daemon and descendants; shared pages may be counted more than once. Requests in flight are not proof of GPU batching.
