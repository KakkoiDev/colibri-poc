"""Every bench the lab app can start, grouped, with presets; and queueing any selection of them.

Items are atomic and have stable ids, so the page only sends ids: the server rebuilds each
job from this catalog and validates it through actions.build_command, never trusting a
client-supplied command. Quality items for the same results folder and style are merged
into one glm_bench job (it runs configs x styles, so merging only by style avoids extras).
"""
import json, re, sys
from pathlib import Path

import actions

ROOT = actions.ROOT
N_PROMPTS = None


def _prompts():
    global N_PROMPTS
    spec = json.loads((ROOT / 'glm-prompts.json').read_text())
    N_PROMPTS = len(spec['prompts'])
    return spec


def _done(name, style, config):
    folder = ROOT / 'results' / f'glm-bench-{name}'
    return len(list(folder.glob(f'*__{style}__{config}.json'))) if folder.exists() else 0


def ollama_bench_name(model):
    slug = re.sub(r'[^A-Za-z0-9_-]', '-', model.replace('.', ''))
    return re.sub(r'-mlx$', '', slug) + '-ollama'   # qwen3.8:27b-mlx -> qwen38-27b-ollama


def _item(id, group, title, what, job, quiet, available=True, why='', done=None, total=None, lossy=False, setting=None, style=None):
    # a finished quality bench stays available: queueing it again measures it afresh (glm_bench --rerun)
    return dict(id=id, group=group, title=title, what=what, kind=job['kind'], job=job, only_when_quiet=quiet,
                available=available, why_not=why or None, done=done, total=total, complete=bool(total) and done >= total,
                lossy=lossy, setting=setting, style=style)


def items():
    sys.path.insert(0, str(ROOT))
    import glm_bench
    spec = _prompts()
    styles = list(spec['styles'])
    suite = {b['id']: b for b in json.loads((ROOT / 'benches' / 'suite.json').read_text())['benches']}
    labels = {'exact': 'exact', 'd030': 'skip 0.3', 'd050': 'skip 0.5', 'd030t12': 'skip 0.3 · 12 threads',
              'd040t12': 'skip 0.4 · 12 threads', 'native': 'Ollama defaults (thinking on)'}
    out, groups = [], []

    # 1. Colibri models in the catalog: standard benches and the quality bench per setting and style
    for m in actions._catalog().values():
        installed = (Path.home() / m['path']).exists()
        why = '' if installed else 'not installed'
        if installed and not m.get('suite'):
            why = m.get('suite_note', 'the bench tools cannot run this model yet')
        gid = f"model:{m['id']}"
        groups.append(dict(id=gid, title=m['name'], engine='Colibri', note=why or None, kind='model', main=bool(m.get('owner_model')),
                           install=not installed, settings=[[c, labels.get(c, c), c != 'exact'] for c in glm_bench.CONFIGS]))
        for b in ('speed', 'threads', 'ram'):
            out.append(_item(f"suite:{b}:{m['id']}", gid, suite[b]['name'], suite[b]['what'],
                             dict(kind='suite', args=dict(bench=b, model=m['id'])), quiet=b == 'ram', available=not why, why=why))
        name = 'v1' if m.get('owner_model') else m['id']
        for st in styles:
            for c in glm_bench.CONFIGS:
                d = _done(name, st, c) if not why else 0
                args = dict(name=name, configs=[c], styles=[st])
                if not m.get('owner_model'):
                    args['model'] = m['id']
                out.append(_item(f"quality:{m['id']}:{c}:{st}", gid, f"Quality · {labels.get(c, c)} · {st}",
                                 f'{N_PROMPTS} graded prompts, results in glm-bench-{name}', dict(kind='bench', args=args),
                                 quiet=True, available=not why, why=why,
                                 done=d, total=N_PROMPTS, lossy=c != 'exact', setting=c, style=st))

    # 2. Ollama models installed on this Mac: the quality bench, exact and as normally run
    for om in sorted(actions.ollama_models()):
        gid = f'ollama:{om}'
        groups.append(dict(id=gid, title=om, engine='Ollama', note=None, kind='model', main=False, install=False,
                           settings=[[c, labels.get(c, c), False] for c in glm_bench.OLLAMA_CONFIGS]))
        name = ollama_bench_name(om)
        for st in styles:
            for c in glm_bench.OLLAMA_CONFIGS:
                d = _done(name, st, c)
                out.append(_item(f'ollama:{om}:{c}:{st}', gid, f"Quality · {labels.get(c, c)} · {st}",
                                 f'{N_PROMPTS} graded prompts through Ollama, results in glm-bench-{name}',
                                 dict(kind='bench', args=dict(name=name, configs=[c], styles=[st], ollama_model=om)),
                                 quiet=True, done=d, total=N_PROMPTS,
                                 setting=c, style=st))

    # 3. Quiet runs on the main model
    groups.append(dict(id='quiet', title='Quiet runs (main model)', engine='Colibri', note='need ≥ 20 GB free for 2 min', kind='flat'))
    for flags, title, what in [([], 'Full quiet run', 'original engine + key cases + planned experiments'),
                               (['skip-original'], 'Quiet comparison', suite['quiet']['what']),
                               (['ram-sweep', 'skip-original'], 'Quiet comparison + RAM sweep', suite['ram']['what']),
                               (['experiments-only'], 'Planned experiments only', 'every ready planned experiment, quiet')]:
        out.append(_item('quiet:' + ('+'.join(flags) or 'full'), 'quiet', title, what,
                         dict(kind='quiet', args=dict(flags=flags)), quiet=True))

    # 4. Ready planned experiments, one by one
    groups.append(dict(id='planned', title='Planned experiments', engine='Colibri', note=None, kind='flat'))
    for eid, e in actions._planned_ids().items():
        import glm_lab
        why = glm_lab.readiness(e)
        out.append(_item(f'planned:{eid}', 'planned', e['title'], e.get('hypothesis') or e.get('change', ''),
                         dict(kind='planned', args=dict(id=eid)), quiet=False, available=why is None, why=why,
                         lossy=bool(e.get('lossy'))))
    return groups, out


def presets(all_items):
    ok = [i for i in all_items if i['available'] and not i['complete']]   # presets fill gaps; running again is a choice per item
    ids = lambda pred: [i['id'] for i in ok if pred(i)]
    owner = next((m['id'] for m in actions._catalog().values() if m.get('owner_model')), None)
    p = [dict(id='everyday-terse', title='Main model: exact + everyday setting, terse',
              ids=ids(lambda i: i['id'] in (f'quality:{owner}:exact:terse', f'quality:{owner}:d030t12:terse'))),
         dict(id='quiet-set', title='Quiet comparison + RAM sweep', ids=ids(lambda i: i['id'] == 'quiet:ram-sweep+skip-original')),
         dict(id='ready-experiments', title='Every ready planned experiment', ids=ids(lambda i: i['group'] == 'planned')),
         dict(id='small-models', title='Small models vs GLM (docs/13)',
              ids=ids(lambda i: i['id'].startswith('ollama:qwen3.8:27b-mlx:') or i['id'] == f'quality:{owner}:d030t12:terse'))]
    for m in actions._catalog().values():
        p.append(dict(id=f"standard:{m['id']}", title=f"Standard benches for {m['name']}",
                      ids=ids(lambda i, m=m: i['group'] == f"model:{m['id']}" and (i['kind'] == 'suite' or i['id'].endswith(':exact:terse')))))
    return [x for x in p if x['ids']]


def jobs_for(ids):
    """Selected ids -> queue jobs in catalog order, quality items merged per (results folder, style)."""
    _, all_items = items()
    by_id = {i['id']: i for i in all_items}
    unknown = [x for x in ids if x not in by_id]
    blocked = [f"{x}: {by_id[x]['why_not']}" for x in ids if x in by_id and not by_id[x]['available']]
    if unknown or blocked:
        raise actions.ActionError('cannot queue: ' + '; '.join([f'{x}: unknown' for x in unknown] + blocked))
    chosen = [i for i in all_items if i['id'] in set(ids)]
    jobs, merged = [], {}
    for i in chosen:
        j = i['job']
        if j['kind'] == 'bench':
            a = dict(j['args'], rerun=True) if i['complete'] else j['args']
            key = (a['name'], a['styles'][0], a.get('model'), a.get('ollama_model'), i['complete'])
            if key in merged:
                merged[key]['args']['configs'].append(a['configs'][0])
                continue
            j = dict(kind='bench', args=dict(a, configs=list(a['configs'])))
            merged[key] = j
        jobs.append(dict(j, only_when_quiet=i['only_when_quiet']))
    return jobs


def queue_selection(ids, front=False, all_when_quiet=False, schedule="default"):
    if schedule not in ("default", "ready", "quiet"):
        raise actions.ActionError("unknown start condition")
    jobs = jobs_for(ids)
    if schedule != "default":
        jobs = [dict(j, only_when_quiet=schedule == "quiet" or j["kind"] == "quiet") for j in jobs]
    if all_when_quiet:
        jobs = [dict(j, only_when_quiet=True) for j in jobs]
    for j in jobs:                                   # validate every job before queueing any
        actions.build_command(j['kind'], j['args'])
    queued = []
    for j in (reversed(jobs) if front else jobs):    # front keeps the selection's own order
        queued.append(actions.queue_add(j['kind'], j['args'], front=front, only_when_quiet=j['only_when_quiet']))
    return queued[::-1] if front else queued
