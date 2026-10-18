# Brief: pick and start any set of benches (lab control app)

For a Designer AI. Add a **bench picker** to the GLM lab control app (local web app,
`lab_app/`, built from [lab-control-app.md](lab-control-app.md)). The owner wants to start
any bench, or any collection of benches, from one well-organised list with checkboxes.

## Today and the problem

The Benches screen has a coverage table (model × standard bench, one Run button per
cell) and a "Run a bench" card: one model, one bench, then options. Starting a set
(e.g. "Qwen on Ollama, both settings, both styles, plus the RAM sweep") takes many trips,
and Ollama models, quiet runs and planned experiments live on other screens.

## Data (already served; do not hard-code any list)

`GET /api/bench-catalog` returns:

- `groups`: `id`, `title`, `engine` (`Colibri` | `Ollama`), `note` (why the group cannot
  run, e.g. "not installed", or a condition like "need ≥ 20 GB free for 2 min").
  Order: Colibri models (main model first), Ollama models, Quiet runs, Planned experiments.
- `items` (~130 today): `id`, `group`, `title`, `what`, `kind` (`suite` | `bench` | `quiet` |
  `planned`), `available`, `why_not` (e.g. "complete", "not installed"), `done` / `total`
  (answers already recorded, quality items only), `est_s` (estimated duration),
  `only_when_quiet`, `lossy` (skip settings change the output: show the existing
  "changes output" tag).
- `presets`: `id`, `title`, `ids` (e.g. "Small models vs GLM", "Every ready planned
  experiment", "Standard benches for <model>"). Only presets with something available.

`POST /api/queue/add-selection` with `{ids: [...], front: bool, only_when_quiet: bool}`
queues the selection (the server merges quality items into as few jobs as possible and
runs them in catalog order) and returns `queued` (the queue items). All-or-nothing: an
error queues nothing and returns a message naming the bad ids. POSTs need the
`X-Lab-Action: 1` header, as today.

Quality items are one cell of **setting × prompt style** per model:
Colibri `exact`, `skip 0.3`, `skip 0.5`, `skip 0.3 · 12 threads`, `skip 0.4 · 12 threads`;
Ollama `exact` and `Ollama defaults (thinking on)`; styles `normal`, `terse`.

## What to design

1. **Where it lives:** a "Start benches" view reachable from the Benches screen and from
   the Now screen's queue card. It can replace the "Run a bench" card.
2. **Organisation:** one collapsible section per group, with its engine and note. Inside a
   model group:
   - standard benches (speed, threads, RAM) as a checkbox row;
   - quality items as a small **matrix**: settings as rows, styles as columns, a checkbox
     in each cell showing progress (`18/24`) or "complete".
   Unavailable items stay visible but disabled, with `why_not` on hover or as a hint.
   Unavailable groups (not installed, needs an adapter) collapse by default.
3. **Selecting:** checkbox per item; "select all" per group and per matrix row or column;
   presets as one-click chips that tick their items (adding to the current selection);
   "clear". A search or filter box (by model, engine or kind) is welcome since the list
   will grow.
4. **Selection summary (sticky footer or side panel):** count, total estimated time
   (sum of `est_s`), how many wait for a quiet machine, and the list of what will run,
   each removable. Buttons: **Add to queue** (primary), **Add to the front of the
   queue**, and a checkbox "only start when the machine is quiet" (forces it for all).
5. **After queueing:** a toast naming what was queued, the selection clears, and a link
   to the queue/timeline.

## Rules the UI must keep visible

- One GPU job at a time: queueing never starts two things at once; the summary says
  "runs one after another".
- Lossy settings always carry the "changes output" tag.
- Quiet-only items show a small "waits for quiet" marker.
- Nothing is downloaded from here: uninstalled models link to the Install screen.

## Acceptance

- Choosing the "Small models vs GLM" preset and pressing Add to queue queues the Qwen
  Ollama bench (exact and Ollama defaults, both styles), plus GLM's everyday terse run
  when that one is not already complete.
- Ticking three settings in one style column queues one job, not three (the server merges
  per model and style).
- Works at phone width; keyboard reachable; follows `lab.css`.
