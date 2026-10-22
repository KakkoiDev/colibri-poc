import json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

import glm_bench
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab_app'))
import actions
import bench_catalog
import server


class RunAgainTests(unittest.TestCase):
    """A finished bench can be measured again from the Run matrix; its old answers are kept, not deleted."""
    def test_rerun_moves_saved_answers_to_attempts(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(glm_bench, 'ROOT', Path(d)):
            out = Path(d) / 'results' / 'glm-bench-x'
            out.mkdir(parents=True)
            for k in ('a__terse__exact', 'b__terse__exact', 'a__normal__exact'):
                (out / f'{k}.json').write_text('{"exit": 0}')
                (out / f'{k}.log').write_text('log')
            self.assertEqual(glm_bench.rerun_archive(out, ['a__terse__exact', 'b__terse__exact']), 2)
            self.assertEqual(sorted(p.name for p in out.glob('*.json')), ['a__normal__exact.json'], 'other styles stay')
            kept = list((out / 'attempts').glob('rerun-*/*.json'))
            self.assertEqual(len(kept), 2)

    def test_a_complete_quality_item_queues_as_run_again(self):
        _, items = bench_catalog.items()
        done = [i for i in items if i['kind'] == 'bench' and i['complete'] and i['available']]
        self.assertTrue(done, 'finished quality benches stay available')
        job = bench_catalog.jobs_for([done[0]['id']])[0]
        self.assertIs(job['args']['rerun'], True)
        argv, title = actions.build_command('bench', job['args'])
        self.assertEqual(argv[-1], '--rerun')
        self.assertIn('run again', title)
        self.assertGreater(server.estimate_item(dict(kind='bench', args=job['args'])), 0, 'a rerun takes the full time')

    def test_presets_only_fill_gaps(self):
        _, items = bench_catalog.items()
        complete = {i['id'] for i in items if i['complete']}
        for p in bench_catalog.presets(items):
            self.assertFalse(complete & set(p['ids']), p['title'])


class MatrixTests(unittest.TestCase):
    def test_every_cell_has_a_state_and_queued_cells_their_place(self):
        d = server.run_matrix()
        self.assertTrue(d['rows'])
        ids = {c['id'] for c in d['columns']}
        some = None
        for r in d['rows']:
            for k, c in r['cells'].items():
                self.assertIn(k.rsplit(':', 1)[0] if k.startswith('q:') else k, ids)   # quality cells are 'q:<setting>:<style>'
                self.assertIn(c['state'], ('done', 'never', 'partial', 'failed', 'queued', 'running', 'blocked'))
                if c['state'] == 'blocked':
                    self.assertTrue(c['why'])
                if c['state'] in ('done', 'never', 'partial', 'failed'):
                    some = some or c
        self.assertTrue(some)
        q = [{'kind': 'suite', 'args': {'bench': 'speed', 'model': 'x'}}]
        cat = bench_catalog.items()[1]
        item = next(i for i in cat if i['id'] == some['id'])
        q.append({'kind': item['kind'], 'args': item['job']['args']})
        with mock.patch.object(actions, 'queue_state', return_value={'paused': False, 'items': q}):
            cells = {c['id']: c for r in server.run_matrix()['rows'] for c in r['cells'].values()}
        self.assertEqual(cells[some['id']]['state'], 'queued')
        self.assertEqual(cells[some['id']]['queue_pos'], 2)

    def test_models_not_installed_are_listed_apart(self):
        d = server.run_matrix()
        shown = {r['id'] for r in d['rows']}
        self.assertFalse(shown & {m['id'] for m in d['not_installed']})


if __name__ == '__main__':
    unittest.main()
