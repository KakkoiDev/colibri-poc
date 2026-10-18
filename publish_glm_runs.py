"""Publish GLM run logs as a path-free runs.csv plus each run's generated text.

    .venv/bin/python publish_glm_runs.py [LOG_DIR] [OUT_DIR]

Defaults: results/glm-raw-20261018/logs -> published-results/glm-20261018.
Raw logs stay local (results/ is ignored); the output holds no home paths.
"""
import csv, glob, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE_LINE = re.compile(r'^(\[[A-Z][A-Z0-9_ -]*\]|PROFIL|PROFILE:|ATTENTION:|P0-EXEC:|METAL|PILOT|DEGRADE_ZERO )')
HOME = os.path.expanduser('~')


def parse(text):
    g = lambda pat: re.search(pat, text)
    m = g(r'decode (\d+) tokens in ([\d.]+)s \(([\d.]+) tok/s\)')
    pf = g(r'prefill (\d+) tokens in ([\d.]+)s')
    sh = g(r'time shares: expert-I/O (\d+)% \| expert-matmul (\d+)% \| attention (\d+)% \| lm_head \d+% \| other (\d+)%')
    env, cfg = g(r'env: (.*)'), g(r'\[PROF\] config: (.*)')
    th = g(r'\((\d+) omp threads\)')
    backend = ('vulkan+metal' if '[VK]' in text and '[METAL]' in text else 'vulkan' if '[VK] ready' in text
               else 'metal' if ('backend Metal' in text or '[METAL]' in text) else 'cpu')
    status = 'ok' if m else ('refused (RAM)' if 'refusing to start' in text else 'failed')
    row = dict(backend=backend, omp_threads=th and th[1], prompt_tokens=pf and pf[1], prefill_s=pf and pf[2],
               decode_tokens=m and m[1], decode_s=m and m[2], tok_s=m and m[3],
               hit_pct=(g(r'expert hit rate ([\d.]+)%') or [None, None])[1],
               rss_gb=(g(r'expert hit rate [^\n]*\| RSS ([\d.]+) GB') or [None, None])[1],
               zeroed_slots=(g(r'zeroed (\d+) miss slots') or [None, None])[1],
               io_pct=sh and sh[1], matmul_pct=sh and sh[2], attn_pct=sh and sh[3], other_pct=sh and sh[4],
               config=cfg[1] if cfg else '', env=env[1].replace(HOME, '~') if env else '', status=status)
    out = re.search(r'PROFILO PREFILL \([^)]*\):\n(.*?)\n---\n', text, re.S)
    text_out = None
    if out:
        raw = re.sub(r'\n\[t=[^\]\n]*\]\n', '', out[1])
        text_out = '\n'.join(l for l in raw.splitlines() if not ENGINE_LINE.match(l)).strip() + '\n'
    return row, text_out


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'results/glm-raw-20261018/logs'
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'published-results/glm-20261018'
    dst.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in sorted(glob.glob(str(src / '*.log'))):
        name = Path(f).stem
        row, text = parse(open(f, errors='replace').read())
        rows.append(dict(run=name, **row))
        if text is not None:
            (dst / f'{name}.output.txt').write_text(text)
    with open(dst / 'runs.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    leaks = [p for p in dst.iterdir() if p.is_file() and (HOME in p.read_text(errors='replace') or '/private/tmp' in p.read_text(errors='replace'))]
    if leaks:
        raise SystemExit(f'Local paths found in: {leaks}')
    print(f"{len(rows)} runs, {sum(r['status'] == 'ok' for r in rows)} ok -> {dst}")


if __name__ == '__main__':
    main()
