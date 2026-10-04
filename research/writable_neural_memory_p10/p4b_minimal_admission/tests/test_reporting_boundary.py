import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from reporting_boundary import clipped_burden
class Boundary(unittest.TestCase):
 def test_pretransition_endpoint_has_no_negative_duration(self):
  a=np.ones(30,dtype=bool);y=np.zeros(30,dtype=int)
  r=clipped_burden(a,y,10,5,20)
  self.assertEqual(r["duration"],0);self.assertEqual(r["clean_points"],0);self.assertIsNone(r["rate"])
 def test_half_open_interval_and_label_exclusion(self):
  a=np.ones(30,dtype=bool);y=np.zeros(30,dtype=int);y[12]=1
  r=clipped_burden(a,y,10,15,20)
  self.assertEqual(r["duration"],5);self.assertEqual(r["clean_points"],4);self.assertEqual(r["alarms"],4)
 def test_censor_clips_endpoint(self):
  r=clipped_burden(np.ones(30),np.zeros(30),10,25,20)
  self.assertEqual(r["duration"],10)
if __name__=="__main__":unittest.main(verbosity=2)
