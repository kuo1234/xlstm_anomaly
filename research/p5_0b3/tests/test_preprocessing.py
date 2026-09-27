"""Unit tests for source-fit B3 preprocessing statistics."""

import importlib.util
from pathlib import Path
import unittest

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "preprocessing.py"
SPEC = importlib.util.spec_from_file_location("p5_b3_preprocessing", SCRIPT)
preprocessing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preprocessing)


class PreprocessingTests(unittest.TestCase):
    def test_fits_median_then_population_mean_std(self):
        train = np.array([[1.0, 2.0], [3.0, np.nan], [5.0, 8.0]], dtype=np.float32)
        fitted = preprocessing.MedianImputeStandardScaler().fit(train)
        actual = fitted.transform(train)
        imputed = np.array([[1.0, 2.0], [3.0, 5.0], [5.0, 8.0]])
        expected = ((imputed - imputed.mean(axis=0)) /
                    imputed.std(axis=0, ddof=0)).astype(np.float32)
        self.assertEqual(actual.dtype, np.float32)
        np.testing.assert_array_equal(actual, expected)
        self.assertTrue(np.isnan(train[1, 1]))

    def test_transform_reuses_training_statistics_without_refitting(self):
        train = np.array([[1.0, 2.0], [3.0, np.nan], [5.0, 8.0]], dtype=np.float32)
        preprocessor = preprocessing.MedianImputeStandardScaler().fit(train)
        transformed = preprocessor.transform(np.array([[9.0, np.nan]], dtype=np.float32))
        # The second feature is imputed with the train median (5), then centered
        # by the training mean (5); transform-time refitting is forbidden.
        expected_first = (9.0 - 3.0) / np.sqrt(8.0 / 3.0)
        np.testing.assert_allclose(transformed, [[expected_first, 0.0]], rtol=1e-7, atol=1e-7)

    def test_zero_or_nonfinite_training_scale_fails(self):
        with self.assertRaises(ValueError):
            preprocessing.MedianImputeStandardScaler().fit(
                np.array([[2.0, 1.0], [2.0, 3.0]], dtype=np.float32))
        with self.assertRaises(ValueError):
            preprocessing.MedianImputeStandardScaler().fit(
                np.array([[np.nan], [np.nan]], dtype=np.float32))

    def test_rejects_infinities_and_unfitted_transform(self):
        with self.assertRaises(ValueError):
            preprocessing.MedianImputeStandardScaler().fit(np.array([[np.inf, 1.0]]))
        with self.assertRaises(ValueError):
            preprocessing.MedianImputeStandardScaler().transform(np.ones((1, 2)))

    def test_rejects_all_nan_support_row(self):
        with self.assertRaises(ValueError):
            preprocessing.MedianImputeStandardScaler().fit(
                np.array([[1.0, 2.0], [np.nan, np.nan], [3.0, 4.0]]))
        fitted = preprocessing.MedianImputeStandardScaler().fit(
            np.array([[1.0, 2.0], [3.0, 4.0]]))
        with self.assertRaises(ValueError):
            fitted.transform(np.array([[np.nan, np.nan]]))

    def test_rejects_nonfinite_float32_cast(self):
        fitted = preprocessing.MedianImputeStandardScaler().fit(
            np.array([[0.0, 0.0], [2e-38, 4e-38]], dtype=np.float64))
        with self.assertRaises(ValueError):
            fitted.transform(np.array([[3e38, 3e38]], dtype=np.float64))


if __name__ == "__main__":
    unittest.main()
