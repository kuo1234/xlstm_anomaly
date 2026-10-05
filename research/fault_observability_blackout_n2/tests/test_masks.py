import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
from masks import masks,summarize
class Contracts(unittest.TestCase):
 def test_gap_creates_exact_history_tail_without_future_fill(self):
  x=np.ones((100,2));obs=np.ones(100,bool);x[40:45]=np.nan;m=masks(x,obs)
  self.assertEqual(np.flatnonzero(m[0]&~m[32]& (np.arange(100)>=45)).tolist(),list(range(45,77)))
  self.assertFalse(m[32][76]);self.assertTrue(m[32][77])
 def test_missing_target_does_not_mean_missing_input_history(self):
  x=np.ones((50,2));obs=np.ones(50,bool);obs[35]=False;m=masks(x,obs)
  self.assertFalse(m[32][35]);self.assertTrue(m[32][36])
 def test_prefix_invariance_and_no_partial_window_warmup(self):
  x=np.ones((100,2));obs=np.ones(100,bool);x[70:]=np.nan
  full=masks(x,obs);prefix=masks(x[:60],obs[:60])
  for w in full:np.testing.assert_array_equal(full[w][:60],prefix[w])
  self.assertFalse(full[32][:32].any())
 def test_outside_extent_is_not_fabricated_opportunity(self):
  r=summarize(np.arange(50),np.ones((50,2)),np.ones(50,bool),40,60)
  self.assertFalse(r['grid_extent_complete']);self.assertEqual(r['W0_available'],10);self.assertEqual(r['expected_targets'],21)
if __name__=='__main__':unittest.main()
