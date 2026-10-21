# Brief: bring the lab-app canvas up to date with the app

For a Designer AI. The lab control app (`lab_app/`, http://127.0.0.1:8766) was reorganised
in code on 2026-10-20 without going through the canvas. On 2026-10-22 its look was put back
to the canvas's (your `project/lab.css`: serif, ink on paper, square corners, booktabs
tables, small-caps labels). **The look is settled; the canvas is now missing the app's
screens and navigation.** Please draw them so the canvas is the source of truth again.

Canvas: https://claude.ai/artifact/NUsd2xNrswXkng96jJtwSg (page "Lab control app").

## Ground rules

- **Keep `project/lab.css` as it is.** Use its tokens and components (cards, `.btn`,
  `.chip` st-*, `.tag-exact` / `.tag-lossy`, `.tbl` booktabs, `.tabs`, `.dialog`, `.kv`,
  `.meter`, `.eyebrow`). If a new component is needed, add it to `lab.css` and to the
  Component set board.
- Draw what the app does today (below). Where you think the flow should change, draw it
  as a separate variant with a note; don't change the main boards silently.
- Desktop boards at 1440 px, phone boards at 390 px, light and dark via the theme prop.
- Sample values are fine; label them as such in the gaps note, as before.
- Reference screenshots of the current app (taken in the old sans look, so use them for
  content and layout, not style): `docs/lab-app/screenshots/*.png` in the repo
  (dashboard, results, results-speed, results-coverage, models, models-downloading,
  queue, bench-v1, dialog-remove; `-narrow` = phone, `-dark` = dark).
- Behaviour and data are documented in `docs/lab-app/design-system.md` (screens,
  tables, forms, accessibility) and `docs/14-dashboard.md` (everyday use).

## 1. Navigation (update `Lab-Nav.dc.html`)

Today the sidebar is task-first:

- **Run benchmarks** (`#dashboard`, the start page)
- **Results** (`#results`)
- **Models** (`#models`; the old Install screen is merged into it)
- **Open on phone** (`#phone`)
- **More tools** (a disclosure, open when one of its screens is active): Queue and logs,
  Select several benches (the picker), Machine status (old Now), Engine runs, Leaderboard,
  Experiments, Research, Settings.
- Foot: GPU status chip with the running job and PID, theme selector (Auto / Light /
  Dark), and "Local + private Tailscale".
- Below 860 px it becomes a sticky top bar: brand, GPU chip, theme; the links wrap below;
  More tools opens full width.

Please also say which old boards this retires or renames: Lab-Now → Machine status,
Lab-Install → merged into Models, Lab-Benches → Results · Coverage, Lab-Runs →
Results · Speed runs (or Engine runs).

## 2. Run benchmarks (new board, desktop + phone)

The start page. Top to bottom:

1. **Header**: "Run benchmarks" and one sentence ("Choose a model and a benchmark, then
   queue it. Jobs run one at a time, in order.").
2. **Three status tiles**: *Running now* (job and "74% · done ~01:58", or "Nothing
   running"), *Queue* ("15 waiting · all done ~05:16", or "paused"), *Machine* ("Busy" /
   "Quiet", "6.3 GB RAM free · quiet needs ≥ 20 GB").
3. **New benchmark run** card, a three-step form with numbered steps:
   1. *Model* (select; hint with the engine; "This model has nothing to run…" when empty);
   2. *Benchmark* (select, grouped; "3 of 13 can be queued now. Unavailable ones show why.");
   3. *When may it start?*: two radio cards, "When the GPU is free" and "Only on a quiet
      machine (≥ 20 GB RAM free for 2 min)", plus a checkbox "Run it next (put it at the
      front of the queue)".
   - A **plan panel** beside or below: benchmark description, *Estimated time*, *Already
     saved* (answers kept from an earlier run), *Queue position*, expected start (e.g.
     "tomorrow 06:03").
   - **One button** whose label says what happens: *Start benchmark*, *Queue benchmark*,
     *Queue and resume* (queue was paused), or *Cannot queue this benchmark* with the reason.
   - Link "Select several at once" (to the picker).
   - **After the click**: a confirmation block (ok colour) naming the job, its position and
     expected start, with links to the queue and to the results. It takes focus.
4. **Running now**: job title, tags (bench kind, "changes output" when lossy), progress
   meter with "89/120 answers · 74% · done ~01:58", *Now answering* (prompt, style,
   setting), PID and a *Stop…* button (opens the existing stop dialog). A disclosure
   "Every case in this bench" shows the per-answer strip (done / correct / wrong /
   running / waiting). An engine the lab did not start shows "Not started by the lab (e.g.
   your own Colibri session): the app never stops it."
5. **Up next**: the first five waiting jobs, numbered (the next one in solid ink), each with
   estimate, start condition ("when quiet") and expected start; link "Reorder and view
   logs" to the queue. Empty: "Nothing waiting. Queued benchmarks appear here…". Paused:
   "Nothing queued starts until you resume."
6. **Recently finished**: done and failed jobs, time, headline result, and **Resume · N
   remaining** on interrupted or failed benches.

States to draw: idle (nothing running, empty queue), running (as above), just launched
(confirmation visible), queue paused, and a failed job in Recently finished.

## 3. Results (new board, desktop + phone; three tabs)

Header "Results" with one action, "Run a benchmark". Tabs: **Answer quality** (count),
**Speed runs** (count), **Coverage** (count).

- **Answer quality**: filters *Model*, *Answer style*, *Output* (exact and lossy / exact
  only / lossy only) and *Sort by* (presets such as "Correct: highest first",
  "Speed: fastest first"), a live row count ("60 of 60 setting × style combinations.
  Bold = best value among the rows shown."). One booktabs table, one row per bench ×
  setting × style. Columns in order: *Model* (bench · answer style), *Setting* (with the
  exact or "changes output" tag), *Correct* (% graded, with "24/24"), *Speed* (tok/s),
  *Answer time* (s, mean), *Prompt read*, *Generated* (tokens), *Same as exact*,
  *Answers* (link to every answer), *Settings* (disclosure with the engine flags).
  Units sit on a second header line; the best value per column is bold; the first column
  stays put while the rest scrolls sideways; sortable headers show ▲ / ▼ / ↕.
  A note under the table explains the automatic grading.
- **Speed runs**: every engine run (`results/runs.csv`), with a search box and
  "Successful runs only". Columns: *Run*, *Model*, *Speed* (tok/s), *Prompt read* (s),
  *Expert hits* (%, cache), *Memory* (GB, process), *Threads*, *Duration*, *Status*,
  *Saved*, *Settings* ("Show" reveals the flags).
- **Coverage**: which standard benches each model has (done / running / queued / missing /
  failed cells, with "Queue" per missing cell), then the standard suite definitions.
- **Answers page** (`#bench/<name>`, reached from *Answers*): every generated answer of
  one bench, filtered by style, setting and grade; each answer shows prompt, grade, time
  and text.

## 4. Models (replace `Lab-Models` and `Lab-Install`, desktop + phone)

Header "Models": "What is installed, how much space it uses, and what you can download or
remove. Removing moves folders to the Trash; results are kept."

- **Disk** card: "Measured now · warns below 30 GB free"; *Free*, *Lab models*, *Other
  model folders*, *Still to download*; a stacked bar (lab models, other folders, free)
  with a legend; "Not managed by the lab: …" list; a warning when under 30 GB free.
- **Downloads** card: chip (idle / downloading / failed), progress meter in GB,
  "Resumable: downloaded parts are kept.", *Stop download…*; idle text "No download
  running. Start one from the table below; one download runs at a time."
- **All models** table (count, "6 installed"): *Model* (name, format, notes), *Status*
  (installed · your model / installed / not installed / downloading), *On disk*
  (measured), *Download* (size), *Benches run* (of the standard set), *Action*:
  *Download…* (opens the existing download confirmation), *Move to Trash…* (opens the
  remove dialog), or the reason it cannot ("Protected: never changed by the app",
  "In use by a running job: stop it first", "Wait for the running download").
  *Details* disclosure per row. Note: "Ollama models are managed by Ollama … and are not
  listed here."

## 5. Open on phone (new board, desktop + phone)

"Open on your phone or tablet": "Connect the other device to Tailscale using your
account, then scan this code or open the address." A QR code (256 px, black on white,
inside a ruled frame), the private Tailscale address as text with a copy action, and the
state when Tailscale is not set up (what to do, no QR). The app is also installable as an
app (PWA); a line on "Add to Dock / Install" fits here.

## 6. Housekeeping on the canvas

- Update the **Component set** with anything new: status tiles, numbered step, radio card
  (`.choice`), plan panel, launch confirmation, per-answer strip, disk bar and legend,
  sortable header with unit line, frozen first column.
- Move the boards that no longer exist as screens to an "Archive" row (or delete them),
  so the canvas shows the app as it is.
- Keep the Start benches picker boards; they match the app.

## Acceptance

- Every route in the app has a board: `#dashboard`, `#results` (three tabs), `#bench/…`,
  `#models`, `#phone`, and the More tools screens (existing boards are fine where they
  still match).
- The nav board matches the app's grouping and labels.
- Light and dark, 1440 px and 390 px for the four new main screens.
- Nothing in `lab.css` changes look; additions only.
