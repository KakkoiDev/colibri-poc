"""GLM lab control app: a local web app over the lab's files, processes and jobs.

    .venv/bin/python lab_app/server.py            # http://127.0.0.1:8766
    .venv/bin/python lab_app/server.py --port N

It shows what is running, models, benches and coverage, runs, experiments and research, and
(v2) can queue and start the lab's own jobs, stop lab jobs by PID and start catalog downloads,
with the safety rules in actions.py. It binds to 127.0.0.1 only; actions need the app's own
X-Lab-Action header and origin, so other web pages cannot trigger them. Data comes from the same files the lab tools write, so nothing is retyped.
"""
import argparse, csv, glob, json, os, re, subprocess, sys, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / 'static'
HOME = Path.home()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import actions  # noqa: E402
RUNNER = {'last': 'not started'}
PORT = 8766

RUNS_CSV = ROOT / 'published-results' / 'glm-20261018' / 'runs.csv'
OUTPUTS = ROOT / 'published-results' / 'glm-20261018'
SAFE_ID = re.compile(r'^[A-Za-z0-9._-]{1,120}$')


# ---------- helpers ----------

def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return default


def etime_seconds(s):
    """ps etime: [[dd-]hh:]mm:ss"""
    days = 0
    if '-' in s:
        d, s = s.split('-', 1); days = int(d)
    parts = [int(p) for p in s.split(':')]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, sec = parts
    return days * 86400 + h * 3600 + m * 60 + sec


def processes():
    out = subprocess.run(['ps', '-axo', 'pid=,ppid=,etime=,command='], capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        p = line.split(None, 3)
        if len(p) == 4:
            rows.append(dict(pid=int(p[0]), ppid=int(p[1]), elapsed_s=etime_seconds(p[2]), command=p[3]))
    return rows


def short(cmd, n=200):
    c = cmd.replace(str(HOME), '~')
    return c if len(c) <= n else c[:n] + '…'


def exe(cmd):
    """The program a command line runs (its first token)."""
    return cmd.split()[0] if cmd.split() else ''


def is_engine(cmd):
    return exe(cmd).endswith('/c/colibri')


def is_python(cmd):
    return os.path.basename(exe(cmd)).startswith('python')


def arg(cmd, flag, default=None):
    m = re.search(rf'{flag}[ =](\S+)', cmd)
    return m.group(1) if m else default


def dir_gb(path):
    if not Path(path).exists():
        return 0.0
    out = subprocess.run(['du', '-sk', str(path)], capture_output=True, text=True).stdout.split()
    return int(out[0]) / 1024 / 1024 if out else 0.0


def catalog():
    return read_json(ROOT / 'models' / 'catalog.json', {'models': []})['models']


def suite():
    return read_json(ROOT / 'benches' / 'suite.json', {'benches': []})


def runs_table():
    if not RUNS_CSV.exists():
        return []
    return list(csv.DictReader(RUNS_CSV.open()))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------- benches ----------

def bench_prompts():
    spec = read_json(ROOT / 'glm-prompts.json', {'prompts': [], 'styles': {}})
    return spec['prompts'], spec['styles']


def bench_records(name):
    recs = []
    for f in sorted(glob.glob(str(ROOT / 'results' / f'glm-bench-{name}' / '*__*.json'))):
        r = read_json(f)
        if r:
            recs.append(r)
    return recs


def bench_summary(recs):
    exact = {(r['id'], r['style']): r.get('text') for r in recs if r['config'] == 'exact'}
    groups = {}
    for r in recs:
        groups.setdefault((r['style'], r['config']), []).append(r)
    rows = []
    for (style, cfg), rs in sorted(groups.items()):
        ok = [r for r in rs if 'decode_s' in r]
        graded = [r for r in ok if r.get('correct') is not None]
        mean = lambda k: round(sum(r[k] for r in ok) / len(ok), 2) if ok else None
        rows.append(dict(style=style, config=cfg, runs=len(rs), ok=len(ok), correct=sum(1 for r in graded if r['correct']),
                         graded=len(graded), same_as_exact=sum(1 for r in ok if exact.get((r['id'], style)) == r.get('text')),
                         answer_s=mean('answer_s'), prefill_s=mean('prefill_s'), output_tokens=mean('output_tokens'),
                         decode_tok_s=mean('decode_tok_s')))
    return rows


def bench_names():
    names = []
    for d in sorted(glob.glob(str(ROOT / 'results' / 'glm-bench-*'))):
        n = Path(d).name[len('glm-bench-'):]
        if Path(d).is_dir() and n != 'smoke':
            names.append(n)
    return names


def mean_answer_s(style, config, default=None):
    """Mean answer time for a (style, config) across every saved bench answer."""
    ts = []
    for f in glob.glob(str(ROOT / 'results' / 'glm-bench-*' / f'*__{style}__{config}.json')):
        r = read_json(f)
        if r and r.get('answer_s'):
            ts.append(r['answer_s'])
    return sum(ts) / len(ts) if ts else default


def bench_job_progress(cmd, elapsed_s=None):
    """Progress of a running `glm_bench.py run`: every answer in run order, with ETA."""
    name = arg(cmd, '--name')
    prompts, styles = bench_prompts()
    configs = (arg(cmd, '--configs') or 'exact,d030,d050').split(',')
    styl = (arg(cmd, '--styles') or 'normal,terse').split(',')
    only = arg(cmd, '--only')
    chosen = [p for p in prompts if not only or p['id'] in only.split(',')]
    folder = ROOT / 'results' / f'glm-bench-{name}'
    started = time.time() - elapsed_s if elapsed_s is not None else None
    items, current_found = [], False
    for st in styl:                     # glm_bench runs style by style, then prompt, then config
        for p in chosen:
            for c in configs:
                key = f"{p['id']}__{st}__{c}"
                f = folder / f'{key}.json'
                it = dict(key=key, prompt=p['id'], kind=p.get('kind'), style=st, config=c)
                if f.exists():
                    r = read_json(f, {})
                    it.update(status='done', correct=r.get('correct'), answer_s=r.get('answer_s'),
                              this_run=started is not None and f.stat().st_mtime >= started)
                elif not current_found:
                    it['status'] = 'running'; current_found = True
                else:
                    it['status'] = 'waiting'
                items.append(it)
    done = [i for i in items if i['status'] == 'done']
    recent = [i['answer_s'] for i in done if i.get('this_run') and i.get('answer_s')]
    per = (sum(recent) / len(recent)) if recent else None
    remaining = [i for i in items if i['status'] != 'done']
    eta = 0.0
    for i in remaining:
        eta += per or mean_answer_s(i['style'], i['config'], 90 if i['style'] == 'terse' else 180)
    cur = next((i['key'] for i in items if i['status'] == 'running'), None)
    return dict(name=name, configs=configs, styles=styl, total=len(items), done=len(done), current=cur,
                items=items, per_answer_s=round(per, 1) if per else None, eta_s=round(eta) if remaining else 0)


def estimate_item(item):
    """Rough duration of a queued job, in seconds."""
    kind, args = item['kind'], item.get('args', {})
    if kind == 'bench':
        n_prompts = len(bench_prompts()[0])
        folder = ROOT / 'results' / f"glm-bench-{args.get('name')}"
        total = 0.0
        for st in args.get('styles', []):
            for c in args.get('configs', []):
                have = len(glob.glob(str(folder / f'*__{st}__{c}.json')))
                per = 20 if args.get('ollama_model') else mean_answer_s(st, c, 90 if st == 'terse' else 180)  # Ollama answers in seconds
                total += max(0, n_prompts - have) * per
        return round(total)
    if kind == 'quiet':
        flags = args.get('flags', [])
        if 'experiments-only' in flags:
            return 30 * 60
        return 45 * 60 + (0 if 'skip-original' in flags else 30 * 60)
    return 4 * 60   # a planned experiment: one run, sometimes repeated


# ---------- now ----------

_machine_cache = {}


def machine():
    if time.time() - _machine_cache.get('t', 0) < 10:
        return _machine_cache['v']
    import glm_quiet
    c = glm_quiet.conditions()
    v = dict(free_gb=c['free_gb'], swap_used_mb=c['swap_used_mb'], process_count=c['process_count'],
             load_avg=[round(x, 1) for x in c['load_avg']], top_apps=c['top_memory_apps'][:6],
             quiet=c['free_gb'] >= glm_quiet.QUIET_FREE_GB, quiet_threshold_gb=glm_quiet.QUIET_FREE_GB)
    st = os.statvfs(str(HOME))
    v['disk_free_gb'] = round(st.f_bavail * st.f_frsize / 1e9)
    _machine_cache.update(t=time.time(), v=v)
    return v


def lock_holders():
    lock = ROOT / '.bench.lock'
    if not lock.exists():
        return []
    out = subprocess.run(['lsof', '-t', str(lock)], capture_output=True, text=True).stdout.split()
    return [int(p) for p in out]


def jobs():
    procs = processes()
    by_pid = {p['pid']: p for p in procs}
    children = {}
    for p in procs:
        children.setdefault(p['ppid'], []).append(p)
    holders = set(lock_holders())
    cat = {m['id']: m for m in catalog()}
    out, claimed = [], set()

    def engine_under(pid, depth=0):
        for c in children.get(pid, []):
            if is_engine(c['command']):
                return c
            if depth < 3:
                e = engine_under(c['pid'], depth + 1)
                if e:
                    return e
        return None

    for p in procs:
        cmd = p['command']
        job = None
        if 'glm_bench.py run' in cmd and is_python(cmd):
            prog = bench_job_progress(cmd, p['elapsed_s'])
            job = dict(kind='Quality bench', title=f"Bench {prog['name']}: {prog['done']}/{prog['total']}",
                       detail=f"configs {', '.join(prog['configs'])} · styles {', '.join(prog['styles'])}"
                              + (f" · next: {prog['current'].replace('__', ' · ')}" if prog['current'] else ''),
                       progress=prog, gpu=True)
        elif 'glm_quiet.py run' in cmd and is_python(cmd):
            job = dict(kind='Quiet run', title='Quiet-machine rerun', detail=short(cmd), gpu=True)
        elif re.search(r'glm_lab\.py (try|run-planned)', cmd) and is_python(cmd):
            job = dict(kind='Experiment', title=' '.join(cmd.split('glm_lab.py', 1)[1].split()[:2]), detail=short(cmd), gpu=True)
        elif 'prep_gguf.sh' in cmd and os.path.basename(exe(cmd)) == 'sh':
            parts = cmd.split()
            name = parts[-1]
            m = next((x for x in cat.values() if x['path'].endswith('/' + name)), {})
            have = dir_gb(HOME / m['download_path']) if m.get('download_path') else 0
            want = m.get('download_gb') or 0
            importing = any('coli import' in c['command'] or ' import ' in c['command'] for c in procs if c['ppid'] == p['pid'])
            job = dict(kind='Download', title=f"{m.get('name', name)}", gpu=False,
                       detail=('importing into Colibri' if importing else f"downloading from {m.get('source', '?')}"),
                       progress=dict(done=round(have, 1), total=want, unit='GB'))
        elif 'prep_mtp_head.sh' in cmd and os.path.basename(exe(cmd)) == 'sh':
            job = dict(kind='Download', title='int8 MTP head for GLM-5.3', detail='download + int8 conversion', gpu=False)
        if job:
            eng = engine_under(p['pid'])
            if eng:
                claimed.add(eng['pid'])
            job.update(pid=p['pid'], command=short(cmd), elapsed_s=p['elapsed_s'], stoppable=True,
                       holds_lock=p['pid'] in holders, engine_pid=eng['pid'] if eng else None)
            out.append(job)
    for p in procs:   # engines no lab job started: e.g. the owner's own chat
        if is_engine(p['command']) and p['pid'] not in claimed:
            parent = by_pid.get(p['ppid'], {})
            out.append(dict(kind='Colibri engine', title='Engine not started by a lab job', gpu=True,
                            detail='parent: ' + short(parent.get('command', ''), 120), pid=p['pid'], command=short(p['command']),
                            elapsed_s=p['elapsed_s'], holds_lock=p['pid'] in holders, engine_pid=None, foreign=True, stoppable=False))
    return out, sorted(holders)


def now():
    js, holders = jobs()
    exps = read_json(ROOT / 'site' / 'data' / 'experiments.json', {})
    entries = exps.get('entries', [])
    recent = [e for e in entries if e.get('runs') and e.get('metrics', {}).get('measured')][::-1][:6]   # registry order = when added
    planned_ready = []
    try:
        import glm_lab
        for e in glm_lab.planned_entries(glm_lab.load_registry()):
            if e.get('plan'):
                why = glm_lab.readiness(e)
                planned_ready.append(dict(id=e['id'], title=e['title'], ready=why is None, why=why or ''))
    except Exception as ex:  # readiness is informative only
        planned_ready.append(dict(id='?', title=f'could not read planned experiments: {ex}', ready=False, why=''))
    tl = timeline(js, planned_ready)
    return dict(time=time.strftime('%Y-%m-%d %H:%M:%S'), jobs=js, lock_holders=holders, machine=machine(), timeline=tl,
                queue=dict(paused=tl['paused'], items=tl['queue'][:5], count=len(tl['queue']), runner=RUNNER.get('last')),
                scoreboard=exps.get('scoreboard', {}), recent=[dict(id=e['id'], title=e['title'], verdict=e['verdict'],
                lossy=e.get('lossy', False), tok_s=e['metrics'].get('tok_s'), ref_tok_s=e['metrics'].get('ref_tok_s'),
                change=e['metrics'].get('speed_change_pct'), date=e.get('date')) for e in recent],
                planned=planned_ready)


# ---------- models and coverage ----------

def installed(m):
    p = HOME / m['path']
    if not p.exists():
        return False
    return (p / m['ready_marker']).exists() if m.get('ready_marker') else True


def suite_runs(runs, bench, mid):
    return [r for r in runs if r['run'].startswith(f'suite-{bench}-{mid}-')]


def bench_folders_for(m):
    names = list(m.get('bench_names', []))
    for d in sorted(glob.glob(str(ROOT / 'results' / f"glm-bench-{m['id']}*"))):
        n = Path(d).name[len('glm-bench-'):]
        if n not in names:
            names.append(n)
    return names


def coverage(m, runs, running):
    """Standard-suite status per bench for one model. `running` maps model id -> {bench id: detail}."""
    cells = {}
    rid = {r['run']: r for r in runs}
    ok = lambda rs: [r for r in rs if r['status'] == 'ok']
    fmt = lambda rs: ' / '.join(f"{num(r['tok_s']):.2f}" for r in rs if num(r['tok_s'])) + ' tok/s'
    # speed reference
    own = [rid.get(r) for r in m.get('speed_runs', [])]
    sr = ok(suite_runs(runs, 'speed', m['id']))
    if own and all(r and r['status'] == 'ok' for r in own):
        cells['speed'] = dict(status='done', detail=fmt(own))
    elif sr:
        latest = sorted(sr, key=lambda r: r['run'])[-4:]
        cells['speed'] = dict(status='done', detail=fmt([r for r in latest if r['run'].endswith(('sky-exact', 'sky-skip050'))]))
    # quality bench
    names = bench_folders_for(m)
    if any(bench_records(n) for n in names):
        n = next(n for n in names if bench_records(n))
        cells['quality'] = dict(status='done', detail=f"bench {n} · {len(bench_records(n))} answers")
    # threads
    tr = [r for r in runs if r['run'].startswith('t-') and r['status'] == 'ok'] if m.get('owner_model') else []
    tr += ok(suite_runs(runs, 'threads', m['id']))
    if tr:
        best = max(tr, key=lambda r: num(r['tok_s']) or 0)
        cells['threads'] = dict(status='done', detail=f"{len(tr)} runs · best {num(best['tok_s']):.2f} tok/s")
    # quiet comparison and RAM sweep
    if m.get('owner_model'):
        quiet = sorted(glob.glob(str(ROOT / 'results' / 'glm-quiet-*' / 'comparison.json')))
        if quiet:
            cj = read_json(quiet[-1], {})
            cells['quiet'] = dict(status='done', detail=Path(quiet[-1]).parent.name)
            if cj.get('ram_sweep'):
                cells['ram'] = dict(status='done', detail=f"{len(cj['ram_sweep'])} budgets")
    rr = ok(suite_runs(runs, 'ram', m['id']))
    if rr and 'ram' not in cells:
        cells['ram'] = dict(status='done', detail=f"{len(rr)} budgets")
    for b, detail in running.get(m['id'], {}).items():
        cells[b] = dict(status='running', detail=detail)
    inst = installed(m)
    for b in suite()['benches']:
        if b['id'] not in cells:
            if not m.get('suite'):
                cells[b['id']] = dict(status='missing', detail='not supported yet')
            else:
                cells[b['id']] = dict(status='missing', detail='never run' if inst else 'not installed')
    return cells


def running_coverage():
    """Benches running right now, per model id, from the process list."""
    out = {}
    cat = catalog()
    for j in jobs()[0]:
        cmd = j.get('command', '')
        if j.get('kind') == 'Quality bench':
            mid = next((m['id'] for m in cat if '--model ~/' + m['path'] + ' ' in cmd + ' '), 'glm-5.3-int4')
            p = j.get('progress') or {}
            out.setdefault(mid, {})['quality'] = f"{p.get('done')}/{p.get('total')}"
        elif 'glm_suite.py run' in cmd:
            parts = cmd.split()
            bench, mid = parts[parts.index('run') + 1], parts[parts.index('--model') + 1]
            out.setdefault(mid, {})[bench] = 'running'
        elif j.get('kind') == 'Quiet run':
            out.setdefault('glm-5.3-int4', {})['quiet'] = 'running'
    return out


def last_downloads():
    """Most recent download attempt started by the app, per model id."""
    res = {}
    for j in actions.refresh_jobs()['jobs']:
        if j['kind'] == 'prep':
            mid = j['args'].get('model')
            if mid not in res:
                tail = job_log(j['id'])['tail'][-4:] if j['status'] == 'failed' else []
                res[mid] = dict(status=j['status'], exit=j.get('exit'), started=j['started'], ended=j.get('ended'), id=j['id'], tail=tail)
    return res


def external():
    return read_json(ROOT / 'models' / 'external-benchmarks.json', {})


def models():
    ext = {r['model']: r for r in external().get('aa_index', {}).get('rows', [])}
    runs = runs_table()
    running = running_coverage()
    downloads = last_downloads()
    exps = read_json(ROOT / 'site' / 'data' / 'experiments.json', {})
    out = []
    for m in catalog():
        inst = installed(m)
        dl = None
        if not inst and m.get('download_path'):
            have = dir_gb(HOME / m['download_path'])
            if have:
                dl = dict(done=round(have, 1), total=m.get('download_gb'))
        cov = coverage(m, runs, running)
        best = {}
        if m.get('owner_model'):
            sb = exps.get('scoreboard', {})
            best = {k: sb[k] for k in ('best_exact', 'best_usable_lossy', 'everyday') if k in sb}
        out.append(dict(m, installed=inst, download=dl, coverage=cov, aa=ext.get(m.get('external_model')), last_download=downloads.get(m['id']),
                        covered=sum(1 for c in cov.values() if c['status'] == 'done'), best=best))
    return dict(models=out, suite=suite())


# ---------- other screens ----------

def benches():
    m = models()
    results = []
    for n in bench_names():
        recs = bench_records(n)
        meta = read_json(ROOT / 'results' / f'glm-bench-{n}' / 'meta.json', {})
        pub = ROOT / 'published-results' / f'glm-bench-{n}'
        results.append(dict(name=n, answers=len(recs), summary=bench_summary(recs), started=meta.get('started'),
                            review='published-results/glm-bench-%s/review.md' % n if (pub / 'review.md').exists() else None,
                            published=pub.exists(),
                            notes=[p.name for p in (ROOT / 'results' / f'glm-bench-{n}').glob('*.md') if p.name != 'report.md']))
    return dict(suite=m['suite'], models=m['models'], results=results)


def bench_detail(name):
    if not SAFE_ID.match(name or ''):
        return None
    prompts = {p['id']: p for p in bench_prompts()[0]}
    recs = bench_records(name)
    return dict(name=name, summary=bench_summary(recs), answers=[dict(
        id=r['id'], kind=r.get('kind'), style=r['style'], config=r['config'], correct=r.get('correct'),
        answer_s=r.get('answer_s'), prefill_s=r.get('prefill_s'), output_tokens=r.get('output_tokens'),
        decode_tok_s=r.get('decode_tok_s'), exit=r.get('exit'), prompt=prompts.get(r['id'], {}).get('prompt'),
        text=r.get('text')) for r in recs])


def experiments():
    return read_json(ROOT / 'site' / 'data' / 'experiments.json', {'entries': []})


def research():
    text = (ROOT / 'research' / 'watchlist.md').read_text() if (ROOT / 'research' / 'watchlist.md').exists() else ''
    items, scans, section = [], [], None
    for line in text.splitlines():
        if line.startswith('## '):
            section = line[3:].strip().lower()
        if not line.startswith('|') or line.startswith('|---'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells[0] in ('Item', 'Date'):
            continue
        if section == 'items' and len(cells) >= 7:
            link = re.search(r'\((https?://[^)]+)\)', cells[2])
            items.append(dict(item=cells[0], type=cells[1], link=link.group(1) if link else None, what=cells[3],
                              relevance=cells[4], decision=cells[5], reviewed=cells[6]))
        elif section == 'scan log' and len(cells) >= 3:
            scans.append(dict(date=cells[0], scope=cells[1], by=cells[2]))
    nxt = re.search(r'Next scan due: ([0-9-]+)', text)
    return dict(items=items, scans=scans, next_scan=nxt.group(1) if nxt else None)


def busy_model_paths():
    """Model folders named on the command line of any running process (engines, downloads)."""
    paths = set()
    md = str(HOME / 'colibri-models')
    for p in processes():
        if os.path.basename(exe(p['command'])).lstrip('-') in ('zsh', 'bash', 'login', 'sudo'):
            continue   # interactive shells and tool wrappers only mention paths
        cmd = p['command'].replace('~/', str(HOME) + '/')
        for m in re.finditer(re.escape(md) + r'/[^\s\'"]+', cmd):
            parts = m.group(0)[len(md) + 1:].split('/')
            paths.add(md + '/' + parts[0])
            if parts[0] == 'gguf' and len(parts) > 1:
                paths.add(md + '/gguf/' + parts[1])
        if 'prep_gguf.sh' in cmd and os.path.basename(exe(cmd)) == 'sh':
            name = cmd.split()[-1]
            paths.update({md + '/' + name, md + '/gguf/' + name})
        if 'prep_mtp_head.sh' in cmd and os.path.basename(exe(cmd)) == 'sh':
            paths.update({md + '/glm-5.3-mtp', md + '/glm-5.3-mtp-head'})
    return sorted(paths)


def storage():
    busy = busy_model_paths()
    known, out = set(), []
    for m in catalog():
        rels = list(dict.fromkeys([m['path']] + ([m['download_path']] if m.get('download_path') else []) + m.get('remove_paths', [])))
        folders = []
        for rel in rels:
            p = HOME / rel
            known.add(str(p))
            if p.exists() or p.is_symlink():
                folders.append(dict(path='~/' + rel, gb=round(dir_gb(p), 1),
                                    in_use=any(b == str(p) or b.startswith(str(p) + '/') for b in busy)))
        if not folders:
            continue
        out.append(dict(id=m['id'], name=m['name'], installed=installed(m), owner_model=bool(m.get('owner_model')),
                        folders=folders, gb=round(sum(f['gb'] for f in folders), 1), in_use=any(f['in_use'] for f in folders),
                        removable=not m.get('owner_model') and bool(m.get('remove_paths'))))
    other = []
    md = HOME / 'colibri-models'
    for p in sorted(list(md.iterdir()) + (list((md / 'gguf').iterdir()) if (md / 'gguf').exists() else [])):
        if p.is_dir() and str(p) not in known and p.name != 'gguf':
            other.append(dict(path=str(p).replace(str(HOME), '~'), gb=round(dir_gb(p), 1)))
    st = os.statvfs(str(HOME))
    return dict(models=out, other=other, disk_free_gb=round(st.f_bavail * st.f_frsize / 1e9))


def gpu_status():
    js, holders = jobs()
    busy = bool(holders) or any(j.get('gpu') for j in js)
    return busy, machine()['quiet']


def timeline(js, planned_ready):
    """What runs now and next: the current GPU job's ETA, then each queued item with an estimate."""
    q = actions.queue_state()
    cur = next((j for j in js if j.get('gpu')), None)
    start = (cur.get('progress') or {}).get('eta_s') if cur else 0
    unknown = cur is not None and start is None
    items = []
    for it in q['items']:
        est = estimate_item(it)
        items.append(dict(it, est_s=est, starts_in_s=None if unknown else start))
        if not unknown:
            start += est
    queued_ids = {i['args'].get('id') for i in q['items'] if i['kind'] == 'planned'}
    not_queued = [p for p in planned_ready if p['ready'] and p['id'] not in queued_ids]
    return dict(paused=q['paused'], current=dict(title=cur['title'], pid=cur['pid'], eta_s=(cur.get('progress') or {}).get('eta_s')) if cur else None,
                queue=items, total_s=None if unknown else start, ready_not_queued=not_queued)


def queue_view():
    js_now, _ = jobs()
    planned = []
    try:
        import glm_lab
        for e in glm_lab.planned_entries(glm_lab.load_registry()):
            if e.get('plan'):
                planned.append(dict(id=e['id'], title=e['title'], ready=glm_lab.readiness(e) is None))
    except Exception:
        pass
    tl = timeline(js_now, planned)
    js = actions.refresh_jobs()['jobs'][:25]
    return dict(paused=tl['paused'], items=tl['queue'], timeline=tl, runner=RUNNER.get('last'), jobs=js)


def job_log(jid):
    js = actions.jobs_state()['jobs']
    j = next((x for x in js if x['id'] == jid), None)
    if not j:
        return None
    lines = (ROOT / j['log']).read_text(errors='replace').replace('\r', '\n').splitlines()
    return dict(id=jid, title=j['title'], status=j['status'], tail=[l.replace(str(HOME), '~') for l in lines[-60:]])


def settings():
    plist = HOME / 'Library' / 'LaunchAgents' / 'dev.kakkoi.glm-lab.plist'
    import glm_quiet
    return dict(repo=str(ROOT).replace(str(HOME), '~'), engine='~/Code/colibri', models='~/colibri-models',
                port=PORT, quiet_threshold_gb=glm_quiet.QUIET_FREE_GB, service_installed=plist.exists(),
                state_dir='results/lab-app', rules=[
                    'One GPU job at a time: the queue starts the next job only when the GPU lock is free and no engine runs.',
                    'Stop is by PID, only for jobs the lab runs; your own Colibri sessions are never stopped from here.',
                    'Downloads start only after a confirmation showing source, size and disk left.',
                    "The owner's engine (~/Code/colibri) and model folder (~/colibri-models/glm-5.3) are never changed.",
                    'Lossy results are labelled "changes output"; only the owner marks a setting usable.',
                    'Runs on a busy machine are recorded as busy; quiet runs need ≥ 20 GB free.'])


def act(path, body):
    if path == '/api/stop':
        js, _ = jobs()
        allowed = {j['pid'] for j in js if j.get('stoppable')}
        return actions.stop(int(body.get('pid', 0)), allowed)
    if path == '/api/run':
        busy, _ = gpu_status()
        if busy:
            item = actions.queue_add(body.get('kind'), body.get('args'), front=True)
            return dict(queued=item, note='GPU busy: added to the front of the queue')
        return dict(started=actions.launch(body.get('kind'), body.get('args')))
    if path == '/api/queue/add':
        return dict(queued=actions.queue_add(body.get('kind'), body.get('args'), front=bool(body.get('front')),
                                             only_when_quiet=bool(body.get('only_when_quiet'))))
    if path == '/api/queue/remove':
        actions.queue_remove(body.get('qid')); return dict(ok=True)
    if path == '/api/queue/move':
        actions.queue_move(body.get('qid'), body.get('dir')); return dict(ok=True)
    if path == '/api/queue/pause':
        actions.queue_pause(body.get('paused')); return dict(ok=True)
    if path == '/api/remove':
        m = next((x for x in catalog() if x['id'] == body.get('model')), None)
        if not m:
            raise actions.ActionError('unknown model')
        return actions.remove_model(m, busy_model_paths())
    if path == '/api/download':
        js, _ = jobs()
        if any(j.get('kind') == 'Download' for j in js):
            raise actions.ActionError('a download is already running; wait for it to finish')
        started = actions.launch('prep', {'model': body.get('model')})
        for _ in range(12):   # a download that cannot start (missing tool, bad repo) dies within seconds
            time.sleep(0.5)
            j = next((x for x in actions.refresh_jobs()['jobs'] if x['id'] == started['id']), None)
            if j and j['status'] != 'running':
                tail = job_log(j['id'])['tail'][-6:]
                raise actions.ActionError('the download stopped right away (exit %s): %s' % (j.get('exit'), ' | '.join(tail)))
        return dict(started=started, note='still running after 6 s; progress shows on Now and Install')
    return None


def run_output(run):
    if not SAFE_ID.match(run or ''):
        return None
    f = OUTPUTS / f'{run}.output.txt'
    return f.read_text() if f.exists() else ''


# ---------- HTTP ----------

API = {
    '/api/now': lambda q: now(),
    '/api/models': lambda q: models(),
    '/api/benches': lambda q: benches(),
    '/api/bench': lambda q: bench_detail(q.get('name', [''])[0]),
    '/api/runs': lambda q: dict(runs=runs_table()),
    '/api/run-output': lambda q: dict(text=run_output(q.get('run', [''])[0])),
    '/api/experiments': lambda q: experiments(),
    '/api/research': lambda q: research(),
    '/api/external': lambda q: external(),
    '/api/queue': lambda q: queue_view(),
    '/api/job-log': lambda q: job_log(q.get('id', [''])[0]),
    '/api/settings': lambda q: settings(),
    '/api/storage': lambda q: storage(),
}
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
         '.svg': 'image/svg+xml', '.json': 'application/json'}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        u = urlparse(self.path)
        origin = self.headers.get('Origin')
        ok_origin = origin in (None, f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}')
        if self.headers.get('X-Lab-Action') != '1' or not ok_origin:
            return self.send(403, b'{"error":"actions are only accepted from the lab app page"}', 'application/json')
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(min(n, 65536)) or b'{}')
            data = act(u.path, body)
        except actions.ActionError as ex:
            return self.send(400, json.dumps(dict(error=str(ex))).encode(), 'application/json')
        except Exception as ex:
            return self.send(500, json.dumps(dict(error=str(ex))).encode(), 'application/json')
        if data is None:
            return self.send(404, b'{"error":"unknown action"}', 'application/json')
        self.send(200, json.dumps(data, ensure_ascii=False).encode(), 'application/json; charset=utf-8')

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in API:
            try:
                data = API[u.path](parse_qs(u.query))
            except Exception as ex:
                return self.send(500, json.dumps(dict(error=str(ex))).encode(), 'application/json')
            if data is None:
                return self.send(400, b'{"error":"bad request"}', 'application/json')
            return self.send(200, json.dumps(data, ensure_ascii=False).encode(), 'application/json; charset=utf-8')
        if u.path.startswith('/api/'):
            return self.send(404, b'{"error":"not found"}', 'application/json')
        name = 'index.html' if u.path in ('/', '') else u.path.lstrip('/')
        f = (STATIC / name).resolve()
        if not str(f).startswith(str(STATIC.resolve())) or not f.is_file():
            return self.send(404, b'not found', 'text/plain')
        self.send(200, f.read_bytes(), TYPES.get(f.suffix, 'application/octet-stream'))


def main():
    global PORT, RUNNER
    ap = argparse.ArgumentParser(description='GLM lab control app (local only)')
    ap.add_argument('--port', type=int, default=8766)
    ap.add_argument('--no-runner', action='store_true', help='do not start queued jobs automatically')
    a = ap.parse_args()
    PORT = a.port
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    if not a.no_runner:
        RUNNER = actions.start_runner(gpu_status)
    print(f'GLM lab app: http://127.0.0.1:{a.port}  (local only; Ctrl+C to stop)', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
