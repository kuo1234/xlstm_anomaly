"""Versioned Phase F-v2 backend wrapper; F-v1 implementation remains untouched."""
import contextlib
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
import phase_f_common as v1

ROOT=v1.ROOT
CONFIG=json.loads((ROOT/'configs/phase_f_v2.json').read_text())
REPORT=ROOT/'reports/phase_f_v2'
DATA=v1.DATA  # sealed F-v1 prefixes/orders are intentionally reused, never regenerated
native=v1.native
PIN=v1.PIN
sha=v1.sha
tensor_hash=v1.tensor_hash
model_hash=v1.model_hash
MatchedLSTM=v1.MatchedLSTM
recurrent_name=v1.recurrent_name
reconstruction_loss=v1.reconstruction_loss
score=v1.score
optimizer=v1.optimizer
forbid_native_predict=v1.forbid_native_predict

def backend_fingerprint(state):
    fields=('cudnn_deterministic','cudnn_benchmark','deterministic_algorithms',
            'matmul_precision','matmul_allow_tf32','cudnn_allow_tf32','torch_threads')
    payload=json.dumps({k:state[k] for k in fields},sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(payload).hexdigest()

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def configure():
    # e2_configure sets every accepted E2 flag except this explicit F-v2 change.
    v1.e2_configure()
    torch.backends.cudnn.allow_tf32=False
    actual=dict(cudnn_deterministic=torch.backends.cudnn.deterministic,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        matmul_precision=torch.get_float32_matmul_precision(),
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,torch_threads=torch.get_num_threads())
    assert actual==CONFIG['backend_state']
    assert backend_fingerprint(actual)==CONFIG['backend_fingerprint']
    return dict(**actual,torch=torch.__version__,cuda=torch.version.cuda,
        cudnn=torch.backends.cudnn.version(),device=torch.cuda.get_device_name(),
        uuid=str(torch.cuda.get_device_properties(0).uuid),python=__import__('sys').version,
        upstream_commit=PIN,backend_fingerprint=backend_fingerprint(actual),
        config_sha256=sha(ROOT/'configs/phase_f_v2.json'))

def build(architecture,seed):
    # v1 constructor is reused byte-for-byte; only the process backend is v2.
    return v1.build(architecture,seed)

def seed_all(seed): return v1.seed_all(seed)

def load_windows(fold): return v1.load_windows(fold)

def verify_sealed_inputs():
    manifest=json.loads((ROOT/'reports/phase_f/preprocessing_manifest.json').read_text())
    assert manifest['labels_read'] is False and manifest['test_sources_used'] is False
    for record in manifest['sources']:
        for path,digest in record['artifacts'].items(): assert sha(ROOT/path)==digest,path
    for info in manifest['orders'].values(): assert sha(ROOT/info['path'])==info['sha256'],info['path']
    assert manifest['config_sha256']==sha(ROOT/'configs/phase_f.json')
    return dict(manifest_sha256=sha(ROOT/'reports/phase_f/preprocessing_manifest.json'),
        source_count=len(manifest['sources']),orders=manifest['orders'],
        prefixes_and_scalers_verified=True,orders_verified=True,regenerated=False,
        labels_read=False,test_sources_used=False)

@contextlib.contextmanager
def backend_state(allow_tf32):
    previous=torch.backends.cudnn.allow_tf32
    torch.backends.cudnn.allow_tf32=bool(allow_tf32)
    try: yield
    finally: torch.backends.cudnn.allow_tf32=previous
