"""Causal forecasting models. Neither API accepts labels or regime identity."""
from copy import deepcopy
import importlib.metadata
import torch
from torch import nn
from xlstm import (xLSTMBlockStack,xLSTMBlockStackConfig,sLSTMBlockConfig,sLSTMLayerConfig,mLSTMBlockConfig,mLSTMLayerConfig)
from common import load_config


class Forecaster(nn.Module):
    def __init__(self,backbone):
        super().__init__()
        cfg=load_config(); m=cfg['model']; d=cfg['dimension']; e=m['embedding']; self.backbone=backbone
        self.input_projection=nn.Linear(d,e)
        self.head=nn.Linear(e,d)
        if backbone=='xlstm':
            assert importlib.metadata.version('xlstm')==m['xlstm_version']
            scalar=sLSTMLayerConfig(backend='vanilla',num_heads=m['heads'],conv1d_kernel_size=m['conv_kernel'])
            for field in ('dtype','dtype_b','dtype_r','dtype_w','dtype_g','dtype_s','dtype_a'):
                setattr(scalar,field,'float32')
            scalar.enable_automatic_mixed_precision=False
            stack_cfg=xLSTMBlockStackConfig(embedding_dim=e,context_length=max(cfg['data']['train_length'],cfg['data']['prefix_length']+cfg['data']['suffix_length']),num_blocks=m['xlstm_blocks'],slstm_at=m['slstm_at'],slstm_block=sLSTMBlockConfig(slstm=scalar,feedforward=None),mlstm_block=mLSTMBlockConfig(mlstm=mLSTMLayerConfig(num_heads=m['heads'],conv1d_kernel_size=m['conv_kernel'],qkv_proj_blocksize=4)),dropout=0.0)
            self.core=xLSTMBlockStack(stack_cfg)
        elif backbone=='lstm':
            assert isinstance(m['lstm_hidden'],int), 'freeze a matched hidden size before training'
            self.core=nn.LSTM(e,m['lstm_hidden'],num_layers=m['lstm_layers'],batch_first=True)
            self.readout=nn.Linear(m['lstm_hidden'],e)
        else:raise ValueError(backbone)

    def forward(self,x):
        z=self.input_projection(x)
        if self.backbone=='xlstm':z=self.core(z)
        else:
            z,_=self.core(z)
            z=self.readout(z)
        return self.head(z)

    def step(self,x,state=None):
        assert x.ndim==3 and x.shape[1]==1
        z=self.input_projection(x)
        if self.backbone=='xlstm':z,state=self.core.step(z,state)
        else:
            z,state=self.core(z,state)
            z=self.readout(z)
        return self.head(z),state


def build(backbone,seed):
    torch.manual_seed(seed)
    return Forecaster(backbone).float()


def parameter_count(model):
    return sum(p.numel() for p in model.parameters())


def carry(model,x,state=None):
    values=[]
    for t in range(x.shape[1]):
        y,state=model.step(x[:,t:t+1],state)
        values.append(y)
    return torch.cat(values,dim=1),state
