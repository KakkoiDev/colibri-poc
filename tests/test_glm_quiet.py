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


if __name__ == '__main__':
    unittest.main()
