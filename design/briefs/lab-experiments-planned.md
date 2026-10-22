# Brief: make the not-yet-run experiments understandable (lab app, Experiments)

For a Designer AI. Lab control app (`lab_app/`), screen **Experiments** (More tools ›
Experiments). Canvas: https://claude.ai/artifact/NUsd2xNrswXkng96jJtwSg, page "Lab
control app" (board `Lab-Experiments.dc.html`). Keep `lab.css` as it is.

The owner, 2026-10-22: "the ux is bad. I don't know what are the never ran experiments."

## What is wrong today

The **Planned** and **Ideas not run** tabs use the same table as finished experiments:
title, a code id (`stack-skip050-lookup-off`), category, then four columns of dashes
(verdict "Not run", tok/s, change, output) and a "Details" disclosure off the right edge.
For an experiment that has not run, every visible cell is empty or cryptic; what it tries,
why, whether it can start and what it is waiting for are hidden.

## What the owner needs to see, per not-yet-run experiment

- **What it tries**, in one plain sentence (`title`, then `change` in words).
- **Why it might help** (`hypothesis`).
- **Changes output?** The "changes output" tag when `lossy` (quality must be checked after).
- **Can it start?** One of three states, each a glyph and a word:
  - **Ready**: can run now; estimated time (`est_s`); buttons **Queue** and **Run now**;
    "Queued" when it already is (`queued`).
  - **Needs something**: what is missing (`needs`, e.g. "missing GLM-5.3 UD-IQ2_M; prepare
    with make glm-prep-iq2m"), with a link to Models when it is a download.
  - **Idea**: not runnable unattended; what it is waiting for (`needs`, e.g. "an external
    NVMe drive", "a qwen36 bench adapter").
- The code id only as secondary text (it is what the logs and links use).

## Suggested structure (improve if you see better)

- Group not-yet-run experiments by state: **Ready to run (9)**, **Needs something (1)**,
  **Ideas (15)**, each group a list of cards or rows sized for reading, not a results table.
- At the top of Ready: **Queue all ready**, with the total estimated time and a note that
  they run one after another, and that the quiet run also picks them up.
- Finished experiments keep today's results table (verdict, tok/s change, output), where
  those columns mean something.
- Phone: one column; the state and the main button stay visible without opening anything.

## Data (served today by `GET /api/experiments`)

Each entry: `id`, `title`, `category`, `change`, `hypothesis`, `lossy`, `verdict`,
`conclusion`, and, for `verdict == "not run"`: `status` (`ready` | `needs` | `idea`),
`needs` (text or null), `est_s` (ready and needs), `queued` (bool). Today: 9 ready,
1 needs, 15 ideas. Actions as today: `POST /api/queue/add` and `/api/run` with
`{kind: 'planned', args: {id}}`.

## Acceptance

- Without opening anything, the owner can say for every not-yet-run experiment what it
  tries, why, and whether it can start now.
- Ready experiments can be queued one by one or all at once.
- Nothing about finished experiments gets harder to read.

## Built ahead of the canvas (2026-10-22): "Not run yet" on the home page

The owner asked to find the never-run tests easily, so a first version was built without
waiting for the canvas (please redraw it; it should match whatever you do for Experiments):

- A **Not run yet** card on Run benchmarks, between the status tiles and the launch form.
- It lists every experiment that has never run **and** every standard bench an installed
  model has never had, in one list: ready and queued first, then "Needs something first",
  then ideas behind a disclosure. Items added since yesterday carry a **new** badge.
- Each item: title, one-line why (two lines max), "changes output" tag, state chip (Ready /
  Queued / Needs something / Idea), estimated time, and **Queue** when ready; "Needs: …"
  says what is missing.
- Header: counts ("9 queued · 2 need something · 15 ideas · 15 new since yesterday"),
  a link to All experiments and **Queue all ready (n, ~time)**. Everything queued from it
  waits for a quiet machine.
- Data: `GET /api/not-run` → `experiments[]` and `benches[]` with `title`, `why`, `status`,
  `needs`, `est_s`, `new`, `lossy`, `queue`; `counts`; `new`. Benches that one model cannot
  run for the same reason are merged into one row.
