# Parallel requests to one model

In Run benchmarks, choose an installed Ollama model and the **Parallel 1/4/10**
column. The normal/terse selector applies. It queues one model at a time through
the usual benchmark lock. Each of 1/4/10 clients sends all 24 graded questions,
with three repetitions and a discarded warm-up. Default thinking is retained,
temperature is zero, context is 4096 and output budget is 4096. No Ollama settings
are changed. The server can queue requests internally: more HTTP clients alone
is not proof of GPU batching.

CLI: `.venv/bin/python model_concurrency.py --model qwen3.8:27b-mlx`

Optional: `--style normal`, `--profile direct` (thinking off, 128 output tokens),
`--levels 1,4,10`, `--repeats 3`. Results are under results/olmoe-concurrency-*
(the shared harness retains its old folder prefix). Raw answers, truncation,
model digest and format, exact settings, per-level throughput and correctness
are saved. Total tokens/s includes prompt work, queues and client grading time;
mean decode tokens/s is separately recorded from server generation telemetry.
The server footprint sums daemon and descendants; shared pages can be counted
more than once. It is not a measurement of expert cache size.

A campaign refuses to begin if any model is already loaded, avoiding interference
with other work. It loads only an installed model, never downloads, and unloads
only its own model afterward. A failed campaign preserves failure.json and raw
requests already saved. Reports publish after a completed dashboard job.
