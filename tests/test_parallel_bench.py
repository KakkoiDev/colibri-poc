import argparse,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
import parallel_bench as p
class ParallelTests(unittest.TestCase):
 def test_serialized(self):
  self.assertEqual(p.overlap_count([dict(events=[1,2,3]),dict(events=[4,5,6])]),0)
 def test_buffered_overlap_is_not_enough(self):
  self.assertEqual(p.overlap_count([dict(events=[1,2,8]),dict(events=[3,4,5])]),0)
 def test_interleaved(self):
  self.assertEqual(p.overlap_count([dict(events=[1,3,5,7]),dict(events=[2,4,6,8])]),2)
 def test_failed_gate_skips_stress(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp); proc=MagicMock();proc.poll.return_value=None
   def api(url,path,*a,**k):
    return {'models':[]} if path=='ps' else {'models':[{'name':'m','digest':'d'}]} if path=='tags' else {'version':'test'}
   with patch.object(p,'ROOT',root),patch.object(p,'api',side_effect=api),patch.object(p,'request'),patch.object(p,'measure',return_value={'overlapping_streams':0}) as measure,patch.object(p.subprocess,'Popen',return_value=proc),patch.object(p.os,'killpg'):
    p.run(argparse.Namespace(model='m',style='terse',max_clients=16,smoke_only=False))
   self.assertEqual(measure.call_count,1)
   data=json.loads(next((root/'results').glob('*/summary.json')).read_text())
   self.assertEqual(data['status'],'not_supported');self.assertEqual(data['stress'],[])
if __name__=='__main__': unittest.main()
