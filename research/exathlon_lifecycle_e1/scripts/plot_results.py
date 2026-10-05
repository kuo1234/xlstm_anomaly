"""Post-result descriptive figure only; no metric/model/gate selection."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from prepare import ROOT,sha,save

def main():
    ag=json.loads((ROOT/'results/aggregations.json').read_text());fam=json.loads((ROOT/'results/family_summary.json').read_text())
    bs=['PCA_SPE','CAUSAL_LSTM_REFERENCE'];colors=['#2463a5','#c3512d'];types=['bursty_input','cpu_contention','stalled_input']
    fig,axes=plt.subplots(1,2,figsize=(11,4.7),gridspec_kw={'width_ratios':[1.6,1]})
    for i,b in enumerate(bs):
        vals=[next(x['trace_macro_Delta'] for x in ag if x['baseline']==b and x['group']=='anomaly_type' and x['value']==t) for t in types]
        pos=np.arange(3)+(i-.5)*.18;axes[0].scatter(pos,vals,color=colors[i],s=65,label='PCA / SPE' if i==0 else 'Causal LSTM reference',zorder=3)
        for x,y in zip(pos,vals):axes[0].annotate(f'{y:.3g}',(x,y),xytext=(6,8 if y<-1000 else 5 if i==0 else -14),textcoords='offset points',fontsize=9,color=colors[i])
    axes[0].set_yscale('symlog',linthresh=1);axes[0].set_ylim(-2e5,2.5);axes[0].set_xticks(range(3),['Bursty input\n5 events /1 trace','CPU contention\n9 events /2 traces','Stalled input\n10 events /3 traces'])
    axes[0].axhline(0,color='#555',lw=.8);axes[0].axhline(1,color='#555',lw=1,ls='--',label='Frozen material margin +1 IQR')
    axes[0].set_ylabel('Trace-macro Delta effect (normal-calibration IQR)\nEEI score minus RCI score; symlog scale');axes[0].set_title('Type-specific directions are heterogeneous');axes[0].legend(loc='lower right',fontsize=8)
    for i,f in enumerate(fam):
        y=f['trace_macro_Delta'];axes[1].bar(i,y,color=colors[i],width=.55);axes[1].text(i,y-.06,f'{y:.3f}',ha='center',va='top',fontsize=11)
        axes[1].scatter(i,f['stationary_event_balanced_Delta'],marker='D',color='black',s=35,zorder=4)
    axes[1].axhline(0,color='#555',lw=.8);axes[1].axhline(1,color='#555',ls='--',lw=1);axes[1].set_ylim(-1.5,1.25);axes[1].set_xticks([0,1],['PCA / SPE','Causal LSTM']);axes[1].set_title('Overall: neither family reaches +1 IQR');axes[1].set_ylabel('Trace-macro Delta effect')
    axes[1].text(.03,.69,'Black diamonds: duration-matched normal\nevent-balanced Delta (about 0.002 /0.001).',transform=axes[1].transAxes,fontsize=8)
    for ax in axes:ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Exathlon E1: NO_ROOT_EFFECT_GAP in the sealed two-family panel',fontsize=13,y=.99)
    fig.text(.02,.01,'Native 1s, 19 features, seed 21, 3 apps. Raw phase coverage valid for 24 events. Strict effect-only/delay N/A due timestamp gaps.\nDescriptive dependent-trace summaries; no universal detector, novelty or method-design claim.',fontsize=8)
    fig.tight_layout(rect=[0,.10,1,.95]);dest=ROOT/'results/lifecycle_contrast.png';fig.savefig(dest,dpi=180);fig.savefig(ROOT/'results/lifecycle_contrast.pdf');plt.close(fig)
    save(ROOT/'provenance/figure.json',{'plot':'post-result descriptive figure; no frozen scientific contract changed','PNG_sha256':sha(dest),'PDF_sha256':sha(ROOT/'results/lifecycle_contrast.pdf'),'input_sha256':{'aggregations.json':sha(ROOT/'results/aggregations.json'),'family_summary.json':sha(ROOT/'results/family_summary.json')}})
if __name__=='__main__':main()
