import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from weights import quantile
import numpy as np
class Contracts(unittest.TestCase):
 def test_virtual_duplication_matches_literal_rows(self):
  groups=[np.array([1.,2.,3.]),np.array([10.,11.])]
  for m in [1,4,16,64]:
   actual=quantile(groups,[m,1],'row_pooled',q=.8)
   expected=np.sort(np.concatenate([np.tile(groups[0],m),groups[1]]))[int(np.ceil(.8*(len(groups[0])*m+len(groups[1]))))-1]
   self.assertEqual(actual,expected)
 def test_balanced_and_dedup_are_invariant_to_record_replays(self):
  groups=[np.arange(100.),np.arange(20.)+100]
  for arm in ['trace_balanced','identity_deduplicated_pooled']:
   for m in [1,4,16,64]:self.assertEqual(quantile(groups,[1,1],arm),quantile(groups,[m,1],arm))
if __name__=='__main__':unittest.main()
