# GLM, Gemma and Qwen: completed benchmark comparison

Updated 22 October 2026. All eight model/format groups below have 24 answers per
setting and style: 1,344 recorded answers, with no execution failures.

## Which should I use?

- **Fast everyday answers: Gemma 4 E4B, terse, thinking off.** 24/24 correct,
  52.25 mean generation tokens/s, 0.1 s median answer time. Its native normal
  setting scored 23/24 at 111.56 tokens/s and 2.1 s median answer time.
- **Best Gemma normal-answer score: Gemma 4 26B, native.** 24/24 correct,
  66.66 tokens/s and 3.4 s median answer time. The 31B model scored 23/24
  and took 8.3 s median; this test provides no reason to prefer it.
- **GLM default: original int4, terse, exact.** 24/24 correct,
  0.41 tokens/s and 44.4 s median answer time. Skip 0.5 also scored 24/24
  at 1.44 tokens/s, but median answer time stayed 44.0 s. Short answers are
  dominated by prompt processing, so faster decoding is not the same as less waiting.
- **GLM normal-answer tradeoff: MTP-labelled run, skip 0.3, 12 threads.**
  22/24 correct, 0.93 tokens/s, 160.5 s median, versus baseline exact
  21/24, 0.41 tokens/s, 297.6 s. Expert skipping **changes output**.
  The IQ2 exact run had the best GLM normal score, 23/24, but took 516.2 s
  median at 0.23 tokens/s. There is no single GLM winner across quality and speed.

## Where Qwen fits

Qwen's saved model alias is `qwen3.8:27b-mlx` (the record label, not an independently
verified model identity). Native normal answers scored **24/24** at **24.74 mean
tokens/s**, with **5.77 s** median answer time and no truncation. This matches
Gemma 26B's score, but Gemma 26B answered in 3.4 s median and generated at 66.66
tokens/s on these runs. Qwen terse, thinking off scored **24/24** at **15.90
tokens/s**, with **0.51 s** median answer time; Gemma E4B matched that score at
0.1 s median. Qwen native terse scored 23/24 at 23.45 tokens/s and 2.73 s median.
Normal short-budget Qwen scored 18/24, but 10/24 answers were cut off, so it is
not a clean measure of its underlying quality. No overall speed or score advantage
for Qwen over the recommended Gemma settings appears on this small prompt set.

## How to read this

These are small automatic checks of 24 fixed prompts, not a general intelligence
ranking. Terse and normal use the same questions with different instructions;
they are not independent repetitions. Scores do not assess explanation quality.
Timing was collected on the owner's everyday machine, not under controlled load.
Generation speed is the mean of per-answer rates; median answer time includes
prompt reading plus decoding and excludes model loading. Tiny answers make token
rates noisy. No repeated-run confidence intervals were measured.

For Ollama, `exact` means thinking off, temperature zero and the short output budget;
`native` uses model defaults and up to 4096 generated tokens. They differ in both
thinking/sampling and token budget. Normal short-budget Gemma answers were cut off
8/24 (26B), 8/24 (31B) and 11/24 (E4B); native normal answers had no truncation.
Do not attribute the native score gains solely to thinking.

GLM `d030`/`d050` skip experts below 0.3/0.5; `t12` uses 12 CPU threads.
Every skip configuration changes computation/output. Quantized formats also change
weights. The label MTP identifies the campaign; it does not prove speculative
multi-token decoding was active or caused a gain. Exact baseline and MTP-labelled
normal rates were both 0.41 tokens/s.

Gemma jobs were rerun under MLX-named Ollama aliases, but the saved folder metadata
still names the earlier non-MLX alias and answers contain no model identity. These
numbers describe the saved latest answers; exact backend attribution needs fresh
per-run metadata before claiming an MLX speedup. GLM formats also used different
engine commits, so this is a practical comparison, not an isolated quantization test.

## All measured settings

| Model / campaign | Style | Setting | Correct | Mean tokens/s | Median answer s | Cut off |
|---|---|---|---:|---:|---:|---:|
| gemma4-26b-ollama | normal | exact | 19/24 | 65.69 | 1.00 | 8 |
| gemma4-26b-ollama | normal | native | 24/24 | 66.66 | 3.41 | 0 |
| gemma4-26b-ollama | terse | exact | 24/24 | 42.72 | 0.35 | 0 |
| gemma4-26b-ollama | terse | native | 23/24 | 62.53 | 4.31 | 1 |
| gemma4-31b-ollama | normal | exact | 18/24 | 20.19 | 1.77 | 8 |
| gemma4-31b-ollama | normal | native | 23/24 | 21.87 | 8.35 | 0 |
| gemma4-31b-ollama | terse | exact | 24/24 | 14.62 | 0.54 | 0 |
| gemma4-31b-ollama | terse | native | 24/24 | 21.40 | 7.13 | 0 |
| gemma4-e4b-ollama | normal | exact | 16/24 | 111.92 | 0.68 | 11 |
| gemma4-e4b-ollama | normal | native | 23/24 | 111.56 | 2.13 | 0 |
| gemma4-e4b-ollama | terse | exact | 24/24 | 52.25 | 0.13 | 0 |
| gemma4-e4b-ollama | terse | native | 24/24 | 82.11 | 1.04 | 0 |
| glm-5.3-iq2m | normal | d030 | 18/24 | 0.38 | 354.27 | 0 |
| glm-5.3-iq2m | normal | d030t12 | 18/24 | 0.68 | 197.51 | 0 |
| glm-5.3-iq2m | normal | d040t12 | 19/24 | 0.77 | 216.27 | 0 |
| glm-5.3-iq2m | normal | d050 | 15/24 | 0.47 | 354.25 | 0 |
| glm-5.3-iq2m | normal | exact | 23/24 | 0.23 | 516.25 | 0 |
| glm-5.3-iq2m | terse | d030 | 23/24 | 0.31 | 82.92 | 0 |
| glm-5.3-iq2m | terse | d030t12 | 23/24 | 0.46 | 46.08 | 0 |
| glm-5.3-iq2m | terse | d040t12 | 24/24 | 0.54 | 47.42 | 0 |
| glm-5.3-iq2m | terse | d050 | 23/24 | 0.42 | 94.28 | 0 |
| glm-5.3-iq2m | terse | exact | 24/24 | 0.20 | 88.22 | 0 |
| glm-5.3-iq3xxs | normal | d030 | 19/24 | 0.35 | 385.79 | 0 |
| glm-5.3-iq3xxs | normal | d030t12 | 19/24 | 0.54 | 247.00 | 0 |
| glm-5.3-iq3xxs | normal | d040t12 | 17/24 | 0.56 | 249.31 | 0 |
| glm-5.3-iq3xxs | normal | d050 | 18/24 | 0.38 | 389.19 | 0 |
| glm-5.3-iq3xxs | normal | exact | 21/24 | 0.21 | 620.09 | 0 |
| glm-5.3-iq3xxs | terse | d030 | 24/24 | 0.31 | 93.67 | 0 |
| glm-5.3-iq3xxs | terse | d030t12 | 24/24 | 0.42 | 49.94 | 0 |
| glm-5.3-iq3xxs | terse | d040t12 | 24/24 | 0.49 | 49.55 | 0 |
| glm-5.3-iq3xxs | terse | d050 | 23/24 | 0.39 | 92.16 | 0 |
| glm-5.3-iq3xxs | terse | exact | 24/24 | 0.18 | 90.56 | 0 |
| glm-5.3-mtp | normal | d030 | 22/24 | 0.84 | 183.90 | 0 |
| glm-5.3-mtp | normal | d030t12 | 22/24 | 0.93 | 160.51 | 0 |
| glm-5.3-mtp | normal | d040t12 | 20/24 | 1.47 | 118.41 | 0 |
| glm-5.3-mtp | normal | d050 | 17/24 | 1.45 | 127.03 | 0 |
| glm-5.3-mtp | normal | exact | 21/24 | 0.41 | 296.34 | 0 |
| glm-5.3-mtp | terse | d030 | 24/24 | 0.70 | 51.78 | 0 |
| glm-5.3-mtp | terse | d030t12 | 24/24 | 0.79 | 50.83 | 0 |
| glm-5.3-mtp | terse | d040t12 | 24/24 | 1.27 | 50.55 | 0 |
| glm-5.3-mtp | terse | d050 | 23/24 | 1.22 | 48.78 | 0 |
| glm-5.3-mtp | terse | exact | 24/24 | 0.34 | 57.38 | 0 |
| qwen38-27b-ollama | normal | exact | 18/24 | 23.66 | 4.83 | 10 |
| qwen38-27b-ollama | normal | native | 24/24 | 24.74 | 5.77 | 0 |
| qwen38-27b-ollama | terse | exact | 24/24 | 15.90 | 0.51 | 0 |
| qwen38-27b-ollama | terse | native | 23/24 | 23.45 | 2.73 | 0 |
| GLM int4 baseline | normal | d030 | 21/24 | 0.86 | 174.97 | 0 |
| GLM int4 baseline | normal | d030t12 | 21/24 | 0.92 | 161.49 | 0 |
| GLM int4 baseline | normal | d040t12 | 18/24 | 1.25 | 129.72 | 0 |
| GLM int4 baseline | normal | d050 | 17/24 | 1.54 | 120.44 | 0 |
| GLM int4 baseline | normal | exact | 21/24 | 0.41 | 297.62 | 0 |
| GLM int4 baseline | terse | d030 | 24/24 | 0.84 | 42.70 | 0 |
| GLM int4 baseline | terse | d030t12 | 24/24 | 0.81 | 44.01 | 0 |
| GLM int4 baseline | terse | d040t12 | 24/24 | 1.25 | 44.21 | 0 |
| GLM int4 baseline | terse | d050 | 24/24 | 1.44 | 43.97 | 0 |
| GLM int4 baseline | terse | exact | 24/24 | 0.41 | 44.42 | 0 |
