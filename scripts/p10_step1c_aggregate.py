"""Aggregate Step 1c raw rows into unit- and summary-level tables.  Usage: python p10_step1c_aggregate.py <run_dir>"""
import sys
import pandas as pd, numpy as np
pd.set_option('display.width',260)
D=sys.argv[1].rstrip('/')+'/'
r=pd.read_csv(D+'step1c_raw.csv.gz')
keys=['phi','machine','phi_seed','family','op','L','delay']
T=r[r.rollback=='T_clean'].groupby(keys)[['fpr','lift_128_identical','lift_256_identical','lift_128_variant']].mean().add_suffix('_T').reset_index()
R=r[r.rollback!='T_clean']
agg=dict(fpr=('fpr','mean'),TR_fpr=('TR_fpr','mean'),l128=('lift_128_identical','mean'),TR_l128=('TR_lift_128_identical','mean'),
 l256=('lift_256_identical','mean'),TR_l256=('TR_lift_256_identical','mean'),l128v=('lift_128_variant','mean'),TR_l128v=('TR_lift_128_variant','mean'),
 res_num=('res_num','sum'),res_den=('res_den','sum'),info_num=('info_num','sum'),par_num=('par_num','sum'),par_den=('par_den','sum'),w2n=('w2_never_num','sum'),
 n_removed=('n_removed','mean'),n_replayed=('n_replayed','mean'))
U=R.groupby(keys+['rollback']).agg(**agg).reset_index().merge(T,on=keys)
U['ratio_T']=U.l128/U.lift_128_identical_T; U['ratio_TR']=U.l128/U.TR_l128; U['TR_over_T']=U.TR_l128/U.lift_128_identical_T
U['ratio256_TR']=U.l256/U.TR_l256; U['ratio128v_TR']=U.l128v/U.TR_l128v
U['residual']=U.res_num/U.res_den; U['info_removed']=U.info_num/U.res_den; U['residual_param']=U.par_num/U.par_den; U['w2_vs_never']=U.w2n/U.res_den
U['dFPR_TR']=U.fpr-U.TR_fpr; U['dFPR_T']=U.fpr-U.fpr_T; U['lost_util']=U.TR_fpr-U.fpr_T
U.round(5).to_csv(D+'units.csv',index=False)
cols=['ratio_T','ratio_TR','TR_over_T','ratio256_TR','ratio128v_TR','residual','residual_param','info_removed','w2_vs_never','dFPR_TR','dFPR_T','lost_util','n_removed','n_replayed']
S=U.groupby(['phi','family','op','L','delay','rollback'])[cols].mean().reset_index()
S2=U.groupby(['phi','family','op','L','delay','rollback']).ratio_TR.agg(['min','max']).add_prefix('ratio_TR_').reset_index()
S=S.merge(S2); S.round(4).to_csv(D+'summary.csv',index=False)
