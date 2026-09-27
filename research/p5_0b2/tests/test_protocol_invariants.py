import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class ProtocolInvariantTests(unittest.TestCase):
    def test_protocol_validator_accepts_the_review_candidate(self):
        result = subprocess.run(
            [sys.executable, "-m", "research.p5_0b2.scripts.validate_protocol"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "PROTOCOL_VALIDATION_PASS\n")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
