"""Actions for the lab control app: queue, job launcher, stop, downloads.

Safety rules (enforced here, not just in the UI):
- Only fixed lab commands can run: planned experiments, quality benches, quiet runs, and
  the catalog's `make glm-prep-*` targets. Arguments are validated against known values.
- One GPU job at a time: the queue starts a job only when no GPU job, no Colibri engine and
  no `.bench.lock` holder exists.
- Stop is by PID and only for jobs the lab runs (bench, quiet run, experiment, download),
  never for a Colibri engine the owner started (e.g. `coli chat`).
- Downloads start only through an explicit request (the UI shows a confirmation first).
- Removing a model moves its catalog `remove_paths` to the macOS Trash (restorable until the
  Trash is emptied). Never the owner's model, never anything outside ~/colibri-models, and
  never a model that is downloading or in use by a running engine.
State lives in results/lab-app/ (git-ignored): queue.json, jobs.json and one log per job.
"""
import json, os, re, signal, subprocess, sys, threading, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / 'results' / 'lab-app'
LOGS = STATE / 'logs'
PY = str(ROOT / '.venv' / 'bin' / 'python')
SAFE = re.compile(r'^[A-Za-z0-9._-]{1,80}$')
GPU_KINDS = {'planned', 'bench', 'quiet', 'suite'}
SUITE_BENCHES = {'speed', 'threads', 'ram'}
QUIET_FLAGS = {'ram-sweep', 'skip-original', 'experiments-only', 'skip-experiments'}
_lock = threading.RLock()
_procs = {}   # pid -> Popen for jobs started by this server process


class ActionError(ValueError):
    pass


def _read(name, default):
    try:
        return json.loads((STATE / name).read_text())
    except (OSError, ValueError):
        return default


def _write(name, data):
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = STATE / (name + '.tmp')
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(STATE / name)


def queue_state():
    return _read('queue.json', {'paused': False, 'items': []})


def jobs_state():
    return _read('jobs.json', {'jobs': []})


# ---------- commands (whitelist) ----------

def _configs():
    sys.path.insert(0, str(ROOT))
    import glm_bench
    return set(glm_bench.CONFIGS)


def _styles():
    return set(json.loads((ROOT / 'glm-prompts.json').read_text())['styles'])


def _planned_ids():
    sys.path.insert(0, str(ROOT))
    import glm_lab
    return {e['id']: e for e in glm_lab.planned_entries(glm_lab.load_registry()) if e.get('plan')}


def _catalog():
    return {m['id']: m for m in json.loads((ROOT / 'models' / 'catalog.json').read_text())['models']}


def _runnable_model(mid):
    m = _catalog().get(mid)
    if not m:
        raise ActionError(f'unknown model: {mid}')
    if not m.get('suite'):
        raise ActionError(f"{m['name']}: {m.get('suite_note', 'benches cannot run on it yet')}")
    if not (Path.home() / m['path']).exists():
        raise ActionError(f"{m['name']} is not installed")
    return m


def ollama_models():
    """Names from `ollama list` (empty when Ollama is not installed or not running)."""
    try:
        out = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return set()
    return {l.split()[0] for l in out.splitlines()[1:] if l.strip()}


def build_command(kind, args):
    """Validated argv for a lab job, plus a human title."""
    args = args or {}
    if kind == 'planned':
        eid = args.get('id', '')
        planned = _planned_ids()
        if eid not in planned:
            raise ActionError(f'not a planned experiment: {eid}')
        return [PY, 'glm_lab.py', 'run-planned', eid], f"Experiment: {planned[eid]['title']}"
    if kind == 'bench':
        name = args.get('name', '')
        configs = args.get('configs') or []
        styles = args.get('styles') or []
        if not SAFE.match(name):
            raise ActionError('bench name must be letters, digits, dot, dash or underscore')
        bad = [c for c in configs if c not in _configs()] + [s for s in styles if s not in _styles()]
        if not configs or not styles or bad:
            raise ActionError(f'unknown or missing configs/styles: {bad or "none given"}')
        argv = [PY, 'glm_bench.py', 'run', '--name', name, '--configs', ','.join(configs), '--styles', ','.join(styles)]
        label = ''
        if args.get('ollama_model'):
            om = args['ollama_model']
            if om not in ollama_models():
                raise ActionError(f'not an installed Ollama model: {om}')
            if configs != ['exact']:
                raise ActionError('Ollama benches run the exact config only (skip settings are Colibri-only)')
            argv += ['--backend', 'ollama', '--ollama-model', om]
            label = f' on Ollama {om}'
        elif args.get('model') and args['model'] != 'glm-5.3-int4':
            m = _runnable_model(args['model'])
            argv += ['--model', '~/' + m['path'], '--coli-dir', m['coli_dir']]
            label = f" on {m['name']}"
        return argv, f"Quality bench {name}{label}: {', '.join(configs)} · {', '.join(styles)}"
    if kind == 'quiet':
        flags = args.get('flags') or []
        if any(f not in QUIET_FLAGS for f in flags):
            raise ActionError(f'unknown quiet-run flags: {flags}')
        return [PY, 'glm_quiet.py', 'run'] + ['--' + f for f in flags], 'Quiet run' + (f" ({', '.join(flags)})" if flags else '')
    if kind == 'suite':
        bench, mid = args.get('bench'), args.get('model', '')
        if bench not in SUITE_BENCHES:
            raise ActionError(f'unknown suite bench: {bench}')
        m = _runnable_model(mid)
        return [PY, 'glm_suite.py', 'run', bench, '--model', mid], f"{bench.capitalize()} bench on {m['name']}"
    if kind == 'prep':
        mid = args.get('model', '')
        cat = {m['id']: m for m in json.loads((ROOT / 'models' / 'catalog.json').read_text())['models']}
        m = cat.get(mid)
        if not m or not m.get('prep', '').startswith('make glm-prep-'):
            raise ActionError(f'no download/prep step for model: {mid}')
        target = m['prep'].split()[1]
        if not re.match(r'^glm-prep-[a-z0-9-]+$', target):
            raise ActionError('bad prep target')
        return ['make', target], f"Download and prepare {m['name']}"
    raise ActionError(f'unknown job kind: {kind}')


# ---------- launching and tracking ----------

def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def launch(kind, args, source='app'):
    argv, title = build_command(kind, args)
    LOGS.mkdir(parents=True, exist_ok=True)
    jid = time.strftime('%Y%m%dT%H%M%S') + '-' + kind
    log = LOGS / f'{jid}.log'
    with open(log, 'w') as fh:
        fh.write(f"# {title}\n# {' '.join(argv)}\n")
        fh.flush()
        p = subprocess.Popen(argv, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             start_new_session=True)
    _procs[p.pid] = p
    with _lock:
        js = jobs_state()
        js['jobs'].insert(0, dict(id=jid, kind=kind, args=args, title=title, argv=argv, pid=p.pid, status='running',
                                  started=time.strftime('%Y-%m-%d %H:%M:%S'), log=str(log.relative_to(ROOT)), source=source))
        js['jobs'] = js['jobs'][:200]
        _write('jobs.json', js)
    return dict(id=jid, pid=p.pid, title=title)


def refresh_jobs():
    with _lock:
        js = jobs_state()
        changed = False
        for j in js['jobs']:
            if j['status'] != 'running':
                continue
            p = _procs.get(j['pid'])
            code = p.poll() if p else (None if _alive(j['pid']) else 'unknown')
            if code is None:
                continue
            j['status'] = 'done' if code == 0 else ('finished' if code == 'unknown' else 'failed')
            j['exit'] = code
            j['ended'] = time.strftime('%Y-%m-%d %H:%M:%S')
            _procs.pop(j['pid'], None)
            changed = True
        if changed:
            _write('jobs.json', js)
        return js


# ---------- queue ----------

def queue_add(kind, args, front=False, only_when_quiet=False):
    if kind not in GPU_KINDS:
        raise ActionError('only GPU jobs (experiments, benches, quiet runs) go through the queue')
    _, title = build_command(kind, args)   # validate now, not when it reaches the head
    item = dict(qid=time.strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8], kind=kind, args=args,
                title=title, only_when_quiet=bool(only_when_quiet), added=time.strftime('%Y-%m-%d %H:%M:%S'))
    with _lock:
        q = queue_state()
        q['items'].insert(0, item) if front else q['items'].append(item)
        _write('queue.json', q)
    return item


def queue_remove(qid):
    with _lock:
        q = queue_state()
        q['items'] = [i for i in q['items'] if i['qid'] != qid]
        _write('queue.json', q)


def queue_move(qid, direction):
    with _lock:
        q = queue_state()
        ids = [i['qid'] for i in q['items']]
        if qid not in ids:
            raise ActionError('no such queue item')
        k = ids.index(qid)
        n = k - 1 if direction == 'up' else k + 1
        if 0 <= n < len(ids):
            q['items'][k], q['items'][n] = q['items'][n], q['items'][k]
        _write('queue.json', q)


def queue_pause(paused):
    with _lock:
        q = queue_state()
        q['paused'] = bool(paused)
        _write('queue.json', q)


def queue_tick(gpu_busy, quiet):
    """Start the queue's first item when the GPU is free. Returns why it waits, if it does."""
    refresh_jobs()
    with _lock:
        q = queue_state()
        if q['paused']:
            return 'queue paused'
        if not q['items']:
            return 'queue empty'
        if gpu_busy:
            return 'GPU busy'
        head = q['items'][0]
        if head.get('only_when_quiet') and not quiet:
            return 'waiting for a quiet machine (≥ 20 GB free)'
        q['items'] = q['items'][1:]
        _write('queue.json', q)
    try:
        launch(head['kind'], head['args'], source='queue')
    except ActionError as ex:
        return f'skipped invalid item: {ex}'
    return 'started ' + head['title']


# ---------- stop ----------

def descendants(pid):
    out = subprocess.run(['ps', '-axo', 'pid=,ppid='], capture_output=True, text=True).stdout
    kids = {}
    for line in out.splitlines():
        a, b = line.split()
        kids.setdefault(int(b), []).append(int(a))
    res, stack = [], [pid]
    while stack:
        for c in kids.get(stack.pop(), []):
            res.append(c); stack.append(c)
    return res


def stop(pid, allowed_pids):
    """SIGTERM a lab job and everything it started. `allowed_pids` comes from the job list."""
    if pid not in allowed_pids:
        raise ActionError(f'PID {pid} is not a lab job; stop it from a terminal if you mean to')
    tree = descendants(pid)
    for p in reversed(tree):
        try:
            os.kill(p, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    return dict(stopped=[pid] + tree)


# ---------- background runner ----------

def start_runner(status_fn, interval=10):
    """status_fn() -> (gpu_busy: bool, quiet: bool). Runs queue_tick forever in a thread."""
    state = {'last': 'starting'}

    def loop():
        while True:
            try:
                busy, quiet = status_fn()
                state['last'] = queue_tick(busy, quiet)
            except Exception as ex:   # keep the runner alive; surface the error in the UI
                state['last'] = f'runner error: {ex}'
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True, name='lab-queue').start()
    return state


# ---------- remove (to the Trash) ----------

MODELS_DIR = Path.home() / 'colibri-models'


def remove_targets(m):
    """Existing folders a catalog model may remove; validated to stay inside ~/colibri-models."""
    if m.get('owner_model'):
        raise ActionError("the owner's model is never removed by the app")
    out = []
    for rel in m.get('remove_paths', []):
        p = Path.home() / rel
        parent = p.parent.resolve()
        if not (parent == MODELS_DIR.resolve() or MODELS_DIR.resolve() in parent.parents):
            raise ActionError(f'refusing a path outside ~/colibri-models: {rel}')
        if p.name in ('', '.', '..', 'glm-5.3') or (p.exists() and p.resolve() == (MODELS_DIR / 'glm-5.3').resolve()):
            raise ActionError(f'refusing to remove {rel}')
        if p.exists() or p.is_symlink():
            out.append(p)
    return out


def remove_model(m, busy_paths):
    targets = remove_targets(m)
    if not targets:
        raise ActionError('nothing to remove: no folders of this model exist')
    for t in targets:
        if any(b == str(t) or b.startswith(str(t) + '/') for b in busy_paths):
            raise ActionError(f'{t.name} is in use by a running job or engine; stop it first')
    trash = Path.home() / '.Trash'
    moved = []
    for t in targets:
        dest = trash / f"{t.name}-{time.strftime('%Y%m%d-%H%M%S')}"
        os.rename(t, dest)   # same volume: instant, nothing is deleted
        moved.append(dict(src=str(t).replace(str(Path.home()), '~'), trash=str(dest).replace(str(Path.home()), '~')))
    return dict(moved=moved)
