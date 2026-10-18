import unittest

import glm_lab as gl

RUNS = {
    'ref': dict(run='ref', status='ok', tok_s='0.40', prefill_s='20', rss_gb='8', hit_pct='2', decode_tokens='24'),
    'fast': dict(run='fast', status='ok', tok_s='0.50', prefill_s='20', rss_gb='6', hit_pct='2', decode_tokens='24'),
    'same': dict(run='same', status='ok', tok_s='0.41', prefill_s='12', rss_gb='8', hit_pct='2', decode_tokens='24'),
    'bad': dict(run='bad', status='failed', tok_s='', prefill_s='', rss_gb='', hit_pct='', decode_tokens=''),
}


class GlmLabTests(unittest.TestCase):
    def check(self, runs, expected, **extra):
        e = dict(id='x', ref='ref', runs=runs, **extra)
        m = gl.evaluate(e, RUNS)
        self.assertEqual(gl.verdict(e, m), expected)
        return m

    def test_verdicts(self):
        m = self.check(['fast'], 'improves')
        self.assertEqual(m['speed_change_pct'], 25.0)
        self.assertEqual(gl.ways(m), ['generation +25%'])          # RSS change is not judged
        self.check(['same'], 'improves')                            # prompt reading 40% faster
        self.check(['bad'], 'failed')
        self.check(['fast'], 'inconclusive', verdict='inconclusive')  # explicit verdict wins
        self.assertEqual(gl.verdict(dict(id='y', runs=[]), gl.evaluate(dict(id='y', runs=[]), RUNS)), 'not run')

    def test_slower_is_worse(self):
        e = dict(id='x', ref='fast', runs=['ref'])
        self.assertEqual(gl.verdict(e, gl.evaluate(e, RUNS)), 'worse')


if __name__ == '__main__':
    unittest.main()
