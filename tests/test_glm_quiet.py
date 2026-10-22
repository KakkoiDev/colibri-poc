import argparse, json, tempfile, unittest
from pathlib import Path

import glm_quiet as gq


class GlmQuietTests(unittest.TestCase):
    def test_every_case_has_a_published_busy_run(self):
        busy = gq.busy_runs()
        for case, busy_name, *_ in gq.CASES:
            self.assertIn(busy_name, busy, case)
            self.assertTrue(busy[busy_name]['tok_s'], case)

    def test_report_compares_with_busy_runs(self):
        busy_text = (gq.ROOT / 'published-results/glm-20261018/c9-best-combo.output.txt').read_text().strip()
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cond = dict(free_gb=24.0, swap_used_mb=0.0, process_count=300)
            (d / 'meta.json').write_text(json.dumps(dict(stamp='T', forced=False, repeats=2,
                                                         conditions_before=cond, conditions_after=cond)))
            for r, (tps, text) in enumerate([(0.50, busy_text), (0.46, 'different')], 1):
                (d / f'exact-sky-24__r{r}.json').write_text(json.dumps(dict(case=f'exact-sky-24__r{r}', decode_tok_s=tps, text=text)))
            (d / 'exact-sky-24-ram26__r1.json').write_text(json.dumps(dict(case='exact-sky-24-ram26__r1', ram=26, refused=True)))
            gq.report(argparse.Namespace(dir=str(d)))
            out = json.loads((d / 'comparison.json').read_text())
            row = next(c for c in out['cases'] if c['case'] == 'exact-sky-24')
            self.assertAlmostEqual(row['quiet_mean'], 0.48)
            self.assertEqual(row['busy_tok_s'], 0.43)
            self.assertEqual(row['same_text'], [True, False])
            md = (d / 'comparison.md').read_text()
            self.assertIn('+12%', md)
            self.assertIn('refused: not enough free RAM', md)

    def test_report_lists_original_engine_runs(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cond = dict(free_gb=24.0, swap_used_mb=0.0, process_count=300)
            (d / 'meta.json').write_text(json.dumps(dict(stamp='T', forced=False, repeats=1, conditions_before=cond)))
            (d / 'original-defaults__r1.json').write_text(json.dumps(dict(case='original-defaults__r1', ram=None, ctx=None,
                refused=True, auto_ram_gb=15.4, refused_reason='that peak also exceeds the 17.5 GB actually available')))
            (d / 'original-r18-c1k__r1.json').write_text(json.dumps(dict(case='original-r18-c1k__r1', ram=18, ctx=1024,
                refused=False, decode_tok_s=0.07, prefill_s=300.1)))
            gq.report(argparse.Namespace(dir=str(d)))
            md = (d / 'comparison.md').read_text()
            self.assertIn('| original-defaults | automatic (15.4 GB) / default | — | — | refused: that peak', md)
            self.assertIn('| original-r18-c1k | 18 GB / 1024 | 0.07 | 300.1 | ok |', md)
            self.assertEqual(len(json.loads((d / 'comparison.json').read_text())['original']), 2)

    def test_only_a_writer_holds_the_bench_lock(self):
        # lsof -F pa: a virtual machine sharing the folder reads the file; the job opened it for writing to flock it
        from unittest import mock
        out = mock.Mock(stdout='p40673\nf38\nar\np17083\nf3\naw\n')
        with mock.patch.object(gq.subprocess, 'run', return_value=out):
            self.assertEqual(gq.lock_holders(), [17083])
        with mock.patch.object(gq.subprocess, 'run', return_value=mock.Mock(stdout='p40673\nf38\nar\n')):
            self.assertEqual(gq.lock_holders(), [])
            self.assertIsNone(gq.lock_holder())


if __name__ == '__main__':
    unittest.main()
