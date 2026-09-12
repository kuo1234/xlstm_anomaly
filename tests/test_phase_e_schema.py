import sys
from pathlib import Path
import unittest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase_e_schema import BASE_COLUMNS,EXPANDED_COLUMNS,summarize,expand_history

class SchemaTests(unittest.TestCase):
    def test_dimensions_and_no_missing_scalar_fallback(self):
        self.assertEqual(len(BASE_COLUMNS),18);self.assertEqual(len(EXPANDED_COLUMNS),234)
        with self.assertRaises(ValueError):summarize([])
        with self.assertRaises(ValueError):summarize([{'hidden':torch.zeros(1,2,4,10)}])

    def test_zero_initial_delta_and_equal_layer_head_pool(self):
        layer={k:torch.full((2,1,4,3),2.) for k in ('hidden','input','retention','memory')}
        out=summarize([layer]);self.assertEqual(out.shape,(2,18))
        self.assertTrue(torch.equal(out[:,3],torch.full((2,),2.)))
        self.assertTrue(torch.equal(out[:,8],torch.full((2,),2.)))
        self.assertTrue(torch.equal(out[:,13],torch.full((2,),2.)))
        other={k:torch.zeros_like(v) for k,v in layer.items()}
        self.assertTrue(torch.equal(summarize([layer,other]),out/2))

    def test_previous_timestep_not_previous_window(self):
        layer={k:torch.arange(3.).reshape(1,3,1,1).expand(2,3,4,3) for k in ('hidden','input','retention','memory')}
        out=summarize([layer]);self.assertEqual(out[0,3],1.)
        self.assertEqual(out[0,8],1.);self.assertEqual(out[0,13],1.)
        self.assertTrue(torch.allclose(out[:,17],torch.ones(2)))

    def test_rolling_warmup_causality_and_slope(self):
        x=torch.arange(50.).unsqueeze(1).expand(50,18).clone()
        a=expand_history(x);x[40:]=10000;b=expand_history(x)
        self.assertTrue(torch.allclose(a[:40],b[:40],equal_nan=True))
        self.assertTrue(torch.isfinite(a[31:]).all())
        self.assertTrue(torch.isnan(a[0,1:13]).all())
        self.assertEqual(a[40,3],1.)
        for n in (0,1,3,8):self.assertEqual(expand_history(x[:n]).shape,(n,234))

    def test_batch_permutation(self):
        g=torch.Generator().manual_seed(71)
        layer={k:torch.randn(4,6,4,10,generator=g) for k in ('hidden','input','retention','memory')}
        perm=torch.tensor([2,0,3,1])
        self.assertTrue(torch.equal(summarize([{k:v[perm] for k,v in layer.items()}]),summarize([layer])[perm]))

if __name__=='__main__':unittest.main(verbosity=2)
