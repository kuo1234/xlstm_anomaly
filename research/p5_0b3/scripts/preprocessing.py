"""Source-fit median imputation and standardization for the B3 smoke input."""

from __future__ import annotations

import numpy as np


class MedianImputeStandardScaler:
    """Fit statistics in float64, then return finite float32 model inputs.

    All-NaN rows are invalid support rows and must be excluded at the stratum
    boundary; this transformer never drops or repairs rows.
    """

    def __init__(self) -> None:
        self.medians_: np.ndarray | None = None
        self.means_: np.ndarray | None = None
        self.scales_: np.ndarray | None = None

    @staticmethod
    def _array(values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=np.float64)
        if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
            raise ValueError("expected nonempty two-dimensional input")
        if np.isinf(array).any():
            raise ValueError("infinite input is not supported")
        if np.isnan(array).all(axis=1).any():
            raise ValueError("all-NaN rows are invalid support rows")
        return array

    def fit(self, training_rows: np.ndarray) -> "MedianImputeStandardScaler":
        """Learn per-column median, mean, and population std from training rows."""
        array = self._array(training_rows)
        if np.isnan(array).all(axis=0).any():
            raise ValueError("a training column has no finite values")
        medians = np.nanmedian(array, axis=0)
        if not np.isfinite(medians).all():
            raise ValueError("a training column has no finite values")
        imputed = self._impute(array, medians)
        means = np.mean(imputed, axis=0, dtype=np.float64)
        scales = np.std(imputed, axis=0, ddof=0, dtype=np.float64)
        minimum_scales = 1e-12 * np.maximum(1.0, np.abs(means))
        if (not np.isfinite(means).all() or not np.isfinite(scales).all() or
                np.any(scales <= minimum_scales)):
            raise ValueError("a source training scale is non-finite or below the frozen floor")
        self.medians_ = medians
        self.means_ = means
        self.scales_ = scales
        return self

    @staticmethod
    def _impute(array: np.ndarray, medians: np.ndarray) -> np.ndarray:
        imputed = array.copy()
        rows, cols = np.where(np.isnan(imputed))
        imputed[rows, cols] = medians[cols]
        return imputed

    def transform(self, values: np.ndarray) -> np.ndarray:
        """Apply stored fit statistics without learning from transform rows."""
        if self.medians_ is None or self.means_ is None or self.scales_ is None:
            raise ValueError("preprocessor has not been fitted")
        array = self._array(values)
        if array.shape[1] != self.medians_.size:
            raise ValueError("feature dimension differs from fitted training data")
        imputed = self._impute(array, self.medians_)
        transformed = (imputed - self.means_) / self.scales_
        if not np.isfinite(transformed).all():
            raise ValueError("transformed values are non-finite")
        with np.errstate(over="ignore", invalid="ignore"):
            model_input = transformed.astype(np.float32)
        if not np.isfinite(model_input).all():
            raise ValueError("float32 transformed values are non-finite")
        return model_input
