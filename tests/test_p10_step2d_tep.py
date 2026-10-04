"""Fail-closed range retrieval, observation isolation and evaluator boundaries."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from p10_step2d_tep_inspect import OfficialRangeFile, observations, evaluator_states, sha256


class TestTEP(unittest.TestCase):
    def info(self):
        return {'download_url':'https://ndownloader.figshare.com/files/26003087','id':26003087,'size':65536}

    def response(self, status=206, content_range='bytes 0-65535/65536'):
        r=Mock();r.status_code=status;r.headers={'Content-Range':content_range};r.raw=io.BytesIO(b'x'*65536)
        r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False)
        return r

    def test_exact_range_and_hash_cache(self):
        with tempfile.TemporaryDirectory() as d:
            session=Mock();session.get.return_value=self.response()
            f=OfficialRangeFile(self.info(),d,session)
            self.assertEqual(f.read(5),b'xxxxx')
            self.assertEqual(f.transferred,65536)
            self.assertEqual(json.loads((Path(d)/'hashes.json').read_text())['0-65535.bin'],sha256(b'x'*65536))
            f.seek(65536);self.assertEqual(f.read(1),b'')
            (Path(d)/'0-65535.bin').write_bytes(b'y'*65536)
            with self.assertRaisesRegex(ValueError,'hash mismatch'):OfficialRangeFile(self.info(),d,session)

    def test_whole_file_or_wrong_range_refused_without_body_read(self):
        for status,cr in [(200,'bytes 0-65535/65536'),(206,'bytes 1-65536/65536')]:
            with tempfile.TemporaryDirectory() as d:
                r=self.response(status,cr);session=Mock();session.get.return_value=r
                f=OfficialRangeFile(self.info(),d,session)
                with self.assertRaisesRegex(ValueError,'range refused'):f.read(1)
                self.assertEqual(r.raw.tell(),0)
                self.assertFalse(list(Path(d).glob('*.bin')))

    def test_unknown_source_and_oversized_read_refused(self):
        with tempfile.TemporaryDirectory() as d:
            info=self.info();info['download_url']='https://mirror.example/file'
            with self.assertRaises(ValueError):OfficialRangeFile(info,d)
            f=OfficialRangeFile({**self.info(),'size':30000000},d)
            with self.assertRaises(ValueError):f.read()
            with self.assertRaises(ValueError):f.seek(-1)

    def test_policy_observation_channels_exclude_time_and_meta(self):
        data=np.arange(4*54,dtype=float).reshape(4,54);data[:,0]=np.arange(4)*.05
        t,x=observations(data)
        self.assertEqual(x.shape,(4,53));np.testing.assert_array_equal(t,data[:,0])
        np.testing.assert_array_equal(x,data[:,1:])
        data[:,1:]=999;self.assertNotEqual(x[0,0],999)
        # No mode/seed/fault-path metadata argument exists at the policy adapter boundary.
        with self.assertRaises(TypeError):observations(data,seed=21812)

    def test_order_and_finite_fail_closed(self):
        data=np.zeros((4,54));data[:,0]=np.arange(4)*.05
        for change in ('nan','order','cadence'):
            x=data.copy()
            if change=='nan':x[1,3]=np.nan
            if change=='order':x[2,0]=x[1,0]
            if change=='cadence':x[3,0]=.2
            with self.assertRaises(ValueError):observations(x)

    def test_half_open_transition_end_is_not_settling(self):
        t=np.array([0.,1.,29.95,30.,39.95,40.,50.])
        x=evaluator_states(t,start=30,duration=10,kind='transition',warmup_end=1,axes_verified=True)
        self.assertEqual(x.tolist(),['WARMUP_EXCLUDED','NORMAL_A','NORMAL_A','TRANSITION','TRANSITION','POST_RAMP_UNVERIFIED','POST_RAMP_UNVERIFIED'])
        y=evaluator_states(t,start=30,duration=10,kind='transition',warmup_end=1,axes_verified=True,settled_at=50)
        self.assertEqual(y[-1],'NORMAL_B');self.assertEqual(y[-2],'POST_RAMP_UNVERIFIED')
        with self.assertRaises(ValueError):evaluator_states(t,start=30,duration=10,kind='transition',warmup_end=1,axes_verified=True,settled_at=35)

    def test_fault_start_inclusive_without_future_endpoint(self):
        x=evaluator_states([29.95,30,100],start=30,duration=0,kind='fault',warmup_end=1,axes_verified=True)
        self.assertEqual(x.tolist(),['NORMAL_A','FAULT','FAULT'])

    def test_unknown_warmup_axes_or_shutdown_never_claim_normal(self):
        for kw in ({'axes_verified':False,'warmup_end':1},{'axes_verified':True,'warmup_end':None},{'axes_verified':True,'warmup_end':1,'stopped':True}):
            x=evaluator_states([0,30,40,100],start=30,duration=10,kind='transition',**kw)
            self.assertEqual(set(x),{'UNKNOWN'})

    def test_checked_artifact_matches_pre_array_selection(self):
        root=Path(__file__).resolve().parents[1]/'research/writable_neural_memory_p10/step2d'
        inspection=json.loads((root/'inspection.json').read_text())
        self.assertEqual(inspection['selection_sha256'],sha256((root/'selection.json').read_bytes()))
        self.assertEqual(inspection['detector_runs'],0)
        self.assertEqual(inspection['scaler_fits'],0)
        self.assertFalse(inspection['policy_metadata_input'])
        self.assertEqual(sum('smoke' in x for x in inspection['runs']),2)
        self.assertFalse(inspection['acquisition']['whole_file_hash_verified'])
        self.assertLess(inspection['acquisition']['cached_bytes'],64*1024**2)


if __name__=='__main__':unittest.main()
