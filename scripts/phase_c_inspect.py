"""Read-only checkpoint/cache/config investigation and environment capture."""
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path
import numpy as np
import torch
from sklearn.metrics import roc_auc_score,precision_recall_curve,auc
from phase_c_run import ROOT,OFFICIAL,REPORT,PUBLISHED,digest,PIN


def main():
    REPORT.mkdir(parents=True,exist_ok=True)
    environment = dict(python=sys.version,platform=platform.platform(),torch=torch.__version__,
        cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),gpu=torch.cuda.get_device_name(0),
        capability=torch.cuda.get_device_capability(0),
        nvidia_smi=subprocess.check_output(['rtk','nvidia-smi'],text=True),
        packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions() if d.metadata['Name']},
        cudnn_deterministic_native=True,cudnn_benchmark_native=False,
        float32_matmul_precision=torch.get_float32_matmul_precision(),
        upstream_environment='No root requirements/lockfile at pinned commit; exact author environment not specified',
        official_commit=PIN,official_checkout=str(OFFICIAL),algorithm_compatibility_patches=[],
        isolated_environment='data/phase_c/venv --system-site-packages; added yacs, wandb, reformer-pytorch for imports',
        telemetry='WANDB.ENABLE=False and WANDB_MODE=disabled; no external logging')
    (REPORT/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    results = []
    for machine in PUBLISHED:
        checkpoint = OFFICIAL/'results'/machine/'MLP/checkpoint_best.pth'
        ck = torch.load(checkpoint,map_location='cpu')
        (REPORT/'logs'/f'{machine}.checkpoint_config.txt').write_text(ck['cfg'])
        for alpha in ('0.5','1.0','5.0'):
            folder = OFFICIAL/'results'/machine/'MLP'/alpha
            y = np.load(folder/'test_labels.npy',allow_pickle=False)
            row = dict(machine=machine,alpha=alpha,published=dict(zip(('AUROC','AUPRC'),PUBLISHED[machine][alpha])),
                checkpoint_sha256=digest(checkpoint),checkpoint_epoch=ck['epoch'],
                upstream_config_sha256=digest(folder/'config.txt'),upstream_test_txt=(folder/'test.txt').read_text(),
                source_type='author-committed cached outputs: NOT our observed reproduction')
            for filename in ('test_scores.npy','test_scores_w_tta.npy'):
                scores = np.load(folder/filename,allow_pickle=False)
                precision,recall,_ = precision_recall_curve(y,scores)
                row[filename] = dict(AUROC=float(roc_auc_score(y,scores)),AUPRC=float(auc(recall,precision)),
                    sha256=digest(folder/filename),n=len(scores))
            results.append(row)
    (REPORT/'upstream_cache_investigation.json').write_text(json.dumps(results,indent=2)+'\n')
    code = {str(p.relative_to(OFFICIAL)):digest(p) for p in OFFICIAL.rglob('*.py') if 'TSB-AD' not in p.parts}
    (REPORT/'official_code_hashes.json').write_text(json.dumps(code,indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
