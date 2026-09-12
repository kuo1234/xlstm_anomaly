"""Exact improved official implementation; supported vanilla backend in float32."""
import contextlib,dataclasses,hashlib,importlib.metadata,json,sys,subprocess
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
OFFICIAL=ROOT/'data/phase_e2/official_xlstmad'
REPORT=ROOT/'reports/phase_e2'
PIN='e8b56ba27352733bb83729e85b1d6196dca70c99'
sys.path.insert(0,str(OFFICIAL))
import xlstmad as native
from dataset import SlidingWindowDataset

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tensor_hash(t):
    a=t.detach().cpu().contiguous().numpy()
    return hashlib.sha256(str(a.dtype).encode()+str(a.shape).encode()+a.tobytes()).hexdigest()
def model_hash(model):
    return hashlib.sha256(''.join(k+tensor_hash(v) for k,v in sorted(model.state_dict().items())).encode()).hexdigest()

def configure():
    assert importlib.metadata.version('xlstm')=='2.0.5'
    assert importlib.metadata.version('lightning')=='2.6.1'
    assert subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'rev-parse','HEAD'],text=True).strip()==PIN
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    torch.set_num_threads(4);torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    torch.set_float32_matmul_precision('highest');torch.backends.cuda.matmul.allow_tf32=False
    assert not torch.are_deterministic_algorithms_enabled()

def build():
    torch.manual_seed(11);torch.cuda.manual_seed_all(11)
    original=native.create_config
    def float32_config(*args,**kwargs):
        cfg=original(*args,**kwargs)
        assert cfg.slstm_block.slstm.backend=='vanilla'
        for name in ('dtype','dtype_b','dtype_r','dtype_w','dtype_g','dtype_s','dtype_a'):
            setattr(cfg.slstm_block.slstm,name,'float32')
        return cfg
    # Precision configuration only, no change to layers, equations or readout.
    native.create_config=float32_config
    try:model=native.xLSTMAD(embedding_dim=40,features_no=8,window_size=64,lr=.001,slstm_backend='vanilla')
    finally:native.create_config=original
    return model.float().cuda().eval()

class ObservationWindows(torch.utils.data.Dataset):
    """Labels cannot enter this API; dummy dataset labels are discarded locally."""
    def __init__(self,x,window=64):
        if len(x)<window:raise ValueError('Insufficient observations; no padding/tail repetition')
        self._dataset=SlidingWindowDataset(x,torch.zeros(len(x),dtype=torch.int64),window_size=window)
    def __len__(self):return len(self._dataset)
    def __getitem__(self,i):return self._dataset[i][0]

def score(model,x):
    """Same reconstruction MSE coordinates as native test_step; no metric labels."""
    return (model(x)-x).square().mean((1,2))

def freeze():
    configure();model=build()
    import xlstm,lightning
    from phase_e2_schema import BASE_COLUMNS,EXPANDED_COLUMNS,SCALAR_CELLS
    paths=[p for p in OFFICIAL.rglob('*') if p.is_file() and '.git' not in p.parts]
    for module in (xlstm,lightning):
        paths.extend(p for p in Path(module.__file__).parent.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.extend((ROOT/'data/phase_e2/wheels').glob('*.whl'))
    paths.append(ROOT/'data/phase_e2/dependency_install.json')
    source={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
    (REPORT/'source_hashes.json').write_text(json.dumps(source,indent=2)+'\n')
    (REPORT/'dependency_install.json').write_bytes((ROOT/'data/phase_e2/dependency_install.json').read_bytes())
    packages={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    env=dict(python=sys.version,packages=packages,torch=torch.__version__,cuda=torch.version.cuda,
        cudnn=torch.backends.cudnn.version(),device=torch.cuda.get_device_name(),uuid=str(torch.cuda.get_device_properties(0).uuid),
        backend='vanilla',precision='float32_no_autocast',cudnn_deterministic=True,cudnn_benchmark=False,
        deterministic_algorithms=False,matmul_precision='highest',matmul_allow_tf32=False,
        cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,torch_threads=torch.get_num_threads())
    (REPORT/'environment.json').write_text(json.dumps(env,indent=2)+'\n')
    cells={n:dataclasses.asdict(m.config) for n,m in model.named_modules() if n.endswith(('slstm_cell','mlstm_cell'))}
    architecture=dict(description='improved official xLSTMAD implementation',commit=PIN,backend='vanilla',dtype='float32',
        config=dict(D=8,W=64,embedding=40,lr=.001,model_seed=11),encoder=dataclasses.asdict(model.encoder.config),
        decoder=dataclasses.asdict(model.decoder.config),cells=cells,
        trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        parameter_shapes={n:list(p.shape) for n,p in model.named_parameters()},initial_model_hash=model_hash(model),
        readout='D→40 projection; full-window encoder→full-window decoder→GELU→40→D projection; B,W,D',
        v1_differences='4 scalar/2 matrix cells versus2 scalar/4 matrix; no last-token bottleneck/singleton decoder rollout; aligned MSE',
        reset='No recurrent/conv state passed between windows; decoder actual previous within-window timestamp')
    (REPORT/'architecture.json').write_text(json.dumps(architecture,indent=2)+'\n')
    schema=dict(base_columns=BASE_COLUMNS,expanded_columns=EXPANDED_COLUMNS,scalar_cells=SCALAR_CELLS,
        dimensions=dict(base=18,internal=234,hidden=52,gate=130,memory=52,history_plus_internal=248),
        pooling='equal within-head statistics, then equal heads and all four scalar layers',
        previous='T−2 for BOTH encoder and full-window decoder; only T=1 uses own zero state',
        gates='xlstm2.0.5 actual stabilized gates: min(exp(i_raw-m_new),1);min(exp(m_prev+logsigmoid(f_raw)-m_new),1)',
        memory='c/n; relative delta denominator norm(previous)+1e-8',
        rolling='4/8/16/32 full trailing decisions; population std and OLS slope; NaN warmup excluded',
        mLSTM_features=False,labels_extracted=False,code_sha256=sha(ROOT/'scripts/phase_e2_schema.py'))
    (REPORT/'schema.json').write_text(json.dumps(schema,indent=2)+'\n')
    print('E2 architecture/schema frozen; parameters',architecture['trainable_parameters'],'scalar cells',len(SCALAR_CELLS))

if __name__=='__main__':freeze()
