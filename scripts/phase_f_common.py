"""Frozen Phase F observation-only models, guards, data and execution settings."""
import contextlib
import hashlib
import json
import random
import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
from phase_e2_common import ROOT, PIN, configure as e2_configure, native, sha, tensor_hash, model_hash

sys.path.insert(0, str(ROOT))
CONFIG = json.loads((ROOT/'configs/phase_f.json').read_text())
REPORT = ROOT/'reports/phase_f'
DATA = ROOT/'data/phase_f'

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def configure():
    e2_configure()
    torch.backends.cudnn.allow_tf32 = True
    actual = dict(cudnn_deterministic=torch.backends.cudnn.deterministic,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        matmul_precision=torch.get_float32_matmul_precision(),
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_allow_tf32=torch.backends.cudnn.allow_tf32, torch_threads=torch.get_num_threads())
    assert actual == CONFIG['backend_state']
    return dict(**actual, torch=torch.__version__, cuda=torch.version.cuda,
        cudnn=torch.backends.cudnn.version(), device=torch.cuda.get_device_name(),
        uuid=str(torch.cuda.get_device_properties(0).uuid), python=sys.version,
        upstream_commit=PIN, config_sha256=sha(ROOT/'configs/phase_f.json'))

def seed_all(seed):
    if seed not in CONFIG['detector_seeds']:
        raise ValueError('Unregistered detector seed')
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)

class MatchedLSTM(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.input_projection = torch.nn.Linear(8,38)
        self.encoder = torch.nn.ModuleList([torch.nn.LSTM(38,38,batch_first=True) for _ in range(3)])
        self.decoder = torch.nn.ModuleList([torch.nn.LSTM(38,38,batch_first=True) for _ in range(3)])
        self.gelu = torch.nn.GELU()
        self.output_projection = torch.nn.Linear(38,8)

    def forward(self, x):
        x = self.input_projection(x)
        for layer in (*self.encoder, *self.decoder):
            x, _ = layer(x)  # Native implicit fresh zero h/c, never cross-window state.
        return self.output_projection(self.gelu(x))

def build(architecture, seed):
    seed_all(seed)
    if architecture == 'lstm':
        model = MatchedLSTM()
    elif architecture == 'xlstm':
        original = native.create_config
        def fp32(*args, **kwargs):
            cfg = original(*args, **kwargs)
            assert cfg.slstm_block.slstm.backend == 'vanilla'
            for name in ('dtype','dtype_b','dtype_r','dtype_w','dtype_g','dtype_s','dtype_a'):
                setattr(cfg.slstm_block.slstm, name, 'float32')
            return cfg
        with patch.object(native, 'create_config', fp32):
            model = native.xLSTMAD(embedding_dim=40,features_no=8,window_size=64,lr=.001,slstm_backend='vanilla')
    else:
        raise ValueError('Unregistered architecture')
    assert sum(p.numel() for p in model.parameters()) == CONFIG['parameters'][architecture]
    return model.float().cuda()

@contextlib.contextmanager
def forbid_native_predict():
    """Fail closed even if a future common-path caller accidentally uses predict."""
    with patch.object(native.xLSTMAD, 'predict_step', side_effect=RuntimeError('Native predict_step forbidden in scientific common path')) as trap:
        yield trap
        if trap.call_count:
            raise RuntimeError('Scientific common path attempted native predict_step')

def reconstruction_loss(model, observations):
    return (model(observations)-observations).square().mean()

def score(model, observations):
    return (model(observations)-observations).square().mean((1,2))

def optimizer(model):
    settings = dict(CONFIG['optimizer']); settings['betas'] = tuple(settings['betas'])
    return torch.optim.Adam(model.parameters(), **settings)

def recurrent_name(name):
    return 'weight_hh' in name or '_recurrent_kernel' in name

def allowed_prefix(source):
    """No truth fields are accessed. Reject test seeds before generator invocation."""
    if source not in CONFIG['train_sources']+CONFIG['validation_sources']:
        raise ValueError('Phase F forbids this source')
    from m0.synthetic import generate
    return np.array(generate(source,'stationary','none').observations[:4096], copy=True)

def prepare():
    DATA.mkdir(parents=True, exist_ok=False)
    records=[]
    for source in CONFIG['train_sources']+CONFIG['validation_sources']:
        raw=allowed_prefix(source)
        assert raw.shape==(4096,8) and np.isfinite(raw).all()
        mean=raw.mean(0); std=raw.std(0,ddof=0); scale=np.where(std==0,1.,std)
        transformed=((raw-mean)/scale).astype(np.float32)
        directory=DATA/'prefixes'/str(source); directory.mkdir(parents=True)
        np.save(directory/'raw.npy',raw,allow_pickle=False)
        np.save(directory/'observations.npy',transformed,allow_pickle=False)
        write_json(directory/'scaler.json',dict(mean=mean.tolist(),population_std=std.tolist(),scale=scale.tolist(),fit=[0,4096]))
        records.append(dict(source=source,fold='train' if source in CONFIG['train_sources'] else 'validation',
            shape=list(raw.shape),windows=4033,interval=[0,4096],scenario='stationary',condition='none',
            artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(directory.iterdir())}))
    orders={}
    for seed in CONFIG['detector_seeds']:
        arr=np.stack([np.random.default_rng(np.random.SeedSequence([seed,e,1701])).permutation(40330) for e in range(50)])
        assert arr.shape==(50,40330) and all(np.array_equal(np.sort(row),np.arange(40330)) for row in arr)
        path=DATA/f'orders_{seed}.npy'; np.save(path,arr,allow_pickle=False)
        orders[str(seed)]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),
            epoch_sha256=[hashlib.sha256(row.tobytes()).hexdigest() for row in arr])
    write_json(REPORT/'preprocessing_manifest.json',dict(sources=records,orders=orders,
        generator_sha256=sha(ROOT/'m0/synthetic.py'),correlation_sha256=sha(ROOT/'m0/correlation.py'),
        generator_config_sha256=sha(ROOT/'configs/synthetic_v1.json'),config_sha256=sha(ROOT/'configs/phase_f.json'),
        train_windows=40330,validation_windows=20165,labels_read=False,test_sources_used=False))

def load_windows(fold):
    sources=CONFIG['train_sources' if fold=='train' else 'validation_sources']
    manifest=json.loads((REPORT/'preprocessing_manifest.json').read_text())
    windows=[]
    for record in manifest['sources']:
        if record['source'] not in sources: continue
        for path,digest in record['artifacts'].items(): assert sha(ROOT/path)==digest
        obs=torch.from_numpy(np.load(DATA/'prefixes'/str(record['source'])/'observations.npy',allow_pickle=False))
        windows.append(obs.unfold(0,64,1).permute(0,2,1).contiguous())
    result=torch.cat(windows).cuda()
    assert result.shape==(len(sources)*4033,64,8)
    return result

if __name__ == '__main__': prepare()
