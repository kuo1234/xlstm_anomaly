"""Run CPU-only scaffold and backend validation unit tests with a JSON record."""
import json
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

if __name__=='__main__':
    start=time.perf_counter()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    record=dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        seconds=time.perf_counter()-start,cpu_only=True,no_model_training=True)
    name=sys.argv[1] if len(sys.argv)>1 else 'unit_tests'
    target=ROOT/'reports/phase_d_v2'/f'{name}.json'
    assert not target.exists()
    target.write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
