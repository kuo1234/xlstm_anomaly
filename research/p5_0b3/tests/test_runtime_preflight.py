"""Pure unit checks for the synthetic runtime preflight contract."""

import importlib.util
import io
from pathlib import Path
from contextlib import redirect_stdout
import unittest
from unittest.mock import patch

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "runtime_preflight.py"
SPEC = importlib.util.spec_from_file_location("runtime_preflight", SCRIPT)
runtime_preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_preflight)


class RuntimePreflightTests(unittest.TestCase):
    def test_frozen_contract_constants(self):
        self.assertEqual(runtime_preflight.PINNED_EFD_COMMIT,
                         "ced470e1386066931bad32f3cb6e24bac9c5bb89")
        self.assertEqual(runtime_preflight.INPUT_DIM, 8)
        self.assertEqual(runtime_preflight.ENCODER, (32, 16))
        self.assertEqual(runtime_preflight.BOTTLENECK, 2)
        self.assertEqual(runtime_preflight.EPOCHS, 100)
        self.assertEqual(runtime_preflight.SEED, 17)
        self.assertEqual(runtime_preflight.N_SAMPLES, 259)
        self.assertEqual(runtime_preflight.NUMPY_VERSION, "1.26.4")
        self.assertEqual(runtime_preflight.TENSORFLOW_VERSION, "2.18.1")
        self.assertEqual(runtime_preflight.PYTHON_VERSION, "3.12.3")

    def test_learning_rate_uses_exact_float32_contract(self):
        contract_value = float(np.float32(0.001))
        adjacent_float32 = float(np.nextafter(np.float32(0.001), np.float32(np.inf)))
        self.assertNotEqual(contract_value, 0.001)
        self.assertTrue(runtime_preflight._learning_rate_matches_contract(contract_value))
        self.assertFalse(runtime_preflight._learning_rate_matches_contract(adjacent_float32))

    def test_synthetic_input_is_byte_repeatable(self):
        left = runtime_preflight._synthetic_input()
        right = runtime_preflight._synthetic_input()
        self.assertEqual(left.dtype, np.float64)
        self.assertEqual(left.shape, (259, 8))
        self.assertEqual(left.tobytes(), right.tobytes())
        self.assertTrue(np.isnan(left).any())

    def test_failure_status_has_no_details(self):
        output = io.StringIO()
        with patch.object(runtime_preflight, "run", side_effect=RuntimeError("private detail")):
            with redirect_stdout(output):
                exit_code = runtime_preflight.main()
        self.assertEqual(exit_code, 1)
        self.assertEqual(output.getvalue(), '{"status":"BLOCKED"}\n')
        self.assertNotIn("private detail", output.getvalue())


if __name__ == "__main__":
    unittest.main()
