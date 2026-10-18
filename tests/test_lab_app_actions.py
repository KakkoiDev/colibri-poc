import json, sys, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab_app'))
import actions as a
import server as s


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = a.STATE, a.LOGS
        a.STATE = Path(self.tmp.name)
        a.LOGS = a.STATE / 'logs'

    def tearDown(self):
        a.STATE, a.LOGS = self.old
        self.tmp.cleanup()

    def test_only_whitelisted_commands(self):
        argv, _ = a.build_command('bench', {'name': 'v9', 'configs': ['exact'], 'styles': ['terse']})
        self.assertEqual(argv[1:5], ['glm_bench.py', 'run', '--name', 'v9'])
        for kind, args in [('bench', {'name': '../x', 'configs': ['exact'], 'styles': ['terse']}),
                           ('bench', {'name': 'v9', 'configs': ['rm -rf'], 'styles': ['terse']}),
                           ('quiet', {'flags': ['force']}), ('prep', {'model': 'glm-5.3-int4'}),
                           ('planned', {'id': 'no-such-experiment'}), ('shell', {'cmd': 'ls'})]:
            with self.assertRaises(a.ActionError, msg=kind):
                a.build_command(kind, args)
        argv, _ = a.build_command('suite', {'bench': 'speed', 'model': 'glm-5.3-int4'})
        self.assertEqual(argv[1:], ['glm_suite.py', 'run', 'speed', '--model', 'glm-5.3-int4'])
        for bad in [{'bench': 'speed', 'model': 'glm-5.3-flash-iq3xxs'}, {'bench': 'rm', 'model': 'glm-5.3-int4'}, {'bench': 'speed', 'model': 'nope'}]:
            with self.assertRaises(a.ActionError):
                a.build_command('suite', bad)
        argv, _ = a.build_command('prep', {'model': 'glm-5.3-iq2m'})
        self.assertEqual(argv, ['make', 'glm-prep-iq2m'])

    def test_ollama_bench_needs_installed_model_and_exact(self):
        old = a.ollama_models
        a.ollama_models = lambda: {'qwen3.8:27b-mlx'}
        try:
            argv, title = a.build_command('bench', {'name': 'qwen38-27b-ollama', 'configs': ['exact'], 'styles': ['normal', 'terse'],
                                                    'ollama_model': 'qwen3.8:27b-mlx'})
            self.assertEqual(argv[-4:], ['--backend', 'ollama', '--ollama-model', 'qwen3.8:27b-mlx'])
            self.assertIn('Ollama', title)
            for bad in [{'ollama_model': 'evil; rm'}, {'ollama_model': 'qwen3.8:27b-mlx', 'configs': ['d030']}]:
                with self.assertRaises(a.ActionError):
                    a.build_command('bench', {'name': 'x', 'configs': ['exact'], 'styles': ['terse'], **bad})
        finally:
            a.ollama_models = old

    def test_queue_add_move_remove_pause_and_gpu_rule(self):
        x = a.queue_add('quiet', {'flags': ['ram-sweep']}, only_when_quiet=True)
        y = a.queue_add('bench', {'name': 'v9', 'configs': ['exact'], 'styles': ['terse']})
        a.queue_move(y['qid'], 'up')
        self.assertEqual([i['qid'] for i in a.queue_state()['items']], [y['qid'], x['qid']])
        with self.assertRaises(a.ActionError):
            a.queue_add('prep', {'model': 'glm-5.3-iq2m'})   # downloads never go through the GPU queue
        self.assertEqual(a.queue_tick(gpu_busy=True, quiet=True), 'GPU busy')
        a.queue_remove(y['qid'])
        self.assertIn('quiet', a.queue_tick(gpu_busy=False, quiet=False))   # waits for a quiet machine
        a.queue_pause(True)
        self.assertEqual(a.queue_tick(gpu_busy=False, quiet=True), 'queue paused')

    def test_stop_only_lab_jobs(self):
        with self.assertRaises(a.ActionError):
            a.stop(1, allowed_pids={12345})

    def test_remove_refuses_owner_and_outside_paths(self):
        with self.assertRaises(a.ActionError):
            a.remove_targets({'owner_model': True, 'remove_paths': ['colibri-models/glm-5.3']})
        with self.assertRaises(a.ActionError):
            a.remove_targets({'remove_paths': ['Documents']})
        with self.assertRaises(a.ActionError):
            a.remove_targets({'remove_paths': ['colibri-models/glm-5.3']})
        self.assertEqual(a.remove_targets({'remove_paths': ['colibri-models/does-not-exist-xyz']}), [])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = s.ThreadingHTTPServer(('127.0.0.1', 0), s.Handler)
        s.PORT = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f'http://127.0.0.1:{s.PORT}'

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def post(self, path, body, headers):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode(), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code

    def test_actions_need_app_header_and_origin(self):
        body = {'kind': 'shell', 'args': {}}
        self.assertEqual(self.post('/api/queue/add', body, {}), 403)
        self.assertEqual(self.post('/api/queue/add', body, {'X-Lab-Action': '1', 'Origin': 'https://evil.example'}), 403)
        self.assertEqual(self.post('/api/queue/add', body, {'X-Lab-Action': '1', 'Origin': self.base}), 400)
        self.assertEqual(self.post('/api/nope', {}, {'X-Lab-Action': '1'}), 404)

    def test_unknown_api_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.base + '/api/does-not-exist')
        self.assertEqual(cm.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
