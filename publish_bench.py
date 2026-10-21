"""Publish a quality bench for sharing: path-free copies plus one JSON the website reads.

    .venv/bin/python publish_bench.py v1
    .venv/bin/python publish_bench.py --manifest     # only refresh titles, groups and order in benches.json

Writes published-results/glm-bench-<name>/ (summary.json, report.md, answers/*.json),
site/data/bench-<name>.json (summary, every answer, and the manual review from
published-results/glm-bench-<name>/review.json) and adds the bench to
site/data/benches.json, the list the bench page reads, and site/data/bench-compare.json
(every published bench in one table: correct answers, waiting time, correct per minute). Raw logs stay local in results/.
"""
import glob, json, os, re, sys
from pathlib import Path

import glm_bench

ROOT = Path(__file__).resolve().parent
HOME = os.path.expanduser('~')
LABELS = {'exact': 'exact', 'native': 'Ollama defaults (thinking on)', 'd030': 'skip 0.3', 'd050': 'skip 0.5', 'd030t12': 'skip 0.3 · 12 threads', 'd040t12': 'skip 0.4 · 12 threads'}


def engine_info(meta):
    if meta.get('backend') == 'openai':
        return dict(engine='MLX server', model=meta['openai_model'])
    if meta.get('backend') == 'ollama':
        return dict(engine='Ollama', model=meta['ollama_model'], ollama_version=meta.get('ollama_version'))
    return dict(engine='Colibri', model=meta.get('model_label', 'GLM-5.3 int4'), colibri_commit=meta.get('colibri_commit'))


GROUPS = {'Colibri': 'GLM-5.3 on Colibri', 'Ollama': 'Ollama, fully in RAM', 'MLX server': 'MLX, fully in RAM'}
TITLES = {  # display names for models the catalog does not name; anything else falls back to its id
    'gemma4:26b': 'Gemma 4 26B', 'gemma4:31b-mlx': 'Gemma 4 31B', 'gemma4:e4b-mlx': 'Gemma 4 E4B',
    'qwen3.8:27b-mlx': 'Qwen3.8-27B', 'gpt-oss:20b': 'gpt-oss 20B', 'olmoe-1b-7b-4bit': 'OLMoE 1B-7B (4-bit)',
}


def with_titles(rows):
    """benches.json rows with a display `title` and `group`, in tab order: GLM on Colibri (v1 first, then catalog
    order), then Ollama and MLX models by title. The website reads both fields; a new bench needs no HTML edit."""
    catalog = [m for m in json.loads((ROOT / 'models' / 'catalog.json').read_text())['models']]
    order = {m['id']: i for i, m in enumerate(catalog)}
    names = {m['id']: re.sub(r'\s*\(.*\)$', '', m['name']).replace(' g64', '') for m in catalog}
    formats = {m['id']: re.sub(r'\s*\(.*\)$', '', m.get('format', '')) for m in catalog}
    out = []
    for r in rows:
        cid = 'glm-5.3-int4' if r['name'] == 'v1' else r.get('model')
        if r.get('engine') == 'Colibri':
            title = names.get(cid, r.get('model'))
        else:
            title = TITLES.get(r.get('model')) or TITLES.get(Path(str(r.get('model'))).name) or r.get('model')
        sub = formats.get(cid) if r.get('engine') == 'Colibri' else f"{r.get('engine')} {Path(str(r.get('model'))).name}"
        out.append(dict(r, title=title, sub=sub or r.get('model'), group=GROUPS.get(r.get('engine'), r.get('engine'))))
    groups = list(GROUPS.values())
    def key(r):
        g = groups.index(r['group']) if r['group'] in groups else len(groups)
        cid = 'glm-5.3-int4' if r['name'] == 'v1' else r.get('model')
        return (g, order.get(cid, len(order)) if r.get('engine') == 'Colibri' else 0, r['title'].lower())
    return sorted(out, key=key)


EXTERNAL = {'GLM-5.3 (Max)': 'GLM-5.3', 'Qwen3.8 27B (Xhigh)': 'Qwen3.8-27B'}   # published scores for models benched here


def write_external(path=None):
    """site/data/external-scores.json: the published intelligence scores of the models benched here, with their source.
    Reported by others; the page labels them so."""
    aa = json.loads((ROOT / 'models' / 'external-benchmarks.json').read_text())['aa_index']
    rows = [dict(model=EXTERNAL[r['model']], listed_as=r['model'], score=r['score']) for r in aa['rows'] if r['model'] in EXTERNAL]
    out = dict(name=aa['name'], version=aa['version'], source=aa['source'],
               fetched=json.loads((ROOT / 'models' / 'external-benchmarks.json').read_text()).get('fetched'), rows=rows)
    Path(path or ROOT / 'site' / 'data' / 'external-scores.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')


def rewrite_manifest(path=None):
    path = Path(path or ROOT / 'site' / 'data' / 'benches.json')
    m = json.loads(path.read_text())
    m['benches'] = with_titles(m['benches'])
    path.write_text(json.dumps(m, ensure_ascii=False, indent=1) + '\n')
    write_external()


def update_manifest(name, info, n_answers):
    path = ROOT / 'site' / 'data' / 'benches.json'
    m = json.loads(path.read_text()) if path.exists() else {'benches': []}
    m['benches'] = [b for b in m['benches'] if b['name'] != name]
    m['benches'].append(dict(name=name, file=f'bench-{name}.json', answers=n_answers, **info))
    m['benches'] = with_titles(m['benches'])   # title, group and tab order (GLM v1 first)
    path.write_text(json.dumps(m, ensure_ascii=False, indent=1) + '\n')
    write_external()
    # one table across every published bench: the trade-off between quality and waiting
    rows = glm_bench.compare(type('A', (), {'names': ','.join(b['name'] for b in m['benches']), 'out': 'published',
                                            'colibri_label': 'GLM-5.3 int4'})())
    models = {b['name']: b['model'] for b in m['benches']}
    for row in rows:
        row['model'] = models[row['bench']]
    (ROOT / 'site' / 'data' / 'bench-compare.json').write_text(json.dumps(dict(labels=LABELS, rows=rows), ensure_ascii=False, indent=1) + '\n')


def main(name):
    src = ROOT / 'results' / f'glm-bench-{name}'
    pub = ROOT / 'published-results' / f'glm-bench-{name}'
    (pub / 'answers').mkdir(parents=True, exist_ok=True)
    glm_bench.report(type('A', (), {'name': name})())
    for f in ('summary.json', 'report.md'):
        (pub / f).write_text((src / f).read_text())
    prompts = {p['id']: p for p in json.loads((ROOT / 'glm-prompts.json').read_text())['prompts']}
    answers = []
    for f in sorted(glob.glob(str(src / '*__*.json'))):
        r = json.loads(Path(f).read_text())
        (pub / 'answers' / Path(f).name).write_text(json.dumps(r, ensure_ascii=False, indent=1))
        answers.append(dict(key=Path(f).stem, id=r['id'], kind=r.get('kind'), style=r['style'], config=r['config'],
                            correct=r.get('correct'), exit=r.get('exit'), answer_s=r.get('answer_s'), prefill_s=r.get('prefill_s'),
                            output_tokens=r.get('output_tokens'), decode_tok_s=r.get('decode_tok_s'),
                            prompt=prompts.get(r['id'], {}).get('prompt'), text=r.get('text')))
    review = json.loads((pub / 'review.json').read_text()) if (pub / 'review.json').exists() else {}
    meta = json.loads((src / 'meta.json').read_text()) if (src / 'meta.json').exists() else {}
    info = engine_info(meta)
    site = dict(name=name, **info, labels=LABELS, summary=json.loads((src / 'summary.json').read_text()), answers=answers,
                review=review.get('answers', {}), review_notes=review.get('notes', []),
                prompt_styles=json.loads((ROOT / 'glm-prompts.json').read_text())['styles'])
    out = ROOT / 'site' / 'data' / f'bench-{name}.json'
    out.write_text(json.dumps(site, ensure_ascii=False))
    for p in [out, ROOT / 'site' / 'data' / 'bench-compare.json'] + list(pub.rglob('*')):
        if p.is_file() and HOME in p.read_text(errors='replace'):
            raise SystemExit(f'home path found in {p}')
    update_manifest(name, info, len(answers))
    print(f'{len(answers)} answers -> {pub.relative_to(ROOT)}, {out.relative_to(ROOT)}')


if __name__ == '__main__':
    if sys.argv[1:] == ['--manifest']:
        rewrite_manifest()
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else 'v1')
