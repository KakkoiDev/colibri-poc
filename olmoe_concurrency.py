"""Total throughput of one model copy serving 1, 4 and 10 requests at once (experiment sm-olmoe-concurrent).

    .venv/bin/python -m mlx_lm.server --model models/olmoe-1b-7b-4bit --host 127.0.0.1 --port 8771 &
    .venv/bin/python olmoe_concurrency.py --server-pid <PID> [--levels 1,4,10] [--repeats 3]

N parallel clients each send the 24 graded prompts (glm-prompts.json, one style) in a different,
rotated order. One warm-up request is discarded. Repeats alternate the order of the levels.
Records per request: latency, time to first token, generated tokens; per level: wall time,
total tok/s, p50/p95 latency, peak memory footprint of the server (GPU memory included; sampled by its exact PID), and whether
each answer is identical to the single-request answer. Writes results/olmoe-concurrency-<stamp>/.
Holds .bench.lock for the whole campaign so no other GPU job starts meanwhile.
"""
import argparse, fcntl, json, subprocess, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import glm_bench

ROOT = Path(__file__).resolve().parent


def percentile(values, q):
    """Nearest-rank percentile (q in 0..100) of a non-empty list."""
    v = sorted(values)
    k = max(1, -(-q * len(v) // 100))   # ceil(q/100 * n), at least 1
    return v[int(k) - 1]


def summarize(records, wall_s):
    """Aggregate one level's requests: records are dicts with latency_s, ttft_s, tokens, same_as_single."""
    tokens = sum(r['tokens'] for r in records)
    lat = [r['latency_s'] for r in records]
    single = [r['tokens'] / r['latency_s'] for r in records if r['latency_s'] > 0]
    same = [r['same_as_single'] for r in records if r['same_as_single'] is not None]
    return dict(requests=len(records), tokens=tokens, wall_s=round(wall_s, 3), retries=sum(r.get('retries', 0) for r in records),
                total_tok_s=round(tokens / wall_s, 2) if wall_s > 0 else None,
                per_request_tok_s=round(sum(single) / len(single), 2) if single else None,
                p50_latency_s=round(percentile(lat, 50), 3) if lat else None,
                p95_latency_s=round(percentile(lat, 95), 3) if lat else None,
                p50_ttft_s=round(percentile([r['ttft_s'] for r in records], 50), 3) if records else None,
                same_as_single=f'{sum(same)}/{len(same)}' if same else 'n/a')


def footprint_kb(pid):
    """Physical footprint of one process in KB, including GPU (IOAccelerator) memory that RSS misses
    on Apple silicon; falls back to RSS when `footprint` is unavailable."""
    out = subprocess.run(['footprint', '-p', str(pid)], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'phys_footprint:' in line:
            num, unit = line.split('phys_footprint:')[1].split()[:2]
            return int(float(num) * {'KB': 1, 'MB': 1024, 'GB': 1024 * 1024}.get(unit, 1))
    rss = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
    return int(rss) if rss.isdigit() else 0


class RssSampler(threading.Thread):
    """Peak physical footprint of one process, by its exact PID."""
    def __init__(self, pid, every=0.5):
        super().__init__(daemon=True)
        self.pid, self.every, self.peak_kb, self.stop = pid, every, 0, threading.Event()

    def run(self):
        while not self.stop.is_set():
            self.peak_kb = max(self.peak_kb, footprint_kb(self.pid))
            self.stop.wait(self.every)


def refused(e):
    """True for a connection reset or refused before the request started: mlx_lm.server is a
    ThreadingHTTPServer whose listen backlog is 5, so a burst of 10 connections can overflow it."""
    reason = getattr(e, 'reason', e)
    return isinstance(reason, (ConnectionResetError, ConnectionRefusedError))


def one(args, prompt, tries=8):
    for k in range(tries):
        try:
            r = glm_bench.openai_generate(args.url, args.model, prompt, args.ngen, args.timeout)
            break
        except OSError as e:          # URLError is an OSError
            if not refused(e) or k == tries - 1:
                raise
            time.sleep(0.05 * 2 ** k)
    u = r.get('usage') or {}
    return dict(latency_s=r['total_s'], ttft_s=r['ttft_s'], tokens=u.get('completion_tokens') or r['chunks'], text=r['text'].strip(),
                finish=r['finish_reason'], retries=k)


def run_level(args, items, n, single_text):
    """n clients; client c sends every prompt, starting at a different offset. Returns (records, wall)."""
    k = len(items)
    orders = [[items[(c * max(1, k // n) + j) % k] for j in range(k)] for c in range(n)]
    recs, lock = [], threading.Lock()

    def client(c):
        for item in orders[c]:
            rec = one(args, item['prompt'])
            ref = single_text.get(item['id'])
            rec.update(id=item['id'], client=c, same_as_single=None if ref is None else rec['text'] == ref,
                       correct=glm_bench.grade(item, rec['text']))
            with lock:
                recs.append(rec)
                if getattr(args, 'output', None):
                    progress = dict(done=len(recs), total=n*k, clients=n, repeat=getattr(args, 'repeat', 1))
                    path = Path(args.output) / 'progress.json'
                    tmp = path.with_suffix('.tmp')
                    tmp.write_text(json.dumps(progress))
                    tmp.replace(path)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=n) as pool:
        list(pool.map(client, range(n)))
    return recs, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--url', default='http://127.0.0.1:8771')
    ap.add_argument('--model', default='default_model', help='the name the server answers to; default_model avoids loading a second copy')
    ap.add_argument('--server-pid', type=int, required=True)
    ap.add_argument('--levels', default='1,4,10')
    ap.add_argument('--repeats', type=int, default=3)
    ap.add_argument('--style', default='terse')
    ap.add_argument('--ngen', type=int, default=128)
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--only', default='', help='prompt ids, comma-separated (smoke tests)')
    ap.add_argument('--name', default='')
    a = ap.parse_args()

    lockf = (ROOT / '.bench.lock').open('w')
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another benchmark is running (.bench.lock held)')
    spec = json.loads((ROOT / 'glm-prompts.json').read_text())
    items = [dict(p, prompt=p['prompt'] + spec['styles'][a.style]) for p in spec['prompts'] if not a.only or p['id'] in a.only.split(',')]
    levels = [int(x) for x in a.levels.split(',')]
    out = ROOT / 'results' / f"olmoe-concurrency-{a.name or time.strftime('%Y%m%dT%H%M%S')}"
    out.mkdir(parents=True, exist_ok=True)
    a.output = str(out)

    one(a, items[0]['prompt'])                                   # warm-up, discarded
    single_text = {}
    for item in items:                                           # reference answers from one request at a time
        single_text[item['id']] = one(a, item['prompt'])['text']

    rows, log = [], (out / 'requests.jsonl').open('w')
    for rep in range(a.repeats):
        a.repeat = rep + 1
        for n in (levels if rep % 2 == 0 else levels[::-1]):
            sampler = RssSampler(a.server_pid)
            sampler.start()
            recs, wall = run_level(a, items, n, single_text)
            sampler.stop.set(); sampler.join()
            s = summarize(recs, wall)
            s.update(level=n, repeat=rep + 1, peak_rss_gb=round(sampler.peak_kb / 1024 / 1024, 2),
                     correct=f"{sum(1 for r in recs if r['correct'])}/{len(recs)}")
            rows.append(s)
            for r in recs:
                log.write(json.dumps(dict(r, level=n, repeat=rep + 1), ensure_ascii=False) + '\n')
            log.flush()
            print(f"N={n:>2} repeat {rep + 1}: {s['total_tok_s']} tok/s total, {s['retries']} retries, {s['per_request_tok_s']} per request, "
                  f"p50 {s['p50_latency_s']} s, p95 {s['p95_latency_s']} s, memory {s['peak_rss_gb']} GB, same {s['same_as_single']}", flush=True)
    log.close()

    med = lambda xs: sorted(xs)[len(xs) // 2]
    by_level = {}
    for n in levels:
        rs = [r for r in rows if r['level'] == n]
        by_level[n] = dict(level=n, total_tok_s=med([r['total_tok_s'] for r in rs]), per_request_tok_s=med([r['per_request_tok_s'] for r in rs]),
                           p50_latency_s=med([r['p50_latency_s'] for r in rs]), p95_latency_s=med([r['p95_latency_s'] for r in rs]),
                           peak_rss_gb=max(r['peak_rss_gb'] for r in rs), retries=sum(r['retries'] for r in rs), same_as_single=[r['same_as_single'] for r in rs],
                           correct=[r['correct'] for r in rs])
    summary = dict(started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), url=a.url, model=a.model, style=a.style, ngen=a.ngen,
                   prompts=len(items), repeats=a.repeats, levels=levels, runs=rows, by_level=list(by_level.values()),
                   note='Median over repeats. total_tok_s = generated tokens of all requests / wall time of the level. '
                        'Each client sends every prompt once, in a rotated order; one warm-up request discarded. '
                        'Connections reset before a request started (server backlog of 5) are retried and counted; latency is the successful attempt.')
    (out / 'summary.json').write_text(json.dumps(summary, indent=1))
    lines = ['| Requests at once | Total tok/s | Per request tok/s | p50 latency s | p95 latency s | Peak server memory GB | Same as single | Correct |',
             '|---:|---:|---:|---:|---:|---:|---|---|']
    for b in by_level.values():
        lines.append(f"| {b['level']} | {b['total_tok_s']} | {b['per_request_tok_s']} | {b['p50_latency_s']} | {b['p95_latency_s']} | "
                     f"{b['peak_rss_gb']} | {', '.join(b['same_as_single'])} | {', '.join(b['correct'])} |")
    (out / 'report.md').write_text(f"# OLMoE concurrency ({a.style}, {a.ngen} tokens max)\n\n" + '\n'.join(lines) + '\n\n' + summary['note'] + '\n')
    print('\n'.join(lines))
    print(f'-> {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
