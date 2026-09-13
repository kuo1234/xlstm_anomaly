"""Phase F-v3: scoped cuDNN-off execution for matched nn.LSTM only."""
import contextlib
import json
import sys
from pathlib import Path
import torch
import phase_f_v2_common as v2

ROOT=v2.ROOT; CONFIG=json.loads((ROOT/'configs/phase_f_v3.json').read_text()); REPORT=ROOT/'reports/phase_f_v3'; DATA=v2.DATA
native=v2.native; PIN=v2.PIN; sha=v2.sha; tensor_hash=v2.tensor_hash; model_hash=v2.model_hash
recurrent_name=v2.recurrent_name; reconstruction_loss=v2.reconstruction_loss; score=v2.score
forbid_native_predict=v2.forbid_native_predict; seed_all=v2.seed_all; load_windows=v2.load_windows
verify_sealed_inputs=v2.verify_sealed_inputs; backend_fingerprint=v2.backend_fingerprint

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def configure():
    environment=v2.configure()
    assert environment['cudnn_allow_tf32'] is False
    environment['matched_lstm_cudnn_scope']='only inside MatchedLSTM.forward'; environment['matched_lstm_cudnn_enabled']=False
    environment['config_sha256']=sha(ROOT/'configs/phase_f_v3.json')
    return environment

class MatchedLSTM(torch.nn.Module):
    """Same H38 architecture/parameter names; only recurrent execution scope changes."""
    def __init__(self):
        super().__init__()
        self.input_projection=torch.nn.Linear(8,38)
        self.encoder=torch.nn.ModuleList([torch.nn.LSTM(38,38,batch_first=True) for _ in range(3)])
        self.decoder=torch.nn.ModuleList([torch.nn.LSTM(38,38,batch_first=True) for _ in range(3)])
        self.gelu=torch.nn.GELU(); self.output_projection=torch.nn.Linear(38,8)
        self.last_cudnn_enabled=None

    def forward(self,x):
        x=self.input_projection(x)
        with torch.backends.cudnn.flags(enabled=False,benchmark=False,deterministic=True,allow_tf32=False):
            self.last_cudnn_enabled=torch.backends.cudnn.enabled
            for layer in (*self.encoder,*self.decoder):
                x,_=layer(x)
        return self.output_projection(self.gelu(x))

def build(architecture,seed):
    seed_all(seed)
    if architecture=='lstm': model=MatchedLSTM()
    elif architecture=='xlstm': return v2.build('xlstm',seed)
    else: raise ValueError('Unregistered architecture')
    assert sum(p.numel() for p in model.parameters())==CONFIG['parameters']['lstm']
    return model.float().cuda()

def optimizer(model): return v2.optimizer(model)

def canary_input():
    generator=torch.Generator(device='cuda').manual_seed(CONFIG['canary']['seed'])
    return torch.randn(*CONFIG['canary']['shape'],device='cuda',generator=generator)
