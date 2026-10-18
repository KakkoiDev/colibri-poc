"""GLM quality and speed bench on the user's Colibri install.

Runs graded prompts (glm-prompts.json) under several engine configurations and
prompt styles, one engine process at a time, and records total time, prompt
processing, generation, output text and a pass/fail grade.

    .venv/bin/python glm_bench.py run --name NAME [--configs exact,d030,d050] [--styles normal,terse]
    .venv/bin/python glm_bench.py run --name NAME --backend ollama --ollama-model qwen3.8:27b-mlx --configs exact
    .venv/bin/python glm_bench.py report --name NAME

Runs are resumable: a finished (prompt, style, config) is skipped. Every run uses
USAGE_SAVE=0, KVSAVE=0 and --no-tune-profile so the user's Colibri state is not
changed. The Ollama backend sends the same prompts to a local Ollama server (thinking
off, temperature 0, same token limit) and reads its timings; only 'exact' applies. Code answers are executed locally in a temporary directory with a
timeout to grade them.
"""
import argparse, fcntl, json, os, re, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOME = Path.home()

BASE_ENV = {'COLI_METAL': '1', 'PIPE': '1', 'DIRECT': '1', 'COLI_METAL_RESSET': '1',
            'COLI_METAL_SPIN': '1', 'USAGE_SAVE': '0', 'KVSAVE': '0', 'COLI_TEMP': '0', 'PROF': '1'}
CONFIGS = {
    'exact': {},
    'd030': {'DEGRADE_ZERO': '1', 'DEGRADE_TAU': '0.30'},
    'd050': {'DEGRADE_ZERO': '1', 'DEGRADE_TAU': '0.50'},
    # 12 threads (OMP_NUM_THREADS) work around colibri#2194; output is identical to 2 threads
    'd030t12': {'DEGRADE_ZERO': '1', 'DEGRADE_TAU': '0.30', 'OMP_NUM_THREADS': '12'},
    'd040t12': {'DEGRADE_ZERO': '1', 'DEGRADE_TAU': '0.40', 'OMP_NUM_THREADS': '12'},
}
ENGINE_LINE = re.compile(r'^(\[[A-Z][A-Z0-9_ -]*\]|PROFIL|PROFILE:|ATTENTION:|P0-EXEC:|METAL|PILOT|DEGRADE_ZERO )')


def parse_log(text):
    out = {}
    m = re.search(r'prefill (\d+) tokens in ([\d.]+)s \| decode (\d+) tokens in ([\d.]+)s \(([\d.]+) tok/s\)', text)
    if m:
        out.update(prompt_tokens=int(m[1]), prefill_s=float(m[2]), output_tokens=int(m[3]),
                   decode_s=float(m[4]), decode_tok_s=float(m[5]))
    z = re.search(r'zeroed (\d+) miss slots', text)
    out['zeroed_slots'] = int(z[1]) if z else 0
    h = re.search(r'expert hit rate ([\d.]+)%', text)
    out['hit_pct'] = float(h[1]) if h else None
    body = re.search(r'PROFILO PREFILL \([^)]*\):\n(.*?)\n---\n', text, re.S)
    if body:
        raw = re.sub(r'\n\[t=[^\]\n]*\]\n', '', body[1])  # progress lines interrupt the stream mid-line
        lines = [l for l in raw.splitlines() if not ENGINE_LINE.match(l)]
        out['text'] = '\n'.join(lines).strip()
    return out


def ollama_record(resp):
    """Map an Ollama /api/generate reply (durations in ns) to the bench's fields."""
    ns = 1e9
    rec = dict(prompt_tokens=resp.get('prompt_eval_count'), prefill_s=round(resp.get('prompt_eval_duration', 0) / ns, 3),
               output_tokens=resp.get('eval_count'), decode_s=round(resp.get('eval_duration', 0) / ns, 3),
               load_s=round(resp.get('load_duration', 0) / ns, 3), text=(resp.get('response') or '').strip())
    rec['decode_tok_s'] = round(rec['output_tokens'] / rec['decode_s'], 2) if rec['output_tokens'] and rec['decode_s'] else None
    return rec


def ollama_generate(url, model, prompt, ngen, timeout):
    body = json.dumps({'model': model, 'prompt': prompt, 'stream': False, 'think': False,
                       'options': {'temperature': 0, 'num_predict': ngen}}).encode()
    req = urllib.request.Request(url.rstrip('/') + '/api/generate', data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def first_code_block(text):
    m = re.search(r'```(?:python|py)?\s*\n(.*?)(?:```|$)', text, re.S)  # unclosed when cut by --ngen
    if m:
        return m[1]
    return text  # terse answers may be bare code


def grade(item, text):
    if text is None:
        return False
    low = text.lower()
    if 'tests' in item:
        with tempfile.TemporaryDirectory() as d:
            src = Path(d, 'answer.py')
            src.write_text(first_code_block(text) + '\n\n' + item['tests'] + '\n')
            try:
                r = subprocess.run([sys.executable, '-I', str(src)], cwd=d, capture_output=True, timeout=10)
            except subprocess.TimeoutExpired:
                return False
            return r.returncode == 0
    if 'number' in item:
        nums = re.findall(r'-?\d[\d,]*(?:\.\d+)?', text)
        vals = []
        for n in nums:
            try:
                vals.append(float(n.replace(',', '')))
            except ValueError:
                pass
        # the final number is the answer; restated question numbers come earlier
        return bool(vals) and vals[-1] == float(item['number'])
    if 'accept' in item:
        if item.get('word'):
            return any(re.search(r'\b' + re.escape(a) + r'\b', low) for a in item['accept'])
        return any(a in low for a in item['accept'])
    return None


def run(args):
    spec = json.loads((ROOT / 'glm-prompts.json').read_text())
    out_dir = ROOT / 'results' / f'glm-bench-{args.name}'
    out_dir.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / '.bench.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another benchmark is running (.bench.lock held)')
    coli = Path(args.coli_dir).expanduser() / 'c' / 'coli'
    configs = args.configs.split(',')
    ollama = args.backend == 'ollama'
    if ollama and (configs != ['exact'] or not args.ollama_model):
        raise SystemExit('the ollama backend needs --ollama-model and --configs exact (skip settings are Colibri-only)')
    styles = args.styles.split(',')
    items = [p for p in spec['prompts'] if not args.only or p['id'] in args.only.split(',')]
    meta = out_dir / 'meta.json'
    if not meta.exists():
        engine = ({'backend': 'ollama', 'ollama_model': args.ollama_model, 'ollama_url': args.ollama_url,
                   'ollama_version': subprocess.run(['ollama', '--version'], capture_output=True, text=True).stdout.strip(),
                   'options': {'temperature': 0, 'think': False}} if ollama else
                  {'backend': 'colibri', 'colibri_commit': subprocess.run(['git', '-C', str(coli.parent.parent), 'rev-parse', 'HEAD'],
                                                                          capture_output=True, text=True).stdout.strip()})
        meta.write_text(json.dumps({'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                    **engine, 'base_env': {} if ollama else BASE_ENV, 'configs': {c: CONFIGS[c] for c in configs},
                                    'styles': {s: spec['styles'][s] for s in styles},
                                    'ram': args.ram, 'ctx': args.ctx, 'ngen': args.ngen}, indent=1))
    total = len(items) * len(styles) * len(configs)
    done = 0
    for style in styles:          # finish one style across all prompts before the next
        for item in items:
            for cfg in configs:
                done += 1
                key = f"{item['id']}__{style}__{cfg}"
                res_path = out_dir / f'{key}.json'
                if res_path.exists():
                    continue
                prompt = item['prompt'] + spec['styles'][style]
                if ollama:
                    t0 = time.time()
                    try:
                        resp, code = ollama_generate(args.ollama_url, args.ollama_model, prompt, args.ngen, args.timeout), 0
                    except Exception as e:  # server down, timeout: recorded as a failed run, like a crashed engine
                        resp, code = {'error': str(e)}, 1
                    wall = time.time() - t0
                    (out_dir / f'{key}.log').write_text(json.dumps(resp, ensure_ascii=False, indent=1))
                    rec = dict(id=item['id'], kind=item['kind'], style=style, config=cfg, exit=code,
                               wall_s=round(wall, 2), **(ollama_record(resp) if code == 0 else {}))
                    rec['answer_s'] = round(rec['prefill_s'] + rec['decode_s'], 2) if code == 0 else None
                    rec['correct'] = grade(item, rec.get('text'))
                    res_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
                    print(f"[{done}/{total}] {key}: exit={code} answer={rec.get('answer_s')}s "
                          f"tokens={rec.get('output_tokens')} correct={rec['correct']}", flush=True)
                    continue
                env = dict(os.environ, **BASE_ENV, **CONFIGS[cfg], RAM_GB=str(args.ram))
                cmd = [str(coli), 'run', '--model', str(Path(args.model).expanduser()), '--no-tune-profile', '--no-think',
                       '--ngen', str(args.ngen), '--ram', str(args.ram), '--ctx', str(args.ctx), prompt]
                t0 = time.time()
                p = subprocess.run(cmd, env=env, capture_output=True, text=True, errors='replace', timeout=args.timeout)
                wall = time.time() - t0
                log = p.stdout + '\n' + p.stderr
                (out_dir / f'{key}.log').write_text(log)
                rec = dict(id=item['id'], kind=item['kind'], style=style, config=cfg, exit=p.returncode,
                           wall_s=round(wall, 2), **parse_log(log))
                rec['answer_s'] = round(rec.get('prefill_s', 0) + rec.get('decode_s', 0), 2) if 'decode_s' in rec else None
                rec['correct'] = grade(item, rec.get('text'))
                res_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
                print(f"[{done}/{total}] {key}: exit={p.returncode} answer={rec.get('answer_s')}s "
                      f"tokens={rec.get('output_tokens')} correct={rec['correct']}", flush=True)


def report(args):
    out_dir = ROOT / 'results' / f'glm-bench-{args.name}'
    recs = [json.loads(p.read_text()) for p in sorted(out_dir.glob('*__*.json'))]
    exact_text = {(r['id'], r['style']): r.get('text') for r in recs if r['config'] == 'exact'}
    groups = {}
    for r in recs:
        groups.setdefault((r['style'], r['config']), []).append(r)
    lines = ['| Style | Config | Runs | Correct (graded) | Same text as exact | Mean answer time s | Mean prefill s | Mean output tokens | Mean decode tok/s |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    summary = []
    for (style, cfg), rs in sorted(groups.items()):
        ok = [r for r in rs if 'decode_s' in r]
        graded = [r for r in ok if r['correct'] is not None]
        corr = sum(1 for r in graded if r['correct'])
        same = sum(1 for r in ok if exact_text.get((r['id'], style)) == r.get('text'))
        mean = lambda k: sum(r[k] for r in ok) / len(ok) if ok else float('nan')
        row = dict(style=style, config=cfg, runs=len(rs), ok=len(ok), correct=corr, graded=len(graded), same_as_exact=same,
                   answer_s=mean('answer_s'), prefill_s=mean('prefill_s'), output_tokens=mean('output_tokens'),
                   decode_tok_s=mean('decode_tok_s'))
        summary.append(row)
        lines.append(f"| {style} | {cfg} | {len(rs)} | {corr}/{len(graded)} | {same}/{len(ok)} | {row['answer_s']:.1f} | "
                     f"{row['prefill_s']:.1f} | {row['output_tokens']:.1f} | {row['decode_tok_s']:.2f} |")
    # per-prompt failures, for review
    fails = [f"- {r['id']} / {r['style']} / {r['config']}" for r in recs if r.get('correct') is False]
    text = '\n'.join(lines) + '\n\nIncorrect answers:\n' + ('\n'.join(fails) if fails else '- none') + '\n'
    (out_dir / 'report.md').write_text(text)
    (out_dir / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(text)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--name', required=True)
    r.add_argument('--configs', default='exact,d030,d050')
    r.add_argument('--styles', default='normal,terse')
    r.add_argument('--only', default='')
    r.add_argument('--ngen', type=int, default=128)
    r.add_argument('--ram', default='18')
    r.add_argument('--ctx', default='1024')
    r.add_argument('--timeout', type=int, default=1200)
    r.add_argument('--model', default='~/colibri-models/glm-5.3')
    r.add_argument('--coli-dir', default='~/Code/colibri')
    r.add_argument('--backend', choices=['colibri', 'ollama'], default='colibri')
    r.add_argument('--ollama-model', default='')
    r.add_argument('--ollama-url', default='http://127.0.0.1:11434')
    p = sub.add_parser('report')
    p.add_argument('--name', required=True)
    a = ap.parse_args()
    run(a) if a.cmd == 'run' else report(a)


if __name__ == '__main__':
    main()
