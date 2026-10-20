# Lab app design system

The lab control app (`lab_app/`, served on `http://127.0.0.1:8766`) has three jobs:

1. **Run benchmarks**: pick a model and a benchmark, queue it with one action, see what runs now and what runs next.
2. **Results**: compare measured values in tables with units, open the settings and the generated answers.
3. **Models**: see what is installed, how much disk it uses, download progress, and remove unused models.

Everything else (the queue editor and logs, the multi-select bench picker, machine status, engine runs,
leaderboard, experiments, research, settings) sits under **More tools** in the sidebar.

The design system lives in one stylesheet, `lab_app/static/lab.css`. The interface is rendered by
`lab_app/static/app.js` with a small `h()` DOM helper. Lab text (answers, logs, titles) is always inserted as text, never as HTML.

## Screens

| Route | Screen | What it shows |
|---|---|---|
| `#dashboard` | Run benchmarks | Status tiles, the three-step launch form with a plan panel, a launch confirmation, the running job, the next jobs and recently finished jobs |
| `#results` | Results · Answer quality | One sortable table with every bench × setting × style, filters, units in headers, links to the answers, and the settings for each bench |
| `#results/speed` | Results · Speed runs | Every engine run from `results/runs.csv`, searchable and sortable, with engine flags behind "Show" |
| `#results/coverage` | Results · Coverage | Which standard benches each model has, plus the bench definitions |
| `#bench/<name>?style=&config=&grade=` | Answers | Every generated answer of one bench, filtered by the query string |
| `#models` | Models | Disk overview, downloads in progress, and one table of all models with status, sizes and actions |
| `#queue`, `#start`, `#now`, `#runs`, `#leaderboard`, `#experiments`, `#research`, `#settings` | More tools | Advanced screens |

Old links still work: `#install` opens Models and `#benches` opens Coverage.

## Workflow rules

- **One action to launch.** The launch form posts `/api/queue/add-selection` with one id. The button label says what will happen: *Start benchmark*, *Queue benchmark*, *Queue and resume*, or *Cannot queue this benchmark* with the reason.
- **Show the plan before the click.** The plan panel shows the estimated time, the answers already saved, the queue position, and the expected start ("tomorrow 06:03" when it is past midnight).
- **Confirm after the click.** A confirmation block names the job, its position and its expected start. It also links to the queue and the results, and takes focus so screen readers announce it.
- **Running, next, finished.** The status tiles and the *Running now* / *Up next* / *Recently finished* panels always show the current state. They refresh every 5 s. Refresh pauses while a dialog or disclosure is open.
- **Destructive actions ask first.** Stop, remove from the queue, and move to the Trash open a dialog that says exactly what will happen. Destructive dialogs open with focus on **Cancel**. The owner's model is protected, and a model in use cannot be removed.

## Tokens

All values are CSS custom properties on `:root` and are redefined for dark mode. Dark mode comes from `prefers-color-scheme`, or you can force it with the theme selector, which sets `body[data-theme]`.

### Typography

| Token | Size | Use |
|---|---|---|
| `--fs-xs` | 12px | hints, table header units, chips |
| `--fs-sm` | 13px | labels, secondary text, notices |
| `--fs-md` | 14px | body text, table cells |
| `--fs-lg` | 16px | card titles, key values |
| `--fs-xl` | 20px | section titles |
| `--fs-2xl` | 26px | page title (`h1`) |

`--font-ui` is the system sans stack. `--font-mono` is used for run ids, prompt ids, paths and commands. Numbers use `font-variant-numeric: tabular-nums`, so columns line up.

### Spacing and shape

The spacing scale is 4px based: `--s1` through `--s7` are 4, 8, 12, 16, 24, 32 and 48px. Cards use `--radius` (8px), and controls use `--radius-sm`. Controls are `--control-h` (40px) tall. Touch targets on narrow screens are at least `--touch` (44px).

### Color

| Token | Light | Dark | Meaning |
|---|---|---|---|
| `--bg` / `--surface` / `--surface-2` | #F6F6F4 / #FFF / #F1F1EE | #111113 / #19191C / #222226 | page, cards, table headers and wells |
| `--fg` / `--fg-2` / `--fg-3` | #18181B / #55555E / #66666F | #EDEDEF / #B0B0B8 / #9696A0 | text, secondary text, units |
| `--accent` | #1F4FBF | #7FA6FF | primary actions, links, current navigation, focus |
| `--ok` | #17663A | #6FCF97 | done, installed |
| `--warn` | #8A5300 | #F2C266 | waits for quiet, low disk |
| `--bad` | #B42318 | #FF8A80 | failed, destructive actions |

Every text and background pair meets WCAG AA for normal text (4.5:1 or more). The lowest pair is `--fg-3` on `--surface-2`, at about 5:1. Color never carries meaning on its own: each status has a word and a shape, and lossy settings carry a hatched "changes output" tag.

## Components

- **Navigation.** The sidebar has the three main screens plus a **More tools** disclosure, which opens automatically when an advanced screen is active. It also shows the GPU status chip and the theme selector. Below 860px it becomes a sticky top bar. The current page has `aria-current="page"`.
- **Page header** (`.head`). An `h1`, one sentence on what the page is for, and at most one action.
- **Cards** (`.card`, `.card-head`). Surfaces for one topic. Status tiles (`.tile`) give a three-number summary.
- **Buttons** (`.btn`).
  - Variants: default (secondary), `.btn-primary` (one per view), `.btn-danger` (outlined; opens a confirmation), `.btn-danger-solid` (the confirm button inside a dialog), `.btn-sm`, `.btn-lg`, and `.icon-btn` (always with an `aria-label`).
  - Disabled buttons keep their label and explain why nearby.
- **Status chips** (`.chip`). Each status pairs a word with a shape:
  - `st-running`: pulsing dot
  - `st-done`: check
  - `st-failed`: square
  - `st-blocked`: diamond
  - `st-paused`: bars
  - `st-waiting`, `st-queued` and `st-missing`: outline
- **Tags.** `.tag-exact` (solid square) and `.tag-lossy` ("changes output", hatched). AGENTS.md requires lossy results to be labelled.
- **Progress.** `.meter` (`role="progressbar"` with values) shows downloads and benchmark progress. The per-answer strip shows every case of a running bench.
- **Notices and toasts.** `.notice-info`, `.notice-ok` and `.notice-warn` are inline. Errors use `.err` with `role="alert"`. Toasts go into `#toasts` (`aria-live="polite"`). Success toasts close after 7 s; error toasts stay until dismissed.
- **Dialogs** (`.dialog` in `.scrim`). They use `role="dialog"` and `aria-modal`, are labelled by their title, trap focus, close with Esc, and return focus to the trigger.
- **Disclosures** (`details.x`, `.card.disclosure`). These hold secondary detail: settings, answers, logs and model details.

## Tables

- Use `table.t` inside `.table-wrap`. The wrapper scrolls horizontally on narrow screens, so the page itself never scrolls sideways, and the header stays sticky.
- Every header names its unit on a second line (`th .u`), for example *Decode speed / tok/s* or *Mean answer time / s*. Cells hold bare numbers, right-aligned and tabular.
- Sortable headers are buttons inside `th`. The `th` carries `aria-sort`. An arrow shows the direction; unsorted columns show a faint ↕.
- The best value in a column, among the rows currently shown, is bold and gets a screen-reader-only "(best)". Columns declare whether best means `max` or `min`.
- Lossy rows get a left rule (`tr.lossy`). Missing values show "—".
- Captions are present for screen readers, and filters show a live row count (`role="status"`).

## Forms

- `.field` stacks a visible `<label>` above the control, with `.help` text linked by `aria-describedby`.
- Selects use `.input` with a custom arrow. Options are grouped with `optgroup`.
- Mutually exclusive choices use `.choice` radio cards inside `fieldset.clean` with a `legend`. Single toggles use `.check`.
- Filters sit in a `.filters` group (`role="group"` with a label) and apply immediately.

## Accessibility checklist

- A skip link goes to `main`. Each route change sets the document title and moves focus to `main`; the focus ring is suppressed on `main` itself.
- Every control has a visible focus ring (`--focus`: a 2px surface gap plus a 2px accent ring).
- Every input has a label. Icon-only buttons have `aria-label`. Repeated links ("Answers", "Details") have specific accessible names.
- Live regions announce row counts, toasts, launch confirmations and the GPU status.
- Motion is limited to the running dot and is disabled under `prefers-reduced-motion`.

## Working on the interface safely

Never test against the real app on port 8766 while it runs benchmarks. Use the isolated demo server instead:

```sh
.venv/bin/python lab_app/demo_server.py                      # http://127.0.0.1:8767, a bench running
.venv/bin/python lab_app/demo_server.py --scenario idle      # nothing running, empty queue
.venv/bin/python lab_app/demo_server.py --scenario download  # a model download in progress
```

The demo uses the real server code and the real result files. However:

- The queue and job history are a throwaway copy, and no runner thread starts anything.
- Start, stop, download and remove return fake results. They still pass the same validation as the real app.
- Processes, memory, disk and the models folder are fixtures.

Screenshots and automatic checks:

```sh
.venv/bin/python scripts/lab_app_screenshots.py                          # light, wide 1440 px and narrow 390 px
.venv/bin/python scripts/lab_app_screenshots.py --theme dark --suffix=-dark
```

The script fails if a page has console errors, horizontal overflow, unlabeled form controls, controls without a name, or images without alt text. Screenshots are in `docs/lab-app/screenshots/`.
