# Working in this lab

**Mission:** GLM-5.x on the owner's 32 GB Apple M6 at 5 tok/s or more, with usable
answers. Multi-year. Read docs/00-lab-guide.md first; it has the bottleneck model,
the experiment workflow (`glm_lab.py try` / `log`) and the research routine.

GLM rules:
- Every experiment gets an entry in experiments/glm-experiments.json, including ideas
  not run (with the reason). Rebuild with `glm_lab.py log`; never retype numbers.
- One GPU job at a time (.bench.lock). Stop running jobs by PID only.
- Test runs must not change the owner's Colibri state: USAGE_SAVE=0 KVSAVE=0
  --no-tune-profile. Never rebuild or reconfigure the owner's installed engine
  without asking.
- Label lossy results "changes output"; check quality before calling them usable.
- State that runs were on a busy machine unless made with glm_quiet.py.
- Record reviewed research in research/watchlist.md.

Keep explanations simple and maintain the Mermaid learning guides in docs/.
Preserve baseline behavior. Put code experiments in pocs/ and register explicit
variants. Never silently change model weights, tokenizer, precision or routing.

Run campaigns serially; keep raw logs, failures, exact settings and output tokens.
Do not call OS-cache-warm runs cold SSD benchmarks. Check output/quality before
claiming a speed win. Clearly distinguish implemented PoCs from research ideas.

Default experiment model: OLMoE-1B-7B-0125-Instruct MLX 4-bit (~3.89 GB).
Do not substitute a much larger model just because it fits the Mac.
The user-reported GLM-5.3 start (0.1 tok/s) is re-measured by glm_quiet.py's original-engine runs.

Use .venv/bin/python, run make test after runner changes, and run a real smoke
benchmark after model/runtime changes. Do not modify the user's running GLM or
Ollama configuration as part of lab setup. Downloads and raw local results stay out of Git. User-authorized, reviewed
archives belong in published-results/ with local home paths removed.
