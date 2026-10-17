import unittest
import bench


def record(name, speed, ids, status='ok', round_id=1):
    return {'variant':name, 'round':round_id, 'status':status, 'data':{'requests':[
        {'phase':'warmup', 'prompt_id':'p', 'decode_tps':9999, 'token_ids':[9], 'tokens':1, 'ttft_s':0},
        {'phase':'measured', 'prompt_id':'p', 'decode_tps':speed, 'token_ids':ids, 'tokens':len(ids), 'ttft_s':0.2}
    ]}}

class ComparisonTests(unittest.TestCase):
    def test_warmup_excluded_and_speedup_paired_by_round(self):
        rows=[record('baseline',10,[1]), record('poc',20,[1]),
              record('baseline',100,[1],round_id=2), record('poc',200,[1],round_id=2)]
        p=bench.summarize(rows,'baseline')[1]
        self.assertEqual(p['paired_median_speedup'],2)
        self.assertEqual(p['median_decode_tps'],110)
        self.assertTrue(p['exact_tokens_match'])

    def test_wrong_output_is_visible_despite_speedup(self):
        p=bench.summarize([record('baseline',10,[1,2]),record('poc',50,[1])],'baseline')[1]
        self.assertFalse(p['exact_tokens_match'])
        self.assertFalse(p['equal_output_lengths'])

    def test_failure_is_retained_and_missing_baseline_not_compared(self):
        rows=[record('baseline',0,[],status='failed'),record('poc',20,[1])]
        b,p=bench.summarize(rows,'baseline')
        self.assertEqual(b['failed_rounds'],1)
        self.assertIsNone(b['median_decode_tps'])
        self.assertIsNone(p['paired_median_speedup'])
        self.assertIsNone(p['exact_tokens_match'])

    def test_typos_and_unsupported_engines_rejected(self):
        with self.assertRaises(ValueError):
            bench.validate({'name':'x','backend':'mlx','pretill_step_size':2})
        with self.assertRaises(ValueError):
            bench.validate({'name':'x','backend':'colibri'})

if __name__=='__main__':
    unittest.main()
