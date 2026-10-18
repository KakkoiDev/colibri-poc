# Tonight's GLM benches: runbook (2026-10-18)

Hand this to the agent or person running tonight's session. Every command runs from the
repo root (`cd ~/Code/colibri-poc`). Background is in
[report-2026-10-18.md](report-2026-10-18.md); the method is in
[docs/00-lab-guide.md](../docs/00-lab-guide.md).

**Goal tonight:** measure every planned experiment on a quiet Mac, including the ones that
need downloads (int8 MTP head, 2-bit and 3-bit GLM-5.3 GGUFs). Optionally, take a first
look at GLM-5.3-Flash.

**Rules:**
- One GPU job at a time.
- Stop processes by PID only. Never use `pkill` with a pattern: the owner's own Colibri
  and the bench run the same binaries.
- Never rebuild or reconfigure `~/Code/colibri` and never edit `~/colibri-models/glm-5.3`.
  Everything new goes to `engines/` or to new folders under `~/colibri-models/`.
- Lossy results are never `usable: true` without the quality bench and the owner.

## 0. Pre-flight (2 min)

```sh
cd ~/Code/colibri-poc && git pull
df -h ~ | tail -1                 # need ~700 GB free for every download below (1.1 TB free at 2026-10-18)
ps -o pid,etime,command -p 33342  # quality bench v1 started this afternoon; is it still running?
.venv/bin/python glm_lab.py planned
```

If the quality bench (`glm_bench.py run --name v1`) is still running, either let it finish
or pause it by PID. It resumes later with `make glm-bench`.
```sh
kill 33342
sleep 5; pgrep -fl 'c/colibri '   # if an engine is left over, kill that PID too
```

## 1. Downloads (start first; they take the longest)

Run these while the Mac is still in normal use, **before** the quiet run: downloads load
the SSD and would distort the timings. Each step is resumable: rerun the same command if
it stops. Downloads are from public repos and need no Hugging Face token.

| Step | Command | Download | Kept on disk | Unlocks |
|---|---|---:|---:|---|
| a. int8 MTP head | `make glm-prep-mtp` | ~16 GB (3 FP8 shards, deleted after conversion) + torch in a throwaway uv env | ~10 GB | `mtp-int8`, `mtp-int8-skip050` |
| b. 3-bit GGUF (recommended) | `make glm-prep-iq3xxs` | ~282 GB | ~282 GB | `gguf-iq3xxs`, `gguf-iq3xxs-skip050` |
| c. 2-bit GGUF | `make glm-prep-iq2m` | ~239 GB | ~239 GB | `gguf-iq2m`, `gguf-iq2m-skip050` |
| d. Optional: GLM-5.3-Flash 3-bit GGUF | `make glm-prep-flash` | ~120 GB | ~120 GB | manual Flash runs (section 4) |

What each one does:
- **a.** Runs Colibri's own converter (`convert_fp8_to_int4.py --mtp --repo zai-org/GLM-5.3`)
  into `~/colibri-models/glm-5.3-mtp-head`. It then builds `~/colibri-models/glm-5.3-mtp`,
  which symlinks every glm-5.3 file plus the `out-mtp-*` files and adds a `.mtp-ready`
  marker. The original model folder is untouched. The head must be int8, the converter's
  default for `--mtp` (int4 heads give ~0% acceptance).
- **b, c, d.** Build the Colibri dev clone `engines/colibri-16239caa` (METAL=1, checks that
  libomp and Metal are linked) if it isn't there yet. Then `hf download` the quant into
  `~/colibri-models/gguf/<name>` and run `coli import` (link mode: weights are read from the
  GGUF in place) into `~/colibri-models/<name>`. Step d also builds `glm53`.

The downloads can run one after another in a single terminal:
```sh
make glm-prep-mtp && make glm-prep-iq3xxs && make glm-prep-iq2m
make glm-prep-flash   # optional
```

Check afterwards (every unlocked experiment should now show `ready`):
```sh
.venv/bin/python glm_lab.py planned
ls -l ~/colibri-models/glm-5.3-mtp-head/out-mtp-*   # int8 head is ~10 GB in total
```

If a step fails:
- **uv/torch install fails (step a):** retry with `--python 3.11` in `scripts/prep_mtp_head.sh`.
- **`coli import` refuses the file:** note the message. The dev build may need a newer
  commit; don't patch the owner's engine.
- **Disk is low:** skip c (the 2-bit file). b has better quality for a smaller speed gain.

## 2. Quiet run: all speed experiments (~1.5-2 h)

Close apps (browsers, Electron apps, IDEs, other agents' engines), then:
```sh
make glm-quiet-check
```
It must say **Ready**: no `.bench.lock` holder, no engine running, at least 20 GB free.
It also lists which planned experiments are ready.

Then:
```sh
.venv/bin/python glm_quiet.py run --ram-sweep --skip-original
```

This runs, in order:
1. The comparison set: 7 cases × 2 repeats, to re-measure the busy-machine numbers quietly.
2. The RAM sweep: exact runs at 22 and 26 GB.
3. **Every ready planned experiment.** Wins of +10% or more are repeated once automatically.

| Experiment | What it measures | Reference |
|---|---|---|
| `lookup-off` | prompt-lookup drafts off, exact, sky | `r2-p0-sky-exact` (0.44 tok/s) |
| `lookup-off-code` | same, code prompt | `r2-p0-code-exact` (0.42) |
| `stack-skip050-lookup-off` | best lossy stack + drafts off | `r2-k-sky-skip050-t12` (1.87) |
| `baseline-16239caa` | Colibri dev (builds the clone), exact | `r2-p0-sky-exact` |
| `stack-skip050-16239caa` | Colibri dev + best lossy stack | `r2-k-sky-skip050-t12` |
| `mtp-int8` / `mtp-int8-skip050` | int8 MTP head, alone / stacked | exact / lossy refs |
| `gguf-iq3xxs` / `gguf-iq3xxs-skip050` | 3-bit GGUF on Colibri dev, alone / stacked | exact / lossy refs |
| `gguf-iq2m` / `gguf-iq2m-skip050` | 2-bit GGUF, alone / stacked | exact / lossy refs |

Only the planned experiments, without the comparison set:
```sh
.venv/bin/python glm_quiet.py run --experiments-only
```
Or a single experiment:
```sh
.venv/bin/python glm_lab.py run-planned lookup-off
```

Add the original-engine runs (~20-40 min) only if there is time:
`.venv/bin/python glm_quiet.py run --skip-experiments` without `--skip-original`.

**First real use of the planned-experiment runner.** `run-planned` and the prep scripts
were written today and have only been syntax-checked and dry-listed. Watch the first
experiment. If it fails, run it alone with `glm_lab.py run-planned <id>` and read the error.
Logs go to `results/glm-raw-20261018/logs/x-<id>.log`.

## 3. Optional overnight: quality bench for the low-bit files

Speed alone doesn't make a lossy result usable. The quality bench runs 24 graded prompts
(about 2-4 h per model). Run these after section 2, one at a time:
```sh
.venv/bin/python glm_bench.py run --name iq3xxs --configs exact,d050 --styles normal \
  --model ~/colibri-models/glm-5.3-iq3xxs --coli-dir engines/colibri-16239caa
.venv/bin/python glm_bench.py run --name iq2m --configs exact,d050 --styles normal \
  --model ~/colibri-models/glm-5.3-iq2m --coli-dir engines/colibri-16239caa
```
Compare them with the int4 bench (`v1`, configs `exact` and `d050`). Resume after an
interruption with the same command.

## 4. Optional: first look at GLM-5.3-Flash (manual)

The lab tools don't handle Flash yet:
- Its engine (`glm53`) has **none of our speed settings**: no `PIPE`, `DIRECT`,
  `DEGRADE_ZERO` or thread sizing. It has `GLM53_EXPERT_GB`, `COLI_METAL` and `COLI_MODEL_MIRROR`.
- It prints speed as `decode N token in X s = Y tok/s`, which the lab parser doesn't read.

So run it by hand and keep the logs. This is a first try: settings and launcher behaviour
are unverified.
```sh
mkdir -p results/flash
USAGE_SAVE=0 KVSAVE=0 COLI_METAL=1 OMP_NUM_THREADS=12 engines/colibri-16239caa/c/coli run \
  --model ~/colibri-models/glm-5.3-flash-iq3xxs --no-tune-profile --no-think --ngen 24 --ram 18 --ctx 1024 \
  "Explain in two sentences why the sky is blue." 2>&1 | tee results/flash/iq3xxs-sky-metal.log
USAGE_SAVE=0 KVSAVE=0 OMP_NUM_THREADS=12 engines/colibri-16239caa/c/coli run \
  --model ~/colibri-models/glm-5.3-flash-iq3xxs --no-tune-profile --no-think --ngen 24 --ram 18 --ctx 1024 \
  "Explain in two sentences why the sky is blue." 2>&1 | tee results/flash/iq3xxs-sky-cpu.log
grep -E 'tok/s|MTP|accept' results/flash/*.log
```
Context: GLM-5.3-Flash has 18B active parameters vs 40B. On vendor benchmarks it is level
with or ahead of GLM-5.2, and Artificial Analysis scores it 42 vs 45 (GLM-5.3) and 34
(GLM-5.2). Whether it counts for the mission is the owner's call.

## 5. After the runs (for the agent)

1. Report the quiet run's folder (`results/glm-quiet-<stamp>`) and `comparison.md`.
2. For every experiment that ran, fill in `conclusion`, `tradeoffs` and `sources` in
   `experiments/glm-experiments.json`. Keep lossy entries `usable: false`.
3. Run `.venv/bin/python glm_lab.py log`.
4. Stacking rule: if `lookup-off`, the dev engine or MTP wins, add a new `stack-*` planned
   entry combining the winners (with a `plan`) so the next quiet run measures the combination.
5. Commit `experiments/`, `docs/12-experiment-log.md`, `site/data/experiments.json` and
   `published-results/glm-20261018/`. Check `git diff --cached | grep /Users/` is empty,
   end the message with the project's Co-Authored-By line, then `git push origin main`.
6. Flash logs: summarise tok/s by hand. Extending `glm_bench.parse_log` / `publish_glm_runs.py`
   to read glm53's `decode ... tok/s` line is the next lab task if Flash looks promising.

## Disk summary

| Item | Path | Size |
|---|---|---:|
| MTP head | `~/colibri-models/glm-5.3-mtp-head` (+ symlink folder `glm-5.3-mtp`) | ~10 GB |
| 3-bit GGUF | `~/colibri-models/gguf/glm-5.3-iq3xxs` (+ import folder) | ~282 GB |
| 2-bit GGUF | `~/colibri-models/gguf/glm-5.3-iq2m` (+ import folder) | ~239 GB |
| Flash 3-bit GGUF | `~/colibri-models/gguf/glm-5.3-flash-iq3xxs` | ~120 GB |
| Dev engine | `engines/colibri-16239caa` | <1 GB |
| **Total** | | **~650 GB** of 1.1 TB free |
