"""CPU-only negative controls for backend/canary validation, not model runs."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import phase_d_v2 as v2


class BackendChecks(unittest.TestCase):
    def fake_torch(self,settings):
        return SimpleNamespace(backends=SimpleNamespace(
            cudnn=SimpleNamespace(deterministic=settings['cudnn_deterministic'],
                benchmark=settings['cudnn_benchmark'],allow_tf32=settings['cudnn_allow_tf32']),
            cuda=SimpleNamespace(matmul=SimpleNamespace(allow_tf32=settings['matmul_allow_tf32']))),
            are_deterministic_algorithms_enabled=lambda:settings['deterministic_algorithms'],
            get_float32_matmul_precision=lambda:settings['float32_matmul_precision'])

    def test_exact_accepted_backend(self):
        with patch.object(v2,'torch',self.fake_torch(v2.EXPECTED)):
            v2.assert_backend()

    def test_every_flag_change_fails_closed(self):
        for key in ('cudnn_deterministic','cudnn_benchmark','deterministic_algorithms',
                    'float32_matmul_precision','matmul_allow_tf32','cudnn_allow_tf32'):
            bad=dict(v2.EXPECTED)
            bad[key]='medium' if key=='float32_matmul_precision' else not bad[key]
            with self.subTest(key=key),patch.object(v2,'torch',self.fake_torch(bad)):
                with self.assertRaises(AssertionError):v2.assert_backend()

    def test_seal_tampering_rejected(self):
        with patch.object(v2,'torch',self.fake_torch(v2.EXPECTED)),patch.object(v2,'digest',return_value='tampered'):
            with self.assertRaises(AssertionError):v2.assert_backend()

    def test_canary_rejects_every_behavior_mutation(self):
        keys=('pre','buffer_sha256','losses','trainable_tensor_hashes','model_sha256',
            'optimizer_sha256','rng_sha256','scores_tensor_sha256','backend_fingerprint')
        reference={k:'original' for k in keys}
        for key in keys:
            changed=copy.deepcopy(reference);changed[key]='changed'
            self.assertNotEqual(v2.behavior(reference),v2.behavior(changed),key)

    def test_canary_ignores_only_diagnostics(self):
        reference={k:'same' for k in ('pre','buffer_sha256','losses','trainable_tensor_hashes','model_sha256',
            'optimizer_sha256','rng_sha256','scores_tensor_sha256','backend_fingerprint')}
        changed=dict(reference,runtime_seconds=999,evaluator_label_sha256='permuted',tag='another_process')
        self.assertEqual(v2.behavior(reference),v2.behavior(changed))


if __name__=='__main__':unittest.main(verbosity=2)
