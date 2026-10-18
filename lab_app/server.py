"""GLM lab control app: a read-only local web app over the lab's files and processes.

    .venv/bin/python lab_app/server.py            # http://127.0.0.1:8766
    .venv/bin/python lab_app/server.py --port N

Version 1 is read-only: it shows what is running, models, benches and coverage, runs,
experiments and research, but it never starts, stops or downloads anything. It binds to
127.0.0.1 only. Data comes from the same files the lab tools write, so nothing is retyped.
"""
import argparse, csv, glob, json, os, re, subprocess, sys, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / 'static'
HOME = Path.home()
sys.path.insert(0, str(ROOT))

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


def bench_job_progress(cmd):
    """Progress of a running `glm_bench.py run` from its arguments and the saved answers."""
    name = arg(cmd, '--name')
    prompts, styles = bench_prompts()
    configs = (arg(cmd, '--configs') or 'exact,d030,d050').split(',')
    styl = (arg(cmd, '--styles') or 'normal,terse').split(',')
    only = arg(cmd, '--only')
    items = [p for p in prompts if not only or p['id'] in only.split(',')]
    keys = [f"{p['id']}__{s}__{c}" for s in styl for p in items for c in configs]
    folder = ROOT / 'results' / f'glm-bench-{name}'
    done = [k for k in keys if (folder / f'{k}.json').exists()]
    nxt = next((k for k in keys if k not in done), None)
    return dict(name=name, configs=configs, styles=styl, total=len(keys), done=len(done), current=nxt)


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
            prog = bench_job_progress(cmd)
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
            job.update(pid=p['pid'], command=short(cmd), elapsed_s=p['elapsed_s'],
                       holds_lock=p['pid'] in holders, engine_pid=eng['pid'] if eng else None)
            out.append(job)
    for p in procs:   # engines no lab job started: e.g. the owner's own chat
        if is_engine(p['command']) and p['pid'] not in claimed:
            parent = by_pid.get(p['ppid'], {})
            out.append(dict(kind='Colibri engine', title='Engine not started by a lab job', gpu=True,
                            detail='parent: ' + short(parent.get('command', ''), 120), pid=p['pid'], command=short(p['command']),
                            elapsed_s=p['elapsed_s'], holds_lock=p['pid'] in holders, engine_pid=None, foreign=True))
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
    return dict(time=time.strftime('%Y-%m-%d %H:%M:%S'), jobs=js, lock_holders=holders, machine=machine(),
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


def coverage(m, runs, running_benches):
    cells = {}
    rid = {r['run']: r for r in runs}
    # speed reference
    sr = [rid.get(r) for r in m.get('speed_runs', [])]
    if sr and all(r and r['status'] == 'ok' for r in sr):
        cells['speed'] = dict(status='done', detail=' / '.join(f"{num(r['tok_s']):.2f}" for r in sr) + ' tok/s')
    # quality bench
    names = m.get('bench_names', [])
    run_names = [n for n in names if n in running_benches]
    if run_names:
        p = running_benches[run_names[0]]
        cells['quality'] = dict(status='running', detail=f"{p['done']}/{p['total']}")
    elif any(bench_records(n) for n in names):
        n = names[0]
        recs = bench_records(n)
        cells['quality'] = dict(status='done', detail=f"bench {n} · {len(recs)} answers")
    # quiet comparison, RAM sweep and thread sweep exist only for the owner's model so far
    if m.get('owner_model'):
        quiet = sorted(glob.glob(str(ROOT / 'results' / 'glm-quiet-*' / 'comparison.json')))
        if quiet:
            cj = read_json(quiet[-1], {})
            cells['quiet'] = dict(status='done', detail=Path(quiet[-1]).parent.name)
            if cj.get('ram_sweep'):
                cells['ram'] = dict(status='done', detail=f"{len(cj['ram_sweep'])} budgets")
        t = [r for r in runs if r['run'].startswith('t-') and r['status'] == 'ok']
        if t:
            best = max(t, key=lambda r: num(r['tok_s']) or 0)
            cells['threads'] = dict(status='done', detail=f"{len(t)} runs · best {num(best['tok_s']):.2f} tok/s")
    inst = installed(m)
    for b in suite()['benches']:
        cells.setdefault(b['id'], dict(status='missing', detail='never run' if inst else 'not installed'))
    return cells


def external():
    return read_json(ROOT / 'models' / 'external-benchmarks.json', {})


def models():
    ext = {r['model']: r for r in external().get('aa_index', {}).get('rows', [])}
    runs = runs_table()
    running = {}
    for j in jobs()[0]:
        if j.get('kind') == 'Quality bench':
            running[j['progress']['name']] = j['progress']
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
        out.append(dict(m, installed=inst, download=dl, coverage=cov, aa=ext.get(m.get('external_model')),
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
        name = 'index.html' if u.path in ('/', '') else u.path.lstrip('/')
        f = (STATIC / name).resolve()
        if not str(f).startswith(str(STATIC.resolve())) or not f.is_file():
            return self.send(404, b'not found', 'text/plain')
        self.send(200, f.read_bytes(), TYPES.get(f.suffix, 'application/octet-stream'))


def main():
    ap = argparse.ArgumentParser(description='GLM lab control app (read-only, local)')
    ap.add_argument('--port', type=int, default=8766)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'GLM lab app: http://127.0.0.1:{a.port}  (read-only, local only; Ctrl+C to stop)', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
