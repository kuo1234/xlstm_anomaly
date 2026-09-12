"""Seal generated v2 reports after log files have closed."""
from phase_c_run import ROOT,digest

REPORT=ROOT/'reports/phase_d_v2'

if __name__=='__main__':
    files=sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT)}\n' for p in files))
    print('Sealed',len(files),'v2 report files')
