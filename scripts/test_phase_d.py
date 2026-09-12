"""CPU/generator-only pre-curve checks for paired buffer invariants."""
import json
import unittest
import numpy as np
from phase_d_buffers import compose,layout,CS,SCENARIOS,TYPES,U
from phase_d_operator import REPORT,tensor_hash
from m0.metrics import metrics
from sklearn.metrics import average_precision_score,roc_auc_score


class Tests(unittest.TestCase):
    def test_layout_unique_causal_and_nested(self):
        starts,endpoints,slots=layout()
        self.assertEqual(len(set(endpoints)),100)
        self.assertEqual(endpoints,sorted(endpoints))
        self.assertLess(max(endpoints),U)
        self.assertEqual(len(set(slots)),30)
        for a,b in zip(CS,CS[1:]): self.assertTrue(set(slots[:a])<=set(slots[:b]))

    def test_all_type_pairs_and_truth_isolation(self):
        for kind in TYPES:
            arms,x,y,mask,m=compose(3000,'abrupt',kind)
            for c in CS:
                self.assertEqual(arms[c].shape,(100,10,8))
                self.assertEqual(int(np.any(arms[c]!=arms[0],axis=(1,2)).sum()),c)
                self.assertEqual(tensor_hash(arms[c]),m['arms'][str(c)]['buffer_sha256'])
            before=tensor_hash(x); y[:]=1-y
            self.assertEqual(before,tensor_hash(x))
            self.assertTrue(mask.any())
            for a,b in zip(m['events'],m['events'][1:]): self.assertLessEqual(a['end'],b['start'])

    def test_deterministic_regeneration(self):
        a=compose(3000,'correlation','mixture'); b=compose(3000,'correlation','mixture')
        self.assertEqual(a[-1],b[-1])
        for c in CS: self.assertTrue(np.array_equal(a[0][c],b[0][c]))
        for x,y in zip(a[1:4],b[1:4]): self.assertTrue(np.array_equal(x,y))

    def test_mixture_margins(self):
        *_,m=compose(3000,'recurring','mixture')
        for kind in TYPES[:3]:
            events=[e for e in m['events'] if e['type']==kind]
            self.assertEqual(sorted(e['severity'] for e in events),[1,2,3])
            self.assertEqual(sorted(e['duration'] for e in events),[1,1,1] if kind=='spike' else [16,64,256])
        for c in CS:
            n=[m['arms'][str(c)]['type_counts'].get(k,0) for k in TYPES[:3]]
            self.assertLessEqual(max(n)-min(n),1)

    def test_metric_semantics_and_undefined(self):
        y=np.array([0,1,0,1,1]); s=np.array([.1,.2,.2,.8,.9])
        m=metrics(y,s,.5)
        self.assertAlmostEqual(m['ap'],average_precision_score(y,s))
        self.assertAlmostEqual(m['auroc'],roc_auc_score(y,s))
        self.assertIsNone(metrics([0,0],[.1,.2],.5)['ap'])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    (REPORT/'pre_curve_tests.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
        status='PASS' if result.wasSuccessful() else 'STOP',model_outcomes_used=False),indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
