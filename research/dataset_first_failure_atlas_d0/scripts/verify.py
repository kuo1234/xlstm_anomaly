"""Verify sources, deterministic D0 replay, arithmetic and report links; no models."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from sources import ROOT, REPO, CACHE, PIN, fetch, sha


def read_csv(path, key='file'):
    with Path(path).open() as handle:
        rows = list(csv.DictReader(handle))
    assert len({r[key] for r in rows}) == len(rows), path
    return {r[key]: r for r in rows}


def fingerprints():
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(ROOT.rglob('*'))
            if p.is_file() and (p.suffix == '.md' or p.parent.name == 'results'
                                and p.suffix in ('.csv', '.json'))}


def main():
    fetch()
    commands = []
    for name in ['atlas.py', 'check_patterns.py', 'semantics_trace.py',
                 'select_sentinels.py', 'reports.py']:
        command = [sys.executable, str(ROOT/'scripts'/name)]
        result = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
        commands.append({'script': name, 'exit_code': result.returncode,
                         'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()})
        assert result.returncode == 0, commands[-1]
    before = fingerprints()
    for command in commands:
        result = subprocess.run([sys.executable, str(ROOT/'scripts'/command['script'])],
                                cwd=REPO, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
    after = fingerprints()
    assert before == after, 'D0 replay changed artifact bytes'
    test = subprocess.run([sys.executable, str(ROOT/'scripts/test_atlas.py'), '-v'],
                          cwd=REPO, text=True, capture_output=True)
    assert test.returncode == 0, test.stderr

    src = CACHE/'StrAD'
    online = read_csv(src/'results/benchmark_eval_results/online/AUC-PR.csv')
    streaming = read_csv(src/'results/benchmark_eval_results/streaming/AUC-PR.csv')
    cd = read_csv(src/'results/benchmark_eval_results/CD.csv')
    atlas = read_csv(ROOT/'results/series_atlas.csv')
    assert online.keys() == streaming.keys() == cd.keys() == atlas.keys()
    rules = json.loads((ROOT/'provenance/analysis_rules.json').read_text())
    oracle_counts = {'ALL_RELEASED': [0, 0, 0], 'TSB_DRIFT': [0, 0, 0], 'NON_DRIFT': [0, 0, 0]}
    family_gaps = {}
    for name in online:
        op = sum(float(online[name][m]) for m in rules['online_portfolio'])/4
        sp = sum(float(streaming[name][m]) for m in rules['streaming_portfolio'])/4
        assert abs(float(atlas[name]['portfolio_gap']) - (sp-op)) < 1e-10
        family_gaps.setdefault(atlas[name]['family'], []).append(sp-op)
        gap = max(float(v) for k, v in streaming[name].items() if k != 'file') - max(float(v) for k, v in online[name].items() if k != 'file')
        index = 0 if gap > 0 else 1 if gap < 0 else 2
        oracle_counts['ALL_RELEASED'][index] += 1
        oracle_counts['TSB_DRIFT' if int(cd[name]['CD']) else 'NON_DRIFT'][index] += 1
    assert oracle_counts == {'ALL_RELEASED': [22, 158, 0], 'TSB_DRIFT': [18, 57, 0], 'NON_DRIFT': [4, 101, 0]}
    family_gap = sum(sum(g)/len(g) for g in family_gaps.values())/len(family_gaps)
    reported = json.loads((ROOT/'results/portfolio_summary.json').read_text())
    assert abs(family_gap-reported['ALL_RELEASED']['equal_family_mean_gap']) < 1e-12
    refs = CACHE/'references'
    all_files = set(read_csv(refs/'TSB-AD-M.csv', 'file_name'))
    eval_files = set(read_csv(refs/'TSB-AD-M-Eva.csv', 'file_name'))
    tuning_files = set(read_csv(refs/'TSB-AD-M-Tuning.csv', 'file_name'))
    assert eval_files == set(online) and not eval_files & tuning_files
    assert all_files == eval_files | tuning_files and len(tuning_files) == 20

    archive = json.loads((ROOT/'provenance/archive_ledger.json').read_text())
    assert sha(refs/'strad_archived.zip') == archive['sha256']
    assert 'md5:'+hashlib.md5((refs/'strad_archived.zip').read_bytes()).hexdigest() == archive['md5_verified']
    comparison = json.loads((ROOT/'provenance/archive_comparison.json').read_text())
    with zipfile.ZipFile(refs/'strad_archived.zip') as bundle:
        assert bundle.namelist() == archive['member_names']
        for row in comparison:
            archived = bundle.read('magaliparrino-StrAD-d2c66c1/'+row['path'])
            assert hashlib.sha256(archived).hexdigest() == row['archived_sha256']
            assert archived == (src/row['path']).read_bytes()
    links = 0
    for doc in ROOT.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            if target.startswith(('http:', 'https:')):
                continue
            target = target.split('#')[0]
            assert (doc.parent/target).exists(), (doc, target)
            links += 1
    for p in (ROOT/'results').glob('*.json'):
        json.loads(p.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    historical = ['reports/phase_a_v4/candidate_inventory.json', 'reports/phase_a/source_groups.json',
                  'reports/phase_a/TSB_source_catalog.html', 'reports/m0_protocol.md']
    evidence = {
        'status': 'PASS', 'verification_date': '2026-10-06', 'upstream_commit': PIN,
        'runtime': {'python': sys.version, 'pandas': __import__('pandas').__version__,
                    'numpy': __import__('numpy').__version__},
        'source_hashes_verified': len(json.loads((ROOT/'provenance/strad_sources.json').read_text()))+len(json.loads((ROOT/'provenance/reference_sources.json').read_text())),
        'replay_commands': commands, 'deterministic_replay': True,
        'tests_exit_code': test.returncode, 'test_output': test.stdout+test.stderr,
        'independent_stdlib_oracle_counts': oracle_counts,
        'independent_family_portfolio_gap': family_gap,
        'official_lists': {'all': len(all_files), 'evaluation': len(eval_files), 'tuning': len(tuning_files),
                           'release_matches_evaluation': True, 'disjoint': True},
        'archived_entries_byte_identical': len(comparison), 'local_report_links_verified': links,
        'historical_inputs_sha256': {p: sha(REPO/p) for p in historical},
        'artifact_sha256': after, 'model_runs': 0, 'D1_runs': 0,
        'limitations': ['No raw score sensitivity or benchmark rerun',
                        'Figure rendering is verified separately; PNG excluded from deterministic numeric replay',
                        'Final gate is a research judgment, not a statistical test']}
    (ROOT/'provenance/verification.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps({k: evidence[k] for k in ['status', 'source_hashes_verified', 'deterministic_replay',
          'independent_stdlib_oracle_counts', 'independent_family_portfolio_gap',
          'archived_entries_byte_identical', 'local_report_links_verified', 'model_runs', 'D1_runs']}, indent=2))


if __name__ == '__main__':
    main()
