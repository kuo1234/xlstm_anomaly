"""Presentation-only rendering of frozen metrics; no model/metric/gate changes."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parent
records=json.loads((root/'mechanism.json').read_text())
summary=json.loads((root/'summary.json').read_text())
fig,axes=plt.subplots(2,3,figsize=(14,7))
for col,mechanism in enumerate(['mean','dynamics','correlation']):
    selected=[r for r in records if r['job'][0]==mechanism]
    if not selected:
        for ax in axes[:,col]:
            ax.set_axis_off()
            ax.text(.5,.58,mechanism.title(),ha='center',fontsize=14,transform=ax.transAxes)
            ax.text(.5,.42,'NOT RUN\nMODEL_SUPPORT_INSUFFICIENT',ha='center',fontsize=11,transform=ax.transAxes,color='#9a3412')
        continue
    for backbone,color in [('xlstm','#2563eb'),('lstm','#d97706')]:
        rows=[r for r in selected if r['job'][2]==backbone]
        group_curves=np.array([np.mean([r['mechanism']['suffix_trace']['history_harm_normalized'] for r in rows if r['job'][1]==g],axis=0) for g in range(5)])
        for row,indices in [(0,np.arange(256)),(1,np.arange(32,64))]:
            ax=axes[row,col]
            ax.plot(indices,group_curves.mean(0)[indices],label=backbone,color=color,lw=1.4)
            ax.fill_between(indices,group_curves.min(0)[indices],group_curves.max(0)[indices],color=color,alpha=.15)
    for row in [0,1]:
        ax=axes[row,col];ax.axhline(0,color='#737373',lw=.7);ax.axhline(.05,color='black',ls='--',lw=.9,label='Material-harm threshold (0.05)');ax.set_xlabel('Suffix target offset');ax.set_ylabel('H / compatible primary MSE');ax.legend(fontsize=8)
    axes[0,col].axvspan(32,63,color='#94a3b8',alpha=.13)
    axes[0,col].set_title('Dynamics: full suffix')
    axes[1,col].set_title('Dynamics: preregistered primary interval')
fig.suptitle('Frozen-history contrast: physical-group mean and range (N=5), not confidence intervals',fontsize=12)
fig.tight_layout();fig.savefig(root/'history_harm.png',dpi=160);plt.close(fig)
