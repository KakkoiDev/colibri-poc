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
| 2026-10-18 | Scheduled scan: Colibri v2.0.0 to dev 16239caa (merged PRs, issues, #2194), zai-org and Unsloth on Hugging Face, arXiv SSD offloading, llama.cpp/MLX, Apple hardware. Machine busy (quality bench running): 0 runs, 5 experiments planned | Claude (scheduled) |

Next scan due: 2026-11-01. A monthly scheduled task (`glm-research-scan`, 1st of each
month at 10:00 on the owner's Mac) appends new items here, plans experiments for new
possibilities, runs the quick safe ones (no downloads, installs or changes to the owner's
engine; only when the machine is free), records them in the experiment log, pushes, and
reports results plus the options that need the owner's OK. Do a deeper manual scan
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
| Colibri thread sizing on M6 | bug | [colibri#2194](https://github.com/JustVugg/colibri/issues/2194) | Uses 2 of 12 cores | `OMP_NUM_THREADS=12`: +19% lossy. Still open, no replies (scan 2026-10-18) | tested; watch for the fix | 2026-10-18 |
| Colibri `int4-rans256-g0` | model format | [colibri#671](https://github.com/JustVugg/colibri/pull/671) | Lossless entropy-coded experts, ~24% fewer bytes | Engine loader not merged (still none on dev 16239caa); CPU decode may cost what it saves. SSD-LLaMA (below) measures -33% SSD traffic with GPU-side rANS decode, so a Metal decoder would make it worth testing | watch (loader, Metal decode) | 2026-10-18 |
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
| Colibri GGUF read in place for GLM-5.2/5.3 | engine feature (dev branch) | [colibri#2140](https://github.com/JustVugg/colibri/pull/2140), [#2130](https://github.com/JustVugg/colibri/pull/2130) | `coli import` runs a llama.cpp `glm-dsa` GGUF directly (all ggml block types, NEON kernels, MTP head from the GGUF) | Opens ready-made 1-3 bit GLM-5.3 quants without a Colibri conversion; GGUF blocks are computed on the CPU only (no Metal copy). On dev, not in a release yet | candidate (dev build; experiment `baseline-16239caa`, `gguf-iq2m`) | 2026-10-18 |
| Unsloth GLM-5.3 GGUF (UD-IQ1_S to Q8_0) | model conversion | [HF repo](https://huggingface.co/unsloth/GLM-5.3-GGUF), [guide](https://unsloth.ai/docs/models/glm-5.3) | Imatrix low-bit GGUFs; UD-IQ2_M is 239 GB (top-1 agreement 78.5%, KLD 0.45), UD-IQ3_XXS 282 GB (84.2%, 0.27), UD-Q4_K_XL 467 GB (94.3%, 0.04) per Unsloth | ~40% fewer expert bytes than the 419 GB int4 container (lossy). Needs the GGUF reader above | candidate (239 GB download, quality bench; `gguf-iq2m`) | 2026-10-18 |
| GLM-5.3-Flash (321B, 18B active, 45 layers; released Aug 2026) | model release + Colibri engine | [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash), [glm53-flash.md](https://github.com/JustVugg/colibri/blob/main/docs/glm53-flash.md) | Smaller GLM-5.x on a new base (hybrid sparse + linear attention, multimodal), same expert shape, hidden 4096, 288 experts, 8 per token. Vendor benches: matches or beats GLM-5.2 on every shared one, ~3-7 points under GLM-5.3; Artificial Analysis index 42 vs 45 (5.3) and 34 (5.2) | ~4.8 GB of int4 experts per token (-62%): exact ceiling ~1.3 tok/s, lossy could near 5. A different model: owner decides if it counts | candidate (~25 h conversion; `glm53-flash`) | 2026-10-18 |
| Colibri int8 MTP head for GLM | engine feature | [tuning.md](https://github.com/JustVugg/colibri/blob/main/docs/tuning.md), `c/tools/repair_mtp_int8.py` | Native draft head, 2.2-2.8 tokens per forward when it pays | Our glm-5.3 container has none (logs: "MTP absent"). Verify rows multiply expert reads on an SSD-bound run; ~10 GB resident | candidate (~10 GB download; `mtp-int8`) | 2026-10-18 |
| Colibri prompt-lookup drafts (`COLI_LOOKUP`) | engine setting | [speculative.md](https://github.com/JustVugg/colibri/blob/main/docs/speculative.md) | n-gram drafts from the prompt, gated, on by default without an MTP head | Already on in every run (1.04 tokens per forward). Unknown whether rejected verifies waste SSD reads | candidate (settings only; `lookup-off`) | 2026-10-18 |
| Colibri expert workers / cluster (`CLUSTER_WORKERS`, COLIEX01) | engine feature | [cluster.md](https://github.com/JustVugg/colibri/blob/main/docs/cluster.md) | Other machines compute experts from their own RAM/SSD; worker read-ahead | Would add a second machine's SSD and RAM; needs hardware and a fast link | watch (hardware) | 2026-10-18 |
| SSD-LLaMA | paper | [arXiv 2609.18110](https://arxiv.org/html/2609.18110v1) | Three-tier expert cache, one aligned block per expert via direct I/O, lossless rANS (-33% SSD traffic) with GPU decode; no prefetch | PC + RTX 5090, not Apple. Confirms our findings (direct I/O, prefetch hides little) and the rANS-with-GPU-decode path | reference; supports rANS watch | 2026-10-18 |
| SeqMoE | paper | [arXiv 2609.12978](https://arxiv.org/pdf/2609.12978) | Predictive, graph-compatible MoE offloading | Full text not read (unverified); prediction-based prefetch has not helped on unified memory | watch | 2026-10-18 |
| llama.cpp MoE disk paging RFC | runtime proposal | [llama.cpp discussion #23324](https://github.com/ggml-org/llama.cpp/discussions/23324) | On-demand paging of experts from disk, CPU-only PoC on an M1 | Proposal only; Colibri already does this | watch | 2026-10-18 |
| NunSpark, mac-code (MLX expert streaming) | projects | [NunSpark](https://pypi.org/project/nunspark/), [mac-code](https://www.sourcepulse.org/projects/26942292) | Expert streaming with an expert-aware cache on small Macs | Small models (30B-class), no GLM-5.x support; nothing Colibri lacks | rejected | 2026-10-18 |
| Apple M5 Pro / M5 Max MacBook Pro (Mar 2026) | hardware | [Neowin](https://www.neowin.net/news/apple-upgrades-macbook-pro-with-m5-pro-and-m5-max-chips-2x-faster-ssd/) | Up to 128 GB, 614 GB/s, SSD up to 14.5 GB/s | ~2x our SSD speed and ~4x the RAM: the "new Mac" lever. No M6 Pro/Max/Ultra announced as of this scan | watch (hardware) | 2026-10-18 |
