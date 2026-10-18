# Research watch list

Every technique, paper, project or release reviewed for the GLM speed goal (5 tok/s on
a 32 GB Apple M6), including the rejected ones, so nobody re-investigates blindly.
How to triage: [lab guide, section 6](../docs/00-lab-guide.md#6-follow-the-research).
Ideas that become experiments also get an entry in `experiments/glm-experiments.json`.

Decision values: **tested** (see the experiment log), **candidate** (worth testing),
**watch** (blocked or not ready; re-check later), **rejected** (does not touch the
bottleneck here).

## Scan log

| Date | Scope | By |
|---|---|---|
| 2026-10-18 | MoE offloading, expert caching and prefetch, speculative prefetch, Apple Silicon SSD streaming (round 1, OLMoE lab) | Claude |
| 2026-10-18 | GLM round 2: pruning, mixed-precision experts, CPU/GPU hybrid, Colibri formats | Claude |

Next scan due: 2026-11-01. A monthly scheduled task (`glm-research-scan`, 1st of each
month at 10:00 on the owner's Mac) appends new items here, adds candidates to the
experiment log, pushes, and reports anything worth testing. Do a deeper manual scan
quarterly or on any new Colibri release, GLM release or Mac.

## Items

| Item | Type | Link | What it does | Relevance here | Decision | Reviewed |
|---|---|---|---|---|---|---|
| Colibri `PIPE`, `DIRECT`, `COLI_METAL_RESSET`, `COLI_METAL_SPIN` | engine settings | [Colibri env docs](https://github.com/JustVugg/colibri/blob/main/docs/ENVIRONMENT.md) | I/O overlap, uncached reads, GPU scheduling | Core of the 4× exact gain | tested | 2026-10-18 |
| Colibri `DEGRADE_ZERO` | engine setting | same | Skip low-weight missed experts | Usable up to skip 0.5 | tested | 2026-10-18 |
| Colibri `CACHE_ROUTE` | engine setting | [CACHE_ROUTE.md](https://github.com/JustVugg/colibri/blob/main/docs/CACHE_ROUTE.md) | Prefer cached experts within top-M | Needs a real cache; 0% swaps at ~1 slot/layer | tested; revisit with more RAM | 2026-10-18 |
| Colibri `PILOT` prefetch | engine setting | same env docs | Cross-layer expert prefetch | No gain; most loads discarded | tested | 2026-10-18 |
| Colibri `COLI_MMAP` | engine setting | same | Page cache as expert cache | GPU out-of-memory on Metal | tested (failed) | 2026-10-18 |
| Colibri `COLI_METAL_PREFILL` | engine setting | same | GPU attention for prompt reading | Prompt reading is SSD-bound; no gain | tested | 2026-10-18 |
| Colibri Vulkan dense chain via MoltenVK | backend | [vulkan.md](https://github.com/JustVugg/colibri/blob/main/docs/vulkan.md) | Whole dense layers on the GPU | Works with a patch, slower than Metal | tested | 2026-10-18 |
| Colibri thread sizing on M6 | bug | [colibri#2194](https://github.com/JustVugg/colibri/issues/2194) | Uses 2 of 12 cores | `OMP_NUM_THREADS=12`: +19% lossy | tested; watch for the fix | 2026-10-18 |
| Colibri `int4-rans256-g0` | model format | [colibri#671](https://github.com/JustVugg/colibri/pull/671) | Lossless entropy-coded experts, ~24% fewer bytes | Engine loader not merged; CPU decode may cost what it saves | watch (loader, Metal decode) | 2026-10-18 |
| Colibri `COLI_MODEL_MIRROR` / `COLI_MODEL_DIRS` | engine setting | [multidisk.md](https://github.com/JustVugg/colibri/blob/main/docs/multidisk.md) | Spread expert reads across drives | Biggest exact lever; needs a second NVMe | candidate (hardware) | 2026-10-18 |
| REAP expert pruning | paper + community GLM models | [arXiv 2510.13999](https://arxiv.org/html/2510.13999) | Remove 25-50% of experts | Still 8 experts per token: bytes per token unchanged | rejected | 2026-10-18 |
| GEMQ / MODE mixed-precision experts | papers | [GEMQ](https://arxiv.org/pdf/2605.23078), [MODE](https://arxiv.org/html/2606.17118v1) | Per-expert bit allocation | int3 ~−25% bytes; 2-bit large losses | candidate (needs conversion) | 2026-10-18 |
| HOBBIT | paper | summarized in [arXiv 2510.16805](https://arxiv.org/pdf/2510.16805) | Low-precision expert on cache miss | Similar to int3 idea; needs two copies on disk | watch | 2026-10-18 |
| SpecMD / Least-Stale eviction | paper | [arXiv 2602.03921](https://arxiv.org/html/2602.03921v1) | Eviction tuned to layer-ordered access | Cache too small for policy to matter today | watch (with more RAM) | 2026-10-18 |
| SpecPrefetch, SPICE, MoE-SpeQ | papers | [SpecPrefetch](https://arxiv.org/html/2607.24787v2), [SPICE](https://arxiv.org/pdf/2608.21240), [MoE-SpeQ](https://arxiv.org/abs/2511.14102) | Draft-model or learned expert prefetch | Prefetch did not help on unified memory (PILOT, Flash-MoE) | watch | 2026-10-18 |
| MoE-CORE | paper | [arXiv 2610.01950](https://arxiv.org/abs/2610.01950) | Layer-wise cache, routing-history eviction, cross-layer prefetch | Server appliance; ideas overlap Colibri's | watch | 2026-10-18 |
| FlashMoE ML cache replacement | paper | arXiv 2601.17063 | Learned eviction, +51% hit rate vs LRU | Hit rate limited by cache size, not policy | watch (with more RAM) | 2026-10-18 |
| KTransformers, HybriMoE | systems | [KTransformers](https://github.com/kvcache-ai/ktransformers) | CPU/GPU expert split | Targets PCIe gap that unified memory does not have | rejected for this Mac | 2026-10-18 |
| Flash-MoE (C/Metal) | project | [write-up](https://lilting.ch/en/articles/flash-moe-qwen35-397b-metal-inference) | Parallel pread, own Metal kernels | Confirms mmap slow, prefetch harmful, LZ4 slower on Apple | reference | 2026-10-18 |
| DeepSeek V4-Flash MLX SSD offload | project | [repo](https://github.com/ssd-moe/deepseek-v4-flash-mlx) | MLX expert streaming on 48 GB Macs | Alternative runtime to compare if Colibri stalls | watch | 2026-10-18 |
| SP-MoE, DraftExpert | papers | [SP-MoE](https://arxiv.org/html/2510.10302v2), [DraftExpert](https://www.alphaxiv.org/abs/2607.24434v1) | Speculative decoding with expert prefetch | Needs an MTP head or draft model for GLM in Colibri | watch | 2026-10-18 |
