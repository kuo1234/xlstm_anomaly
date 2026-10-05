"""Fixed normal-only PCA and one-step LSTM; no labels in the model interface."""
import numpy as np
import torch
from torch import nn
class Predictor(nn.Module):
    def __init__(self,n_features=19,hidden=32):
        super().__init__();self.rnn=nn.LSTM(n_features,hidden,batch_first=True);self.head=nn.Linear(hidden,n_features)
    def forward(self,history):return self.head(self.rnn(history)[0][:,-1])
def target_ids(x,observed,w):
    finite=np.isfinite(x).all(axis=1)
    counts=np.convolve(finite.astype(int),np.ones(w+1,dtype=int),'valid')
    return np.flatnonzero((counts==w+1)&observed[w:])+w

def windows(x,ids,w):return np.stack([x[i-w:i] for i in ids]).astype(np.float32)
def pca_fit(x,k):
    _,_,v=np.linalg.svd(x.astype(np.float64),full_matrices=False);return v[:k]
def pca_score(x,basis):return np.mean((x-x@basis.T@basis)**2,axis=1)
def infer_lstm(model,x,observed,w,batch=512):
    ids=target_ids(x,observed,w);out=np.full(len(x),np.nan);model.eval()
    with torch.no_grad():
        for off in range(0,len(ids),batch):
            ix=ids[off:off+batch];pred=model(torch.from_numpy(windows(x,ix,w))).numpy()
            out[ix]=np.mean((pred-x[ix])**2,axis=1)
    return out
