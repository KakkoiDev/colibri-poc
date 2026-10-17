# Working in this lab

Keep explanations simple and maintain the Mermaid learning guides in docs/.
Preserve baseline behavior. Put code experiments in pocs/ and register explicit
variants. Never silently change model weights, tokenizer, precision or routing.

Run campaigns serially; keep raw logs, failures, exact settings and output tokens.
Do not call OS-cache-warm runs cold SSD benchmarks. Check output/quality before
claiming a speed win. Clearly distinguish implemented PoCs from research ideas.

Default experiment model: OLMoE-1B-7B-0125-Instruct MLX 4-bit (~3.89 GB).
Do not substitute a much larger model just because it fits the Mac.
The user's GLM-5.3 speed of 0.1 token/s is user-reported context, not a lab result.

Use .venv/bin/python, run make test after runner changes, and run a real smoke
benchmark after model/runtime changes. Do not modify the user's running GLM or
Ollama configuration as part of lab setup. Downloads and results stay out of Git.
