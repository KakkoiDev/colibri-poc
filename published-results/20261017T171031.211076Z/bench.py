"""Serial, isolated MLX experiment campaigns. No third-party imports in coordinator."""
import argparse
import datetime
import hashlib
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(os.environ.get('COLIBRI_POC_ROOT', Path(__file__).resolve().parent)).resolve()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def save(path, data):
    temporary = Path(str(path) + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)

def validate(v):
    allowed = {'name', 'backend', 'description', 'prefill_step_size', 'kv_bits', 'kv_group_size', 'quantized_kv_start', 'plugin', 'env'}
    unknown = set(v) - allowed
    if unknown:
        raise ValueError(f'Unknown variant fields: {sorted(unknown)}')
    if v.get('backend') != 'mlx':
        raise ValueError('Only mlx backend implemented; other engines require an adapter')
    if v.get('prefill_step_size', 512) < 1:
        raise ValueError('prefill_step_size must be positive')
    if not v.get('name') or not all(c.isalnum() or c in '-_' for c in v['name']):
        raise ValueError('Use letters, numbers, hyphens or underscores for variant name')
    return v

def measure_worker(args):
    import mlx.core as mx
    from mlx_lm import load, stream_generate
    from mlx_lm.sample_utils import make_sampler
    v = validate(read(args.variant))
    if not mx.metal.is_available():
        raise RuntimeError('Metal is unavailable; refusing CPU fallback')
    mx.set_default_device(mx.gpu)
    mx.random.seed(0)
    mod = None
    plugin_hash = None
    if v.get('plugin'):
        plugin = (ROOT / v['plugin']).resolve()
        spec = importlib.util.spec_from_file_location('poc_plugin', plugin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.install(v)  # Runs before load: patch kernels/modules here.
        plugin_hash = digest(plugin.read_bytes())
    load_start = time.perf_counter()
    mx.reset_peak_memory()
    model, tokenizer = load(str(ROOT / 'models/olmoe-1b-7b-4bit'), **getattr(mod, 'load_options', {}))
    if mod is not None and hasattr(mod, 'after_load'):
        mod.after_load(model, tokenizer, ROOT)
    mx.synchronize()
    load_s = time.perf_counter() - load_start
    prompts = read(args.workload)
    rows = []
    out = {'variant': v, 'plugin_sha256': plugin_hash, 'load_s': load_s, 'load_peak_gpu_gb': mx.get_peak_memory()/1e9,
           'loaded_active_gpu_gb': mx.get_active_memory()/1e9,
           'metal_available': True, 'cache_state': 'OS page cache uncontrolled; fresh KV per request; weights resident',
           'metal_device': mx.device_info(), 'requests': rows}
    if mod is not None and hasattr(mod, 'cache_description'):
        out['cache_state'] = mod.cache_description
    save(args.output, out)
    for phase, prompt in [('warmup', prompts[0])] + [('measured', p) for p in prompts]:
        text = tokenizer.apply_chat_template([{'role':'user','content':prompt['text']}],
                                             tokenize=False, add_generation_prompt=True)
        mx.synchronize()
        mx.reset_peak_memory()
        start = time.perf_counter()
        first_token = first_text = None
        chunks, ids = [], []
        last = None
        opts = {k:v[k] for k in ('prefill_step_size','kv_bits','kv_group_size','quantized_kv_start') if k in v}
        for response in stream_generate(model, tokenizer, text, max_tokens=args.tokens,
                                        sampler=make_sampler(temp=0), **opts):
            now = time.perf_counter()
            if first_token is None:
                first_token = now - start
            if response.text and first_text is None:
                first_text = now - start
            chunks.append(response.text)
            ids.append(response.token)
            last = response
        mx.synchronize()
        elapsed = time.perf_counter() - start
        if last is None or last.generation_tokens < 1:
            raise RuntimeError('Empty generation')
        row = {'phase':phase, 'prompt_id':prompt['id'], 'prompt_tokens':last.prompt_tokens,
               'tokens':last.generation_tokens, 'prompt_tps':last.prompt_tps,
               'decode_tps':last.generation_tps, 'request_s':elapsed,
               'ttft_s':first_token, 'first_text_s':first_text, 'peak_gpu_gb':last.peak_memory,
               'finish_reason':last.finish_reason, 'token_ids':ids, 'text':''.join(chunks)}
        if mod is not None and hasattr(mod, 'telemetry'):
            row['plugin_telemetry'] = mod.telemetry()
        import resource
        row['process_peak_rss_gb'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9
        rows.append(row)
        save(args.output, out)
        print(f"{v['name']} {phase} {prompt['id']}: {last.generation_tps:.2f} tok/s", flush=True)

def summarize(records, baseline):
    successful = [r for r in records if r['status'] == 'ok']
    by_round = {(r['round'], r['variant']):r for r in successful}
    result = []
    for name in dict.fromkeys(r['variant'] for r in records):
        attempts = [r for r in records if r['variant'] == name]
        runs = [r for r in successful if r['variant'] == name]
        rows = [x for r in runs for x in r['data']['requests'] if x['phase']=='measured']
        ratios, matches, lengths = [], [], []
        for run in runs:
            base = by_round.get((run['round'], baseline))
            if base is None:
                continue
            br = {x['prompt_id']:x for x in base['data']['requests'] if x['phase']=='measured'}
            for row in run['data']['requests']:
                if row['phase']!='measured' or row['prompt_id'] not in br:
                    continue
                b = br[row['prompt_id']]
                ratios.append(row['decode_tps']/b['decode_tps'])
                matches.append(row['token_ids']==b['token_ids'])
                lengths.append(row['tokens']==b['tokens'])
        speeds = [x['decode_tps'] for x in rows]
        result.append({'variant':name, 'successful_rounds':len(runs), 'failed_rounds':len(attempts)-len(runs),
                       'median_decode_tps':statistics.median(speeds) if speeds else None,
                       'min_decode_tps':min(speeds) if speeds else None, 'max_decode_tps':max(speeds) if speeds else None,
                       'paired_median_speedup':statistics.median(ratios) if ratios else None,
                       'exact_tokens_match':all(matches) if matches else None,
                       'equal_output_lengths':all(lengths) if lengths else None,
                       'median_ttft_s':statistics.median(x['ttft_s'] for x in rows) if rows else None})
    return result

def campaign(args):
    lock = (ROOT / '.bench.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError('Another benchmark campaign is already running')
    variants = [validate(read(p)) for p in args.variants]
    plugin_sources = {v['plugin']:(ROOT/v['plugin']).resolve().read_bytes()
                      for v in variants if v.get('plugin')}
    names = [v['name'] for v in variants]
    if len(names)!=len(set(names)) or args.baseline not in names:
        raise ValueError('Variant names must be unique and include baseline')
    if not (ROOT/'model.lock.json').exists():
        raise ValueError('Run prepare_model.py first')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    folder = ROOT/'results'/stamp
    folder.mkdir(parents=True)
    manifest = {'schema':1, 'tokens':args.tokens, 'rounds':args.rounds, 'baseline':args.baseline,
                'model':read(ROOT/'model.lock.json'), 'prompts_sha256':digest((ROOT/'prompts.json').read_bytes()),
                'runner_sha256':digest(Path(__file__).read_bytes()), 'python':sys.version,
                'platform':platform.platform(), 'host':platform.machine(),
                'packages':subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True) if importlib.util.find_spec('pip') else subprocess.check_output(['uv','pip','freeze','--python',sys.executable],text=True),
                'records':[]}
    (folder/'prompts.json').write_bytes((ROOT/'prompts.json').read_bytes())
    (folder/'bench.py').write_bytes(Path(__file__).read_bytes())
    if (ROOT/'model.files.json').exists():
        manifest['model_files'] = read(ROOT/'model.files.json')
    for round_id in range(args.rounds):
        # Alternate direction, avoiding one fixed thermal/order advantage.
        order = list(range(len(variants)))
        if round_id%2:
            order.reverse()
        for i in order:
            v = variants[i]
            tag = f"r{round_id+1}-{v['name']}"
            if v.get('plugin'):
                plugin = (ROOT/v['plugin']).resolve()
                plugin_snapshot = folder/f'{tag}.plugin.py'
                plugin_snapshot.write_bytes(plugin_sources[v['plugin']])
                v = dict(v, plugin=str(plugin_snapshot))
            config = folder/f'{tag}.variant.json'
            save(config, v)
            output = folder/f'{tag}.json'
            record = {'round':round_id+1,'variant':v['name'],'status':'running','output':output.name}
            manifest['records'].append(record)
            save(folder/'campaign.json', manifest)
            command = [sys.executable, str(folder/'bench.py'), '_worker', '--variant',str(config), '--output',str(output),'--tokens',str(args.tokens), '--workload',str(folder/'prompts.json')]
            print(f"Running {tag}", flush=True)
            try:
                env = dict(os.environ, **v.get('env', {}))
                env['COLIBRI_POC_ROOT'] = str(ROOT)
                with (folder/f'{tag}.log').open('w') as log:
                    proc = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
                if proc.returncode:
                    raise RuntimeError(f'worker exit {proc.returncode}; see {tag}.log')
                data = read(output)
                expected = {p['id'] for p in read(folder/'prompts.json')}
                actual = {r['prompt_id'] for r in data['requests'] if r['phase']=='measured'}
                if actual != expected:
                    raise RuntimeError('Incomplete workload')
                record.update(status='ok', data=data)
            except (OSError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
                record.update(status='failed', error=str(exc))
                print(f'{tag}: {exc}', flush=True)
            save(folder/'campaign.json', manifest)
    summary = summarize(manifest['records'], args.baseline)
    save(folder/'summary.json', summary)
    lines = ['# Benchmark results', '', 'OS file cache uncontrolled; no cold-storage claim. Fresh KV per request.','',
             '| Variant | Median tok/s | Paired speedup | Exact tokens | Failed rounds |', '|---|---:|---:|---|---:|']
    for r in summary:
        lines.append(f"| {r['variant']} | {r['median_decode_tps']} | {r['paired_median_speedup']} | {r['exact_tokens_match']} | {r['failed_rounds']} |")
    lines += ['', 'Output mismatches need quality investigation; they are not automatically a quality regression.',
              'Unequal output lengths can confound throughput. Inspect raw rows and finish reasons.']
    (folder/'summary.md').write_text('\n'.join(lines)+'\n')
    print(folder/'summary.md')
    return int(any(r['status']!='ok' for r in manifest['records']))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action',required=True)
    run = sub.add_parser('run')
    run.add_argument('--variants',nargs='+',default=[str(p) for p in sorted((ROOT/'variants').glob('*.json'))])
    run.add_argument('--baseline',default='baseline')
    run.add_argument('--rounds',type=int,default=3)
    run.add_argument('--tokens',type=int,default=128)
    run.add_argument('--timeout',type=int,default=900)
    worker = sub.add_parser('_worker')
    worker.add_argument('--variant',required=True)
    worker.add_argument('--output',required=True)
    worker.add_argument('--workload',required=True)
    worker.add_argument('--tokens',type=int,required=True)
    args = p.parse_args()
    if args.tokens<1 or (args.action=='run' and (args.rounds<1 or args.timeout<1)):
        p.error('tokens, rounds and timeout must be positive')
    if args.action=='_worker':
        measure_worker(args)
        return 0
    return campaign(args)

if __name__=='__main__':
    sys.exit(main())
