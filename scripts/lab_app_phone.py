#!/usr/bin/env python3
"""Enable private, persistent phone access without changing other Serve ports."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'lab_app'))
import remote_access


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['enable', 'disable', 'status'])
    ap.add_argument('--port', type=int, default=9443)
    args = ap.parse_args()
    binary = shutil.which('tailscale')
    if not binary:
        raise SystemExit('Install and sign into Tailscale first.')
    def ts(*argv):
        return subprocess.check_output([binary, *argv], text=True, timeout=30)
    if args.action == 'status':
        print(json.dumps(remote_access.config(), indent=2))
        print(ts('serve', 'status'))
        return
    if args.action == 'disable':
        old = remote_access.config()
        if old:
            from urllib.parse import urlsplit
            port = urlsplit(old['url']).port or 443
            print(ts('serve', f'--https={port}', 'off'))
            remote_access.CONFIG.unlink(missing_ok=True)
        return
    if not 1024 <= args.port <= 65535:
        raise SystemExit('Use a dedicated HTTPS port from 1024 to 65535.')
    status = json.loads(ts('status', '--json'))
    if status.get('BackendState') != 'Running':
        raise SystemExit('Sign into Tailscale before enabling phone access.')
    own = status['Self']
    host = own['DNSName'].rstrip('.')
    user = status['User'][str(own['UserID'])]['LoginName']
    serve = json.loads(ts('serve', 'status', '--json'))
    key = f'{host}:{args.port}'
    existing = serve.get('Web', {}).get(key)
    target = 'http://127.0.0.1:8766'
    if str(args.port) in serve.get('TCP', {}) and not existing:
        raise SystemExit(f'Port {args.port} is already used by another Serve listener.')
    if existing and existing != {'Handlers': {'/': {'Proxy': target}}}:
        raise SystemExit(f'Port {args.port} is already used by another Serve configuration; choose another --port.')
    old = remote_access.config()
    url = f'https://{key}'
    if old and old['url'] != url:
        raise SystemExit('Disable the previous lab sharing configuration before changing ports.')
    # --bg persists in tailscaled across terminal closure and daemon restarts.
    print(ts('serve', '--bg', f'--https={args.port}', target))
    remote_access.CONFIG.parent.mkdir(parents=True, exist_ok=True)
    remote_access.CONFIG.write_text(json.dumps(dict(url=url, users=[user]), indent=2) + '\n')
    remote_access.CONFIG.chmod(0o600)
    print(f'Phone address: {url}\nQR code: http://127.0.0.1:8766/#phone')


if __name__ == '__main__':
    main()
