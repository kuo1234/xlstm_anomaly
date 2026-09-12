"""Seal v4 CPU review artifacts and regression results, preserving old reports."""
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    for folder in ('phase_a','phase_a_v3','phase_b'):
        for line in Path(f'reports/{folder}/SHA256SUMS').read_text().splitlines():
            expected,path = line.split('  ',1)
            assert digest(path)==expected,path
    for machine in json.loads(Path('reports/phase_a/smd_seal.json').read_text()):
        for asset in machine['assets']:
            assert digest(asset['path'])==asset['sha256'],asset['path']
    out = Path('reports/generator_validation_v4')
    summary = json.loads((out/'summary.json').read_text())
    assert summary['base_cases']==125 and summary['passed']==125 and summary['failed']==0
    for path,expected in summary['code_config_sha256'].items():
        assert digest(path)==expected,path
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().discover('tests',pattern='test_*.py'))
    suite.addTests(unittest.TestLoader().discover('scripts',pattern='test_phase_a.py'))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (out/'regression_tests.log').write_text(log.getvalue())
    (out/'regression_summary.json').write_text(json.dumps(dict(tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        passed=result.wasSuccessful(),prior_audits_and_A1_seals='verified_unchanged'),indent=2)+'\n')
    print(log.getvalue())
    if not result.wasSuccessful():
        raise SystemExit(1)
    for directory in (Path('reports/phase_a_v4'),out):
        files = sorted(p for p in directory.iterdir() if p.is_file() and p.name!='SHA256SUMS')
        (directory/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p}\n' for p in files))


if __name__=='__main__':
    main()
