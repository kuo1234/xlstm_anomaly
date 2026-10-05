"""Pure availability contracts, no detector/model/labels."""
import numpy as np

def masks(x,observed,windows=(0,8,16,32)):
 x=np.asarray(x);observed=np.asarray(observed,dtype=bool)
 finite=np.isfinite(x).all(axis=1);prefix=np.r_[0,np.cumsum(finite)]
 result={}
 for w in windows:
  out=np.zeros(len(x),bool)
  if len(x)>w:
   ends=np.arange(w,len(x));out[ends]=observed[ends]&((prefix[ends+1]-prefix[ends-w])==w+1)
  result[w]=out
 return result

def summarize(t,x,observed,start,end,windows=(0,8,16,32)):
 t=np.asarray(t);assert np.all(np.diff(t)==1) and np.all(t==np.floor(t));contract=masks(x,observed,windows)
 within=(t>=start)&(t<=end);expected=int(end-start+1)
 row={'expected_targets':expected,'grid_extent_complete':bool(t[0]<=start and t[-1]>=end),'observed_targets':int((within&observed).sum()),'observed_fraction':float((within&observed).sum()/expected)}
 for w,valid in contract.items():
  row[f'W{w}_available']=int((within&valid).sum());row[f'W{w}_fraction']=row[f'W{w}_available']/expected
  row[f'W{w}_additional_blocked']=int((within&contract[0]&~valid).sum());row[f'W{w}_additional_fraction']=row[f'W{w}_additional_blocked']/expected
 return row
