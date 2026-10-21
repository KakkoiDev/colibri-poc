# Brief: one coherent public site (GitHub Pages)

For a Designer AI. Supersedes [bench-page-tabs.md](bench-page-tabs.md), which was never
drawn and is folded in here. Canvas: https://claude.ai/artifact/NUsd2xNrswXkng96jJtwSg,
page "Results page" (it holds `Main.dc.html`, the report).

Live site: https://kakkoidev.github.io/colibri-poc/ (source: `site/` in the repo).

## Why: the site grew into a mess

Automated publishing and several work sessions added pages and data faster than the design:

| Page | State today |
|---|---|
| `index.html` Report | Paper theme. The GLM-5.3 speed story. Links only to `bench.html`. |
| `bench.html` Bench | Paper theme, but shows **1 of 9** published benches (GLM v1) and prints **all 240 answers inline**: the page is ~284,000 px tall. |
| `comparison.html` | Plain unstyled HTML. GLM vs Gemma vs Qwen guidance and a table of every setting. |
| `findings.html` | Plain unstyled HTML. What the results mean, cache experiments, OLMoE. |
| `speed.html` | Different ad-hoc style (system font, blue). Table of 107 engine runs. No navigation. |

There is no shared header, so a reader cannot find most of it, and two styles mix.

## Goal

One small site that reads like a set of technical notes, in the paper theme you designed
(Source Serif 4, ink on paper, booktabs tables, square corners, 760 px text column, wider
only for tables). A visitor should be able to answer, in this order:

1. **Which model and setting should I use on a Mac like this?** (comparison + guidance)
2. **How good and how fast is each one?** (per-bench results, every answer on demand)
3. **Why?** (findings, the GLM speed story, raw speed runs)

## Structure (proposal; improve it if you see better)

A shared header on every page: site name, links **Report · Benchmarks · Findings · Speed
runs · Repository**, and the Auto / Light / Dark switch (already on `bench.html`; remembered
per browser, applied before first paint).

1. **Report** (`index.html`): keep the existing design; only the header changes, and its
   "Quality vs speed bench" section links to Benchmarks.
2. **Benchmarks** (`bench.html`): the core page.
   - **Compare** tab first (default): the guidance from `comparison.html` ("Which should I
     use?", "Where Qwen fits", "How to read this") above one trade-off table and one figure:
     correct answers (y) against answers per minute or tok/s (x), one point per model ×
     setting × style, labelled. Lossy settings hatched and tagged "changes output".
     Published intelligence scores as context (GLM-5.3 45, Qwen3.8-27B 34, from
     `models/external-benchmarks.json`), clearly marked as reported by others.
   - **One tab per bench**, grouped: *GLM-5.3 on Colibri* (int4 `v1`, + int8 MTP head,
     UD-IQ3_XXS, UD-IQ2_M) and *Ollama, fully in RAM* (Qwen3.8-27B, Gemma 4 26B,
     Gemma 4 31B, Gemma 4 E4B, gpt-oss 20B). Nine tabs need a scalable pattern: a grouped
     tab row that scrolls, a select on phones, or a short model list beside the content.
   - Inside a bench: **Results** (summary table + answer-time figure), **Manual review**
     (only where one exists, today v1), **Answers**, **Method and data**. Hide empty sections.
   - **Answers are never all printed at once.** Default: a compact table (question ×
     setting × style with ✓ / ✗ and time); opening a cell or row shows that answer. Filters
     (style, setting, question, grade) and paging (e.g. 20 at a time).
3. **Findings** (`findings.html`): the same prose and numbers, in the paper theme, with
   numbered sections and figures for the GLM cache sweep (RAM budget vs tok/s and hit rate).
4. **Speed runs** (`speed.html`): the 107-run table in booktabs style with search and
   sorting, units on a second header line, the time-share columns (SSD / matmul /
   attention) as a small stacked bar, and a note on what busy-machine runs mean.

`comparison.html` becomes a redirect to `bench.html#bench=compare` (old links keep working).

## Shareable links (required, from the earlier brief)

- `bench.html#bench=<name>&tab=<section>`, plus for Answers `&style=&config=&q=&grade=`,
  and `&answer=<question>__<style>__<config>` to open and scroll to one answer.
- `bench.html#bench=compare` for the comparison.
- Changing tab or filter updates the hash (Back works between tabs). Unknown values fall
  back silently. A small "copy link" control on section headings and on each answer.
- Old links keep working: `bench.html`, `bench.html#answers`, `bench.html#data`.

## Data (all already published; load at runtime, never retype numbers)

- `site/data/benches.json`: the 9 benches, `{name, file, answers, engine, model}`; order
  is tab order, `v1` first.
- `site/data/bench-<name>.json`: one bench (summary rows, every answer with prompt, text,
  grade, times; manual review where present; labels for settings).
- `site/data/bench-compare.json`: one row per bench × setting × style: `correct`, `graded`,
  `median_answer_s`, `mean_answer_s`, `median_prefill_s`, `mean_tok_s`,
  `correct_per_min`, `truncated`; `labels` names the settings.
- `site/data/completed-comparison.json`: 56 rows `{model, style, config, runs, correct,
  graded, tok_s, median_s, truncated}` behind today's comparison page.
- `site/data/findings.json`: findings content (terse vs normal, GLM cache sweep:
  `ram_budgets_gb`, `decode_tok_s`, `hit_pct`; OLMoE; the planned Qwen memory experiment).
- `site/data/speed-runs.json`: 107 runs `{run, backend, omp_threads, prompt_tokens,
  prefill_s, decode_tokens, decode_s, tok_s, hit_pct, rss_gb, io_pct, matmul_pct,
  attn_pct}` (numbers are strings today).
- `site/data/glm-performance.json`, `experiments.json`: the report's data.

Settings differ by engine. Colibri: `exact` and skip settings (lossy, always tagged
"changes output"). Ollama: `exact` (thinking off, temperature 0, 128 tokens, comparable
with Colibri) and `native` ("Ollama defaults (thinking on)": one sample, up to 4096 tokens).

## Constraints

- Static GitHub Pages, no build step, no framework; vanilla JS. External fonts from Google
  Fonts only.
- One stylesheet for the whole site (today each page carries its own `<style>`); the paper
  tokens already in `bench.html` are the base, light and dark.
- Phone width: no horizontal page scroll; wide tables scroll inside their box with the
  first column frozen.
- Accessible: real tabs (`role="tablist"`, arrow keys), labelled filters, figures with text
  alternatives, colour never the only signal.
- Every page states the busy-machine caveat where it shows timings, and no author name
  (removed on purpose).
- Pages are rewritten by automated publishing: keep content in the JSON files, so a new
  bench appears by adding `bench-<name>.json` and a row in `benches.json`, with no HTML edit.

## What to draw

- Shared header (desktop and phone).
- Benchmarks: Compare tab; one bench's Results; Answers (table + one opened answer +
  filters); the bench switcher with 9 benches; phone versions of these.
- Findings and Speed runs pages, desktop and phone.
- Light and dark for the Benchmarks Compare tab at least.

## Acceptance

- Every published bench is reachable from Benchmarks; adding a 10th needs no HTML change.
- `bench.html` is a normal page length; answers load on demand.
- One look and one header across Report, Benchmarks, Findings and Speed runs.
- The deep links above open the right bench, tab, filters or answer.
