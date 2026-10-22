import unittest

import olmoe_concurrency as oc


class ConcurrencyMathTests(unittest.TestCase):
    def test_percentile_nearest_rank(self):
        xs = [5, 1, 4, 2, 3]
        self.assertEqual(oc.percentile(xs, 50), 3)
        self.assertEqual(oc.percentile(xs, 95), 5)
        self.assertEqual(oc.percentile([7], 95), 7)
        self.assertEqual(oc.percentile(list(range(1, 21)), 95), 19)

    def test_summarize_totals_and_equality(self):
        recs = [dict(latency_s=2.0, ttft_s=0.2, tokens=40, same_as_single=True),
                dict(latency_s=1.0, ttft_s=0.1, tokens=10, same_as_single=False),
                dict(latency_s=4.0, ttft_s=0.4, tokens=80, same_as_single=None)]
        s = oc.summarize(recs, wall_s=5.0)
        self.assertEqual(s['tokens'], 130)
        self.assertEqual(s['total_tok_s'], 26.0)             # all tokens / wall time of the level
        self.assertEqual(s['per_request_tok_s'], 16.67)      # mean of 20, 10 and 20 tok/s
        self.assertEqual((s['p50_latency_s'], s['p95_latency_s']), (2.0, 4.0))
        self.assertEqual(s['same_as_single'], '1/2')         # unknown references are not counted

    def test_retries_only_connection_resets(self):
        import urllib.error
        calls = []
        def flaky(url, model, prompt, ngen, timeout):
            calls.append(1)
            if len(calls) < 3:
                raise urllib.error.URLError(ConnectionResetError(54, 'reset'))
            return dict(total_s=1.0, ttft_s=0.1, usage={'completion_tokens': 5}, chunks=5, text='ok', finish_reason='stop')
        old, old_sleep = oc.glm_bench.openai_generate, oc.time.sleep
        oc.glm_bench.openai_generate, oc.time.sleep = flaky, lambda s: None
        args = type('A', (), dict(url='u', model='m', ngen=8, timeout=5))()
        try:
            self.assertEqual(oc.one(args, 'p')['retries'], 2)
            oc.glm_bench.openai_generate = lambda *a: (_ for _ in ()).throw(urllib.error.URLError(TimeoutError('slow')))
            with self.assertRaises(urllib.error.URLError):
                oc.one(args, 'p')                      # other errors are not retried
        finally:
            oc.glm_bench.openai_generate, oc.time.sleep = old, old_sleep

    def test_clients_start_at_different_prompts(self):
        items = [dict(id=str(i)) for i in range(24)]
        seen = {}
        def fake_one(args, prompt):
            return dict(latency_s=1, ttft_s=0.1, tokens=1, text='x', finish='stop', retries=0)
        old_one, old_grade = oc.one, oc.glm_bench.grade
        oc.one, oc.glm_bench.grade = fake_one, lambda item, text: True
        try:
            items = [dict(id=str(i), prompt=str(i), kind='fact', accept=['x']) for i in range(24)]
            recs, wall = oc.run_level(None, items, 4, {})
        finally:
            oc.one, oc.glm_bench.grade = old_one, old_grade
        self.assertEqual(len(recs), 96)
        for c in range(4):
            seen[c] = [r['id'] for r in recs if r['client'] == c]
            self.assertEqual(sorted(seen[c], key=int), [str(i) for i in range(24)])   # every client sends every prompt once


if __name__ == '__main__':
    unittest.main()
