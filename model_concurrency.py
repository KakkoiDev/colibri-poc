"""Use the existing graded concurrency harness with an installed Ollama model.
One shared serving endpoint, 1/4/10 clients, 3 repeats; no server configuration changes.
"""
import argparse
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

import olmoe_concurrency as harness

ROOT = Path(__file__).resolve().parent


def api(path, body=None):
    req = urllib.request.Request('http://127.0.0.1:11434/api/' + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=600))


def generate(args, prompt, profile):
    body = dict(model=args.model, messages=[dict(role='user', content=prompt)], stream=True,
                keep_alive='5m', options=dict(temperature=0, num_predict=args.ngen, num_ctx=4096))
    if profile == 'direct':
        body['think'] = False
    req = urllib.request.Request(args.url + '/api/chat', data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
    start, first, parts, thinking, final = time.time(), None, [], 0, {}
    with urllib.request.urlopen(req, timeout=args.timeout) as response:
        for line in response:
            ev = json.loads(line)
            if ev.get('error'):
                raise RuntimeError(ev['error'])
            msg = ev.get('message', {})
            text, thought = msg.get('content', ''), msg.get('thinking', '')
            if text or thought:
                first = first or time.time()
            parts.append(text)
            thinking += len(thought)
            if ev.get('done'):
                final = ev
    end = time.time()
    if not final or not isinstance(final.get('eval_count'), int):
        raise RuntimeError('Missing final token telemetry')
    duration = final.get('eval_duration', 0) / 1e9
    return dict(latency_s=end-start, ttft_s=(first or end)-start, tokens=final['eval_count'],
                text=''.join(parts).strip(), finish=final.get('done_reason'), retries=0,
                decode_tok_s=final['eval_count']/duration if duration else None,
                thinking_chars=thinking, request_started=start, first_token_at=first, request_ended=end)


def process_tree(pid):
    out = subprocess.check_output(['ps', '-axo', 'pid=,ppid='], text=True)
    pairs = [tuple(map(int, line.split())) for line in out.splitlines() if len(line.split()) == 2]
    ids = {pid}
    while True:
        more = {p for p, parent in pairs if parent in ids}
        if more <= ids:
            return ids
        ids |= more


def tree_footprint_kb(pid):
    return sum(ORIGINAL_FOOTPRINT(p) for p in process_tree(pid))


ORIGINAL_FOOTPRINT = harness.footprint_kb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--style', choices=['normal', 'terse'], default='terse')
    parser.add_argument('--profile', choices=['direct', 'native'], default='native')
    parser.add_argument('--levels', default='1,4,10')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--only', default='')
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats > 3 or any(x not in {'1','2','4','10'} for x in args.levels.split(',')):
        parser.error('Use 1..3 repeats and levels from 1,2,4,10')
    tags = {m['name']: m for m in api('tags')['models']}
    if args.model not in tags:
        parser.error('Model is not installed; this command never downloads')
    loaded = api('ps')['models']
    if loaded:
        raise SystemExit('A model is already loaded; wait until it is idle/unloaded. Nothing was changed.')
    procs = subprocess.check_output(['ps','-axo','pid=,command='], text=True)
    pid = next(int(line.split()[0]) for line in procs.splitlines() if line.strip().endswith('ollama serve'))
    slug = ''.join(c if c.isalnum() or c in '-_' else '-' for c in args.model)
    name = f"{slug}-{args.profile}-{args.style}-{time.strftime('%Y%m%dT%H%M%S')}"
    out = ROOT / 'results' / ('olmoe-concurrency-' + name)
    out.mkdir(parents=True)
    meta = dict(campaign_pid=os.getpid(), model=tags[args.model], profile=args.profile, style=args.style, levels=args.levels,
                repeats=args.repeats, server_pid=pid, temperature=0, num_ctx=4096,
                num_predict=128 if args.profile == 'direct' else 4096,
                note='Existing Ollama settings; no parallelism reconfiguration. One model at a time. '
                     'Native keeps model default thinking with temperature zero. Footprint sums daemon and descendants; '
                     'shared pages may be counted more than once. Requests in flight are not proof of GPU batching.')
    (out/'meta.json').write_text(json.dumps(meta, indent=1))
    harness.one = lambda a, prompt: generate(a, prompt, args.profile)
    harness.footprint_kb = tree_footprint_kb
    sys.argv = ['olmoe_concurrency.py','--url','http://127.0.0.1:11434','--model',args.model,
                '--server-pid',str(pid),'--levels',args.levels,'--repeats',str(args.repeats),
                '--style',args.style,'--ngen',str(meta['num_predict']),'--name',name]
    if args.only:
        sys.argv += ['--only',args.only]
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        harness.main()
        path = out/'summary.json'
        summary = json.loads(path.read_text())
        records = [json.loads(line) for line in (out/'requests.jsonl').read_text().splitlines()]
        for row in summary['by_level']:
            rs = [x for x in records if x['level']==row['level']]
            row['truncated'] = sum(x.get('finish')=='length' for x in rs)
            row['correct_count'] = sum(x.get('correct') is True for x in rs)
            row['graded_count'] = sum(x.get('correct') is not None for x in rs)
            row['mean_decode_tok_s'] = sum(x.get('decode_tok_s') or 0 for x in rs)/len(rs)
            row['overlapping_generation_observed'] = any(
                a.get('first_token_at') and b.get('first_token_at') and
                max(a['first_token_at'],b['first_token_at']) < min(a['request_ended'],b['request_ended'])
                for i,a in enumerate(rs) for b in rs[i+1:] if a['repeat']==b['repeat'])
        summary['campaign_metadata'] = meta
        path.write_text(json.dumps(summary, indent=1))
        report = (out/'report.md').read_text().replace('# OLMoE concurrency', '# '+args.model+' concurrency')
        (out/'report.md').write_text(report+'\n'+meta['note']+'\n')
    except (Exception, KeyboardInterrupt) as error:
        (out/'failure.json').write_text(json.dumps(dict(error=str(error),type=type(error).__name__)))
        raise
    finally:
        # Only unload the model this campaign loaded; the initial loaded-model list was empty.
        api('generate', dict(model=args.model, keep_alive=0))


if __name__ == '__main__':
    main()
