"""Isolated demo server for the lab app: the real server code and the lab's real files, with
nothing that can change the Mac.

    .venv/bin/python lab_app/demo_server.py                     # http://127.0.0.1:8767, a bench running
    .venv/bin/python lab_app/demo_server.py --scenario idle     # nothing running, empty queue
    .venv/bin/python lab_app/demo_server.py --scenario download # a model download in progress

Use it to design, test and screenshot the interface while the real app (port 8766) keeps
running benchmarks. What it does differently from server.py:
- The queue and job history are a throwaway copy of results/lab-app in a temp folder, so
  queueing, reordering, pausing and removing only change that copy.
- No queue runner thread: nothing ever starts.
- Start, stop, download and remove are answered with fake results: no process is launched or
  signalled, nothing is downloaded, nothing moves to the Trash.
- Processes, memory, disk and the models folder are fixtures (below), so every screen shows a
  realistic state on any machine. Bench results, runs and experiments are the real files.
"""
import argparse, json, os, shutil, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import server as s  # noqa: E402
import actions as a  # noqa: E402

GB = {   # model folder -> size on disk (GB), as measured on the owner's Mac on 2026-10-20
    'colibri-models/glm-5.3': 390.5, 'colibri-models/glm-5.3-mtp': 0, 'colibri-models/glm-5.3-mtp-head': 9.3,
    'colibri-models/glm-5.3-iq3xxs': 0, 'colibri-models/gguf/glm-5.3-iq3xxs': 262.3,
    'colibri-models/glm-5.3-iq2m': 0, 'colibri-models/gguf/glm-5.3-iq2m': 311.4,
    'colibri-models/glm-5.3-flash-iq3xxs': 0, 'colibri-models/gguf/glm-5.3-flash-iq3xxs': 112.1,
    'colibri-models/qwen36-35b-a3b': 21.4, 'colibri-models/deepseek-v4-flash-reap': 78.9,
}
OLLAMA = ['gemma4:26b', 'gemma4:26b-mlx', 'gemma4:31b-mlx', 'gemma4:e4b-mlx', 'gpt-oss:20b', 'qwen3.8:27b-mlx']
BENCH_PID, ENGINE_PID, DOWNLOAD_PID = 73401, 14168, 81234


def fixture_processes(scenario, stopped):
    procs = [dict(pid=1, ppid=0, elapsed_s=99999, command='/sbin/launchd')]
    if scenario == 'busy' and BENCH_PID not in stopped:
        procs += [
            dict(pid=BENCH_PID, ppid=1, elapsed_s=5798, command='.venv/bin/python glm_bench.py run --name glm-5.3-iq3xxs '
                 '--configs exact,d030,d050,d030t12,d040t12 --styles terse --model ~/colibri-models/glm-5.3-iq3xxs --coli-dir engines/colibri-16239caa'),
            dict(pid=ENGINE_PID, ppid=BENCH_PID, elapsed_s=40, command=str(s.ROOT / 'engines/colibri-16239caa/c/colibri') + ' 0'),
        ]
    if scenario == 'download' and DOWNLOAD_PID not in stopped:
        procs.append(dict(pid=DOWNLOAD_PID, ppid=1, elapsed_s=1260, command='sh scripts/prep_gguf.sh glm-5.3-iq2m'))
    return procs


def main():
    ap = argparse.ArgumentParser(description='GLM lab app, isolated demo (nothing can run, stop, download or delete)')
    ap.add_argument('--port', type=int, default=8767)
    ap.add_argument('--scenario', choices=['busy', 'idle', 'download'], default='busy')
    opt = ap.parse_args()

    # 1. Throwaway state: a copy of the real queue and job history (or an empty one for idle).
    tmp = Path(tempfile.mkdtemp(prefix='glm-lab-demo-'))
    state = tmp / 'lab-app'
    if opt.scenario != 'idle' and a.STATE.exists():
        shutil.copytree(a.STATE, state, ignore=shutil.ignore_patterns('*.log', 'server.log'))
    state.mkdir(parents=True, exist_ok=True)
    (state / 'logs').mkdir(exist_ok=True)
    if opt.scenario == 'idle':
        (state / 'queue.json').write_text(json.dumps({'paused': False, 'items': []}))
    a.STATE, a.LOGS = state, state / 'logs'

    # 2. A fake home with the installed models' folders, so "installed" checks are real file checks.
    home = tmp / 'home'
    for rel in GB:
        (home / rel).mkdir(parents=True, exist_ok=True)
    for m in s.catalog():
        if m.get('ready_marker') and (home / m['path']).exists():
            (home / m['path'] / m['ready_marker']).touch()
    if opt.scenario == 'download':   # the 2-bit GGUF is mid-download: folder present, marker missing
        for m in s.catalog():
            if m['id'] == 'glm-5.3-iq2m' and m.get('ready_marker'):
                (home / m['path'] / m['ready_marker']).unlink(missing_ok=True)
    s.HOME = home
    a.MODELS_DIR = home / 'colibri-models'
    real_home = Path.home
    Path.home = classmethod(lambda cls: home)
    s.dir_gb = lambda p: GB.get(str(Path(p)).replace(str(home) + '/', ''), 0) * (0.37 if opt.scenario == 'download' and str(p).endswith('gguf/glm-5.3-iq2m') else 1)

    # 3. Processes, lock and machine state are fixtures.
    stopped = set()
    s.processes = lambda: fixture_processes(opt.scenario, stopped)
    s.lock_holders = lambda: [BENCH_PID] if opt.scenario == 'busy' and BENCH_PID not in stopped else []
    a.ollama_models = lambda: set(OLLAMA)
    real_machine = s.machine

    def machine():
        return dict(free_gb=6.3 if opt.scenario == 'busy' else 22.4, swap_used_mb=4736.06, process_count=476, load_avg=[6.9, 6.7, 6.5],
                    top_apps=[dict(name='colibri', rss_gb=1.84), dict(name='Claude Helper (Renderer)', rss_gb=0.6),
                              dict(name='Claude', rss_gb=0.25), dict(name='Codex (Renderer)', rss_gb=0.2)],
                    quiet=opt.scenario != 'busy', quiet_threshold_gb=20, disk_free_gb=453,
                    quiet_for_s=0 if opt.scenario == 'busy' else 600)
    s.machine = machine
    real_storage = s.storage
    s.storage = lambda: dict(real_storage(), disk_free_gb=453)

    # 4. Actions that would touch the Mac answer with fake results.
    def fake_launch(kind, args, source='app', only_when_quiet=False):
        argv, title = a.build_command(kind, args)   # still validated exactly like the real app
        jid = time.strftime('%Y%m%dT%H%M%S') + '-' + kind
        with a._lock:
            js = a.jobs_state()
            js['jobs'].insert(0, dict(id=jid, kind=kind, args=args, title=title, argv=argv, pid=0, status='running' if kind == 'prep' else 'done', exit=None if kind == 'prep' else 0,
                                      started=time.strftime('%Y-%m-%d %H:%M:%S'), log='', source='demo'))
            a._write('jobs.json', js)
        return dict(id=jid, pid=0, title=title + ' (demo: not started)')

    def fake_stop(pid, allowed):
        if pid not in allowed:
            raise a.ActionError(f'PID {pid} is not a lab job; stop it from a terminal if you mean to')
        stopped.add(pid)
        return dict(stopped=[pid], demo=True)

    def fake_remove(m, busy):
        targets = a.remove_targets(m)   # same safety checks as the real app
        if not targets:
            raise a.ActionError('nothing to remove: no folders of this model exist')
        return dict(moved=[dict(src=str(t).replace(str(home), '~'), trash='(demo: nothing moved)') for t in targets])

    a.launch, a.stop, a.remove_model = fake_launch, fake_stop, fake_remove
    a.refresh_jobs = a.jobs_state   # never probes real PIDs
    s.RUNNER = {'last': 'demo: runner off, nothing starts'}
    s.PORT = opt.port

    srv = s.ThreadingHTTPServer(('127.0.0.1', opt.port), s.Handler)
    print(f'GLM lab demo ({opt.scenario}): http://127.0.0.1:{opt.port}  state copy in {state}', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        Path.home = real_home
        s.machine = real_machine
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
