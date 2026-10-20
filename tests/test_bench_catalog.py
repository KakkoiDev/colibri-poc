import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab_app'))
import actions as a
import bench_catalog as bc


class BenchCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = a.STATE, a.LOGS, a.ollama_models
        a.STATE = Path(self.tmp.name)
        a.LOGS = a.STATE / 'logs'
        a.ollama_models = lambda: {'qwen3.8:27b-mlx'}

    def tearDown(self):
        a.STATE, a.LOGS, a.ollama_models = self.old
        self.tmp.cleanup()

    def test_ollama_names_match_the_queued_bench(self):
        self.assertEqual(bc.ollama_bench_name('qwen3.8:27b-mlx'), 'qwen38-27b-ollama')
        self.assertEqual(bc.ollama_bench_name('gpt-oss:20b'), 'gpt-oss-20b-ollama')

    def test_selection_merges_quality_items_per_style_and_queues_in_order(self):
        ids = ['ollama:qwen3.8:27b-mlx:exact:terse', 'ollama:qwen3.8:27b-mlx:native:terse',
               'ollama:qwen3.8:27b-mlx:native:normal', 'quiet:ram-sweep+skip-original']
        jobs = bc.jobs_for(ids)
        self.assertEqual([(j['kind'], j['args'].get('configs'), j['args'].get('styles')) for j in jobs],
                         [('bench', ['native'], ['normal']), ('bench', ['exact', 'native'], ['terse']), ('quiet', None, None)])
        queued = bc.queue_selection(ids)
        self.assertEqual(len(queued), 3)
        self.assertTrue(all(q['only_when_quiet'] for q in queued))
        self.assertEqual([i['qid'] for i in a.queue_state()['items']], [q['qid'] for q in queued])

    def test_start_condition_is_explicit_and_quiet_runs_stay_quiet(self):
        queued = bc.queue_selection(['ollama:qwen3.8:27b-mlx:exact:terse', 'quiet:skip-original'], schedule='ready')
        self.assertFalse(queued[0]['only_when_quiet'])
        self.assertTrue(queued[1]['only_when_quiet'])
        queued = bc.queue_selection(['ollama:qwen3.8:27b-mlx:native:terse'], schedule='quiet')
        self.assertTrue(queued[0]['only_when_quiet'])

    def test_invalid_start_condition_queues_nothing(self):
        with self.assertRaises(a.ActionError):
            bc.queue_selection(['quiet:skip-original'], schedule='surprise')
        self.assertEqual(a.queue_state()['items'], [])

    def test_unknown_or_blocked_ids_queue_nothing(self):
        for ids in (['nope'], ['ollama:qwen3.8:27b-mlx:exact:terse', 'suite:speed:glm-5.3-flash-iq3xxs']):
            with self.assertRaises(a.ActionError):
                bc.queue_selection(ids)
        self.assertEqual(a.queue_state()['items'], [])

    def test_front_puts_the_selection_first_in_catalog_order(self):
        x = a.queue_add('quiet', {'flags': []}, only_when_quiet=True)
        q = bc.queue_selection(['quiet:experiments-only', 'quiet:skip-original'], front=True)
        self.assertEqual([i['qid'] for i in a.queue_state()['items']], [q[0]['qid'], q[1]['qid'], x['qid']])
        self.assertEqual([i['args']['flags'] for i in q], [['skip-original'], ['experiments-only']])


if __name__ == '__main__':
    unittest.main()
