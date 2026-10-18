# Brief: GLM performance page (GitHub Pages)

For a Designer AI. Build one static page that shows how GLM-5.3 got faster on the
user's 32 GB Apple M6, and what each speed-up costs. The page must be honest:
every chart shows its caveat, and lossy results never sit next to exact results
without a label.

## Audience and goal

- **Primary reader:** the owner and technically curious visitors to the public repo.
  They know what "tokens per second" means but not Colibri's internals.
- **One sentence the page must land:** "Exact tuning made GLM about 4× faster on
  this Mac; going further means trading answer quality, and 5 tok/s was not
  reachable here."
- Reading time: under 5 minutes for the story, with details on demand.

## Data (single source of truth)

- `site/data/glm-performance.json`: every number on the page. Load it at runtime
  or inline it at build time. **Do not retype numbers.**
- `published-results/glm-20261018/runs.csv` and `*.output.txt`: raw per-run
  numbers and generated text, for "view raw data" links.
- `published-results/glm-bench-v1/summary.json` (pending; the bench is still
  running): quality vs speed on 24 graded prompts. Design a slot for it now
  and show "pending" until the file exists.
- Background docs to link to, not to copy: `docs/11-glm-on-this-mac.md`,
  `docs/09-two-track-experiments.md`, `docs/10-next-experiments.md`.

Field notes: `tok_s` is generation speed (decode only). `prefill_s` is time to
read the prompt. `time_share_pct` splits generation time into SSD wait, expert
math, attention and other. `tau` is the skip threshold (0 = exact).

## Page structure

1. **Hero**: big numbers `0.10 → 0.43 tok/s` (exact, ~4.3×) and
   `→ ~1.5 tok/s` (lossy). A small "target 5 tok/s: not reached" badge. One line
   on the machine and model.
2. **Why it was slow**: three short cards, each with its fix:
   - single-threaded build (missing libomp) → install libomp;
   - CPU-only build → Metal;
   - no RAM left for an expert cache → explicit `--ram 18 --ctx 1024`.
3. **Exact speed-ups** (chart A + table): the step-by-step progression.
4. **Where the time goes** (chart B): stacked bars of `time_share_pct`, CPU vs Metal
   vs best exact vs lossy 0.5. They show the bottleneck moving from compute to SSD to
   attention.
5. **The hard ceiling** (chart C + D): SSD readers vs GB/s; cache size vs share of
   expert reads served. A callout with the arithmetic: 12.7 GB per token × 5 tok/s
   = 64 GB/s needed vs 6.5 GB/s available.
6. **Trading quality for speed** (chart E + quiz table): the threshold curve, with
   quality zones colored. Include the factual quiz table with correct/incorrect marks.
7. **Quality vs speed bench** (chart F, pending): accuracy and answer time per
   config × prompt style (normal vs terse).
8. **What didn't work**: a compact table of negative results (`exact_negative`,
   `lossy_cache_route`, `vulkan`). Negative results are first-class content.
9. **How to run it**: copyable commands (exact and lossy, from docs/11), with
   the warnings about `COLI_METAL_SPIN` power use and `--ctx 1024`.
10. **Caveats and method**: the `caveats` array verbatim, plus links to raw data.

## Charts

| ID | Data | Type | Notes |
|---|---|---|---|
| A | `exact_progression` | horizontal bar, tok/s | Start with a ghost bar for the user-reported 0.10. Label each bar with tok/s and ×-speedup vs 0.10. Same color for all exact bars. |
| B | `exact_progression` (CPU, Metal, best) + `lossy_threshold_curve` tau 0.5 | 100% stacked bar | Segments: SSD wait, expert math, attention, other. Same segment colors everywhere. |
| C | `ssd_readers_gbs` | line with points | Annotate "more readers don't help past 2". |
| D | `cache_projection` | line, x = cache GB (log scale), y = % served | Mark "~5 GB: what this Mac can spare" and "~100 GB: ~82%". Note the small sample. |
| E | `lossy_threshold_curve` + `code_prompt` | line, x = tau, y = tok/s | Background bands by `quality`: identical → reworded → errors → broken. Exact point distinct. Second series for the code prompt. |
| F | bench `summary.json` | scatter, x = mean answer time s, y = % correct | One point per config × style; shape = style, color = config. Pending state until the data exists. |

Chart rules:
- **Exact and lossy are visually distinct everywhere**: e.g. solid vs hatched, or
  two hues. Lossy always carries a "changes output" tag.
- Axes start at zero for tok/s bars. No 3D, no dual axes.
- Every chart has a one-line caption saying what to notice, and a footnote with
  run count ("single run").
- Tooltips show the run ID, which links to its raw output text.
- Colorblind-safe palette; text contrast WCAG AA; works in light and dark.

## Tables

- **Exact progression**: setting, tok/s, × vs 0.10, SSD share, output same as
  baseline (all ✓).
- **Lossy curve**: threshold, tok/s, % expert loads skipped (from `zeroed_slots`),
  quality note.
- **Quiz**: from `quiz.rows`, with ✓/✗ per cell (the Japanese row is the
  instruction-following regression).
- **Negative results**: what was tried, result, one-line why.

## Tone and wording

- Plain language. Define "expert", "token/s" and "skip threshold" once, in a
  small glossary or inline tooltips.
- Never write "lossless" for anything with tau > 0. Use "changes output".
- Never imply 5 tok/s was achieved, or that results transfer to other machines.
- Credit Colibri (JustVugg/colibri) and link it.

## Technical constraints

- GitHub Pages, static. Prefer one `index.html` under `site/` plus the JSON. No
  build step required. A small chart library from a CDN is fine (e.g. Chart.js,
  Observable Plot or Vega-Lite), pinned to an exact version.
- Responsive down to 375 px wide; tables scroll horizontally on mobile.
- No tracking or analytics. No local paths (`/Users/...`) anywhere in the output.
- Page must still read correctly if the pending bench file is missing.

## Acceptance checklist

- [ ] Every number on the page traces to `glm-performance.json` or `summary.json`.
- [ ] Hero shows exact (~4.3×) and lossy (~15×) separately, plus "5 tok/s not reached".
- [ ] Exact vs lossy are distinguishable without color alone.
- [ ] The ceiling arithmetic (12.7 GB/token, 6.5 GB/s, 64 GB/s needed) is visible.
- [ ] The negative-results section exists and includes Vulkan, mmap, PILOT and CACHE_ROUTE.
- [ ] The caveats are on the page, not only in a linked doc.
- [ ] Works at 375 px and in dark mode; passes an accessibility contrast check.
