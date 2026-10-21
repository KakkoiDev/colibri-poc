"""Publish saved bench results without staging the owner's working tree."""
import argparse
import csv
import fcntl
import io
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'dev.kakkoi.glm-lab-results'


def run(args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT, timeout=180)


def clean(text):
    return re.sub(r'/Users/[^/\s"]+', '~', text).replace('/private/tmp/', '<tmp>/')


def saved_json(path):
    try:
        return json.loads(clean(path.read_text()))
    except (OSError, ValueError):
        return None  # An answer may still be being written.


def snapshot(source, target):
    """Only allowlisted public data; logs, credentials and user edits stay local."""
    for folder in sorted((source / 'results').glob('glm-bench-*')):
        name = folder.name.removeprefix('glm-bench-')
        if name in ('smoke', '.', '..') or not re.fullmatch(r'[a-zA-Z0-9_.-]+', name):
            continue
        records = {}
        # Preserve previously published answers while a local resume is in progress.
        old = target / 'published-results' / folder.name / 'answers'
        for path in list(old.glob('*__*.json')) + list(folder.glob('*__*.json')):
            value = saved_json(path)
            if isinstance(value, dict) and all(k in value for k in ('id', 'style', 'config', 'exit')):
                records[path.name] = value
        if not records:
            continue
        dest = target / 'results' / folder.name
        dest.mkdir(parents=True, exist_ok=True)
        meta = saved_json(folder / 'meta.json') or {}
        meta['model_label'] = meta.get('ollama_model') or ('GLM-5.3 int4' if name == 'v1' else name)
        (dest / 'meta.json').write_text(json.dumps(meta))
        for filename, value in records.items():
            (dest / filename).write_text(json.dumps(value))
        run([sys.executable, 'publish_bench.py', name], target)
    src = source / 'published-results/glm-20261018'
    dst = target / 'published-results/glm-20261018'
    dst.mkdir(parents=True, exist_ok=True)
    if (src / 'runs.csv').exists():
        text = clean((src / 'runs.csv').read_text())
        reader = csv.DictReader(io.StringIO(text))
        fields = reader.fieldnames
        rows = list(reader)
        if not fields or 'run' not in fields or not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError('Speed CSV is incomplete; retry next time')
        previous = list(csv.DictReader((dst / 'runs.csv').open())) if (dst / 'runs.csv').exists() else []
        merged = {row['run']: row for row in previous + rows}
        with (dst / 'runs.csv').open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(merged.values())
        for path in src.glob('*.output.txt'):
            (dst / path.name).write_text(clean(path.read_text()))
        # Public, machine-readable complete speed table, alongside the curated story.
        (target / 'site/data/speed-runs.json').write_text(json.dumps(list(merged.values()), indent=1) + '\n')
    run([sys.executable, 'glm_lab.py', 'log'], target)
    # Failed rows have undefined means; browsers require strict JSON nulls.
    for path in (target / 'site/data').glob('*.json'):
        text = path.read_text()
        if re.search(r'(?<![\w\"])NaN(?![\w\"])', text):
            value = json.loads(text, parse_constant=lambda _: None)
            path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n')


def sync():
    state = ROOT / 'results/lab-app'
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'publisher.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        remote = run(['git', 'remote', 'get-url', 'origin']).strip()
        with tempfile.TemporaryDirectory(prefix='colibri-publish-') as temp:
            checkout = Path(temp) / 'repo'
            run(['git', 'clone', '--shared', str(ROOT), str(checkout)])
            run(['git', 'remote', 'set-url', 'origin', remote], checkout)
            run(['git', 'fetch', 'origin', 'main'], checkout)
            run(['git', 'checkout', '--detach', 'FETCH_HEAD'], checkout)
            snapshot(ROOT, checkout)
            paths = ['published-results', 'site/data', 'docs/12-experiment-log.md']
            run(['git', 'add', '--', *paths], checkout)
            changed = run(['git', 'diff', '--cached', '--name-only'], checkout).strip()
            if not changed:
                print('No new results', flush=True)
                return
            run(['git', 'commit', '-m', 'Publish latest saved benchmark results'], checkout)
            # Normal fast-forward push; concurrent main changes are retried next cycle.
            print(run(['git', 'push', 'origin', 'HEAD:main'], checkout), flush=True)
            # Fetch updates tracking refs without changing the working tree or index.
            run(['git', 'fetch', 'origin', 'main'])


def install(remove=False):
    plist = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
    domain = 'gui/' + str(os.getuid())
    subprocess.run(['launchctl', 'bootout', domain + '/' + LABEL], capture_output=True)
    if remove:
        plist.unlink(missing_ok=True)
        return
    logs = ROOT / 'results/lab-app/publisher.log'
    logs.parent.mkdir(parents=True, exist_ok=True)
    env = {k: os.environ[k] for k in ('HOME', 'PATH', 'SSH_AUTH_SOCK') if k in os.environ}
    config = dict(Label=LABEL, ProgramArguments=[sys.executable, str(Path(__file__).resolve()), 'once'],
                  WorkingDirectory=str(ROOT), EnvironmentVariables=env, StartInterval=300,
                  RunAtLoad=True, StandardOutPath=str(logs), StandardErrorPath=str(logs))
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps(config))
    run(['launchctl', 'bootstrap', domain, str(plist)])
    print('Automatic public results publishing enabled: every five minutes at login.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['once', 'install', 'uninstall'])
    args = parser.parse_args()
    if args.command == 'once':
        sync()
    else:
        install(args.command == 'uninstall')
