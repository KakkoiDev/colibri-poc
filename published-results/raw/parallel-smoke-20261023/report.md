# Parallel generation smoke test — 2026-10-23

Busy everyday 32 GiB Apple M6. Isolated Ollama 0.40.7 endpoint; owner server configuration unchanged. Existing campaign paused and its lab-owned PID stopped. Queue remains paused, with four pending jobs preserved.

Two 128-token streamed requests with thinking disabled: Gemma 26B, Gemma 26B MLX and Qwen 27B MLX serialized despite OLLAMA_NUM_PARALLEL=4. GPT-OSS 20B produced overlapping token streams on llama.cpp. This is a backend result, not proof that Gemma/Qwen cannot batch in another engine.

GPT-OSS capacity: one shared model, 16 configured slots, 2048-token context capacity per slot; short ~79-token prompts and 128 generated tokens. Peak overlapping streams inferred from first/last streamed content times. This proves concurrent progress, not literal simultaneous GPU kernels. No correctness benchmark performed. Outputs intentionally reached the requested token cap.

| Clients | Overlapping streams | Total tokens/s | Wall seconds |
|---:|---:|---:|---:|
| 1 | 1 | 36.55 | 3.50 |
| 2 | 2 | 58.73 | 4.36 |
| 4 | 4 | 83.15 | 6.16 |
| 8 | 8 | 110.91 | 9.23 |
| 16 | 16 | 129.98 | 15.76 |

Swap stayed at 1537.06 MiB throughout capacity levels; pre-existing swap is not zero. Engine allocation log projects 13728 MiB GPU memory (12036 model + 1248 context + 443 compute) plus host allocations. This is allocator telemetry, not measured peak system RAM. Automatic process footprint sampling missed llama-server and has been removed from results rather than reported as zero.

Conclusion: **at least 16 simultaneously generating requests fit for this bounded workload**. Maximum untested; long contexts, realistic histories and sustained quality are untested. These are 16 request slots in one server, not 16 model processes. Temporary server stopped and test model unloaded after testing.
