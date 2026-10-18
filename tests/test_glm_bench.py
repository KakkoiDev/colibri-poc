import unittest

import glm_bench as gb

LOG = """[prefill] layer 77/78 · 17 token · +20.1s
[prefill] layer 78/78 · 17 token · +21.0s
PROFILO PREFILL (21.0s):
The answer is Canb
[t=16  RSS 5.59 GB  hit 2%  0.43 tok/s  1.00 tok/fw]
erra.
[1, 2]
---
prefill 17 tokens in 23.20s | decode 24 tokens in 54.08s (0.44 tok/s) | expert hit rate 2.1% (pin 0.0% + lru 2.1%) | RSS 10.98 GB
DEGRADE_ZERO tau=0.300 (zeroed 120 miss slots; top layers: L57:15)
"""


class GlmBenchTests(unittest.TestCase):
    def test_parse_log_extracts_timing_text_and_skips(self):
        r = gb.parse_log(LOG)
        self.assertEqual(r['prompt_tokens'], 17)
        self.assertEqual(r['output_tokens'], 24)
        self.assertAlmostEqual(r['prefill_s'], 23.20)
        self.assertAlmostEqual(r['decode_tok_s'], 0.44)
        self.assertEqual(r['zeroed_slots'], 120)
        self.assertEqual(r['text'], 'The answer is Canberra.\n[1, 2]')

    def test_fact_number_and_word_grading(self):
        self.assertTrue(gb.grade({'accept': ['canberra']}, 'Canberra.'))
        self.assertFalse(gb.grade({'accept': ['canberra']}, 'Sydney'))
        self.assertTrue(gb.grade({'accept': ['au'], 'word': True}, 'The symbol is Au.'))
        self.assertFalse(gb.grade({'accept': ['au'], 'word': True}, 'Australia'))
        self.assertTrue(gb.grade({'number': 391}, '17 × 23 = 391'))
        self.assertTrue(gb.grade({'number': 1024}, '2^10 is 1,024'))
        self.assertFalse(gb.grade({'number': 15}, 'You have 16 apples.'))
        self.assertFalse(gb.grade({'number': 1}, 'Sally has 1 brother, so 2 sisters'))
        self.assertIsNone(gb.grade({}, 'anything'))
        self.assertFalse(gb.grade({'accept': ['x']}, None))

    def test_code_grading_runs_tests(self):
        item = {'tests': 'assert f(2)==4'}
        self.assertTrue(gb.grade(item, 'Here:\n```python\ndef f(x):\n    return x*x\n```'))
        self.assertTrue(gb.grade(item, 'def f(x):\n    return x*2'))
        self.assertFalse(gb.grade(item, '```python\ndef f(x):\n    return x+3\n```'))
        self.assertTrue(gb.grade(item, '```python\ndef f(x):\n    return x*x\n'))


if __name__ == '__main__':
    unittest.main()
