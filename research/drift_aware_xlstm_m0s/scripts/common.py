"""Shared protocol, provenance and observation-only helpers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
CONFIG = ROOT / 'configs/protocol.json'


def load_config():
    return json.loads(CONFIG.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_hash(x):
    x = np.ascontiguousarray(x)
    return hashlib.sha256(str((x.dtype.str, x.shape)).encode() + x.tobytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def configure():
    if load_config()['model']['device']=='cpu':
        assert not torch.cuda.is_available(), 'CPU protocol requires CUDA_VISIBLE_DEVICES empty before import'
    torch.set_num_threads(load_config()['training']['threads'])
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.set_float32_matmul_precision('highest')


def state_leaves(obj, prefix=''):
    if isinstance(obj, torch.Tensor):
        return {prefix: obj}
    if isinstance(obj, dict):
        return {p: t for k, v in obj.items() for p, t in state_leaves(v, prefix+'/'+str(k)).items()}
    if isinstance(obj, (tuple, list)):
        return {p: t for k, v in enumerate(obj) for p, t in state_leaves(v, prefix+'/'+str(k)).items()}
    return {}


def tensor_tree_hash(obj):
    h = hashlib.sha256()
    for key, tensor in sorted(state_leaves(obj).items()):
        h.update(key.encode())
        h.update(array_hash(tensor.detach().cpu().numpy()).encode())
    return h.hexdigest()


def model_hash(model):
    return tensor_tree_hash({'parameters': dict(model.named_parameters()), 'buffers': dict(model.named_buffers())})


def verify_freeze():
    """Fail closed unless committed protocol and upstream sources match the remote seal."""
    seal_path = Path(os.environ.get('M0S_FREEZE_SEAL', ROOT/'provenance/remote_freeze.json'))
    seal = json.loads(seal_path.read_text())
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip() == seal['commit'], 'wrong frozen checkout'
    for relative, digest in seal['files'].items():
        assert sha(REPO/relative) == digest, 'frozen file changed: '+relative
    import xlstm
    base = Path(xlstm.__file__).parent
    for relative, digest in json.loads((ROOT/'provenance/xlstm_source_hashes.json').read_text()).items():
        assert sha(base/relative) == digest, 'xlstm source mismatch: '+relative
    assert subprocess.check_output(['git','status','--porcelain','--',str(ROOT/'configs'),str(ROOT/'scripts'),str(ROOT/'tests')],cwd=REPO,text=True).strip() == ''
    return seal
