"""Native architecture metadata without executing an unavailable CUDA kernel."""
import dataclasses,json
from unittest.mock import patch
from phase_e_common import *
from xlstm.blocks.slstm.cell import sLSTMCell_cuda

if __name__=='__main__':
    original=sLSTMCell_cuda.__init__
    def metadata_only(self,config,skip_backend_init=False):original(self,config,skip_backend_init=True)
    with patch.object(sLSTMCell_cuda,'__init__',metadata_only):model=build(50)
    result=dict(status='METADATA_ONLY_NOT_EXECUTABLE',skip_backend_init=True,forward_executed=False,
        trainable_parameters=sum(p.numel() for p in model.parameters()),
        encoder_config=dataclasses.asdict(model.lstm_encoder.config),
        scalar_configs={n:dataclasses.asdict(m.config) for n,m in model.named_modules() if n.endswith('slstm_cell')},
        parameter_shapes={n:list(p.shape) for n,p in model.named_parameters()})
    reference=json.loads((REPORT/'architecture.json').read_text())
    assert result['trainable_parameters']==reference['trainable_parameters']
    assert {n:__import__('math').prod(v) for n,v in result['parameter_shapes'].items()}=={n:__import__('math').prod(v) for n,v in reference['parameters'].items()}
    (REPORT/'native_architecture_metadata.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Native configured parameter count',result['trainable_parameters'],'metadata only; no CUDA parity claimed')
