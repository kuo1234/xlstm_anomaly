"""Native backend construction/forward attempt, not training or reproduction metrics."""
import json,time,traceback,sys
import torch
from phase_e_common import *
if __name__=='__main__':
    configure();seal_sources()
    (REPORT/'environment.json').write_text(json.dumps(environment(),indent=2)+'\n')
    start=time.perf_counter();variant=sys.argv[1] if len(sys.argv)>1 else 'native'
    result=dict(variant=variant,official_modified=False)
    try:
        model=build(w=50,float32=variant=='float32')
        result['parameters']=sum(p.numel() for p in model.parameters())
        result['resolved_encoder']=dataclasses.asdict(model.lstm_encoder.config)
        x=torch.randn(4,50,8,device='cuda')
        with torch.no_grad():output=model(x)
        result.update(status='PASS',output_shape=list(output.shape),finite=bool(torch.isfinite(output).all()))
    except Exception as exc:
        result.update(status='BLOCKED',error=repr(exc),traceback=traceback.format_exc())
    result['seconds']=time.perf_counter()-start
    (REPORT/f'{variant}_backend.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
