import numpy as np
def fraction(t,score,lo,hi,threshold):
 t=np.asarray(t);score=np.asarray(score);mask=(t>=lo)&(t<=hi)&np.isfinite(score)
 expected=int(hi-lo+1);n=int(mask.sum());coverage=n/expected
 return {'count':n,'expected':expected,'coverage':coverage,'eligible':coverage>=.95 and n>=30,'alarm_fraction':float(np.mean(score[mask]>threshold)) if n else None}
