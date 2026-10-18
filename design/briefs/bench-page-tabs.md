# Brief: bench page with one tab per bench, and shareable links

For a Designer AI. Update `site/bench.html` (the scientific-paper theme: Source Serif 4,
760 px column, booktabs tables) so it can show several quality benches, not just GLM's,
and so any view can be shared as a URL.

## Why

The page shows one bench today: GLM-5.3 on Colibri (`v1`). A second one is coming:
Qwen3.8-27B running normally in Ollama, fully in RAM (`qwen38-27b-ollama`). The owner
wants to see the **trade-off** between them: GLM is smarter on published scores (45 vs
34) but takes minutes per answer here, while Qwen answers in seconds. More benches will
follow (Qwen3.6-35B-A3B, lower-RAM profiles), so the design must scale to ~6 benches.

## Data (load at runtime, never retype numbers)

- `site/data/benches.json`: the list of benches. Per bench: `name`, `file`, `engine`
  (`Colibri` or `Ollama`), `model`, `answers`. Order = tab order; the first is the default.
- `site/data/bench-<name>.json`: one bench, same shape as today's `bench-v1.json`
  (summary rows, every answer, manual review, labels), plus `engine` and `model`.
- `site/data/bench-compare.json`: every bench in one table. Per row: `bench`, `model`,
  `engine`, `style`, `config`, `correct`/`graded`, `median_answer_s`, `mean_answer_s`,
  `median_prefill_s`, `mean_tok_s`, `correct_per_min`, `truncated`; `labels` names the
  configs.

Config labels differ by engine. Colibri: `exact` and skip settings (lossy: label them
"changes output", as today). Ollama: `exact` (thinking off, temperature 0, 128 tokens,
comparable with Colibri) and `native` ("Ollama defaults (thinking on)": the model's
default thinking level and sampling, up to 4096 tokens; one sample, so grades vary a
little between runs). `truncated` counts answers that hit the token limit.

## Structure

1. **Title, abstract, key results**: stay, but describe the bench in the selected tab.
2. **Bench tabs** under the key results, one per bench in `benches.json`, plus a final
   **Compare** tab. Tab label: model + engine, e.g. "GLM-5.3 · Colibri",
   "Qwen3.8-27B · Ollama".
3. **Section tabs inside a bench**: Results (table + figure), Manual review, Answers
   (appendix with filters), Method and data. Hide a section tab with no data (e.g. no
   manual review yet) instead of showing it empty.
4. **Compare tab**: the trade-off table from `bench-compare.json`, one row per model ×
   setting × style, plus one figure: correct answers per minute (x) against correct
   answers out of 24 (y), one point per row, labelled. Notes under it: published
   intelligence (GLM-5.3 45, Qwen3.8-27B 34, from `models/external-benchmarks.json`), and
   the busy-machine caveat for GLM runs.
5. **Pending bench**: a bench with 0 answers shows its tab with "running / queued" and the
   method, not an empty table.

## Shareable links (required)

- The URL hash holds the view: `bench.html#bench=<name>&tab=<section>`, with optional
  filters for the Answers tab: `&style=terse&config=native&q=<question id>`, and
  `&answer=<key>` to open and scroll to one answer
  (key = `<question>__<style>__<config>`).
- Opening such a URL selects that bench and tab and scrolls to it (or to the answer).
- Changing tab or filters updates the hash with `history.replaceState` (tab changes may
  push, so Back works between tabs). Unknown values fall back to the defaults silently.
- A small "copy link" control on each section heading and on each answer.
- Old links keep working: `bench.html` alone and `bench.html#answers` open the first
  bench as today.

## Constraints

- Static GitHub Pages, no build step, no frameworks; vanilla JS as today.
- Same paper theme, light and dark; tabs read as a paper's navigation (small caps,
  underline for the active one), not app pills.
- Phone width: tabs scroll horizontally inside their row, never the page.
- Accessible: `role="tablist"`/`tab`/`tabpanel`, arrow keys move between tabs.

## Acceptance

- `bench.html#bench=qwen38-27b-ollama&tab=answers&config=native` opens the Qwen bench's
  answers filtered to the native setting.
- `bench.html#bench=compare` shows the trade-off table and figure.
- Adding a bench needs only a new `bench-<name>.json` and a row in `benches.json`.
