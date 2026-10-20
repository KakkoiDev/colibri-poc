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


if __name__ == '__main__':
    unittest.main()
