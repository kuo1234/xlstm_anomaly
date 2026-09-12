"""Paired single-update H1 experiment; fail-closed parity/manifest/compute gates."""
import copy
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import numpy as np
import torch
from phase_d_operator import ROOT,REPORT,DATA,authorize,update,restore_rng,object_hash,tensor_hash,SANA
from phase_d_backbone import SEEDS,config,MLP,construct_optimizer,score
from phase_d_buffers import SCENARIOS,TYPES,CS,compose
from phase_c_run import digest,state_hash
from m0.metrics import metrics


def load(seed):
    p=DATA/f'backbone_{seed}/pre_intervention.pth'
    state=torch.load(p,weights_only=False)
    cfg=config(seed); cfg.TRAIN.ENABLE=False
    model=MLP(cfg).cuda()
    for x in model.parameters(): x.requires_grad=False
    model.sana_in=SANA(cfg).cuda(); model.sana_out=SANA(cfg).cuda(); model.eval()
    cfg.SOLVER=cfg.TEST.TTA.SOLVER
    optimizer=construct_optimizer(model,cfg)
    return SimpleNamespace(model=model,cfg=cfg,optimizer=optimizer),state


def reset(adapter,state):
    adapter.model.load_state_dict(state['model_state'])
    adapter.optimizer.load_state_dict(copy.deepcopy(state['optimizer_state']))
    adapter.model.eval(); restore_rng(state['rng'])
    assert state_hash(adapter.model)==object_model_hash(state)
    assert object_hash(adapter.optimizer.state_dict())==object_hash(state['optimizer_state'])


def object_model_hash(state):
    if '_model_hash' not in state:
        import hashlib
        h=hashlib.sha256()
        for k,t in sorted(state['model_state'].items()):
            a=t.detach().cpu().contiguous().numpy()
            h.update(k.encode()+str(a.dtype).encode()+str(a.shape).encode()+a.tobytes())
        state['_model_hash']=h.hexdigest()
    return state['_model_hash']


def run(source,scenario,condition,seed):
    tag=f'{source}_{scenario}_{condition}_{seed}'
    path=REPORT/'rows'/f'{tag}.json'
    assert not path.exists()
    start=time.perf_counter()
    arms,x,y,primary,manifest=compose(source,scenario,condition)
    sealed=json.loads((REPORT/'buffer_manifest.json').read_text())['rows']
    assert manifest==next(m for m in sealed if (m['source'],m['scenario'],m['condition'])==(source,scenario,condition))
    adapter,state=load(seed)
    mean=np.array(state['scaler']['scaler_mean']); scale=np.array(state['scaler']['scaler_scale'])
    test=torch.from_numpy(np.ascontiguousarray((x-mean)/scale,dtype=np.float32))
    directory=DATA/'grid'/tag; directory.mkdir(parents=True,exist_ok=False)
    result=[]; baseline_scores=None
    for c in [None,*CS]:
        reset(adapter,state)
        torch.cuda.reset_peak_memory_stats(); before=time.perf_counter()
        losses=[]
        if c is not None:
            buffer=torch.from_numpy(np.ascontiguousarray((arms[c]-mean)/scale,dtype=np.float32)).cuda()
            losses=update(adapter,buffer)
        scores=score(adapter.model,test)
        torch.cuda.synchronize()
        assert np.isfinite(scores).all()
        if c is None: baseline_scores=scores.copy()
        m=metrics(y[primary],scores[primary],state['threshold'])
        assert m['ap'] is not None
        diff=0.
        for k,p in adapter.model.named_parameters():
            if p.requires_grad: diff+=float(torch.sum((p-state['model_state'][k])**2))
            else: assert torch.equal(p,state['model_state'][k])
        name='no_update' if c is None else str(c)
        np.save(directory/f'scores_{name}.npy',scores,allow_pickle=False)
        row=dict(source=source,scenario=scenario,condition=condition,detector_seed=seed,c=c,
            metrics=m,stress_metrics=metrics(y[~primary],scores[~primary],state['threshold']),
            clean_normal_fpr=m['fpr'],fixed_threshold=state['threshold'],parameter_delta_l2=diff**.5,
            update_losses=losses,optimizer_steps=len(losses),loss_exposures=100*len(losses),
            anomalous_loss_exposures=0 if c is None else c*len(losses),
            score_summary=dict(mean=float(scores[primary].mean()),std=float(scores[primary].std()),
                quantiles=np.quantile(scores[primary],[0,.25,.5,.75,.95,1]).tolist(),
                mean_delta_vs_no_update=float((scores[primary]-baseline_scores[primary]).mean()),
                mean_abs_delta_vs_no_update=float(np.abs(scores[primary]-baseline_scores[primary]).mean())),
            buffer_sha256=None if c is None else manifest['arms'][str(c)]['buffer_sha256'],
            pre_model_sha256=object_model_hash(state),pre_optimizer_sha256=object_hash(state['optimizer_state']),
            pre_rng_sha256=object_hash(state['rng']),final_model_sha256=state_hash(adapter.model),
            score_path=str((directory/f'scores_{name}.npy').relative_to(ROOT)),
            score_sha256=digest(directory/f'scores_{name}.npy'),runtime_seconds=time.perf_counter()-before,
            peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved())
        result.append(row)
    output=dict(tag=tag,rows=result,total_seconds=time.perf_counter()-start)
    path.parent.mkdir(exist_ok=True); path.write_text(json.dumps(output,indent=2)+'\n')
    print(tag,'seconds',output['total_seconds'],flush=True)
    return output


def check():
    assert not (REPORT/'execution_stop.json').exists(), 'Phase D stopped: versioned repair and review required; do not resume quarantined grid'
    authorize()
    assert json.loads((REPORT/'operator_parity.json').read_text())['status']=='PASS'
    manifest=json.loads((REPORT/'synthetic_backbone_manifest.json').read_text())
    assert [r['detector_seed'] for r in manifest['rows']]==SEEDS
    for r in manifest['rows']:
        for p,h in r['artifacts'].items(): assert digest(ROOT/p)==h
    import subprocess
    # Full backbone/buffer seals must already have been committed/pushed.
    for name in ('synthetic_backbone_manifest.json','buffer_manifest.json'):
        assert subprocess.check_output(['rtk','git','show',f'origin/main:reports/phase_d/{name}'])==(REPORT/name).read_bytes()


def main():
    check()
    if sys.argv[1]=='dry':
        r=run(3000,'abrupt','spike',11)
        training=sum(json.loads((REPORT/f'backbone_{s}.json').read_text())['total_seconds'] for s in SEEDS)
        estimated=training+2*r['total_seconds']*800
        data=dict(dry_run=r['tag'],dry_seconds=r['total_seconds'],estimated_total_seconds=estimated,
            conservative_factor=2,remaining_pairs=799,limit_seconds=24*3600,
            status='PASS' if estimated<=24*3600 else 'STOP_COMPUTE_REVIEW',training_seconds=training)
        (REPORT/'compute_preflight.json').write_text(json.dumps(data,indent=2)+'\n')
        print(data,flush=True)
    elif sys.argv[1]=='grid':
        assert json.loads((REPORT/'compute_preflight.json').read_text())['status']=='PASS'
        for source in range(3000,3010):
            for scenario in SCENARIOS:
                for condition in TYPES:
                    for seed in SEEDS:
                        path=REPORT/'rows'/f'{source}_{scenario}_{condition}_{seed}.json'
                        if path.exists():
                            assert len(json.loads(path.read_text())['rows'])==6
                            continue
                        run(source,scenario,condition,seed)
    else: raise ValueError('Unknown mode')


if __name__=='__main__': main()
