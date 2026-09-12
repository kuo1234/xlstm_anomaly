"""Record CPU software-test outcomes; never loads detector/model-result files."""
import hashlib
import io
import json
import platform
import sys
import time
import unittest
from pathlib import Path
import numpy as np
import scipy

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from m0.correlation import verify


def main():
    for line in Path('reports/phase_a/SHA256SUMS').read_text().splitlines():
        expected,path = line.split('  ',1)
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
            raise RuntimeError(f'Original audit seal mismatch: {path}')
    for machine in json.loads(Path('reports/phase_a/smd_seal.json').read_text()):
        for asset in machine['assets']:
            if hashlib.sha256(Path(asset['path']).read_bytes()).hexdigest()!=asset['sha256']:
                raise RuntimeError(f'A1 seal mismatch: {asset["path"]}')
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.discover('tests',pattern='test_*.py'))
    # Separate loader because unittest fixes discovery top-level on first call.
    suite.addTests(unittest.TestLoader().discover('scripts',pattern='test_phase_a.py'))
    log = io.StringIO()
    start = time.monotonic()
    result = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    elapsed = time.monotonic()-start
    out = Path('reports/phase_b')
    out.mkdir(parents=True,exist_ok=True)
    (out/'tests.log').write_text(log.getvalue())
    report = dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                  skipped=len(result.skipped),elapsed_seconds=elapsed,passed=result.wasSuccessful(),
                  python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                  correlation_checks={str(s):verify(s) for s in (None,11,22,33,44,55)},
                  hardware_scope='CPU only',model_training=False,model_result_files_inspected=False,
                  synthetic_observations='Software tests only; no full experiment dataset sweep',
                  original_phase_a_unchanged=True)
    (out/'test_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(log.getvalue())
    print(json.dumps(report))
    if not result.wasSuccessful():
        raise SystemExit(1)
    a2 = Path('reports/phase_a_v3')
    source = Path('data/phase_a/GHL_original_abstract.html')
    (a2/'GHL_original_abstract.html').write_bytes(source.read_bytes())
    (a2/'source_correction.json').write_text(json.dumps(dict(
        family='GHL',synthetic=True,url='https://arxiv.org/abs/1612.06676',
        retrieved='2026-09-12',sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        scope='Original author abstract: Modelica-generated dataset; no performance section inspected'),indent=2)+'\n')
    for directory in (a2,out):
        paths = sorted(p for p in directory.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
        (directory/'SHA256SUMS').write_text(''.join(
            f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n' for p in paths))


if __name__=='__main__':
    main()
