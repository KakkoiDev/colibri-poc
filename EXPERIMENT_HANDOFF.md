## LIVE UPDATE 4 (newest, takes precedence over everything below)

All planned campaigns are FINISHED. Nothing is running. GPU idle.

- `COLIBRI_GPU_TESTS=1 make test`: 14/14 passed.
- Broad streaming screen `20261017T171558.896165Z`: 32/32 workers succeeded; published.
- Deferred/unequal screen `20261017T172211.404589Z`: 7/7 succeeded; published.
- Resident confirmation `20261017T190252.063406Z` (baseline, fused, compiled,
  compiled-fused; 3 rounds, 256 tokens): 12/12 succeeded, all tokens exact.
  Paired gains 0.6-0.9%, below run-to-run drift. Fusion costs +0.09 GB GPU and
  ~0.1 s first use. NO all-aspects resident win. Published.
- Streaming confirmation `20261017T190508.176615Z` (baseline, stream-lru-32,
  slots-packed-grouped, slots-lfu, slots-deferred-packed, slots-unequal-packed,
  slots-deferred-lfu-4; 3 rounds, 128 tokens): 21/21 succeeded. Published.
  Winner at equal 32-slot budget: `slots-deferred-lfu-4`, paired ratio 0.336 vs
  0.245 for old stream-lru-32 (~1.37x), better on every prompt and worst case,
  startup GPU 0.268 vs 4.110 GB. Unequal allocation lost again (negative result).
- Token equality: old stream-lru-32 diverges on `explain` at token 36; all fixed
  slot variants match 4/5 prompts and diverge on `long-context` at token 9
  (prefill partitioning is the suspected cause; not proven).
- Results written in docs/09 "Confirmation campaigns". Research for the next
  round is in docs/10-next-experiments.md (trace simulator with Belady bound,
  global pool + Least-Stale, logit-level divergence, real-SSD read methods
  needing user approval, next-layer prediction accuracy first).
- Remaining open ablation: deferred+4 readers without LFU; deferred+LFU with
  one reader. Not run.

---

## LIVE UPDATE 3

- Checkpoint `a77a524` includes resident/smoke public archives and the analysis tool.
- Broad streaming screen `20261017T171558.896165Z` is still active, session `31960`;
  last observed round 2 capacity variants. All first-round variants succeeded.
- Preliminary first-round tok/s (NOT final rankings): old stream32 48.4,
  fixed packed-grouped32 46.1, LFU32 51.2, hybrid32 51.1, workers4 48.6,
  prefetch32 46.3 (increased bytes), capacity48 69.8, capacity8 23.8.
- New `slots-deferred-lfu-4` combines deferred waits, LFU and 4 workers at uniform32.
- After broad screen: run expanded tests (expected 14), then deferred/unequal screen:
  `.venv/bin/python bench.py run --variants variants/baseline.json variants/stream-lru-32.json variants/streaming/slots-deferred-packed.json variants/streaming/compact-deferred-packed.json variants/streaming/slots-unequal-packed.json variants/streaming/compact-deferred-unequal-packed.json variants/streaming/slots-deferred-lfu-4.json --rounds 1 --tokens 32 --timeout 600`
- Then clean resident confirmation (baseline + fused + compiled + compiled-fused,
  three rounds, 256 tokens), and streaming finalist confirmation (at least three
  rounds, 128 tokens; include old32 and new uniform32 controls). Preserve all
  output differences. Update docs/09 and publish each completed campaign.
- `make bench-matrix`, `bench-resident`, `bench-streaming` targets added, default
  three rounds/128 tokens; preparation verifies ignored packed file. Deferred
  and unequal variants were registered after broad screen started and still pending.

---

## LIVE UPDATE 2

- Source matrix checkpoint pushed as `a62bc6c` after initial handoff `5ae9d69`.
- Streaming broad screen is `results/20261017T171558.896165Z`, process `31960`.
  Last observed round 2 descending through worker-count variants; no failures so far.
  This campaign froze pre-deferred source at start and contains 16 variants x 2 rounds.
- Resident screen and streaming smoke have extended `analysis.json` / `analysis.md`
  and sanitized public copies. New tool `analyze_campaign.py TIMESTAMP` reports
  startup, first-use and memory alongside paired throughput; read-byte deltas
  exclude warmup but include measured prefill.
- Added deferred-synchronization ablations AFTER broad screen started:
  `variants/streaming/slots-deferred-packed.json`, `compact-deferred-packed.json`.
  They have NOT run yet. Timers are enqueue-only for deferred upload/compute;
  end-to-end request timings still synchronized. Pending new GPU tests cover both.
- S6 allocation GENERATED from completed pilot worker
  `results/20261017T171558.896165Z/r1-slots-packed-grouped.json`.
  `derive_cache_allocation.py` creates `slots-unequal-packed` and
  `compact-deferred-unequal-packed` variants, with worker hash/provenance.
  Capacities: [34,37,34,32,31,29,29,29,31,33,35,31,32,32,32,31], sum 512.
  Equal retained bytes to uniform32; NOT benchmarked yet.
- New docs/09-two-track-experiments.md explains methods and preliminary findings.
- Exact next action AFTER broad screen completes: run
  `COLIBRI_GPU_TESTS=1 make test` (expanded suite now expected 14 tests), then
  short deferred/unequal screen, then three-round longer confirmation campaigns.
- Source pocs/stream_slots.py and tests changed after checkpoint, but running
  campaign uses its own frozen source; do not confuse live source with snapshots.
- No validated all-aspects resident winner. Fixed slots were slower than old
  streaming in smoke despite better bounded prefill/startup. Preserve negatives.

---

## LIVE UPDATE (takes precedence over historical notes below)

- Handoff document was pushed in commit `5ae9d69`.
- Resident screen `20261017T171031.211076Z` FINISHED: all 30 runs succeeded.
  Compiled+fused paired median ratio 1.0086, exact tokens true; other candidates
  did not beat paired baseline overall. No all-aspects win established.
- Nine real Metal tests PASSED, including new fixed-slot prefill/eviction test.
- Streaming smoke `20261017T171457.120637Z` FINISHED: all three runs succeeded.
  Lazy startup peak GPU 0.268 GB versus resident 4.110 GB. Fixed-slot decode around
  43 tok/s; tokens differed. Need final longer-output comparisons.
- Added `compact-packed-grouped` streaming variant: retains individual expert
  arrays and packs only active rows instead of updating full banks. Same per-layer
  retained-capacity limit and prefill partitions. This is an additional ablation
  because MLX indexed bank updates may copy large banks. No speed result yet.
- All streaming variants are now RUNNING as a serial broad screen:
  `.venv/bin/python bench.py run --variants variants/baseline.json variants/stream-lru-32.json variants/streaming/*.json --rounds 2 --tokens 32 --timeout 600`
  Process session `31960`. Find campaign with latest results folder / campaign.json.
  Do not overlap GPU work. Source is frozen at campaign start.
- Need add a compact-mode numerical test after this campaign (existing fixed-slot
  test does not yet exercise compact mode), generate unequal-layer variant from
  pilot, run confirmations, document/public archive and push remaining results.
- Experiment source is checkpointed with this update; weight artifacts stay ignored.

---

# Acceleration experiments: handoff for another agent

Updated during active work on 2026-10-18 JST (benchmark timestamps use UTC).

## User authorization and objectives

The user explicitly said to **run all proposed experiments now**, and previously
said to commit and push results to this public repository. Continue autonomously.
Two objectives must remain separate:

1. Improve resident OLMoE baseline across speed, first-token latency, memory,
   startup, and output correctness. A tradeoff is not an all-aspects win.
2. Reproduce partial expert loading in RAM and improve speed at a fixed memory
   budget, with eventual relevance to the user's much larger GLM-5.3 model.

Read AGENTS.md. Use `[CANARY]` in user-facing updates. Keep explanations simple,
add Mermaid diagrams, preserve baseline, retain failures and output token IDs.
Do not alter the user's GLM/Ollama configuration. Do not spawn agents unless
explicitly authorized. Run GPU campaigns and numerical GPU tests serially.

## Repository and environment

- Local: `/Users/kakkoidev/Code/colibri-poc`
- Public: https://github.com/KakkoiDev/colibri-poc
- Branch: `main`; last pushed commit before this work: `a08da39a8215760afcd2742ad134d0df5922eb0a`
- New work described below is initially UNCOMMITTED; inspect status before editing.
- Python: `.venv/bin/python` (3.12), pinned MLX/MLX-LM dependencies.
- Model: `models/olmoe-1b-7b-4bit`, original pinned MLX 4-bit OLMoE,
  64 experts/layer, 8 selected/token, 16 layers, checkpoint ~3.89 GB.
- Mac: Apple M6, 32 GB unified memory, Metal available.
- Tools may start in sibling `/Users/kakkoidev/Code/pi-local-harness`.
  Set workdir explicitly. Writes/Metal/network operations in colibri-poc have
  required `sandbox_permissions: require_escalated`; user authorized these actions.
- User's GLM speed 0.1 tok/s is reported context, NOT a measured lab result.
  GLM checkpoint ~419 GB; do not extrapolate OLMoE ratios to it.

## Current active process: CHECK BEFORE STARTING ANY GPU WORK

A resident campaign was launched with:

```sh
.venv/bin/python bench.py run --variants variants/baseline.json variants/resident/*.json --rounds 3 --tokens 128 --timeout 300
```

- Tool process session ID: `47332` (may only be usable in original session).
- Campaign: `results/20261017T171031.211076Z`
- Last observed: round 3, progressing through allocator/grouping variants.
- Inspect `campaign.json`, logs, processes and `.bench.lock` for current status.
- Never assume this historical status means it is still running.
- Do not delete the lock file to bypass its advisory lock.

No streaming GPU campaign or new GPU tests had run yet when this file was first
written. The layout preparation completed successfully (see below).

## Changes already implemented in this work

### Harness changes: bench.py

- Plugin can expose `load_options` (e.g. `{'lazy': True}`), passed to mlx_lm.load.
- Reset startup GPU peak before loading.
- Save `load_peak_gpu_gb` and `loaded_active_gpu_gb` alongside `load_s`.
- Each request includes process peak RSS using macOS resource.ru_maxrss / 1e9.
  RSS is process-lifetime high water, not instantaneous per-request RSS.
- Existing plugin telemetry, after_load hooks and campaign-start source snapshots
  remain. Plugins are self-contained so snapshotting includes their experiment code.

### Resident matrix: pocs/resident_matrix.py

Self-contained source embeds/adapts the earlier MIT-attributed fused and grouping
PoCs; no live dependency on mutable plugin files.

Variants in `variants/resident/`:

- `resident-fused`: compact gate/up fusion, releases original arrays into views.
- `resident-compiled`: mx.compile per-layer SwitchGLU closure.
- `resident-compiled-fused`: both, with eager packing before tracing.
- `allocator-off`: disables MLX allocator cache (0 MB).
- `allocator-256mb`: caps allocator cache at 256 MiB.
- `group-0`, `group-32`, `group-128`, `group-256`: grouping threshold sweep;
  baseline MLX threshold is 64 selected indices.

R1 fusion, R2 compilation, R4 grouping, R5 combination are implemented and running.
R3 allocator variants are a **proxy for allocation reuse**, NOT a custom in-place
resident activation-buffer implementation. Say this clearly in results.

First-round diagnostics were all successful, around 193–202 tok/s versus baseline
200 tok/s. Do not rank these preliminary values as results. Layout repacking ran
concurrently on CPU/disk during part of the resident campaign: label the broad
campaign a screen and recheck selected finalists after implementation activity ends.

### Lossless expert layout: prepare_expert_layout.py

Run:

```sh
.venv/bin/python prepare_expert_layout.py
```

ALREADY COMPLETED: byte-for-byte verified all 9,216 original expert tensors.
Generated ignored artifacts:

- `models/olmoe-1b-7b-4bit/experts-contiguous.bin` (3,623,878,656 bytes)
- `models/olmoe-1b-7b-4bit/experts-contiguous.json`

The original checkpoint scatters weight/scales/biases tensors across the file.
The new file places all nine tensors for one expert together, ordered by
layer/expert/up-gate-down/weight-scales-biases. Index records source and packed
SHA256 hashes, tensor shapes/dtypes/offsets and verification count.
It is a byte copy, NOT requantization. Preparation checks existing hashes on rerun.
Do not commit weight files. Include hashes/provenance in published results/docs.

### Streaming implementation: pocs/stream_slots.py

NEW, NOT YET VALIDATED ON METAL at initial handoff creation.

- Patches complete SwitchGLU rather than each projection: one routing sync per GLU.
- Fixed-capacity banks for up/gate/down weight/scales/biases; expert-to-slot map.
- Replaces only missing rows; evaluates banks before use.
- Prefill groups original expert indices and partitions sorted work into chunks
  with at most capacity distinct experts; concatenates and restores original order.
  Decode's eight selected experts fit minimum capacity eight.
- Retained banks are bounded; updates and read payloads still need transient memory.
  **Do not claim peak memory equals retained bank bytes.** Measure actual peaks.
- GPU banks use indexed updates; MLX arrays can copy on update. This is an experiment,
  not proof of zero-copy or in-place behavior.
- Uses original quantization values and routing, but remapped slot order and
  sorted_indices=False change kernel layout and can change numerical results.
- Reads either original checkpoint tensors or packed expert layout.
- Optional merges physically adjacent tensor/expert reads, with no gap overread.
- Optional thread pool with 1/2/4/8 I/O workers.
- LRU, LFU, or hybrid frequency/recency eviction.
- Optional one asynchronous temporal prefetch record per layer. Predicts the
  most frequently seen expert currently absent from cache. This is NOT a
  next-layer router predictor. Measures useful/submitted/discarded records.
- Lazy loading is default: mlx_lm.load(lazy=True), remove expert graph parameters
  in after_load, then evaluate dense parameters only. This avoids deliberately
  materializing all expert arrays before streaming. Verify startup GPU/RSS peaks;
  lazy file mappings/initialization still exist, so no claim of arbitrary huge
  checkpoint support or GLM compatibility without testing.
- Eager startup is an explicit comparison variant.
- Telemetry: requested read bytes/calls, summed read time (parallel thread times
  can overlap), hits/misses, upload+bank-update wall time, evaluated compute time,
  retained bank bytes, per-layer hits/misses/capacity, prefetch stats and layout hash.
  Cumulative since worker start including warmup.

Registered `variants/streaming/`:

- `slots-eager-original`, `slots-lazy-original`: isolate startup path.
- `slots-packed-separate`: packed layout with separate tensor reads.
- `slots-packed-grouped`: packed layout and merged contiguous reads (1 worker).
- `slots-workers-2`, `slots-workers-4`, `slots-workers-8`: grouped packed layout.
- `slots-lfu`, `slots-hybrid`: grouped packed layout, capacity 32.
- `slots-prefetch`: grouped packed, four workers, temporal prefetch enabled.
- `slots-capacity-8`, `slots-capacity-16`, `slots-capacity-48`.
- Default capacity for other variants: 32 complete experts/layer.

### New test: tests/test_stream_slots.py

Opt-in Metal numerical check with a small synthetic 64-expert quantized GLU.
Saves original expert tensors, deletes resident projection tensors, tests fixed
banks and hybrid eviction, 8-expert decode, multi-row prefill requiring partitions,
and reload after eviction. Checks 1e-4 allclose and bank capacity bounds.
Not yet run when first writing this file.

## Exact next steps

1. Wait for resident campaign to finish (or inspect failure). Preserve all records.
2. With GPU idle, run tests:

```sh
COLIBRI_GPU_TESTS=1 make test
```

   Expected previous suite: eight tests. New slot test makes nine. Fix real failures
   and record them. Never overlap tests with timing campaigns.
3. Run a short streaming smoke to catch integration issues before a long matrix:

```sh
.venv/bin/python bench.py run --variants variants/baseline.json variants/streaming/slots-lazy-original.json variants/streaming/slots-packed-grouped.json --rounds 1 --tokens 16 --timeout 300
```

   Inspect telemetry, startup peaks, output shape/length, retained bytes, real logs.
4. Run ALL registered streaming variants, including prior `stream-lru-32` reference:

```sh
.venv/bin/python bench.py run --variants variants/baseline.json variants/stream-lru-32.json variants/streaming/*.json --rounds 2 --tokens 32 --timeout 600
```

   This is a broad screen, not a final ranking. Keep workloads identical. If it
   runs very slowly, keep going and report progress; don't silently omit variants.
5. IMPLEMENT remaining S6 unequal-layer allocation using measured per-layer miss
   pressure from capacity-32 pilot. Allocate exactly 512 total expert slots across
   16 layers, each 8..64. A simple explicitly-labelled heuristic:
   start each at eight, allocate remaining slots greedily by
   `pilot_layer_misses / (capacity * (capacity+1))`.
   Save the pilot campaign and actual array in variant env `SLOTS_CAPACITIES`.
   The plugin already parses this JSON string. Compare to uniform 32 at equal
   retained bytes (experts equal-sized in this model). This heuristic is NOT an
   optimal reuse predictor; a negative result is useful. Register a named variant.
6. Recheck resident finalists after CPU/disk development activity ends, with
   baseline plus compact-fused, compiled and compiled-fused (or meaningful best
   alternatives) for at least three rounds and 256 output tokens. Separate this
   from streaming. All-aspects claim needs startup + memory + TTFT + per-prompt
   decode/prefill, not overall median only. Initial compile/packing can occur
   during warmup; report cold first-use separately from steady state.
7. Run streaming confirmation with baseline, old stream-lru-32, new best uniform32,
   unequal32, best prefetch/policy candidate at same budget, at least three rounds
   and 128 tokens. Longer output matters: previous streaming divergence began at
   token index 36, so a 32-token screen can miss it.
8. Analyze paired same-round same-prompt ratios, not ratios of pooled medians.
   Report token equality, equal lengths, worst per-prompt latency/memory, failures.
   Useful primary stream score: output tok/s at fixed memory, plus requested
   bytes/output token (exclude or explicitly include warmup; counters cumulative).
9. Add simple Mermaid guide/results to docs/09-two-track-experiments.md; update
   README, research tracker and Makefile with reproducible commands.
10. Publish each completed campaign:

```sh
.venv/bin/python publish_results.py TIMESTAMP
```

   This removes home paths in public copies and retains raw local originals.
   Review published content (no secrets, weights or home paths). Preserve negative
   experiments and failures. Ignore raw weights/results as established.
11. Run tests/checks appropriate to final changes, git diff --check, commit and
   push origin main (already authorized). Verify remote hash and clean checkout.
12. Update THIS handoff file with completed campaign IDs/results and remaining work
   before nearing a usage limit. The user specifically requested this document.

## Experiment coverage mapping / honest limitations

- R1 compact fusion, R2 compilation, R4 grouping, R5 combination: implemented.
- R3 resident buffer reuse: allocator reuse proxies implemented. Dedicated
  activation-buffer engineering is not implemented; document rather than pretend.
- S1 reusable GPU expert slots: implemented, needs validation/timing.
- S2 contiguous experts: prepared and byte-verified, needs timing.
- S3 grouped reads: implemented, needs timing.
- S4 bounded parallel reads: implemented, needs timing.
- S5 hybrid eviction: implemented, needs timing.
- S6 unequal layer allocation: pending generation from pilot measurements.
- S7 temporal predictive prefetch: implemented; no next-layer predictor.
- S8 lazy streaming startup: implemented; verify actual memory peaks.

There is no verified physical-SSD condition yet. OLMoE fits in OS cache.
Do NOT flush global OS caches, change system memory settings or claim cold reads.
A direct-I/O/F_NOCACHE dedicated copy could be a separate controlled future test,
with physical I/O telemetry, but it has NOT been implemented or authorized as a
system-wide setting. All present reads must remain labelled OS cache uncontrolled.

## Earlier established results (already public)

- Resident baseline usually ~195–204 tok/s short prompts, ~141 long prompt.
- Old Python streaming: capacity8 ~28.4, capacity32 ~48.6, capacity64 ~69.5 tok/s.
- LFU32 requested ~12% fewer bytes than LRU32 but similar speed.
- Full-cache pack-once eventually reaches resident speed on final long prompt,
  but early prompts still pay staging and memory becomes fully resident.
- Prior compact gate/up fusion ~1% possible gain; not robust enough to declare win.
- Quantized KV helps long-context decode but changes precision/tokens.

Relevant existing docs: docs/07-experiment-round-two.md and
 docs/08-expert-streaming.md. Existing unit tests and benchmark snapshots are
useful references; inspect implementation rather than assuming this note is exact.
