"""Truth-free model/selector/step API. No file readers or dataset identities."""
import hashlib,json
import numpy as np
from scipy.stats import chi2
from base import ah
class LinearAE:
 def __init__(self,mu,sd,encoder,decoder,tau,refs_h,refs_m,invcov,cfg):
  self.mu=mu.copy();self.sd=sd.copy();self.encoder=encoder.copy();self.decoder=decoder.copy()
  self.tau=float(tau);self.refs_h=refs_h.copy();self.refs_m=refs_m.copy();self.invcov=invcov.copy();self.cfg={k:cfg[k] for k in ["learning_rate","latent_dim","threshold_quantile","CANDI"]}
  self.sim_cutoff=float(chi2.ppf(cfg["CANDI"]["chi_square_p"],len(invcov)))
  self.fixed_hash=hashlib.sha256(b"".join(v.tobytes() for v in [self.mu,self.sd,self.encoder,self.refs_h,self.refs_m,self.invcov])+np.array([self.tau]).tobytes()).hexdigest()
 @classmethod
 def fit(cls,fit,cal,cfg):
  mu=fit.mean(0);sd=fit.std(0);sd=np.where(sd<1e-8,1,sd);x=(fit-mu)/sd
  _,_,vh=np.linalg.svd(x,full_matrices=False);E=vh[:cfg["latent_dim"]].T.copy()
  for i in range(E.shape[1]):
   if E[np.argmax(np.abs(E[:,i])),i]<0:E[:,i]*=-1
  z=x@E;L=np.column_stack([z,np.ones(len(z))]);D=np.linalg.lstsq(L,x,rcond=None)[0]
  xc=(cal-mu)/sd;zc=xc@E;lc=np.column_stack([zc,np.ones(len(zc))]);scores=np.mean((lc@D-xc)**2,axis=1)
  tau=float(np.quantile(scores,cfg["threshold_quantile"]))
  cc=cfg["CANDI"];order=np.argsort(scores,kind="stable")
  hard=zc[order[-max(1,int(np.ceil(len(cal)*cc["hard_top_calibration_fraction"]))):]]
  q1,q3=np.quantile(scores,[.25,.75]);moderate=zc[(scores>=q1)&(scores<=q3)]
  def cap(ref):
   return ref[np.linspace(0,len(ref)-1,min(len(ref),cc["reference_cap"]),dtype=int)]
  inv=np.linalg.inv(np.cov(zc,rowvar=False)+cc["covariance_ridge"]*np.eye(zc.shape[1]))
  return cls(mu,sd,E,D,tau,cap(hard),cap(moderate),inv,cfg)
 def encode(self,x):
  v=(np.array(x,dtype=float)-self.mu)/self.sd;z=v@self.encoder
  return v,z,np.r_[z,1.]
 def score(self,x):
  v,z,l=self.encode(x);return float(np.mean((l@self.decoder-v)**2)),z.copy()
 def state_hash(self):
  return hashlib.sha256(b"".join(v.tobytes() for v in [self.mu,self.sd,self.encoder,self.refs_h,self.refs_m,self.invcov,self.decoder])+np.array([self.tau,self.sim_cutoff,self.cfg["learning_rate"]]).tobytes()).hexdigest()
 def write(self,points):
  V=np.stack(points);Z=V@self.encoder;L=np.column_stack([Z,np.ones(len(Z))])
  grad=2/(len(V)*V.shape[1])*L.T@(L@self.decoder-V)
  self.decoder-=self.cfg["learning_rate"]*grad
  if not np.isfinite(self.decoder).all():raise ValueError("nonfinite decoder; STOP")
 def similar(self,z,kind):
  refs=self.refs_h if kind=="hard" else self.refs_m
  d=refs-z;mahal=np.einsum("ni,ij,nj->n",d,self.invcov,d)
  return bool(np.any(mahal<self.sim_cutoff))
 def copy(self):
  return LinearAE(self.mu,self.sd,self.encoder,self.decoder,self.tau,self.refs_h,self.refs_m,self.invcov,self.cfg)
class Runtime:
 def __init__(self,model,policy):
  self.model=model;self.policy=policy;self.buffers={"hard":[],"moderate":[]};self.count=0;self.start=-1;self.released=False
 def step(self,x,t):
  # Immutable output is captured before selection/update; no labels/arm/onset inputs.
  pre=self.model.state_hash();score,z=self.model.score(x);alarm=bool(score>self.model.tau)
  before_count=self.count;reset=bool(not alarm and before_count)
  if alarm:
   if not self.count:self.start=t
   self.count+=1
  else:self.count=0;self.start=-1;self.released=False
  decision="WAIT";selected=[];written=[];weights=[];entry=[];exits=[];kind=""
  pending_pre={k:len(v) for k,v in self.buffers.items()};v,_,_=self.model.encode(x)
  if self.policy=="FROZEN":decision="FROZEN"
  elif self.policy=="IMMEDIATE_UPDATE":
   if alarm:selected=[t];written=[t];weights=[1.];points=[v];decision="UPDATE"
  elif self.policy=="M2N2_STYLE_CAUSAL":
   if not alarm:selected=[t];written=[t];weights=[1.];points=[v];decision="UPDATE"
  elif self.policy=="CANDI_STYLE_CAUSAL":
   kind="hard" if alarm else "moderate"
   if self.model.similar(z,kind):
    selected=[t];entry=[t];self.buffers[kind].append((t,v.copy()));decision="SELECT"
    if len(self.buffers[kind])>=self.model.cfg["CANDI"]["min_samples"]:
     written=[i for i,_ in self.buffers[kind]];points=[q for _,q in self.buffers[kind]]
     weights=[1/len(points)]*len(points);exits=written.copy();self.buffers[kind]=[];decision="UPDATE"
  elif self.policy.startswith("QUARANTINE_"):
   Q=int(self.policy.rsplit("_",1)[1])
   if alarm and self.count>=Q:
    selected=[t];written=[t];weights=[1.];points=[v]
    decision="UPDATE" if self.released else "PROMOTE";self.released=True
  else:raise ValueError("unknown policy")
  if written:self.model.write(points)
  post=self.model.state_hash();mutated=pre!=post
  if decision=="PROMOTE" and not mutated:decision="PROMOTE_NO_EFFECT"
  effective=written.copy() if mutated else []
  row={"point_id":int(t),"score_time":int(3*t),"score":score,"alarm":int(alarm),
       "latent0":float(z[0]),"latent1":float(z[1]),"decision_time":int(3*t+1),"decision":decision,
       "mutation_time":int(3*t+2) if mutated else -1,
       "candidate_start":int(self.start),"candidate_count":int(self.count),"candidate_reset":int(reset),
       "selected_ids":selected,"buffer_entry_ids":entry,"buffer_exit_ids":exits,"buffer_kind":kind,
       "pending_pre":pending_pre,"pending_post":{k:len(v) for k,v in self.buffers.items()},
       "loss_ids":written,"loss_weights":weights,"effective_written_ids":effective,
       "parameter_mutation":int(mutated),"adapter_mutation":0,"optimizer_state_mutation":0,
       "scaler_EMA_mutation":0,"reference_mutation":0,"calibration_mutation":0,"encoder_mutation":0,
       "rollback":"NOT_IMPLEMENTED","full_state_pre_hash":pre,"full_state_post_hash":post}
  return row,self.model.decoder.copy()
 def pending(self):return {k:[i for i,_ in v] for k,v in self.buffers.items()}
def run_array(x,model,policy,start):
 r=Runtime(model.copy(),policy);rows=[];states=[]
 for t in range(start,len(x)):
  row,d=r.step(x[t],t);rows.append(row);states.append(d)
 return rows,np.array(states),r.pending()
def probe(model,decoder,x):
 pre=model.state_hash();m=model.copy();m.decoder=decoder.copy()
 values=np.array([m.score(v)[0] for v in x])
 if model.state_hash()!=pre:raise AssertionError("probe modified live model")
 return {"FPR":float(np.mean(values>model.tau)),"mean_score":float(values.mean()),"median_score":float(np.median(values)),
         "score_q05_q25_q75_q95":np.quantile(values,[.05,.25,.75,.95]).tolist(),"read_only":True}
