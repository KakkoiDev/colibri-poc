"""Quiet-machine GLM rerun: repeat the busy-machine runs with other apps closed.

    .venv/bin/python glm_quiet.py check              # is the machine quiet enough? (changes nothing)
    .venv/bin/python glm_quiet.py run                # ~15-20 min: comparison set, 2 repeats
    .venv/bin/python glm_quiet.py run --ram-sweep    # + exact runs at larger RAM budgets
    .venv/bin/python glm_quiet.py run --full         # + the full 144-run quality bench (hours)
    .venv/bin/python glm_quiet.py report results/glm-quiet-<stamp>

Each case reuses a busy-machine run's prompt, length and settings, so the report can
compare them one to one. Machine conditions (free RAM, swap, process count) are
recorded before and after. Nothing is closed or killed for you: close apps yourself.
User Colibri state is not changed (USAGE_SAVE=0, KVSAVE=0, --no-tune-profile).
"""
import argparse, csv, fcntl, json, os, re, subprocess, sys, time
from pathlib import Path

import glm_bench as gb

ROOT = Path(__file__).resolve().parent
BUSY_CSV = ROOT / 'published-results' / 'glm-20261018' / 'runs.csv'
SKY = 'Explain in two sentences why the sky is blue.'
CODE = 'Write a Python function that returns the n-th Fibonacci number iteratively, then state its time complexity.'
SKIP = lambda tau: {'DEGRADE_ZERO': '1', 'DEGRADE_TAU': tau}
# (case, busy run to compare with, prompt, generated tokens, extra env)
CASES = [
    ('exact-sky-24', 'c9-best-combo', SKY, 24, {}),
    ('skip030-sky-48', 'l8-degrade-030', SKY, 48, SKIP('0.30')),
    ('skip050-sky-48', 'l10-degrade-050', SKY, 48, SKIP('0.50')),
    ('exact-code-48', 'q0-code-exact', CODE, 48, {}),
    ('skip050-code-48', 'q3-code-degrade-050', CODE, 48, SKIP('0.50')),
]
RAM_SWEEP = [22, 26]          # exact sky runs at larger total budgets (busy runs used 18)
QUIET_FREE_GB = 20.0          # free RAM we call "quiet" (busy runs had 10-17.5 GB)


def free_gb():
    out = subprocess.run(['vm_stat'], capture_output=True, text=True).stdout
    page = int(re.search(r'page size of (\d+)', out)[1])
    pages = lambda k: int(re.search(rf'{k}:\s+(\d+)', out)[1])
    # free + inactive + speculative + purgeable: what macOS can hand out without swapping
    return (pages('Pages free') + pages('Pages inactive') + pages('Pages speculative') + pages('Pages purgeable')) * page / 1e9


def conditions():
    swap = subprocess.run(['sysctl', '-n', 'vm.swapusage'], capture_output=True, text=True).stdout.strip()
    used = re.search(r'used = ([\d.]+)M', swap)
    procs = subprocess.run(['ps', '-axo', 'rss=,comm='], capture_output=True, text=True).stdout.splitlines()
    rows = sorted(((int(r.split(None, 1)[0]), os.path.basename(r.split(None, 1)[1])) for r in procs if r.strip()), reverse=True)
    pressure = subprocess.run(['memory_pressure'], capture_output=True, text=True).stdout
    pct = re.search(r'free percentage: (\d+)%', pressure)
    return dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), free_gb=round(free_gb(), 1),
                memory_free_pct=int(pct[1]) if pct else None, swap_used_mb=float(used[1]) if used else None,
                process_count=len(rows), load_avg=os.getloadavg(),
                top_memory_apps=[dict(name=n, rss_gb=round(r / 1e6, 2)) for r, n in rows[:8]])


def lock_holder():
    p = ROOT / '.bench.lock'
    if not p.exists():
        return None
    out = subprocess.run(['lsof', '-t', str(p)], capture_output=True, text=True).stdout.split()
    return out or None


def check(args, quiet=False):
    c = conditions()
    holder = lock_holder()
    engines = subprocess.run(['pgrep', '-fl', 'c/colibri '], capture_output=True, text=True).stdout.strip()
    coli = Path(args.coli_dir).expanduser() / 'c' / 'colibri'
    metal = 'Metal' in subprocess.run(['otool', '-L', str(coli)], capture_output=True, text=True).stdout
    print(f"Free RAM: {c['free_gb']} GB (busy runs had 10-17.5; quiet target >= {QUIET_FREE_GB})")
    print(f"Swap used: {c['swap_used_mb']} MB | processes: {c['process_count']} | load: {', '.join(f'{x:.1f}' for x in c['load_avg'])}")
    print('Largest apps still open:')
    for a in c['top_memory_apps']:
        print(f"  {a['rss_gb']:6.2f} GB  {a['name']}")
    problems = []
    if holder:
        problems.append(f'another benchmark holds .bench.lock (PID {", ".join(holder)}); stop it by PID or wait')
    if engines:
        problems.append('a Colibri engine is already running:\n    ' + engines.replace('\n', '\n    '))
    if not metal:
        problems.append(f'{coli} is not a Metal build (make -C {coli.parent} glm METAL=1)')
    if c['free_gb'] < QUIET_FREE_GB:
        problems.append(f"only {c['free_gb']} GB free: close more apps for a quiet run (or pass --force)")
    print('\nReady.' if not problems else '\nNot ready:\n- ' + '\n- '.join(problems))
    return c, problems


def run_case(out_dir, coli, model, name, prompt, ngen, extra, ram, ctx):
    env = dict(os.environ, **gb.BASE_ENV, **extra, RAM_GB=str(ram))
    cmd = [str(coli), 'run', '--model', model, '--no-tune-profile', '--no-think', '--ngen', str(ngen),
           '--ram', str(ram), '--ctx', str(ctx), prompt]
    t0 = time.time()
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, errors='replace', timeout=3600)
    log = p.stdout + '\n' + p.stderr
    (out_dir / f'{name}.log').write_text(log)
    rec = dict(case=name, exit=p.returncode, wall_s=round(time.time() - t0, 2), ram=ram, ctx=ctx, ngen=ngen,
               env=extra, refused='refusing to start' in log, **gb.parse_log(log))
    (out_dir / f'{name}.json').write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    print(f"  {name}: {rec.get('decode_tok_s', 'no result')} tok/s"
          f"{' (refused: not enough free RAM)' if rec['refused'] else ''}", flush=True)
    return rec


def run(args):
    before, problems = check(args)
    if problems and not args.force:
        raise SystemExit('\nFix the items above, or rerun with --force to record a run anyway.')
    lock = (ROOT / '.bench.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another benchmark is running (.bench.lock held)')
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    out_dir = ROOT / 'results' / f'glm-quiet-{stamp}'
    out_dir.mkdir(parents=True)
    coli = Path(args.coli_dir).expanduser() / 'c' / 'coli'
    model = str(Path(args.model).expanduser())
    meta = dict(stamp=stamp, forced=bool(problems), repeats=args.repeats, conditions_before=before,
                colibri_commit=subprocess.run(['git', '-C', str(coli.parent.parent), 'rev-parse', 'HEAD'],
                                              capture_output=True, text=True).stdout.strip())
    (out_dir / 'meta.json').write_text(json.dumps(meta, indent=1))
    print(f'\nWriting to {out_dir}')
    for r in range(1, args.repeats + 1):
        print(f'Repeat {r}/{args.repeats}')
        for case, _busy, prompt, ngen, extra in CASES:
            run_case(out_dir, coli, model, f'{case}__r{r}', prompt, ngen, extra, 18, 1024)
    if args.ram_sweep:
        print('RAM sweep (exact, sky prompt)')
        for ram in RAM_SWEEP:
            run_case(out_dir, coli, model, f'exact-sky-24-ram{ram}__r1', SKY, 24, {}, ram, 1024)
    meta['conditions_after'] = conditions()
    (out_dir / 'meta.json').write_text(json.dumps(meta, indent=1))
    lock.close()
    report(argparse.Namespace(dir=str(out_dir)))
    if args.full:
        print('\nStarting the full quality bench (hours). It resumes if interrupted.')
        subprocess.run([sys.executable, str(ROOT / 'glm_bench.py'), 'run', '--name', f'quiet-{stamp}',
                        '--coli-dir', args.coli_dir], check=False)
    print(f'\nDone. Tell Claude: "quiet run finished: results/glm-quiet-{stamp}"')


def busy_runs():
    return {r['run']: r for r in csv.DictReader(BUSY_CSV.open())} if BUSY_CSV.exists() else {}


def report(args):
    out_dir = Path(args.dir)
    meta = json.loads((out_dir / 'meta.json').read_text())
    recs = [json.loads(p.read_text()) for p in sorted(out_dir.glob('*__r*.json'))]
    busy = busy_runs()
    busy_text = {}
    for case, busy_name, *_ in CASES:
        f = ROOT / 'published-results' / 'glm-20261018' / f'{busy_name}.output.txt'
        busy_text[case] = f.read_text().strip() if f.exists() else None
    rows, table = [], ['| Case | Busy tok/s | Quiet tok/s (each repeat) | Quiet mean | Change | Same text as busy |',
                       '|---|---:|---|---:|---:|---|']
    for case, busy_name, *_ in CASES:
        rs = [r for r in recs if r['case'].startswith(case + '__') and 'decode_tok_s' in r]
        b = float(busy[busy_name]['tok_s']) if busy_name in busy and busy[busy_name]['tok_s'] else None
        vals = [r['decode_tok_s'] for r in rs]
        mean = sum(vals) / len(vals) if vals else None
        change = f'{(mean / b - 1) * 100:+.0f}%' if (mean and b) else '—'
        same = [busy_text[case] is not None and r.get('text', '').strip() == busy_text[case] for r in rs]
        rows.append(dict(case=case, busy_run=busy_name, busy_tok_s=b, quiet_tok_s=vals, quiet_mean=mean,
                         same_text=same))
        table.append(f"| {case} | {b if b is not None else '—'} | {', '.join(f'{v:.2f}' for v in vals) or '—'} | "
                     f"{f'{mean:.2f}' if mean else '—'} | {change} | {sum(same)}/{len(same)} |")
    sweep = [r for r in recs if '-ram' in r['case']]
    if sweep:
        table += ['', '| RAM budget GB | tok/s | Expert hit rate % | Result |', '|---:|---:|---:|---|']
        for r in sweep:
            table.append(f"| {r['ram']} | {r.get('decode_tok_s', '—')} | {r.get('hit_pct', '—')} | "
                         f"{'refused: not enough free RAM' if r['refused'] else 'ok'} |")
    cb, ca = meta['conditions_before'], meta.get('conditions_after', {})
    head = [f"# Quiet-machine GLM rerun {meta['stamp']}", '',
            f"Free RAM before/after: {cb['free_gb']} / {ca.get('free_gb', '—')} GB "
            f"(busy runs: 10-17.5 GB). Swap used before: {cb['swap_used_mb']} MB. "
            f"Processes: {cb['process_count']}. Repeats: {meta['repeats']}."
            + (' **Run was forced on a machine that failed the quiet check.**' if meta['forced'] else ''), '']
    text = '\n'.join(head + table) + '\n'
    (out_dir / 'comparison.md').write_text(text)
    (out_dir / 'comparison.json').write_text(json.dumps(dict(meta=meta, cases=rows, ram_sweep=sweep), ensure_ascii=False, indent=1))
    print('\n' + text)


def main():
    ap = argparse.ArgumentParser(description='Quiet-machine GLM rerun')
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('check', 'run'):
        p = sub.add_parser(name)
        p.add_argument('--coli-dir', default='~/Code/colibri')
        p.add_argument('--model', default='~/colibri-models/glm-5.3')
        if name == 'run':
            p.add_argument('--repeats', type=int, default=2)
            p.add_argument('--ram-sweep', action='store_true')
            p.add_argument('--full', action='store_true')
            p.add_argument('--force', action='store_true')
    r = sub.add_parser('report')
    r.add_argument('dir')
    a = ap.parse_args()
    if a.cmd == 'check':
        _, problems = check(a)
        sys.exit(1 if problems else 0)
    run(a) if a.cmd == 'run' else report(a)


if __name__ == '__main__':
    main()
