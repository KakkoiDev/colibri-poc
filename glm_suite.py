"""Run one standard bench from benches/suite.json on any catalog model.

    .venv/bin/python glm_suite.py run speed   --model glm-5.3-iq3xxs
    .venv/bin/python glm_suite.py run threads --model glm-5.3-int4
    .venv/bin/python glm_suite.py run ram     --model glm-5.3-int4

Quality benches use glm_bench.py and quiet comparisons glm_quiet.py; this script covers the
short speed benches. Each run is named suite-<bench>-<model>-<stamp>-<case>, logged and
published like every other run (glm_lab.execute), so the lab app's coverage grid and the
website pick them up. One GPU job at a time (.bench.lock). The owner's Colibri state is
not changed (USAGE_SAVE=0, KVSAVE=0, --no-tune-profile).
"""
import argparse, json, re, sys, time
from pathlib import Path

import glm_lab

ROOT = Path(__file__).resolve().parent
SKIP05 = {'DEGRADE_ZERO': '1', 'DEGRADE_TAU': '0.50'}
# bench -> list of (case, prompt, tokens, extra env, ram)
CASES = {
    'speed': [('sky-exact', 'sky', 24, {}, 18), ('code-exact', 'code', 24, {}, 18),
              ('sky-skip050', 'sky', 48, SKIP05, 18), ('code-skip050', 'code', 48, SKIP05, 18)],
    'threads': [('sky-exact-t2', 'sky', 24, {'OMP_NUM_THREADS': '2'}, 18), ('sky-exact-t6', 'sky', 24, {'OMP_NUM_THREADS': '6'}, 18),
                ('sky-exact-t12', 'sky', 24, {'OMP_NUM_THREADS': '12'}, 18),
                ('sky-skip050-t2', 'sky', 48, dict(SKIP05, OMP_NUM_THREADS='2'), 18),
                ('sky-skip050-t12', 'sky', 48, dict(SKIP05, OMP_NUM_THREADS='12'), 18)],
    'ram': [('sky-exact-ram18', 'sky', 24, {}, 18), ('sky-exact-ram22', 'sky', 24, {}, 22), ('sky-exact-ram26', 'sky', 24, {}, 26)],
}


def model(mid):
    for m in json.loads((ROOT / 'models' / 'catalog.json').read_text())['models']:
        if m['id'] == mid:
            return m
    raise SystemExit(f'unknown model: {mid}')


def run(bench, mid, run_id=None):
    m = model(mid)
    if not m.get('suite'):
        raise SystemExit(f"{mid}: {m.get('suite_note', 'not supported by the suite')}")
    mdir = Path('~/' + m['path']).expanduser()
    if not mdir.exists():
        raise SystemExit(f'{mid} is not installed ({mdir})')
    lock = glm_lab.acquire_lock()
    stamp = run_id or time.strftime('%Y%m%dT%H%M%S')
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', stamp):
        raise SystemExit('invalid run id')
    if m['coli_dir'].startswith('engines/'):
        glm_lab.build_engine({'coli_dir': m['coli_dir'], 'build': {'ref': m['coli_dir'].split('-')[-1]}})
    for case, prompt, ngen, env, ram in CASES[bench]:
        name = f'suite-{bench}-{mid}-{stamp}-{case}'
        previous = glm_lab.runs_table().get(name, {})
        if previous.get('status') == 'ok':
            print(f'  {name} saved; skipping', flush=True)
            continue
        # execute publishes to fixed paths: retain previous attempts before retry.
        for base, suffix in ((glm_lab.RAW_LOGS, '.log'), (glm_lab.PUBLISHED, '.output.txt')):
            old = base / (name + suffix)
            if old.exists():
                archive = ROOT / 'results' / 'suite-attempts' / name / str(time.time_ns())
                archive.mkdir(parents=True, exist_ok=True)
                (archive / old.name).write_bytes(old.read_bytes())
        if previous:
            archive = ROOT / 'results' / 'suite-attempts' / name
            archive.mkdir(parents=True, exist_ok=True)
            (archive / (str(time.time_ns()) + '.json')).write_text(json.dumps(previous))
        glm_lab.execute(name, prompt, ngen, env, coli_dir=m['coli_dir'], model=str(mdir), ram=ram)
        print(f'  {name} done', flush=True)
    lock.close()


def main():
    ap = argparse.ArgumentParser(description='Run a standard bench on any catalog model')
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('bench', choices=sorted(CASES))
    r.add_argument('--model', required=True)
    r.add_argument('--run-id', help='Stable sweep identity; successful cases are reused on resume')
    a = ap.parse_args()
    run(a.bench, a.model, a.run_id)


if __name__ == '__main__':
    main()
