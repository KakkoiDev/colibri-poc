# Brief: one place to start any bench (lab app, Run benchmarks)

For a Designer AI. Lab control app (`lab_app/`). Canvas:
https://claude.ai/artifact/NUsd2xNrswXkng96jJtwSg, page "Lab control app". Keep `lab.css`.

The owner, 2026-10-22: "there is no way to start jobs easily. check what other benching
programs [do] to copy a really good UX. tired of that broken page."

## What is broken today (measured on the live app, 22 Oct)

- **Almost nothing can start.** Of the 120 bench items in the catalog, 7 can be queued:
  34 are greyed out as "complete" (they ran once, so there is no way to run them again),
  65 say "not installed" (models that were moved to the Trash still appear) and 13 wait for a
  Qwen adapter. In the model select, 12 of the 13 models read "nothing to run".
- **Five places start a job, each with its own rules:** the 3-step form on Run benchmarks,
  "Select several benches", the home "Not run yet" card, Experiments, and the quiet run.
- **Results and runs are kept apart.** Starting a bench never shows what it scored last time,
  and "Recently finished" shows "done" with no number.
- **The form asks too much in order:** model, then a long list of greyed-out benchmarks, then
  "When may it start?" with three options, then a summary, then Start.

## What good bench tools do (to copy)

- **Dagster, asset graph:** every asset shows a status (missing, stale, fresh). You pick
  assets and press one **Materialize** button, and shortcuts select "missing" or "stale". It
  never auto-skips done assets on purpose: running something again is always allowed.
  ([virtual assets and staleness](https://docs.dagster.io/guides/build/assets/virtual-assets),
  [staff answer on not skipping](https://discuss.dagster.io/t/8595572/i-find-downstream-assets-materialization-won-t-run-if-upstre))
- **promptfoo, results viewer:** a matrix with models as columns and tests as rows. Every
  cell shows its result, and **Edit and re-run** starts the same evaluation again.
  ([web UI](https://promptfoo.dev/docs/usage/web-ui/))
- **GitHub Actions:** a finished run has **Re-run all jobs** and **Re-run failed jobs**. A
  confirmation lists exactly what will run.
  ([partial re-runs](https://github.blog/news-insights/product-news/save-time-partial-re-runs-github-actions/))
- **Phoronix Test Suite:** passing a saved result runs the same tests again and shows the new
  numbers next to the old ones.
  ([9.0 result viewer](https://www.phoronix.com/review/phoronix-test-suite-90))

The common idea: **the results grid is the launcher.** You look at what you have, select
cells, and run them. "Run again to compare" is normal, not an error.

## Proposal (improve it)

**One screen, "Run", replacing the 3-step form, "Select several" and the queue buttons on
the home card.**

1. **A matrix.** Rows are installed models: Colibri models first, then Ollama models.
   Columns are the standard benches: Speed, Threads, RAM, and Quality split by style
   (normal, terse) and setting (exact, skip 0.3, …). Experiments get their own tab with
   the same rows and states.
2. **Each cell shows the last result, or why it cannot run:**
   - a number and date (e.g. "0.44 tok/s · 21 Oct", "17/24 · 22 Oct");
   - **never run**;
   - **failed** (link to the log);
   - **queued #3** or **running 2/24**;
   - **can't run**, with a one-word reason and the full reason on hover or tap (e.g.
     "adapter", "download").
   Lossy settings carry "changes output". Cells that cannot run never get a checkbox.
3. **Click cells to select them.** You can also click a row or column header. Shortcuts
   above the grid: **Select never run**, **Select failed**, **Clear**. Done cells can be
   selected: that is "run again".
4. **A sticky bar at the bottom** whenever something is selected: "**4 selected · about
   16 min** · [Start when: GPU free ▾ / quiet machine] · **Run**". Over an hour or more than
   ten items, a confirmation lists them (the GitHub pattern).
5. **The queue in a side panel:** what runs now, with progress; what's next, in order, with
   remove and reorder. On a phone it becomes a bottom sheet.
6. **Every result screen links back:** "Run again" on a result row selects that cell and
   opens the bar.
7. **Models that aren't installed** go in one collapsed line ("4 models not installed ·
   Models"), not as greyed-out rows.

## Data that exists today

- `GET /api/bench-catalog`: every item, with `id`, `group` (model), `kind`, `style`,
  `setting`, `available`, `why_not`, `est_s` and the queue job.
- `GET /api/benches`: coverage per model and bench, with the last result.
- `GET /api/experiments`: experiments with `status`, `needs`, `est_s`, `queue_pos`.
- `POST /api/queue/add-selection` with `{ids, only_when_quiet}` already queues several
  catalog items. The back end will allow re-running a "complete" item. Today "complete"
  only blocks the item in the catalog.

## Acceptance

- From one screen, the owner can start any bench or experiment that can run, including
  one that already ran, in two clicks: select, then Run.
- Every cell shows the last result or why it cannot run, without opening anything.
- Nothing greyed out is shown without its reason. Models that aren't installed don't fill
  the grid.
- On a phone, the matrix scrolls sideways inside its own frame, with the model column
  fixed, and the Run bar stays visible.

## Built directly (2026-10-22, the owner asked not to wait for the canvas)

Run benchmarks is now this matrix (`GET /api/run-matrix`), with a normal/terse switch for the
quality columns, "Select never run", "Select failed", whole-row and whole-column selection,
quiet runs and planned experiments as checkboxes under the grid, and a sticky Run bar with
the start condition. What runs now and the queue sit below the grid rather than in a side
panel. The 3-step form, "Select several benches" and the home "Not run yet" card are gone.
Finished quality benches queue as "run again" (`glm_bench --rerun`; the old answers move to
`attempts/rerun-<time>/`). Not done yet: "Run again" links from the result screens.
Please redraw it on the canvas so the two match again.
