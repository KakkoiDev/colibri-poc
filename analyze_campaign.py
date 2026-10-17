"""Report latency, startup, memory and streaming counters alongside throughput."""
import argparse
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parent

def median(values):
    values=list(values)
    return statistics.median(values) if values else None

def analyze(folder):
    campaign=json.loads((folder/'campaign.json').read_text())
    summaries=json.loads((folder/'summary.json').read_text())
    output=[]
    for summary in summaries:
        runs=[r['data'] for r in campaign['records'] if r['variant']==summary['variant'] and r['status']=='ok']
        rows=[x for r in runs for x in r['requests'] if x['phase']=='measured']
        streaming=[]
        for run in runs:
            measured=[x for x in run['requests'] if x['phase']=='measured']
            warmup=next((x for x in run['requests'] if x['phase']=='warmup'),None)
            if not measured or not warmup:continue
            end=measured[-1].get('plugin_telemetry',{})
            begin=warmup.get('plugin_telemetry',{})
            if 'read_bytes' in end:
                tokens=sum(x['tokens'] for x in measured)
                streaming.append(dict(read_gb=(end['read_bytes']-begin['read_bytes'])/1e9,
                    bytes_per_output_token=(end['read_bytes']-begin['read_bytes'])/tokens,
                    read_calls=end['read_calls']-begin['read_calls'],
                    retained_gb=end['retained_expert_bytes']/1e9))
        output.append(dict(summary,
            median_load_s=median(r['load_s'] for r in runs),
            median_load_peak_gpu_gb=median(r['load_peak_gpu_gb'] for r in runs if 'load_peak_gpu_gb' in r),
            median_loaded_active_gpu_gb=median(r['loaded_active_gpu_gb'] for r in runs if 'loaded_active_gpu_gb' in r),
            median_first_use_ttft_s=median(x['ttft_s'] for r in runs for x in r['requests'] if x['phase']=='warmup'),
            median_load_plus_first_token_s=median(r['load_s']+next(x['ttft_s'] for x in r['requests'] if x['phase']=='warmup') for r in runs),
            worst_request_peak_gpu_gb=max((x['peak_gpu_gb'] for x in rows),default=None),
            median_measured_read_gb=median(s['read_gb'] for s in streaming),
            median_requested_bytes_per_output_token=median(s['bytes_per_output_token'] for s in streaming),
            median_measured_read_calls=median(s['read_calls'] for s in streaming),
            median_retained_expert_gb=median(s['retained_gb'] for s in streaming)))
    (folder/'analysis.json').write_text(json.dumps(output,indent=2)+'\n')
    columns=[('variant','Variant'),('median_decode_tps','Decode tok/s'),('paired_median_speedup','Paired ratio'),
        ('median_ttft_s','TTFT s'),('median_load_s','Load s'),('median_load_plus_first_token_s','Load + first token s'),
        ('median_load_peak_gpu_gb','Startup GPU GB'),('worst_request_peak_gpu_gb','Worst request GPU GB'),
        ('median_requested_bytes_per_output_token','Requested bytes/output token'),('exact_tokens_match','Exact tokens')]
    lines=['# Extended experiment measurements','',
        'OS cache uncontrolled. Startup GPU peak includes loading; first use includes compilation/packing.',
        'Load + first token excludes Python startup/imports. Request GPU peaks exclude earlier startup peaks.',
        'Requested bytes/output token includes measured prompt prefill, excludes warmup; not physical disk traffic.','',
        '| '+' | '.join(label for _,label in columns)+' |','|'+'|'.join('---' for _ in columns)+'|']
    for row in output:
        values=[]
        for key,_ in columns:
            v=row.get(key);values.append(f'{v:.4f}' if isinstance(v,float) else str(v))
        lines.append('| '+' | '.join(values)+' |')
    (folder/'analysis.md').write_text('\n'.join(lines)+'\n')
    print(folder/'analysis.md')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('campaign');args=parser.parse_args()
    if Path(args.campaign).name!=args.campaign:parser.error('Use campaign folder name only')
    analyze(ROOT/'results'/args.campaign)
