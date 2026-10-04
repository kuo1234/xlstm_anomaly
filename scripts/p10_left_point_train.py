"""Healthy-only official forward training; never imports/opens event loader/metadata."""
import json,time,random,sys
from pathlib import Path
import numpy as np,torch
from torch.utils.data import Dataset,DataLoader
from p10_left_point_data import OUT,RAW,check_upstream,healthy_numeric,sha,save,utc
from p10_left_point_model import create

class HealthyWindows(Dataset):
 def __init__(self,arrays,L):
  self.arrays=arrays;self.L=L;self.index=[(i,j) for i,a in enumerate(arrays) for j in range(L,len(a)+1)]
 def __len__(self):return len(self.index)
 def __getitem__(self,index):
  i,j=self.index[index];return torch.from_numpy(self.arrays[i][j-self.L:j].astype(np.float32))

def fit_scaler(arrays):
 a=np.concatenate(arrays);return a.mean(0),np.maximum(a.std(0),.02)

def transform(arrays,mu,sd):return [np.clip((x-mu)/sd,-20,20) for x in arrays]

@torch.no_grad()
def validation(model,loader):
 model.eval();losses=[]
 for b in loader:
  loss,_=model(b.to('cuda'),None,None,None);assert torch.isfinite(loss);losses.append((float(loss),len(b)))
 return sum(v*n for v,n in losses)/sum(n for v,n in losses)

def main():
 check_upstream();cfg=json.loads((OUT/'training_config.json').read_text());train=healthy_numeric('train');valid=healthy_numeric('validation');mu,sd=fit_scaler(train)
 train=transform(train,mu,sd);valid=transform(valid,mu,sd);(OUT/'run').mkdir(exist_ok=True);(RAW/'checkpoints').mkdir(exist_ok=True)
 np.savez(OUT/'run/scaler.npz',mean=mu,sd=sd);all_models=[]
 for anchor,name in [('PSM','primary'),('SMD','robustness')]:
  config=json.loads((OUT/f'left_config_{name}.json').read_text());L=config['seq_len']
  for seed in cfg['model_seeds']:
   random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed);torch.set_num_threads(4)
   torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
   model=create(config);opt=torch.optim.Adam(model.parameters(),lr=cfg['learning_rate'])
   td=HealthyWindows(train,L);vd=HealthyWindows(valid,L);tl=DataLoader(td,batch_size=cfg['batch_size'],shuffle=True,drop_last=True,num_workers=0);vl=DataLoader(vd,batch_size=16,shuffle=False,num_workers=0)
   log=[];best=float('inf');bad=0;best_epoch=None;best_step=None;started=time.time();speed_start=None;measured=None;cp=RAW/'checkpoints'/f'{anchor}_s{seed}.pt'
   for epoch in range(1,cfg['epochs_max']+1):
    model.train();losses=[];ep=time.time()
    for b in tl:
     b=b.to('cuda');opt.zero_grad(set_to_none=True);loss,_=model(b,None,None,None)
     if not torch.isfinite(loss):raise RuntimeError('HEALTHY_TRAINING_SUPPORT_INSUFFICIENT nonfinite healthy loss')
     loss.backward();opt.step();losses.append(float(loss.detach()))
     if model.step==3:torch.cuda.synchronize();speed_start=time.time()
     if model.step==23:
      torch.cuda.synchronize();measured=(time.time()-speed_start)/20;estimate=measured*len(tl)*cfg['epochs_max']
      save(OUT/'run'/f'{anchor}_throughput.json',{'seconds_per_step':measured,'steps_per_epoch':len(tl),'max_epochs':cfg['epochs_max'],'estimated_train_seconds':estimate,'budget_seconds':cfg['training_wall_budget_seconds_per_anchor'],'healthy_only':True})
      print(anchor,'throughput',measured,'estimate',estimate,flush=True)
      if estimate>cfg['training_wall_budget_seconds_per_anchor']:raise RuntimeError('BLOCKED healthy-only throughput exceeds frozen budget; do not change cases/config')
     if time.time()-started>cfg['training_wall_budget_seconds_per_anchor']:raise RuntimeError('BLOCKED frozen training wall budget exceeded')
    val=validation(model,vl);row={'epoch':epoch,'step':model.step,'train_loss':float(np.mean(losses)),'healthy_validation_loss':val,'seconds':time.time()-ep,'eligible_checkpoint':model.step>=cfg['min_optimizer_steps_for_checkpoint']};log.append(row);save(OUT/'run'/f'{anchor}_s{seed}_training.json',log)
    print(anchor,seed,row,flush=True)
    if row['eligible_checkpoint']:
     if val<best:
      best=val;bad=0;best_epoch=epoch;best_step=model.step;torch.save({'state_dict':model.state_dict(),'model_step':model.step,'config':config,'seed':seed,'healthy_validation_loss':val,'epoch':epoch},cp)
     else:bad+=1
     if bad>=cfg['patience_epochs']:break
   if best_epoch is None:raise RuntimeError('HEALTHY_TRAINING_SUPPORT_INSUFFICIENT curriculum never completed')
   all_models.append({'anchor':anchor,'seed':seed,'checkpoint_file':cp.name,'sha256':sha(cp),'best_epoch':best_epoch,'best_step':best_step,'healthy_validation_loss':best,'parameter_count':sum(p.numel() for p in model.parameters()),'epochs_run':len(log),'steps_run':model.step,'wall_seconds':time.time()-started,'gpu_hours_upper_bound':(time.time()-started)/3600,'healthy_train_windows':len(td),'healthy_validation_windows':len(vd),'seed_robustness':'NOT_EVALUATED; single seed minimal pilot'})
   save(OUT/'run/checkpoints_manifest.json',all_models);del model,opt;torch.cuda.empty_cache()
 print('healthy training completed',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  save(OUT/'training_failure.json',{'utc':utc(),'error':str(e),'event_scores_read':0,'event_training':False});raise
