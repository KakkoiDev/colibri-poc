import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import glm_bench
import glm_suite
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab_app'))
import actions
import server


class ResumeTests(unittest.TestCase):
    def test_requeue_preserves_settings_and_quiet_condition_and_rejects_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(actions, 'STATE', Path(tmp)):
            job = dict(id='old', kind='bench', status='failed', args=dict(name='saved', configs=['exact'], styles=['terse']),
                       only_when_quiet=True, started='2026-10-20 01:00:00')
            actions._write('jobs.json', {'jobs': [job]})
            with patch.object(actions, 'resume_progress', return_value=dict(done=2, total=4, remaining=2)):
                actions.queue_pause(True)
                queued = server.act('/api/job/resume', {'id':'old'})['queued']
                self.assertEqual(queued['args'], job['args'])
                self.assertTrue(queued['only_when_quiet'])
                self.assertFalse(actions.queue_state()['paused'])
                with self.assertRaises(actions.ActionError):
                    actions.resume_job('old')
                self.assertEqual(len(actions.queue_state()['items']), 1)
                actions.queue_remove(queued['qid'])
                with patch.object(actions, 'resume_progress', return_value=None):
                    with self.assertRaises(actions.ActionError):
                        actions.resume_job('old')

    def test_quality_resume_keeps_success_retries_failure_and_archives_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy(glm_bench.ROOT / 'glm-prompts.json', root)
            folder = root / 'results' / 'glm-bench-saved'
            folder.mkdir(parents=True)
            success = folder / 'fact-capital__terse__exact.json'
            failure = folder / 'fact-gold__terse__exact.json'
            success.write_text(json.dumps(dict(exit=0, text='saved answer')))
            failure.write_text(json.dumps(dict(exit=1, text='failed attempt')))
            failure.with_suffix('.log').write_text('old log')
            args = types.SimpleNamespace(name='saved', configs='exact', styles='terse', only='fact-capital,fact-gold',
                backend='ollama', ollama_model='test', ollama_url='local', ram=18, ctx=1024, ngen=8, timeout=5, coli_dir='x')
            with (patch.object(glm_bench, 'ROOT', root), patch.object(glm_bench.subprocess, 'run', return_value=types.SimpleNamespace(stdout='test')),
                    patch.object(glm_bench, 'ollama_generate', return_value={}) as generate):
                glm_bench.run(args)
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(json.loads(success.read_text())['text'], 'saved answer')
            self.assertEqual(json.loads(failure.read_text())['exit'], 0)
            archived = list((folder / 'attempts').glob('*/*.json'))
            self.assertEqual(len(archived), 1)
            self.assertEqual(json.loads(archived[0].read_text())['exit'], 1)
            self.assertEqual(archived[0].with_suffix('.log').read_text(), 'old log')

    def test_sweep_resume_reuses_identity_skips_only_successful_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prefix = 'suite-speed-test-stable-'
            records = {prefix+'sky-exact':dict(status='ok'), prefix+'code-exact':dict(status='failed')}
            with (patch.object(glm_suite, 'ROOT', root), patch.object(glm_suite, 'model', return_value=dict(suite=True,path='.',coli_dir='other')),
                    patch.object(glm_suite.glm_lab, 'acquire_lock', return_value=types.SimpleNamespace(close=lambda:None)),
                    patch.object(glm_suite.glm_lab, 'runs_table', return_value=records), patch.object(glm_suite.glm_lab, 'execute') as execute):
                glm_suite.run('speed', 'test', 'stable')
            self.assertEqual([c.args[0] for c in execute.call_args_list], [prefix+c for c in ('code-exact','sky-skip050','code-skip050')])
            self.assertTrue(list((root / 'results' / 'suite-attempts').glob('*/*.json')))

    def test_resume_counts_successes_even_when_job_exit_was_zero(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(actions, 'ROOT', Path(tmp)):
            root = Path(tmp)
            (root / 'glm-prompts.json').write_text(json.dumps({'prompts':[{'id':'a'},{'id':'b'},{'id':'c'}]}))
            folder = root / 'results' / 'glm-bench-saved'
            folder.mkdir(parents=True)
            (folder / 'a__terse__exact.json').write_text(json.dumps(dict(exit=0, correct=False)))
            (folder / 'b__terse__exact.json').write_text(json.dumps(dict(exit=1)))
            job = dict(kind='bench',status='done',args=dict(name='saved',configs=['exact'],styles=['terse']))
            self.assertEqual(actions.resume_progress(job), dict(done=1,total=3,remaining=2))
            job['status']='running'
            self.assertIsNone(actions.resume_progress(job))

    def test_legacy_sweep_uses_original_launch_minute(self):
        self.assertEqual(actions.suite_identity(dict(args={},started='2026-10-20 07:41:07'))['run_id'], '20261020T0741')
        with self.assertRaises(actions.ActionError):
            actions.build_command('suite', dict(bench='speed', model='glm-5.3-int4', run_id='../bad'))


if __name__ == '__main__':
    unittest.main()
