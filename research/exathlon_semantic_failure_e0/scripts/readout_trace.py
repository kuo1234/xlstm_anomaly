"""No-model execution of one inspected upstream readout on constant window scores."""
import ast
import json
import numpy as np
from sources import CACHE,RESULT


def trace_native_ae(n=100,w=40):
    path=CACHE/'exathlon/src/scoring/reconstruction/reconstruction_scorers.py'
    tree=ast.parse(path.read_text())
    cls=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='ReconstructionScorer')
    fn=next(c for c in cls.body if isinstance(c,ast.FunctionDef) and c.name=='score_period_from_w_scores')
    module=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(module)
    namespace={'np':np};exec(compile(module,str(path),'exec'),namespace)
    spy=type('ReadoutSpy',(),{})();spy.normality_model=type('Window',(),{'window_size':w})()
    out=namespace[fn.name](spy,np.ones(n-w+1))
    latest_available=np.array([min(i,n-w)+w-1 for i in range(n)])
    lags=latest_available-np.arange(n)
    return {'fixture':'constant arbitrary window scores=1; no data/model/labels/threshold used',
            'n':n,'window':w,'cadence_seconds':1,'constant_window_score_readout':out.tolist(),
            'max_future_window_availability_lag_seconds':int(lags.max()),
            'targets_with_later_window_information':int((lags>0).sum()),
            'last_readout_with_constant_input':float(out[-1]),
            'tail_expected_if_count_normalized':1.0,
            'scope':'actual inspected readout body only; not release-score reproduction or artifact dominance'}


if __name__=='__main__':
    result=trace_native_ae()
    (RESULT/'native_readout_trace.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='constant_window_score_readout'},indent=2))
