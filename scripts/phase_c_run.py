"""Pinned native CANDI entrypoint runner; outputs outside immutable checkout.

Post-predict observation only in native mode. Audit instrumentation is separate.
No backbone training; native author checkpoints and all script hyperparameters.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import runpy
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT/'data/phase_c/official_candi'
REPORT = ROOT/'reports/phase_c'
PIN = '28c9679e503832f59e351208cde63657fcb51cad'
PUBLISHED = {'SMD_1-8': {'0.5':(.872,.432),'1.0':(.872,.434),'5.0':(.867,.423)},
             'SMD_2-1': {'0.5':(.725,.319),'1.0':(.711,.314),'5.0':(.780,.348)}}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state_hash(model):
    h = hashlib.sha256()
    for key,t in sorted(model.state_dict().items()):
        a = t.detach().cpu().contiguous().numpy()
        h.update(key.encode()+str(a.dtype).encode()+str(a.shape).encode()+a.tobytes())
    return h.hexdigest()


def main():
    global REPORT
    parser = argparse.ArgumentParser()
    parser.add_argument('--machine',choices=list(PUBLISHED),required=True)
    parser.add_argument('--alpha',choices=['0.5','1.0','5.0'],required=True)
    parser.add_argument('--mode',choices=['native','audit','audit_permuted','native_replay_1','native_replay_2',
        'native_v2','native_label_control','native_label_permuted','native_c3','native_d0'],default='native')
    parser.add_argument('--seed',type=int,default=0)
    args = parser.parse_args()
    version2 = args.mode.startswith('native_')
    if args.mode=='native_d0':
        assert (args.machine,args.alpha,args.seed)==('SMD_1-8','5.0',0)
        REPORT=ROOT/'reports/phase_d'
        import phase_d_operator
        phase_d_operator.authorize()
        import phase_c_v2
        phase_c_v2.REPORT=REPORT
        phase_c_v2.environment()
    elif args.mode=='native_c3':
        REPORT = ROOT/'reports/phase_c3'
        from phase_c3 import authorize,environment
        authorize(args.machine,args.alpha,args.seed)
        environment()
    elif version2:
        assert args.seed==0
        REPORT = ROOT/'reports/phase_c_v2'
        from phase_c_v2 import authorize,environment
        authorize(args.machine,args.alpha,args.mode)
        environment()
    sys.dont_write_bytecode = True
    sys.path.insert(0,str(OFFICIAL))
    sys.path.insert(0,str(ROOT/'scripts'))
    head = subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'rev-parse','HEAD'],text=True).strip()
    assert head==PIN
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    for machine in json.loads((ROOT/'reports/phase_a/smd_seal.json').read_text()):
        for asset in machine['assets']:
            assert digest(ROOT/asset['path'])==asset['sha256']
            if '/smd_candi/' in asset['path']:
                assert digest(OFFICIAL/'data/ServerMachineDataset/preprocessed'/Path(asset['path']).name)==asset['sha256']
    tag = f'{args.machine}_alpha_{args.alpha}_seed_{args.seed}_{args.mode}'
    work = ROOT/'data/phase_c/runs'/tag
    work.mkdir(parents=True,exist_ok=False)
    (work/'data').symlink_to(OFFICIAL/'data',target_is_directory=True)
    checkpoint_dir = work/'results'/args.machine/'MLP'
    checkpoint_dir.mkdir(parents=True)
    checkpoint = OFFICIAL/'results'/args.machine/'MLP/checkpoint_best.pth'
    if version2:
        expected = {'SMD_1-8':'08ec432dc29275114e132002c4599eae391ff2785287948a4f310be1d4fd881e',
                    'SMD_2-1':'b374a7a9163db506c2f71028fd7c47edb97ada4bdceddc9ffd2e308b246a81a8'}
        assert digest(checkpoint)==expected[args.machine]
    (checkpoint_dir/'checkpoint_best.pth').symlink_to(checkpoint)
    script = OFFICIAL/'scripts'/args.machine/f'{args.machine}_alpha_{args.alpha}.sh'
    argv = shlex.split(script.read_text())[2:]
    if args.seed!=0:
        argv += ['SEED',str(args.seed)]
    os.chdir(work)
    import torch
    import predictor
    if version2:
        import utils.parser
        original_load_config = utils.parser.load_config
        def guarded_config(*a,**kw):
            cfg = original_load_config(*a,**kw)
            assert not cfg.TRAIN.ENABLE and cfg.SEED==args.seed
            return cfg
        utils.parser.load_config = guarded_config
    captured = {}
    original_predict = predictor.Predictor.predict
    def observed_predict(self):
        assert not self.cfg.TRAIN.ENABLE,'Backbone training not authorized in native checkpoint reproduction'
        captured['predictor'] = self
        return original_predict(self)
    predictor.Predictor.predict = observed_predict
    audit = None
    if version2:
        import phase_c_audit
        phase_c_audit.REPORT = REPORT
        from tta.candi import adapter_candi
        audit = phase_c_audit.Audit(args.mode,tag)
        audit.instrument(adapter_candi,predictor)
        if args.mode=='native_d0':
            capture=phase_d_operator.Capture()
            capture.install(predictor,adapter_candi)
    elif args.mode!='native':
        from phase_c_audit import Audit
        audit = Audit(args.mode,tag)
        audit.install(predictor)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    start_event,end_event = torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
    start_event.record()
    start = time.perf_counter()
    sys.argv = [str(OFFICIAL/'main.py'),*argv]
    print('OFFICIAL_ENTRYPOINT',shlex.join(sys.argv),flush=True)
    error = None
    try:
        runpy.run_path(str(OFFICIAL/'main.py'),run_name='__main__')
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
        import traceback
        traceback.print_exc()
    end_event.record()
    torch.cuda.synchronize()
    runtime = time.perf_counter()-start
    record = dict(tag=tag,machine=args.machine,alpha=args.alpha,seed=args.seed,mode=args.mode,
        official_commit=PIN,official_script=str(script.relative_to(OFFICIAL)),script_sha256=digest(script),
        command=shlex.join([str(Path(sys.executable)),str(ROOT/'scripts/phase_c_run.py'),
                           '--machine',args.machine,'--alpha',args.alpha,'--mode',args.mode,'--seed',str(args.seed)]),
        native_argv=sys.argv,working_directory=str(work),checkpoint_sha256=digest(checkpoint),
        runtime_seconds=runtime,cuda_event_span_ms=start_event.elapsed_time(end_event),
        peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),
        memory_note='PyTorch peak allocator statistics; GB10 nvidia-smi device memory accounting unsupported',
        cuda_time_note='Event span includes host gaps; not a sum of active GPU kernel durations',error=error)
    if error is None:
        p = captured['predictor']
        pred = p.test_scores_w_tta>p.thresholder.threshold
        observed = p.get_results(p.test_scores_w_tta,p.test_labels,pred)
        auroc,pr = PUBLISHED[args.machine][args.alpha]
        record.update(published=dict(AUROC=auroc,AUPRC=pr),observed=observed,
            discrepancy=dict(AUROC=abs(observed['AUROC']-auroc),AUPRC=abs(observed['AUPRC']-pr)),
            status='PASS' if abs(observed['AUROC']-auroc)<=.02 and abs(observed['AUPRC']-pr)<=.02 else 'INVESTIGATE',
            resolved_config=p.cfg.dump(),native_threshold=float(p.thresholder.threshold),
            final_model_sha256=state_hash(p.model),native_window_count=len(p.test_labels),
            official_counters={k:int(getattr(p.adapter,k)) for k in ('iter','n_adapt','total_samples_to_adapt_hard','total_anomalies_in_hard',
               'total_samples_to_adapt_moderate','total_anomalies_in_moderate','n_samples_to_adapt_hard','n_samples_to_adapt_moderate')},
            artifact_hashes={str(q.relative_to(work)):digest(q) for q in sorted((checkpoint_dir/args.alpha).glob('*')) if q.is_file()})
        torch.save(p.model.state_dict(),work/'final_model.pth')
        record['final_checkpoint_sha256'] = digest(work/'final_model.pth')
        if audit:
            record['audit'] = audit.finish(p)
            if args.mode=='native_d0':
                capture.verify(audit)
        if version2:
            import numpy as np
            assert np.isfinite(p.test_scores_w_tta).all()
            record['paper_comparison_status'] = 'MATCH' if record['status']=='PASS' else 'MISMATCH'
            record['status'] = 'COMPLETE_PENDING_V2_VERIFICATION'
    else:
        record['status'] = 'STOP'
    REPORT.mkdir(parents=True,exist_ok=True)
    (REPORT/'runs').mkdir(exist_ok=True)
    (REPORT/'runs'/f'{tag}.json').write_text(json.dumps(record,indent=2)+'\n')
    print('RUN_RECORD',json.dumps({k:v for k,v in record.items() if k not in ('audit','resolved_config','artifact_hashes')}),flush=True)
    if error:
        raise SystemExit(1)


if __name__=='__main__':
    main()
