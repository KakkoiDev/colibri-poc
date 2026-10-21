"""Loopback backend + explicit Tailscale Serve host/user allowlist."""
import json
from pathlib import Path
from urllib.parse import urlsplit

CONFIG = Path(__file__).resolve().parent.parent / 'results/lab-app/access.json'


def config():
    try:
        value = json.loads(CONFIG.read_text())
        url = urlsplit(value['url'])
        if url.scheme != 'https' or not url.hostname or not url.hostname.endswith('.ts.net') or url.path or url.query or url.fragment or url.username:
            return {}
        if not value.get('users'):
            return {}
        return value
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def allowed(headers, port, mutation=False):
    host = headers.get('Host', '')
    origin = headers.get('Origin')
    local = {f'127.0.0.1:{port}', f'localhost:{port}'}
    if host in local:
        return not mutation or origin in (None, *('http://' + h for h in local))
    cfg = config()
    if not cfg:
        return False
    remote = urlsplit(cfg['url']).netloc
    return (host == remote and headers.get('Tailscale-User-Login') in cfg['users']
            and origin in (None, cfg['url']))
