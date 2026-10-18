# Smaller models for lower-end machines (plan)

**Question:** can a smaller model, run the way we run GLM, give more useful intelligence
per minute of waiting on this Mac and on lower-end Macs (8-24 GB)?

Status (2026-10-18): `sm-arch-check` **done**; `sm-qwen38-27b-ollama` **queued** (runs when
the machine is quiet); the rest planned. Each experiment below is also an entry
in the [experiment log](12-experiment-log.md) (category `small-models`).

## The candidates

| Model | Total / active parameters | Kind | Colibri id | On disk (int4) | Published intelligence |
|---|---|---|---|---:|---:|
| GLM-5.3 (reference) | 744B / 40B | MoE, 256 experts, 8 active | `glm-5.2/5.3` | 419 GB | 45 |
| GLM-5.3-Flash | 321B / 18B | MoE | `glm53` | ~195 GB | 42 |
| **Qwen3.8-27B** | 27B / 27B | **dense** (no experts) | `qwen3.8-27b-colibri` | ~20 GB | **34** |
| **Qwen3.6-35B-A3B** | 35B / ~3B | **MoE** | `qwen36-35b` | ~23 GB | **18** |

Published intelligence = Artificial Analysis Intelligence Index v4.3.2 (reported by others,
not measured here; frontier reference: Claude Opus 5.5 = 58). Sources:
[GLM-5.3](https://artificialanalysis.ai/models), [Qwen comparison](https://artificialanalysis.ai/models/comparisons/qwen3-8-27b-vs-qwen3-6-35b-a3b).
Artificial Analysis lists Qwen3.8-27B as "3B active"; the model's own config says otherwise
(`sm-arch-check`, from the official `config.json` files):

| | Qwen3.8-27B | Qwen3.6-35B-A3B |
|---|---|---|
| Architecture | `Qwen3_5ForConditionalGeneration` | `Qwen3_5MoeForConditionalGeneration` |
| Layers / hidden size | 64 / 5120 | 40 / 2048 |
| Feed-forward | one MLP per layer (17408 wide) | 256 experts, 8 routed + 1 shared (512 wide) |
| Used per token | all ~27.8B | ~3B, of which routed experts ~1.0B (~0.55 GB at int4) |

The owner's "27B with 3B active" combines the two Qwen models. They behave very
differently on a small machine:

```mermaid
flowchart LR
    D[Dense 27B<br/>every weight, every token] --> D1[~13.5 GB read per token<br/>if it does not fit in RAM]
    D1 --> D2[fits a 32 GB Mac;<br/>on 16 GB it is SSD-bound]
    M[MoE 35B, ~3B active] --> M1[~0.55 GB of routed experts per token]
    M1 --> M2[streams experts like GLM:<br/>runs on 8-16 GB, faster]
```

- **Qwen3.8-27B (dense)** is the smarter of the two (34 vs 18) and already installed in
  Ollama as `qwen3.8:27b-mlx` (18 GB). It fits in this Mac's RAM, so it does not need our
  streaming tricks here; on a 16 GB machine it would have to read most of its weights from
  the SSD for every token.
- **Qwen3.6-35B-A3B (MoE)** is the one that can use the GLM approach: only ~3B
  parameters are used per token, ~1B of them routed experts (~0.55 GB at int4), so expert streaming keeps it usable
  on 8-16 GB machines. Colibri reports 6.0 tok/s on a CPU and 9.9 tok/s on an integrated
  GPU (Vulkan), with 10-20 GB of RAM.

## How "lower-end machines" are simulated

This Mac (M6, 32 GB, ~6.5 GB/s SSD) stands in for smaller ones by capping what the engine
may use:

| Profile | RAM budget given to the engine | Threads | What it stands for |
|---|---:|---:|---|
| 8 GB Mac | 5 GB | 4 | base model, apps open |
| 16 GB Mac | 11 GB | 6 | common laptop |
| 24 GB Mac | 17 GB | 8 | upgraded laptop |
| This Mac | 24 GB | 12 | M6, 32 GB |

Caveat: a RAM cap does not reproduce a slower SSD or GPU. Base Macs often read at
~3 GB/s, half of this machine, so real low-end numbers will be lower where the SSD
dominates. Results will be labelled "simulated" until run on such a machine.

## Measurements (same as for GLM)

- **Speed:** generation tok/s and prompt reading time on the `sky` and `code` prompts.
- **Quality:** the 24-question quality bench (`glm_bench.py`), terse and normal styles,
  graded automatically and reviewed by hand, so results sit next to GLM's in
  [the bench](https://kakkoidev.github.io/colibri-poc/bench.html).
- **The comparison that matters:** correct answers per minute of waiting, next to the
  published intelligence score, for each model and machine profile.

## Experiments

| Id | What | Needs | Expected outcome |
|---|---|---|---|
| `sm-arch-check` | Read both Qwen configs: experts, active parameters, layers | nothing (config files only) | Confirms dense vs MoE |
| `sm-qwen38-27b-ollama` | Qwen3.8-27B through the installed Ollama MLX model: speed and quality bench | an Ollama backend for `glm_bench.py` (small code change) | Fast in RAM (tens of tok/s); quality close to GLM on these questions? |
| `sm-qwen36-a3b-resident` | Qwen3.6-35B-A3B on Colibri with every expert in RAM | ~23 GB download (`make glm-prep-qwen36`), a Colibri adapter for the bench tools | Upper bound for the MoE on this Mac |
| `sm-qwen36-a3b-ram-sweep` | Same, at the 5 / 11 / 17 / 24 GB profiles | as above | How speed falls as RAM shrinks; usable on 8 GB? |
| `sm-qwen36-a3b-vulkan` | Vulkan expert tier through MoltenVK vs CPU | our MoltenVK patch (engines/ clone) | Colibri saw 9.9 vs 6.0 tok/s on another integrated GPU |
| `sm-qwen38-27b-lowram` | Dense 27B on Colibri at the 11 / 17 GB profiles | Colibri conversion of Qwen3.8-27B | Shows why dense models fall off on small machines |
| `sm-intelligence-per-minute` | Combine quality bench, answer time and published scores for GLM-5.3, Qwen3.8-27B and Qwen3.6-35B-A3B per machine profile | the runs above | The table and chart this plan is for |

```mermaid
flowchart TD
    A[sm-arch-check] --> B[sm-qwen38-27b-ollama<br/>no download]
    A --> C[download Qwen3.6-35B-A3B ~23 GB]
    C --> D[sm-qwen36-a3b-resident]
    D --> E[sm-qwen36-a3b-ram-sweep]
    D --> F[sm-qwen36-a3b-vulkan]
    B --> G[sm-qwen38-27b-lowram]
    E --> H[sm-intelligence-per-minute]
    F --> H
    G --> H
```

## What is needed before running

1. **Bench tools for other engines.** Ollama: **done**. `glm_bench.py run --backend ollama
   --ollama-model NAME --configs exact` sends the same prompts to the local Ollama server
   (thinking off, temperature 0, same 128-token limit), reads its prompt and generation
   timings and grades the answers the same way; the lab app's bench jobs accept an
   installed Ollama model. Still to do: an adapter for Colibri's Qwen engine (`qwen36`).
2. **A download, with your OK:** Qwen3.6-35B-A3B in Colibri format,
   `Kreuzzelg/qwen36-35b-a3b-colibri-i4-gs64` (~23 GB), prepared with
   `make glm-prep-qwen36` and shown in the lab app's Install screen.
3. **A quiet machine** for the speed numbers (≥ 20 GB free), like every other bench.

## Success criteria

- A model counts as a "lower-end option" if, on the 16 GB profile, it answers the terse
  quality bench at ≥ 20 of 24 correct in under a minute per answer.
- It counts as "extra intelligence on this Mac" if it beats GLM-5.3's correct answers per
  minute at equal or better quality on the bench. Published scores say GLM-5.3 is smarter
  (45 vs 34 vs 18), so the expected trade is speed for intelligence, measured, not assumed.
