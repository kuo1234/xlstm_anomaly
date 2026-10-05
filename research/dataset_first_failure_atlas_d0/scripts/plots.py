"""Standalone scientific figures from saved atlas numbers; no result selection."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];r=ROOT/'results'
f=pd.read_csv(r/'family_summary.csv');all_f=f[f.subset.eq('ALL_RELEASED')].set_index('family');drift=f[f.subset.eq('TSB_DRIFT')].set_index('family')
order=all_f.sort_values('portfolio_gap').index.tolist();y=np.arange(len(order))
fig,ax=plt.subplots(figsize=(10,7))
ax.barh(y-.17,all_f.loc[order,'portfolio_gap'],height=.32,label='All released',color='#475569')
values=[drift.loc[n,'portfolio_gap'] if n in drift.index else np.nan for n in order]
ax.barh(y+.17,values,height=.32,label='Drift subset',color='#2563eb')
ax.axvline(0,color='black',lw=.8);ax.set_yticks(y,[f'{name} ({int(all_f.loc[name,"n"])} / {int(drift.loc[name,"n"]) if name in drift.index else 0})' for name in order]);ax.set_xlabel('Fixed Streaming4 mean AUC-PR minus Online4 mean AUC-PR');ax.set_title('Source-family gaps; labels show nAll / nDrift\nPositive favors Streaming; absent drift bar is not a zero effect');ax.legend();fig.tight_layout();fig.savefig(r/'family_gap.png',dpi=160);plt.close(fig)
e=pd.read_csv(r/'efficiency.csv');fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True)
for ax,subset in zip(axes,['ALL_RELEASED','TSB_DRIFT']):
 g=e[e.subset.eq(subset)]
 for mode,color,marker in [('online','#d97706','o'),('streaming','#2563eb','s')]:
  h=g[g['mode'].eq(mode)];ax.scatter(h.throughput,h.auc_pr,c=color,marker=marker,s=30,label=mode)
 front=g[g.family_front].sort_values('throughput');ax.plot(front.throughput,front.auc_pr,color='#475569',ls='--',lw=1)
 for i,row in enumerate(front.itertuples()):ax.annotate(row.method,(row.throughput,row.auc_pr),xytext=(4,7 if i%2 else -13),textcoords='offset points',fontsize=8)
 ax.set_xscale('log');ax.set_xlabel('Published throughput (call/point units unsealed)');ax.set_title(subset);ax.grid(alpha=.15);ax.legend(fontsize=8)
axes[0].set_ylabel('Equal source-family fixed-method AUC-PR');fig.suptitle('Conditional released-data Pareto fronts; mixed backend / GPU paths, LEAP batch latency unresolved',fontsize=11);fig.tight_layout();fig.savefig(r/'pareto.png',dpi=160);plt.close(fig)
# Explicit envelope label prevents any oracle plot from resembling selector quality.
o=json.loads((r/'oracle_envelope.json').read_text());fig,ax=plt.subplots(figsize=(8,4))
labels=['ALL_RELEASED','TSB_DRIFT','NON_DRIFT'];x=np.arange(3)
ax.bar(x-.18,[o[z]['positive_series'] for z in labels],.35,label='Oracle Streaming wins',color='#2563eb');ax.bar(x+.18,[o[z]['negative_series'] for z in labels],.35,label='Oracle Online wins',color='#d97706')
for i,z in enumerate(labels):
 ax.text(i-.18,o[z]['positive_series']+2,str(o[z]['positive_series']),ha='center');ax.text(i+.18,o[z]['negative_series']+2,str(o[z]['negative_series']),ha='center')
ax.set_xticks(x,labels);ax.set_ylabel('Released series count (descriptive, not iid N)');ax.set_title('ORACLE_ENVELOPE — test-label per-series maxima\nOnline pool19 vs Streaming pool10; not deployable selection');ax.legend(fontsize=9);fig.tight_layout();fig.savefig(r/'oracle_envelope.png',dpi=160);plt.close(fig)
print('3 figures rendered')
