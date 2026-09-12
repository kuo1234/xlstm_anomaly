"""Import exact pinned reconstruction module, preserving upstream files."""
import contextlib,dataclasses,hashlib,importlib.metadata,json,sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
OFFICIAL=ROOT/'data/phase_e/official_xlstmad'
REPORT=ROOT/'reports/phase_e'
sys.path.insert(0,str(OFFICIAL))
import models.xlstmad_rec_ad as native

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

@contextlib.contextmanager
def config_overlay(backend=None,float32=False):
    original=native.create_config
    def config(*a,**kw):
        cfg=original(*a,**kw)
        if backend:cfg.slstm_block.slstm.backend=backend
        if float32:
            for name in ('dtype','dtype_b','dtype_r','dtype_w','dtype_g','dtype_s','dtype_a'):
                setattr(cfg.slstm_block.slstm,name,'float32')
        return cfg
    native.create_config=config
    try:yield
    finally:native.create_config=original

def build(w=64,backend=None,float32=False):
    torch.manual_seed(11);torch.cuda.manual_seed_all(11)
    with config_overlay(backend,float32):
        return native.xLSTMModel(w,8,40,128,torch.device('cuda')).cuda().eval()

def environment():
    return dict(python=sys.version,packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()},
        torch=torch.__version__,cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),
        device=torch.cuda.get_device_name(),uuid=str(torch.cuda.get_device_properties(0).uuid),
        cudnn_deterministic=torch.backends.cudnn.deterministic,cudnn_benchmark=torch.backends.cudnn.benchmark,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        matmul_precision=torch.get_float32_matmul_precision(),matmul_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_tf32=torch.backends.cudnn.allow_tf32)

def seal_sources():
    import xlstm,subprocess
    assert subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'rev-parse','HEAD'],text=True).strip()=='3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6'
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    paths=[p for p in OFFICIAL.rglob('*') if p.is_file() and '.git' not in p.parts]
    paths+=[p for p in Path(xlstm.__file__).parent.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths+=list((ROOT/'data/phase_e/wheels').glob('*'))
    (REPORT/'source_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},indent=2)+'\n')

def configure():
    torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    torch.set_float32_matmul_precision('highest');torch.backends.cuda.matmul.allow_tf32=False
    assert not torch.are_deterministic_algorithms_enabled()
