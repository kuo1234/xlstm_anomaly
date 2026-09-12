"""Phase A audit tests only; no Phase B implementation."""
import unittest
import numpy as np
import pandas as pd
from phase_a_audit import assign, contained_offset, digest_array, inspect_frame, BUCKETS


class AuditTests(unittest.TestCase):
    def test_numeric_and_intervals(self):
        df = pd.DataFrame(dict(a=np.arange(576), b=np.ones(576), Label=np.zeros(576)))
        result = inspect_frame(df, 320)
        self.assertTrue(result['numeric_pass'])
        self.assertEqual(result['fit_interval'], [0, 256])
        self.assertEqual(result['calibration_interval'], [256, 320])
        df.loc[319, 'Label'] = 1
        self.assertIn('contaminated_original_training_prefix', inspect_frame(df, 320)['numeric_exclusions'])
        df.loc[319, 'Label'] = 0
        df.loc[320, 'Label'] = 1
        self.assertTrue(inspect_frame(df, 320)['numeric_pass'])

    def test_invalid_values(self):
        df = pd.DataFrame(dict(a=np.ones(576), b=np.ones(576), Label=np.zeros(576)))
        df.loc[400, 'a'] = np.inf
        df.loc[400, 'Label'] = 2
        errors = inspect_frame(df, 320)['numeric_exclusions']
        self.assertIn('nonfinite_observations', errors)
        self.assertIn('nonbinary_or_nonfinite_labels', errors)
        self.assertIn('training_prefix_lt_320', inspect_frame(df, 319)['numeric_exclusions'])
        self.assertIn('test_lt_256', inspect_frame(df, 321)['numeric_exclusions'])
        self.assertIn('D_lt_2', inspect_frame(df.drop(columns='b'), 320)['numeric_exclusions'])

    def test_exact_crop(self):
        x = np.arange(40).reshape(20, 2)
        self.assertEqual(contained_offset(x[3:9], x), 3)
        self.assertEqual(contained_offset(x, x), 0)
        self.assertIsNone(contained_offset(x+1, x))
        self.assertEqual(digest_array(np.array([0.])), digest_array(np.array([-0.])))

    def test_global_assignment_not_greedy(self):
        rows = [dict(file=str(i), source_group=str(i), eligible=True, tags=[b])
                for i, b in enumerate(b for b in BUCKETS for _ in range(3))]
        # Earliest continuous candidate is needed by periodic: solver must backtrack.
        rows.append(dict(file='00', source_group='6', eligible=True, tags=['continuous']))
        result = assign(rows)
        self.assertEqual(len(result), 12)
        self.assertNotIn('00', [r['file'] for r in result])
        self.assertEqual(len({r['source_group'] for r in result}), 12)

    def test_shared_bucket_sources_stop(self):
        rows = [dict(file=f'{b}{i}', source_group=str(i), eligible=True, tags=[b])
                for b in BUCKETS for i in range(3)]
        self.assertIsNone(assign(rows))


if __name__ == '__main__':
    unittest.main(verbosity=2)
