"""Durable fresh-process v2 launcher; old reports never written."""
import sys
import phase_d_launch as launcher
launcher.REPORT=launcher.ROOT/'reports/phase_d_v2'
if __name__=='__main__':launcher.main()
