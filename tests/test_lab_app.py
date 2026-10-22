import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab_app'))
import server as s


class LabAppTests(unittest.TestCase):
    def test_etime(self):
        self.assertEqual(s.etime_seconds('05:09'), 309)
        self.assertEqual(s.etime_seconds('01:02:03'), 3723)
        self.assertEqual(s.etime_seconds('2-00:00:01'), 172801)

    def test_process_kinds(self):
        self.assertTrue(s.is_engine('/Users/x/Code/colibri/c/colibri 0'))
        self.assertFalse(s.is_engine('/bin/zsh -c cd /Users/x/Code/colibri/c/colibri && make'))
        self.assertTrue(s.is_python('.venv/bin/python glm_bench.py run --name v1'))
        self.assertFalse(s.is_python('/bin/zsh -c .venv/bin/python glm_bench.py run'))

    def test_bench_progress_counts_saved_answers(self):
        p = s.bench_job_progress('.venv/bin/python glm_bench.py run --name v1 --configs exact --styles terse --only fact-capital,fact-gold')
        self.assertEqual(p['total'], 2)
        self.assertLessEqual(p['done'], 2)

    def test_one_action_queues_with_explicit_schedule_and_resumes(self):
        from unittest.mock import patch
        with patch.object(s.bench_catalog, 'queue_selection', return_value=[{'qid':'test'}]) as enqueue, \
             patch.object(s.actions, 'queue_pause') as pause, \
             patch.object(s.actions, 'queue_state', return_value={'paused':False}):
            result=s.act('/api/queue/add-selection', {'ids':['test'], 'schedule':'ready', 'resume':True})
            self.assertEqual(result['queued'],[{'qid':'test'}])
            self.assertEqual(enqueue.call_args.kwargs['schedule'],'ready')
            pause.assert_called_once_with(False)

    def test_existing_queue_action_does_not_resume_without_request(self):
        from unittest.mock import patch
        with patch.object(s.bench_catalog, 'queue_selection', return_value=[]), \
             patch.object(s.actions, 'queue_pause') as pause, \
             patch.object(s.actions, 'queue_state', return_value={'paused':True}):
            result=s.act('/api/queue/add-selection', {'ids':['test']})
            self.assertTrue(result['paused'])
            pause.assert_not_called()

    def test_safe_ids(self):
        self.assertIsNone(s.bench_detail('../etc'))
        self.assertIsNone(s.run_output('../../secret'))

    def test_research_and_external_parse(self):
        r = s.research()
        self.assertTrue(r['items'])
        self.assertIn('decision', r['items'][0])
        e = s.external()
        self.assertTrue(any(x.get('lab') for x in e['aa_index']['rows']))

    def test_bench_settings_fill_known_configs(self):
        st = s.bench_settings({'configs': {'exact': {}}, 'base_env': "{'PIPE': '1'}", 'ram': '18', 'ngen': 128})
        self.assertEqual(st['backend'], 'colibri')
        self.assertIn('d030t12', st['configs'])          # known configs fill an older meta file
        self.assertIsInstance(st['base_env'], dict)
        o = s.bench_settings({'backend': 'ollama', 'ollama_model': 'm', 'ollama_configs': {'exact': {'think': False}}})
        self.assertEqual(o['backend'], 'ollama')
        self.assertEqual(o['configs']['exact'], {'think': False})
        self.assertIn('native', o['configs'])

    def test_demo_server_never_touches_the_mac(self):
        import demo_server, inspect
        src = inspect.getsource(demo_server.main)
        for name in ('a.launch', 'a.stop', 'a.remove_model', 'a.refresh_jobs'):
            self.assertIn(name, src)           # each one is replaced by a fake
        self.assertNotIn('start_runner', src)  # the queue never runs in the demo




class NotRunTests(unittest.TestCase):
    """The dashboard's "Not run yet" card: every never-run experiment and missing bench, with a state and a way to queue."""
    def test_every_item_has_a_state_and_ready_ones_can_be_queued(self):
        d = s.not_run()
        self.assertEqual(set(d), {'experiments', 'benches', 'counts', 'new', 'new_days'})
        items = d['experiments'] + d['benches']
        self.assertTrue(items)
        for x in items:
            self.assertIn(x['status'], ('ready', 'queued', 'needs', 'idea'), x['title'])
            if x['status'] == 'ready':
                self.assertTrue(x['queue'], x['title'])
            if x['status'] in ('needs', 'idea'):
                self.assertTrue(x.get('needs'), x['title'] + ' says what it is waiting for')
        self.assertEqual(sum(d['counts'].values()), len(items))
        states = [x['status'] for x in d['experiments']]
        self.assertEqual(states, sorted(states, key=['ready', 'queued', 'needs', 'idea'].index), 'ready first, ideas last')

    def test_the_log_is_regenerated_when_the_registry_is_newer(self):
        import os, time
        reg, out = s.ROOT / 'experiments' / 'glm-experiments.json', s.ROOT / 'site' / 'data' / 'experiments.json'
        old = out.stat().st_mtime
        os.utime(out, (old - 3600, old - 3600))   # pretend the log is older than the registry
        try:
            s.sync_experiment_log()
            self.assertGreaterEqual(out.stat().st_mtime, reg.stat().st_mtime)
        finally:
            if out.stat().st_mtime < reg.stat().st_mtime:
                os.utime(out, (old, old))


if __name__ == '__main__':
    unittest.main()
