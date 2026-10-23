import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('results_sync', Path(__file__).resolve().parents[1] / 'scripts/lab_results_sync.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class PublisherTests(unittest.TestCase):
    def test_remove_machine_paths(self):
        self.assertEqual(sync.clean('/Users/alice/Code/model /private/tmp/job'), '~/Code/model <tmp>/job')

    def test_skip_in_progress_json(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'answer.json'
            path.write_text('{"id":')
            self.assertIsNone(sync.saved_json(path))
            path.write_text('{"text":"/Users/alice/model"}')
            self.assertEqual(sync.saved_json(path), {'text': '~/model'})

    def test_snapshot_preserves_published_answer(self):
        from unittest.mock import patch
        import json
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'source', Path(temp) / 'target'
            local = source / 'results/glm-bench-v1'
            old = target / 'published-results/glm-bench-v1/answers'
            local.mkdir(parents=True)
            old.mkdir(parents=True)
            (target / 'site/data').mkdir(parents=True)
            answer = dict(id='p', style='normal', config='exact', exit=0)
            (old / 'p__normal__exact.json').write_text(json.dumps(answer))
            (local / 'p__normal__exact.json').write_text('{')
            with patch.object(sync, 'run'):
                sync.snapshot(source, target)
            self.assertEqual(json.loads((target / 'results/glm-bench-v1/p__normal__exact.json').read_text()), answer)

    def test_only_job_completion_triggers_publish(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(sync, 'ROOT', Path(temp)), patch.object(sync, 'completed_jobs', return_value={'old'}) as jobs, patch.object(sync, 'sync') as publish:
                sync.check_completions()
                sync.check_completions()
                publish.assert_not_called()
                jobs.return_value = {'old', 'new'}
                sync.check_completions()
                sync.check_completions()
                publish.assert_called_once()

    def test_failed_push_keeps_completion_pending(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(sync, 'ROOT', Path(temp)), patch.object(sync, 'completed_jobs', return_value=set()) as jobs, patch.object(sync, 'sync') as publish:
                sync.check_completions()
                jobs.return_value = {'new'}
                publish.side_effect = RuntimeError('offline')
                with self.assertRaises(RuntimeError):
                    sync.check_completions()
                publish.side_effect = None
                sync.check_completions()
                self.assertEqual(publish.call_count, 2)
    def test_archive_preserves_failed_runs_and_excludes_app_state(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp)/'source', Path(temp)/'target'
            (source/'results/parallel-bench-test').mkdir(parents=True)
            (source/'results/parallel-bench-test/failure.json').write_text('{"error":"/Users/alice/model"}')
            (source/'results/lab-app').mkdir()
            (source/'results/lab-app/queue.json').write_text('{"private":"state"}')
            (target/'site/data').mkdir(parents=True)
            sync.archive_results(source,target)
            manifest=json.loads((target/'site/data/bench-archive.json').read_text())
            self.assertEqual(len(manifest['files']),1)
            file=target/'published-results/raw/parallel-bench-test/failure.json'
            self.assertNotIn('/Users/alice',file.read_text())
            import hashlib
            self.assertEqual(manifest['files'][0]['sha256'],hashlib.sha256(file.read_bytes()).hexdigest())
