import unittest
from m0.correlation import verify


class CorrelationTests(unittest.TestCase):
    def test_all_protocol_invariants(self):
        self.assertGreaterEqual(verify()['correlation_difference'], .2)

    def test_fixed_permutations(self):
        for seed in (11,22,33,44,55):
            with self.subTest(seed=seed):
                verify(seed)
