"""Archive a completed local campaign for public review; remove local home paths."""
import argparse
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign',help='Folder name under results/')
    args=parser.parse_args()
    if not re.fullmatch(r'\d{8}T\d{6}\.\d+Z',args.campaign):
        parser.error('Expected a timestamped campaign folder name')
    source=ROOT/'results'/args.campaign
    data=json.loads((source/'campaign.json').read_text())
    if any(r['status']=='running' for r in data['records']):
        parser.error('Campaign is still running')
    target=ROOT/'published-results'/args.campaign
    target.mkdir(parents=True,exist_ok=True)
    for file in source.iterdir():
        if file.suffix in ('.json','.log','.md','.py'):
            text=file.read_text().replace(str(Path.home()),'~')
            (target/file.name).write_text(text)
    rows=[]
    for name in dict.fromkeys(r['variant'] for r in data['records']):
        measured=[x for r in data['records'] if r['variant']==name and r['status']=='ok' for x in r['data']['requests'] if x['phase']=='measured']
        for prompt in dict.fromkeys(x['prompt_id'] for x in measured):
            samples=[x for x in measured if x['prompt_id']==prompt]
            values=[statistics.median(x[k] for x in samples) for k in ('decode_tps','prompt_tps','ttft_s','peak_gpu_gb')]
            rows.append('| '+name+' | '+prompt+' | '+' | '.join(f'{x:.3f}' for x in values)+' |')
    report=['# Per-prompt results','',f"{data['rounds']} rounds; up to {data['tokens']} output tokens. Medians below exclude warmup.",
            'OS file cache uncontrolled. Peak GPU allocation is not whole-system memory.','',
            '| Variant | Prompt | Decode tok/s | Prefill tok/s | First token s | Peak GPU GB |',
            '|---|---|---:|---:|---:|---:|',*rows,'',
            'See summary.json for paired output equality flags and failures. Different token streams require quality evaluation.',
            'Home-directory paths are replaced with ~ in public copies; raw local originals are unchanged.']
    (target/'by-prompt.md').write_text('\n'.join(report)+'\n')
    print(target)

if __name__=='__main__':
    main()
