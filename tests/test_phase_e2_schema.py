import sys,unittest
from pathlib import Path
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from phase_e2_schema import *

class E2SchemaTests(unittest.TestCase):
    def fixture(self,T=3):
        return {cell:{k:torch.arange(1,T+1,dtype=torch.float32).reshape(1,T,1,1).expand(2,T,4,10).clone()
            for k in ('hidden','input','retention','memory')} for cell in SCALAR_CELLS}
    def test_dimensions_and_exact_cell_binding(self):
        self.assertEqual(len(BASE_COLUMNS),18);self.assertEqual(len(EXPANDED_COLUMNS),234)
        with self.assertRaises(ValueError):summarize({})
        x=self.fixture();x['matrix_cell']=x[SCALAR_CELLS[0]]
        with self.assertRaises(ValueError):summarize(x)
    def test_decoder_actual_previous_not_singleton_zero(self):
        x=self.fixture();out=summarize(x)
        self.assertEqual(out[0,3],1.);self.assertEqual(out[0,8],1.);self.assertEqual(out[0,13],1.)
        self.assertTrue(torch.allclose(out[:,17],torch.full((2,),.5)))
        for cell in SCALAR_CELLS:
            if cell.startswith('decoder'):
                for value in x[cell].values():value[:,-2]=1
        out2=summarize(x)
        self.assertEqual(out2[0,3],1.5)
        self.assertTrue(torch.allclose(out2[:,17],torch.full((2,),1.25)))
    def test_zero_origin_only_for_true_singleton(self):
        out=summarize(self.fixture(1));self.assertEqual(out[0,3],1.)
        self.assertGreater(out[0,17],1e8)
    def test_equal_heads_layers(self):
        x=self.fixture();baseline=summarize(x)
        for v in x[SCALAR_CELLS[-1]].values():v.zero_()
        self.assertTrue(torch.allclose(summarize(x),baseline*.75))
    def test_no_missing_or_nonfinite_scalar(self):
        x=self.fixture();del x[SCALAR_CELLS[0]]['memory']
        with self.assertRaises(ValueError):summarize(x)
        x=self.fixture();x[SCALAR_CELLS[0]]['hidden'][0,0,0,0]=float('nan')
        with self.assertRaises(ValueError):summarize(x)
    def test_trailing_causality_warmup_slope(self):
        x=torch.arange(50.).reshape(-1,1).expand(50,18).clone();a=expand_history(x)
        x[40:]=10000;b=expand_history(x)
        self.assertTrue(torch.allclose(a[:40],b[:40],equal_nan=True))
        self.assertTrue(torch.isnan(a[0,1:13]).all());self.assertTrue(torch.isfinite(a[31:]).all())
        self.assertEqual(a[40,3],1.)
        for n in (0,1,3,8):self.assertEqual(expand_history(x[:n]).shape,(n,234))
    def test_permutation(self):
        g=torch.Generator().manual_seed(710)
        x={cell:{k:torch.randn(4,5,4,10,generator=g) for k in ('hidden','input','retention','memory')} for cell in SCALAR_CELLS}
        p=torch.tensor([2,0,3,1])
        self.assertTrue(torch.equal(summarize({c:{k:v[p] for k,v in l.items()} for c,l in x.items()}),summarize(x)[p]))

if __name__=='__main__':unittest.main(verbosity=2)
