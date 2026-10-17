"""Generate an equal-budget unequal-layer cache variant from a completed pilot worker."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def allocation(misses,total=512):
    capacities=[8]*len(misses)
    if not len(misses)*8<=total<=len(misses)*64:raise ValueError('Invalid total slot budget')
    while sum(capacities)<total:
        eligible=[i for i,c in enumerate(capacities) if c<64]
        i=max(eligible,key=lambda i:misses[i]/(capacities[i]*(capacities[i]+1)))
        capacities[i]+=1
    return capacities

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('worker_json');args=parser.parse_args()
    source=Path(args.worker_json).resolve();data=json.loads(source.read_text())
    telemetry=data['requests'][-1]['plugin_telemetry']
    layers=sorted(telemetry['layers'],key=lambda x:x['layer'])
    if len(layers)!=16 or [x['layer'] for x in layers]!=list(range(16)):raise ValueError('Expected 16 OLMoE layers')
    capacities=allocation([x['misses'] for x in layers])
    for compact in (False,True):
        base=ROOT/'variants/streaming'/('compact-deferred-packed.json' if compact else 'slots-packed-grouped.json')
        variant=json.loads(base.read_text())
        variant['name']=('compact-deferred' if compact else 'slots')+'-unequal-packed'
        variant['env']['SLOTS_CAPACITIES']=json.dumps(capacities)
        variant['description']=f'Miss-pressure allocation from {source.parent.name}/{source.name}, sha256 {hashlib.sha256(source.read_bytes()).hexdigest()}; exactly 512 slots; capacities {capacities}; heuristic, not optimal'
        (ROOT/'variants/streaming'/f'{variant["name"]}.json').write_text(json.dumps(variant,indent=2)+'\n')
    print(capacities,sum(capacities))

if __name__=='__main__':main()
