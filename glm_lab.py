"""GLM experiment log: try a change, measure it against a reference run, record the verdict.

    .venv/bin/python glm_lab.py try ID "Title" --env KEY=VALUE ... [--prompt sky|code|"text"]
            [--ngen 24] [--ref RUN] [--category C] [--lossy] [--hypothesis "..."]
    .venv/bin/python glm_lab.py log        # rebuild docs/12-experiment-log.md and site/data/experiments.json
    .venv/bin/python glm_lab.py planned    # planned experiments and whether each can run now
    .venv/bin/python glm_lab.py run-planned [ID ...]   # run planned experiments (all ready ones by default)

`try` runs Colibri once with the best exact settings plus your --env overrides, saves the
log, republishes the run data, appends an entry to experiments/glm-experiments.json and
rebuilds the log. Edit the entry afterwards to add the conclusion and tradeoffs; `log`
recomputes every number from the published runs, so nothing is retyped.

Verdict rules (when an entry does not set one): any failed run -> failed; generation
speed change >= +10% -> improves (peak RSS is recorded but not judged: it is too noisy); <= -10% -> worse; otherwise prompt reading change
<= -20% -> improves (prompt reading); otherwise no clear change. Single runs: changes
under ~10% are noise. USAGE_SAVE=0, KVSAVE=0 and --no-tune-profile keep the user's
Colibri state unchanged.

Planned experiments are registry entries with `"verdict": "not run"` and a `plan`
object: {prompt, ngen, env, ref, coli_dir, model, build: {ref}, needs: [paths], prep}.
`run-planned` builds the engine clone when `build` is set, skips entries whose `needs`
paths are missing (printing the `prep` command), runs the rest in registry order, and
runs a second time any result that looks like a win (>= +10%), so wins are repeated.
`glm_quiet.py run` calls it after its own cases.
"""
import argparse, csv, fcntl, json, os, subprocess, sys, time
from pathlib import Path

import publish_glm_runs as pub

ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / 'experiments' / 'glm-experiments.json'
RAW_LOGS = ROOT / 'results' / 'glm-raw-20261018' / 'logs'
PUBLISHED = ROOT / 'published-results' / 'glm-20261018'
LOG_MD = ROOT / 'docs' / '12-experiment-log.md'
SITE_JSON = ROOT / 'site' / 'data' / 'experiments.json'
PROMPTS = {'sky': 'Explain in two sentences why the sky is blue.',
           'code': 'Write a Python function that returns the n-th Fibonacci number iteratively, then state its time complexity.'}
BEST = {'USAGE_SAVE': '0', 'KVSAVE': '0', 'COLI_TEMP': '0', 'PROF': '1', 'COLI_METAL': '1', 'PIPE': '1', 'DIRECT': '1',
        'COLI_METAL_RESSET': '1', 'COLI_METAL_SPIN': '1', 'OMP_NUM_THREADS': '12'}
DEFAULT_REF = {'sky': 'r2-p0-sky-exact', 'code': 'r2-p0-code-exact'}
CATEGORIES = ['build', 'gpu', 'threads', 'io', 'cache', 'memory', 'prompt', 'backend', 'lossy-routing', 'model-format']


def load_registry():
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else []


def save_registry(entries):
    REGISTRY.parent.mkdir(exist_ok=True)
    REGISTRY.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n')


def runs_table():
    return {r['run']: r for r in csv.DictReader((PUBLISHED / 'runs.csv').open())}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def output_of(run):
    f = PUBLISHED / f'{run}.output.txt'
    return f.read_text().strip() if f.exists() else None


def pct(new, old):
    return None if new is None or not old else round((new / old - 1) * 100, 1)


def evaluate(e, runs):
    """Numbers for one entry, all from the published runs."""
    if not e.get('runs'):
        return dict(measured=False)
    rs = [runs.get(r) for r in e['runs']]
    ok = [r for r in rs if r and r['status'] == 'ok']
    failed = [name for name, r in zip(e['runs'], rs) if not r or r['status'] != 'ok']
    mean = lambda k, rows: (sum(num(r[k]) for r in rows) / len(rows)) if rows and all(num(r[k]) is not None for r in rows) else None
    ref = runs.get(e.get('ref')) if e.get('ref') else None
    m = dict(measured=True, n_runs=len(e['runs']), failed_runs=failed,
             tok_s=mean('tok_s', ok), prefill_s=mean('prefill_s', ok), rss_gb=mean('rss_gb', ok), hit_pct=mean('hit_pct', ok),
             ref_tok_s=num(ref['tok_s']) if ref else None, ref_prefill_s=num(ref['prefill_s']) if ref else None,
             ref_rss_gb=num(ref['rss_gb']) if ref else None)
    m['speed_change_pct'] = pct(m['tok_s'], m['ref_tok_s'])
    m['prefill_change_pct'] = pct(m['prefill_s'], m['ref_prefill_s'])
    m['rss_change_pct'] = pct(m['rss_gb'], m['ref_rss_gb'])
    ref_text = output_of(e['ref']) if e.get('ref') else None
    texts = [output_of(r) for r in e['runs'] if runs.get(r) and runs[r]['status'] == 'ok']
    same_len = ref and ok and all(r['decode_tokens'] == ref['decode_tokens'] for r in ok)
    if ref_text is None or not texts or not same_len:
        m['output'] = 'n/a'
    else:
        m['output'] = 'identical' if all(t == ref_text for t in texts) else 'changed'
    return m


def verdict(e, m):
    if e.get('verdict'):
        return e['verdict']
    if not m.get('measured'):
        return 'not run'
    if m['failed_runs'] and m['tok_s'] is None:
        return 'failed'
    s, p = m.get('speed_change_pct'), m.get('prefill_change_pct')
    if s is not None and s >= 10:
        return 'improves'
    if s is not None and s <= -10:
        return 'worse'
    if p is not None and p <= -20:
        return 'improves'
    return 'no clear change'


def ways(m):
    out = []
    if m.get('speed_change_pct') is not None and abs(m['speed_change_pct']) >= 10:
        out.append(f"generation {m['speed_change_pct']:+.0f}%")
    if m.get('prefill_change_pct') is not None and abs(m['prefill_change_pct']) >= 10:
        out.append(f"prompt reading {m['prefill_change_pct']:+.0f}% time")
    # Peak RSS is recorded but not judged: two runs with identical settings measured
    # 6.2 and 9.3 GB (c9 vs c15), so it reflects what macOS kept resident, not the change.
    if m.get('output') == 'changed':
        out.append('output changed')
    return out


TARGET_TOK_S = 5.0


def scoreboard(rows):
    """Best measured exact run, best lossy run marked usable, and the gap to the target."""
    ok = [r for r in rows if r['metrics'].get('measured') and r['metrics'].get('tok_s') and r['verdict'] not in ('failed',)]
    exact = [r for r in ok if not r.get('lossy')]
    usable = [r for r in ok if r.get('lossy') and r.get('usable')]
    pick = lambda xs: max(xs, key=lambda r: r['metrics']['tok_s']) if xs else None
    out = dict(target_tok_s=TARGET_TOK_S)
    everyday = [r for r in ok if r.get('everyday')]
    for name, r in (('best_exact', pick(exact)), ('best_usable_lossy', pick(usable)), ('everyday', pick(everyday))):
        if r:
            t = r['metrics']['tok_s']
            out[name] = dict(id=r['id'], title=r['title'], tok_s=round(t, 2), runs=r['runs'],
                             gap_x=round(TARGET_TOK_S / t, 1), pct_of_target=round(t / TARGET_TOK_S * 100))
    return out


def build(_args=None):
    entries, runs = load_registry(), runs_table()
    rows = []
    for e in entries:
        m = evaluate(e, runs)
        rows.append(dict(e, metrics=m, verdict=verdict(e, m), effects=ways(m) if m.get('measured') else []))
    board = scoreboard(rows)
    SITE_JSON.write_text(json.dumps(dict(schema=1, generated=time.strftime('%Y-%m-%d'), scoreboard=board, entries=rows),
                                    ensure_ascii=False, indent=1) + '\n')
    f2 = lambda v, d=2: '—' if v is None else f'{v:.{d}f}'
    sg = lambda v: '—' if v is None else f'{v:+.0f}%'
    counts = {}
    for r in rows:
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1
    lines = ['# GLM experiment log', '',
             'Every GLM experiment on the 32 GB Apple M6: what was changed, what it was compared with, and what it did.',
             'Generated by `glm_lab.py log` from `experiments/glm-experiments.json` and the published runs; do not edit by hand.',
             '', '> Measured on a busy everyday machine with other apps open; single runs unless noted, so changes under ~10% are noise.',
             '', '## Scoreboard', '',
             f"Target: **{board['target_tok_s']} tok/s**. " + ' '.join(
                 f"{lab}: **{board[k]['tok_s']} tok/s** ({board[k]['title']}, {board[k]['pct_of_target']}% of target, {board[k]['gap_x']}x to go)."
                 for k, lab in (('best_exact', 'Best exact'), ('best_usable_lossy', 'Best usable lossy'),
                                ('everyday', 'Everyday setting')) if k in board),
             '', 'Memory is not judged: peak RSS varied 6.2-9.3 GB between two runs with identical settings, so it reflects what macOS kept resident rather than the setting.',
             '', 'Verdicts: ' + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())) + '.', '',
             '```mermaid', 'flowchart LR', '    T[glm_lab.py try] --> R[run + log] --> P[published runs] --> L[glm_lab.py log] --> D[this page + website]', '```', '']
    for cat in CATEGORIES + sorted({r.get('category', 'other') for r in rows} - set(CATEGORIES)):
        group = [r for r in rows if r.get('category') == cat]
        if not group:
            continue
        lines += [f'## {cat}', '', '| Experiment | Verdict | tok/s (ref → new) | Change | Prompt reading s (ref → new) | Output | Effects | Runs |',
                  '|---|---|---|---:|---|---|---|---|']
        for r in group:
            m = r['metrics']
            tag = ' *(changes output)*' if r.get('lossy') else ''
            runs_cell = ', '.join(r.get('runs', [])) or '—'
            lines.append(f"| **{r['title']}**{tag} | {r['verdict']} | {f2(m.get('ref_tok_s'))} → {f2(m.get('tok_s'))} | "
                         f"{sg(m.get('speed_change_pct'))} | {f2(m.get('ref_prefill_s'), 1)} → {f2(m.get('prefill_s'), 1)} | "
                         f"{m.get('output', 'n/a') if m.get('measured') else '—'} | {'; '.join(r['effects']) or '—'} | {runs_cell} |")
        lines.append('')
        for r in group:
            lines.append(f"- **{r['title']}** (`{r['id']}`): change `{r.get('change', '')}`. "
                         f"Why: {r.get('hypothesis', '—')} Result: {r.get('conclusion', '—')}"
                         + (f" Tradeoffs: {r['tradeoffs']}" if r.get('tradeoffs') else '')
                         + (f" Reference: `{r['ref']}`." if r.get('ref') else ''))
        lines.append('')
    LOG_MD.write_text('\n'.join(lines))
    print(f'{len(rows)} experiments -> {LOG_MD.relative_to(ROOT)}, {SITE_JSON.relative_to(ROOT)}')


def acquire_lock():
    lock = (ROOT / '.bench.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another benchmark is running (.bench.lock held); pause it first')
    return lock


def execute(run, prompt, ngen, extra, coli_dir='~/Code/colibri', model='~/colibri-models/glm-5.3',
            no_base=False, ram=18, ctx=1024, timeout=3600):
    """One Colibri run with the best exact settings plus `extra`; the log goes to RAW_LOGS."""
    prompt = PROMPTS.get(prompt, prompt)
    env = dict(os.environ, **({} if no_base else BEST), **extra)
    env.setdefault('RAM_GB', str(ram))
    coli = Path(coli_dir).expanduser()
    coli = (coli if coli.is_absolute() else ROOT / coli) / 'c' / 'coli'
    cmd = [str(coli), 'run', '--model', str(Path(model).expanduser()), '--no-tune-profile', '--no-think',
           '--ngen', str(ngen), '--ram', str(ram), '--ctx', str(ctx), prompt]
    print(f'Running {run} ...', flush=True)
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, errors='replace', timeout=timeout)
    RAW_LOGS.mkdir(parents=True, exist_ok=True)
    shown = ' '.join(f'{k}={v}' for k, v in extra.items())
    (RAW_LOGS / f'{run}.log').write_text(f'# {run} env: {shown}\n' + p.stdout + '\n' + p.stderr)
    argv, sys.argv = sys.argv, [sys.argv[0]]
    pub.main()
    sys.argv = argv
    return shown


def engine_dir(plan):
    d = Path(plan.get('coli_dir', '~/Code/colibri')).expanduser()
    return d if d.is_absolute() else ROOT / d


def build_engine(plan):
    """Clone and build plan['build']['ref'] into plan['coli_dir'] (never the installed engine)."""
    d, ref = engine_dir(plan), plan['build']['ref']
    if (d / 'c' / 'colibri').exists():
        return True
    if not str(d.resolve()).startswith(str((ROOT / 'engines').resolve())):
        raise SystemExit(f'refusing to build outside engines/: {d}')
    print(f'Building Colibri {ref} in {d.relative_to(ROOT)} ...', flush=True)
    src = Path('~/Code/colibri').expanduser()
    for cmd in (['git', 'clone', '-q', '--local', str(src), str(d)],
                ['git', '-C', str(d), 'fetch', '-q', 'https://github.com/JustVugg/colibri', ref],
                ['git', '-C', str(d), 'checkout', '-q', 'FETCH_HEAD'],
                ['make', '-C', str(d / 'c'), '-j8', 'glm', 'METAL=1']):
        if not (d.exists() and cmd[1] == 'clone'):
            subprocess.run(cmd, check=True, capture_output=cmd[0] == 'make')
    libs = subprocess.run(['otool', '-L', str(d / 'c' / 'colibri')], capture_output=True, text=True).stdout
    if 'libomp' not in libs or 'Metal' not in libs:
        print(f'  build of {ref} lacks libomp or Metal; skipping its experiments')
        return False
    return True


def readiness(e):
    """None when a planned entry can run now, else the reason it cannot."""
    plan = e.get('plan')
    if not plan:
        return 'no runnable plan (needs a decision or hardware)'
    missing = [n for n in plan.get('needs', []) if not Path(n).expanduser().exists()]
    if missing:
        return f"missing {', '.join(missing)}" + (f"; prepare with: {plan['prep']}" if plan.get('prep') else '')
    return None


def planned_entries(entries, ids=None):
    return [e for e in entries if e.get('verdict') == 'not run' and (not ids or e['id'] in ids)]


def planned(_args=None):
    for e in planned_entries(load_registry()):
        why = readiness(e)
        print(f"{'ready  ' if why is None else 'waiting'}  {e['id']}: {e['title']}" + (f'\n           {why}' if why else ''))


def run_planned(ids=None, hold_lock=True):
    """Run planned experiments; returns the ids that ran. Wins (>= +10%) get a second run."""
    lock = acquire_lock() if hold_lock else None
    entries, ran = load_registry(), []
    built = {}
    for e in planned_entries(entries, ids):
        why = readiness(e)
        if why:
            print(f"Skipping {e['id']}: {why}")
            continue
        plan = e['plan']
        if plan.get('build'):
            key = plan['build']['ref']
            if key not in built:
                built[key] = build_engine(plan)
            if not built[key]:
                continue
        kw = dict(coli_dir=str(engine_dir(plan)), model=plan.get('model', '~/colibri-models/glm-5.3'))
        run = f"x-{e['id']}"
        execute(run, plan.get('prompt', 'sky'), plan.get('ngen', 24), plan.get('env', {}), **kw)
        e['runs'] = [run]
        e['ref'] = plan.get('ref', e.get('ref'))
        e['plan']['note'] = e.get('conclusion', '')
        e['conclusion'] = ''
        e['date'] = time.strftime('%Y-%m-%d')
        e.pop('verdict', None)
        m = evaluate(e, runs_table())
        if (m.get('speed_change_pct') or 0) >= 10:
            print(f"  {e['id']}: {m['speed_change_pct']:+.0f}%, repeating once to confirm")
            execute(run + '-r2', plan.get('prompt', 'sky'), plan.get('ngen', 24), plan.get('env', {}), **kw)
            e['runs'].append(run + '-r2')
            m = evaluate(e, runs_table())
        save_registry(entries)
        ran.append(e['id'])
        print(f"  {e['id']}: {m.get('tok_s')} tok/s vs {m.get('ref_tok_s')} ({m.get('speed_change_pct')}%), output {m.get('output')}")
    build()
    if lock:
        lock.close()
    return ran


def try_(args):
    entries = load_registry()
    if any(e['id'] == args.id for e in entries):
        raise SystemExit(f'experiment id {args.id} already exists')
    lock = acquire_lock()
    run = f'x-{args.id}'
    extra = dict(kv.split('=', 1) for kv in args.env)
    shown = execute(run, args.prompt, args.ngen, extra, args.coli_dir, args.model, args.no_base, args.ram, args.ctx,
                    args.timeout)
    ref = args.ref or DEFAULT_REF.get(args.prompt)
    entries.append(dict(id=args.id, title=args.title, category=args.category, change=shown or '(base settings)',
                        hypothesis=args.hypothesis, ref=ref, runs=[run], lossy=args.lossy,
                        date=time.strftime('%Y-%m-%d'), conclusion='', tradeoffs=''))
    save_registry(entries)
    build()
    m = evaluate(entries[-1], runs_table())
    print(f"{run}: {m.get('tok_s')} tok/s vs {m.get('ref_tok_s')} ({m.get('speed_change_pct')}%), "
          f"prompt reading {m.get('prefill_s')} s vs {m.get('ref_prefill_s')} s, output {m.get('output')}")


def main():
    ap = argparse.ArgumentParser(description='GLM experiment log')
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('try')
    t.add_argument('id'); t.add_argument('title')
    t.add_argument('--env', nargs='*', default=[], metavar='KEY=VALUE')
    t.add_argument('--prompt', default='sky'); t.add_argument('--ngen', type=int, default=24)
    t.add_argument('--ref'); t.add_argument('--category', default='other', choices=CATEGORIES + ['other'])
    t.add_argument('--lossy', action='store_true'); t.add_argument('--hypothesis', default='')
    t.add_argument('--no-base', action='store_true', help='do not apply the best exact settings')
    t.add_argument('--ram', type=int, default=18); t.add_argument('--ctx', type=int, default=1024)
    t.add_argument('--timeout', type=int, default=3600)
    t.add_argument('--model', default='~/colibri-models/glm-5.3'); t.add_argument('--coli-dir', default='~/Code/colibri')
    sub.add_parser('log')
    sub.add_parser('planned')
    rp = sub.add_parser('run-planned')
    rp.add_argument('ids', nargs='*', help='planned experiment ids (default: every ready one)')
    a = ap.parse_args()
    if a.cmd == 'run-planned':
        run_planned(a.ids)
    else:
        {'try': try_, 'log': build, 'planned': planned}[a.cmd](a)


if __name__ == '__main__':
    main()
