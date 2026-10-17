# First results: the lab works, no optimization winner yet

18 October 2026, Apple M6 Mac mini, 32 GB unified memory. MLX 0.32.4,
MLX-LM 0.32.2. Model revision and file checksums are pinned in the repo.

Campaign: `results/20261017T161556.968805Z/` (folder names use UTC).
Two rounds, three variants, five measured prompts per round, up to 128 output
tokens per prompt. All six workers completed. One warmup request per worker
was excluded. Each variant loaded the same 3.89 GB OLMoE 4-bit weights on Metal.

| Variant | Median decode tokens/s across requests | Median paired ratio | Exact output vs baseline |
|---|---:|---:|---|
| baseline, prefill chunk 512 | 67.07 | 1.00 | reference |
| chunk 1024 | 50.56 | 0.95 | differs on long prompt |
| chunk 256 | 64.60 | 0.91 | differs on long prompt |

The median speed ratio is calculated per matched prompt and round, so it is not
the ratio of the two headline medians. Min/max in summary JSON span different
prompts as well as rounds; they are not a confidence interval.

**Do not declare a winner from this campaign.** Decode speed varies widely
between requests. Prefill chunk size primarily targets prompt processing, not
decode speed. These short and long workloads should be analyzed separately
and repeated under controlled machine load before selecting a setting.

Both candidates changed token IDs on the long-context prompt, in both rounds.
Short-prompt outputs matched. The baseline matched itself across both rounds.
Output lengths were equal. Different chunking can change numerical ordering,
but we have not diagnosed the exact cause of the differences or evaluated their
quality. The runner correctly exposes the differences instead of claiming a
quality-preserving speedup.

This measures a small **resident** model. It does not establish any improvement
for the user's large streamed GLM-5.3 model, reported at 0.1 token/s.

A later smoke campaign verifies that the final runner uses frozen copies of
its own code, prompts and optional plugin code. Smoke token limits are too
short for performance conclusions. Unit tests cover paired comparisons,
failed/missing runs, warmup exclusion and changed outputs.
