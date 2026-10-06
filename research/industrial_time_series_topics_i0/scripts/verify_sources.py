"""Read-only source identity / prior tracked-file preservation checks."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path('research/industrial_time_series_topics_i0')
BASE='08cec9b402990831790c2e1be8849f4d531be8cf'
checks=[]

def visit(obj):
    if isinstance(obj,dict):
        if isinstance(obj.get('path'),str) and obj.get('sha256'):
            path=Path(obj['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==obj['sha256'],str(path)
            assert subprocess.run(['git','check-ignore','-q',str(path)]).returncode==0,str(path)
            checks.append(str(path))
        if obj.get('tree_path') and obj.get('tree_sha256'):
            assert hashlib.sha256(Path(obj['tree_path']).read_bytes()).hexdigest()==obj['tree_sha256']
            checks.append(obj['tree_path'])
        for value in obj.values():visit(value)
    elif isinstance(obj,list):
        for value in obj:visit(value)

for path in (ROOT/'provenance').glob('*.json'):
    if path.name not in ('verification.json',):visit(json.loads(path.read_text()))
for path in (ROOT/'scripts').glob('*.py'):ast.parse(path.read_text())
seal=json.loads((ROOT/'provenance/linear_probe_seal.json').read_text())
assert hashlib.sha256((ROOT/'scripts/linear_feasibility.py').read_bytes()).hexdigest()==seal['script_sha256']
old=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE]).decode().splitlines()
for path in old:assert Path(path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path]),path
subprocess.run(['git','diff','--check'],check=True)
print(json.dumps({'baseline':BASE,'baseline_tracked_files_preserved':len(old),'source_identity_paths_checked':sorted(set(checks)),'script_ast_checks':'passed','seal_script_hash':'passed','diff_check':'passed','quality_predictive_results_verified':False,'not_a_novelty_or_performance_certificate':True},indent=2))
