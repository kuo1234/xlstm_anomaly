"""Pinned official LEFT with return-only AST instrumentation and endpoint wrapper."""
import ast,inspect,textwrap,sys,json
from pathlib import Path
import numpy as np,torch
ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'data/left_point_pilot/upstream'
sys.path.insert(0,str(UP))
from models.Left.LEFT import Left
from models.Left import LEFT as M

MAPS=['score_time','score_freq','score_ms','prototype_gate','cross_path_consistency','cycle','score_total']

def instrument(model):
 tree=ast.parse(textwrap.dedent(inspect.getsource(Left._ms_anomaly_score)))
 function=tree.body[0];assert isinstance(function.body[-1],ast.Return)
 added=ast.parse("self.last_components={'score_time':score_time,'score_freq':score_freq,'score_ms':score_ms,'prototype_gate':gate_point.unsqueeze(-1),'cross_path_consistency':(X_hat_ms-X_hat_from_S).abs(),'cycle':score_t,'score_total':score}").body[0]
 function.body.insert(-1,added);scope={};exec(compile(ast.fix_missing_locations(tree),'<LEFT return-only instrumentation>','exec'),M.__dict__,scope)
 import types
 model._ms_anomaly_score=types.MethodType(scope['_ms_anomaly_score'],model)
 return model

def create(config,device='cuda'):
 from types import SimpleNamespace
 return instrument(Left(SimpleNamespace(**config)).to(device))

def windows(x,ends,L):
 # End index exclusive: only<=point, never a future real observation.
 ends=np.asarray(ends);assert np.all(ends>=L) and np.all(ends<=len(x))
 return np.stack([x[e-L:e] for e in ends])

@torch.no_grad()
def endpoint(model,x,ends,batch=16):
 model.eval();result={k:[] for k in MAPS};L=model.seq_len;device=next(model.parameters()).device
 for start in range(0,len(ends),batch):
  b=torch.from_numpy(windows(x,ends[start:start+batch],L).astype(np.float32)).to(device)
  total,_=model.infer(b,None,None,None);c=model.last_components
  assert torch.equal(total,c['score_total'])
  for k in MAPS:
   value=c[k][:,-1].detach().cpu().numpy();assert np.isfinite(value).all(),f'nonfinite {k}';result[k].append(value)
 return {k:np.concatenate(v) for k,v in result.items()}
