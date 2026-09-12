"""Frozen D8 MLP training on source-disjoint normal prefixes only."""
import copy
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader,TensorDataset
from sklearn.preprocessing import StandardScaler
from phase_d_operator import ROOT,REPORT,DATA,OFFICIAL,authorize,rng_state,restore_rng,object_hash,tensor_hash,SANA
from phase_c_run import digest,state_hash
sys.path.insert(0,str(ROOT))
from m0.synthetic import generate
from config import get_cfg_defaults
from models.mlp.modeling_mlp import MLP
from models.mlp.trainer_mlp import MLPTrainer
from models.optimizer import construct_optimizer,get_epoch_lr,set_lr
from utils.misc import set_seeds

SEEDS=[11,22,33,44,55]


def config(seed):
    cfg=get_cfg_defaults()
    reference=json.loads((ROOT/'reports/phase_c_v2/runs/SMD_1-8_alpha_5.0_seed_0_native_label_control.json').read_text())
    cfg.merge_from_other_cfg(type(cfg).load_cfg(reference['resolved_config']))
    cfg.SEED=seed; cfg.DATA.NAME='synthetic_D8'; cfg.DATA.N_VAR=8
    cfg.TIMESNET.enc_in=8; cfg.TIMESNET.c_out=8
    cfg.TRAIN.ENABLE=True; cfg.TRAIN.SHUFFLE=True; cfg.TRAIN.DROP_LAST=True
    cfg.RESULT_DIR=str(DATA/f'backbone_{seed}'); cfg.TRAIN.CHECKPOINT_DIR=cfg.RESULT_DIR
    return cfg


def windows(x):
    return np.ascontiguousarray(np.lib.stride_tricks.sliding_window_view(x,10,axis=0).transpose(0,2,1),dtype=np.float32)


@torch.no_grad()
def score(model,x):
    return torch.cat([model.get_anomaly_scores(x[i:i+256].cuda()).cpu() for i in range(0,len(x),256)]).numpy()


def train(seed):
    authorize()
    assert json.loads((REPORT/'operator_parity.json').read_text())['status']=='PASS'
    assert seed in SEEDS
    directory=DATA/f'backbone_{seed}'; directory.mkdir(parents=True,exist_ok=False)
    t=time.perf_counter()
    train_sources=[generate(s,'stationary','none') for s in range(1000,1010)]
    val_sources=[generate(s,'stationary','none') for s in range(2000,2005)]
    scaler=StandardScaler().fit(np.concatenate([s.observations[:4096] for s in train_sources]))
    xt=torch.from_numpy(np.concatenate([windows(scaler.transform(s.observations[:4096])) for s in train_sources]))
    xv=torch.from_numpy(np.concatenate([windows(scaler.transform(s.observations[:4096])) for s in val_sources]))
    xc=torch.from_numpy(np.concatenate([windows(scaler.transform(s.observations[4096:5120])) for s in train_sources]))
    provenance=dict(train_seeds=list(range(1000,1010)),validation_seeds=list(range(2000,2005)),fit_interval=[0,4096],
        calibration_interval=[4096,5120],train_array_sha256=tensor_hash(xt),validation_array_sha256=tensor_hash(xv),
        calibration_array_sha256=tensor_hash(xc),scaler_mean=scaler.mean_.tolist(),scaler_scale=scaler.scale_.tolist(),scaler_var=scaler.var_.tolist())
    cfg=config(seed); set_seeds(seed)
    torch.cuda.reset_peak_memory_stats()
    model=MLP(cfg).cuda(); optimizer=construct_optimizer(model,cfg)
    trainer=object.__new__(MLPTrainer); trainer.model=model; trainer.optimizer=optimizer; trainer.cfg=cfg
    loader=DataLoader(TensorDataset(xt,torch.zeros(len(xt))),batch_size=256,shuffle=True,drop_last=True,num_workers=0)
    best=float('inf'); history=[]
    train_start=time.perf_counter()
    for epoch in range(30):
        model.train(); losses=[]
        for i,inputs in enumerate(loader):
            set_lr(optimizer,get_epoch_lr(epoch+(i+1)/len(loader),cfg))
            out=trainer.train_step(inputs); losses.append(float(out['losses'][0].detach()))
        row=dict(epoch=epoch+1,train_mse=float(np.mean(losses)))
        if (epoch+1)%5==0:
            model.eval()
            with torch.no_grad():
                total=0.
                for i in range(0,len(xv),256):
                    x=xv[i:i+256].cuda(); total+=float(F.mse_loss(model(x),x,reduction='sum'))
                val=total/xv.numel()
            row['validation_mse']=val
            if val<best:
                best=val; best_epoch=epoch+1
                torch.save(dict(model_state=model.state_dict(),optimizer_state=optimizer.state_dict(),cfg=cfg.dump(),epoch=best_epoch),directory/'checkpoint_best.pth')
        history.append(row)
    torch.cuda.synchronize(); training_seconds=time.perf_counter()-train_start
    checkpoint=torch.load(directory/'checkpoint_best.pth',weights_only=False)
    model.load_state_dict(checkpoint['model_state'])
    backbone_hash=state_hash(model)
    cfg.TRAIN.ENABLE=False; model.eval()
    set_seeds(seed)
    for p in model.parameters(): p.requires_grad=False
    model.sana_in=SANA(cfg).cuda(); model.sana_out=SANA(cfg).cuda()
    adapt_cfg=cfg.clone(); adapt_cfg.SOLVER=adapt_cfg.TEST.TTA.SOLVER
    opt=construct_optimizer(model,adapt_cfg)
    pre_rng=rng_state()
    calibration=score(model,xc)
    assert np.isfinite(calibration).all()
    threshold=float(np.quantile(calibration,.95))
    restore_rng(pre_rng)
    state=dict(model_state=model.state_dict(),optimizer_state=opt.state_dict(),rng=pre_rng,cfg=cfg.dump(),
        threshold=threshold,scaler=provenance,backbone_sha256=backbone_hash)
    torch.save(state,directory/'pre_intervention.pth')
    np.save(directory/'calibration_scores.npy',calibration,allow_pickle=False)
    manifest=dict(detector_seed=seed,best_epoch=best_epoch,history=history,training_seconds=training_seconds,
        total_seconds=time.perf_counter()-t,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),resolved_config=cfg.dump(),preprocessing=provenance,
        backbone_tensor_sha256=backbone_hash,initial_model_sha256=state_hash(model),
        sana_in_sha256=state_hash(model.sana_in),sana_out_sha256=state_hash(model.sana_out),
        optimizer_sha256=object_hash(opt.state_dict()),rng_sha256=object_hash(pre_rng),threshold=threshold,
        artifacts={str(p.relative_to(ROOT)):digest(p) for p in directory.iterdir() if p.is_file()},
        authorized_test_sources_used=False,architecture='Official MLP 80-40-20-128-20-40-80; reconstruction MSE')
    (REPORT/f'backbone_{seed}.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ('detector_seed','best_epoch','training_seconds','total_seconds','initial_model_sha256')}),flush=True)
    return manifest


def main():
    seed=int(sys.argv[1])
    train(seed)


if __name__=='__main__': main()
