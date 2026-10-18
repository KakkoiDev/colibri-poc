"""Publish a quality bench for sharing: path-free copies plus one JSON the website reads.

    .venv/bin/python publish_bench.py v1

Writes published-results/glm-bench-<name>/ (summary.json, report.md, answers/*.json) and
site/data/bench-<name>.json (summary, every answer, and the manual review from
published-results/glm-bench-<name>/review.json). Raw logs stay local in results/.
"""
import glob, json, os, sys
from pathlib import Path

import glm_bench

ROOT = Path(__file__).resolve().parent
HOME = os.path.expanduser('~')
LABELS = {'exact': 'exact', 'd030': 'skip 0.3', 'd050': 'skip 0.5', 'd030t12': 'skip 0.3 · 12 threads', 'd040t12': 'skip 0.4 · 12 threads'}


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
    site = dict(name=name, labels=LABELS, summary=json.loads((src / 'summary.json').read_text()), answers=answers,
                review=review.get('answers', {}), review_notes=review.get('notes', []),
                prompt_styles=json.loads((ROOT / 'glm-prompts.json').read_text())['styles'])
    out = ROOT / 'site' / 'data' / f'bench-{name}.json'
    out.write_text(json.dumps(site, ensure_ascii=False))
    for p in [out] + list(pub.rglob('*')):
        if p.is_file() and HOME in p.read_text(errors='replace'):
            raise SystemExit(f'home path found in {p}')
    print(f'{len(answers)} answers -> {pub.relative_to(ROOT)}, {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'v1')
