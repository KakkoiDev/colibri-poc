# What the results mean: correctness, tokens per second and expert memory

Our primary comparison is **generation tokens per second alongside correctness**.
Show prompt style, setting, graded count and truncation beside those numbers.
Answer time and prompt-reading time remain secondary: they explain responsiveness,
but do not replace the generation-throughput comparison. Rates for tiny outputs
are noisy; do not compare different prompt styles as an isolated engine speedup.

## Did terse prompts improve quality?

They improved the measured automatic score. Original GLM int4 exact rose from
21/24 normal to 24/24 terse while both averaged 0.41 generation tokens/s.
This does not show that the model became generally more capable. Short replies
fit the 128-token budget; verbose replies may be cut off. The numeric grader uses
the last number, code tests use the first code block, and fact checks look for
accepted text. Extra explanations can trigger a failure without proving the core
answer was wrong. The prompt-file note incorrectly says first number; the actual
grader checks the last. Explanation usefulness is not scored.

Use terse prompts for direct answers. To test general quality, give both styles
enough output budget and independently review the answers, including reasoning.
Native Ollama runs also change sampling/thinking and allow 4096 tokens, so they
are not a controlled test of wording alone.

## Why did extra GLM RAM barely help?

The 18/22/26 GB budget sweep measured 0.40/0.41/0.42 tokens/s, with expert hits
2.1/2.8/3.6%. Crucially, the RAM26 log still reports a dynamic cache of ONE expert
per layer (about 1.6 GB), plus 91 pinned experts (about 1.9 GB). The Metal fast-SSD
heuristic explicitly favors OS page cache and says to override capacity with --cap.
So these runs did not establish that a substantially larger dynamic expert cache
would be useless. RAM budget is not actual retained expert memory. Logical cache
misses also do not prove physical SSD reads: OS page cache may serve them.

## How can we improve caching?

1. **Test actual capacity first:** explicit 1/2/4/8 experts per layer, fixed pin set,
   no expert skipping, and memory preflight. Skip any unsafe capacity.
2. **Keep useful experts:** frequency-aware admission or a protected hot set can
   prevent one-use experts evicting repeatedly useful ones. Compare against LRU
   at the same retained-byte budget. This is a hypothesis, not a measured win.
3. **Allocate unevenly:** spend memory on layers with the largest avoided read
   cost per byte. Pinning already exists; the new experiment improves selection.
4. **Test prefetch separately:** a correct prediction may hide latency without
   improving demand-cache hits. Count useful and wasted reads and total time.
5. **Keep execution efficient:** avoid duplicate copies and repacking. OLMoE showed
   that better cache coverage alone does not remove transfer/packing overhead.

Preserving selected experts can preserve model computation, but changed kernels
may still change numeric output. Choosing different experts because they are in
cache is a separate **changes output** experiment, not an exact cache optimization.
Judge every proposal by tokens/s plus correctness, with memory and bytes read as
diagnostics; a higher hit percentage is not itself success.

## What is OLMoE?

[OLMoE](https://huggingface.co/allenai/OLMoE-1B-7B-0125) is Allen AI's open
mixture-of-experts model, approximately 7B total parameters with about 1B active
per token. Our 4-bit copy is about 3.9 GB. It is the small testbed used for the
resident/streaming experiments. It is not Qwen and those results do not establish
a Qwen speedup. OLMoE resident reached 199 median tokens/s versus 28/49/70 for
LRU capacities 8/32/64 in the same campaign; some outputs differed.

## Qwen experiment added: same model, different expert cache sizes

The campaign is specified in experiments/qwen-expert-memory.json, and registered
as sm-qwen36-a3b-ram-sweep. Use the downloaded Qwen3.6-35B-A3B Colibri int4 weights,
not the dense Qwen alias used in the existing quality table. Compare capacities
8/16/32/64/128/256 with unchanged routing, precision, threads and engine, three
paired repetitions, the same prompts, and normal/terse grading. Verify all-expert
residency from telemetry; 256 or a large RAM budget alone is not proof. Record
actual retained bytes, peak memory, demand hits and output changes. Skip profiles
that cannot safely fit. First-use and warmed results must stay separate.

**Status: specified, not run.** The isolated Qwen engine build and benchmark
adapter are prerequisites. The current Colibri Qwen path is CPU/Vulkan, not Metal;
this campaign must not be advertised as a Metal comparison. A RAM cap does not
simulate another machine's SSD. The GLM explicit-capacity campaign is separately
specified in experiments/glm-cache-capacity.json.
