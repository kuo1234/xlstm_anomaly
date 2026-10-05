import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from utility import fraction
import numpy as np
class Contracts(unittest.TestCase):
 def test_missing_scores_are_not_normal(self):
  t=np.arange(50);s=np.ones(50);s[:5]=np.nan;r=fraction(t,s,0,49,.5)
  self.assertEqual(r['alarm_fraction'],1);self.assertFalse(r['eligible']);self.assertEqual(r['coverage'],.9)
 def test_closed_range_and_no_point_expansion(self):
  r=fraction([0,1,2],[1,0,1],1,1,.5);self.assertEqual(r['count'],1);self.assertEqual(r['alarm_fraction'],0);self.assertFalse(r['eligible'])
if __name__=='__main__':unittest.main()
