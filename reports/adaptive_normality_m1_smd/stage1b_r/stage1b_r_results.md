# M1 Stage-1B-R diagnostic and feasibility audit

Decision: `FINAL_STAGE1_GATE_ALREADY_IMPOSSIBLE`

This nine-machine result is diagnostic only. It cannot establish Stage-1 success.
The remaining 19 machines were not opened or evaluated.

R score seal: `f791ec764d65f2660b9f60c21babc710efd0a8fa`
Metric evaluator: `3ae3fdb4c88ad4994b6a75459d63e411e99c1ff6` (`fd07303ddb64ac5cfd2a72fe5b2a903cfe0309b633b539e45f447360c5492046`)

## Per-machine metrics

| Machine | Prevalence | Score | AP | AUROC | AP/prevalence | Event detection | Onset delay | Miss fraction | Normal FPR | False alarm points/10k | False alarm runs/10k | Recovery delay | Recovery censored | Catastrophic |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| machine-1-7 | 0.10229939 | r_native_window | 0.59925427 | 0.93215253 | 5.8578479 | 0.69230769 | 11.307692 | 0.30769231 | 0.16095614 | 1609.5614 | 5.2273915 | 224.15385 | 2 | False |
| machine-1-7 | 0.10229939 | r_endpoint | 0.73805206 | 0.92504046 | 7.2146282 | 1 | 6.5384615 | 0 | 0.0050373046 | 50.373046 | 26.612175 | 14.923077 | 0 | False |
| machine-1-7 | 0.10229939 | control_fusion | 0.47504139 | 0.89219573 | 4.6436385 | 1 | 5.2307692 | 0 | 0.054697524 | 546.97524 | 13.781305 | 94.230769 | 1 | False |
| machine-1-7 | 0.10229939 | forecast_control_fusion | 0.47473549 | 0.89236529 | 4.6406483 | 1 | 5.2307692 | 0 | 0.054697524 | 546.97524 | 13.781305 | 94.230769 | 1 | False |
| machine-1-7 | 0.10229939 | xlstmad_f | 0.74829261 | 0.92739948 | 7.3147319 | 1 | 5.2307692 | 0 | 0.0028513045 | 28.513045 | 13.781305 | 12.307692 | 0 | False |
| machine-1-7 | 0.10229939 | lstm_f | 0.72527103 | 0.88778082 | 7.0896907 | 1 | 5.2307692 | 0 | 0.0032790001 | 32.790001 | 16.157392 | 12.307692 | 0 | False |
| machine-1-7 | 0.10229939 | last_value | 0.16485802 | 0.5750959 | 1.611525 | 1 | 5.4615385 | 0 | 0.0036591741 | 36.591741 | 20.434349 | 10 | 0 | False |
| machine-1-7 | 0.10229939 | moving_median | 0.23339779 | 0.58865686 | 2.281517 | 1 | 5.2307692 | 0 | 0.0089340873 | 89.340873 | 14.256522 | 22 | 0 | False |
| machine-1-7 | 0.10229939 | var1 | 0.66813191 | 0.82302723 | 6.5311427 | 1 | 5.2307692 | 0 | 0.0052749133 | 52.749133 | 40.868697 | 10.384615 | 0 | False |
| machine-1-3 | 0.034844543 | r_native_window | 0.035992421 | 0.52871985 | 1.0329428 | 0.083333333 | 65.666667 | 0.91666667 | 0.034114008 | 341.14008 | 1.3256739 | 66.083333 | 1 | False |
| machine-1-3 | 0.034844543 | r_endpoint | 0.095751817 | 0.5169325 | 2.7479717 | 0.33333333 | 58.5 | 0.66666667 | 0.030711445 | 307.11445 | 5.3026955 | 66.083333 | 1 | False |
| machine-1-3 | 0.034844543 | control_fusion | 0.082919104 | 0.66547006 | 2.3796869 | 0.75 | 16 | 0.25 | 0.033451171 | 334.51171 | 17.675652 | 66.25 | 1 | False |
| machine-1-3 | 0.034844543 | forecast_control_fusion | 0.082967203 | 0.66546852 | 2.3810673 | 0.75 | 15.916667 | 0.25 | 0.033451171 | 334.51171 | 17.675652 | 66.25 | 1 | False |
| machine-1-3 | 0.034844543 | xlstmad_f | 0.20642259 | 0.59956925 | 5.9241009 | 0.75 | 16.333333 | 0.25 | 0.032302254 | 323.02254 | 19.001326 | 66.083333 | 1 | False |
| machine-1-3 | 0.034844543 | lstm_f | 0.20822046 | 0.6090095 | 5.9756979 | 0.75 | 16.333333 | 0.25 | 0.032125497 | 321.25497 | 18.117543 | 66.083333 | 1 | False |
| machine-1-3 | 0.034844543 | last_value | 0.23824327 | 0.66461608 | 6.8373194 | 0.83333333 | 13.083333 | 0.16666667 | 0.0095890411 | 95.890411 | 56.562086 | 11.083333 | 0 | False |
| machine-1-3 | 0.034844543 | moving_median | 0.24169655 | 0.71098276 | 6.9364246 | 0.91666667 | 11.416667 | 0.083333333 | 0.017587274 | 175.87274 | 64.95802 | 19.5 | 0 | False |
| machine-1-3 | 0.034844543 | var1 | 0.1998897 | 0.67820059 | 5.7366142 | 0.75 | 16.5 | 0.25 | 0.032390632 | 323.90632 | 20.327 | 66.083333 | 1 | False |
| machine-1-5 | 0.0042643923 | r_native_window | 0.027630553 | 0.90007195 | 6.4793646 | 0.85714286 | 1.7142857 | 0.14285714 | 0.21974304 | 2197.4304 | 17.987152 | 293.14286 | 0 | False |
| machine-1-5 | 0.0042643923 | r_endpoint | 0.54757065 | 0.9261182 | 128.40532 | 1 | 1.7142857 | 0 | 0.016745182 | 167.45182 | 84.796574 | 35.428571 | 0 | False |
| machine-1-5 | 0.0042643923 | control_fusion | 0.015571497 | 0.85330236 | 3.6515161 | 1 | 1.4285714 | 0 | 0.23203426 | 2320.3426 | 30.406852 | 293.14286 | 0 | False |
| machine-1-5 | 0.0042643923 | forecast_control_fusion | 0.015561688 | 0.85271392 | 3.6492159 | 1 | 1.4285714 | 0 | 0.23203426 | 2320.3426 | 30.406852 | 293.14286 | 0 | False |
| machine-1-5 | 0.0042643923 | xlstmad_f | 0.42497513 | 0.8875045 | 99.656668 | 0.85714286 | 2.8571429 | 0.14285714 | 0.013062099 | 130.62099 | 115.20343 | 21.428571 | 0 | False |
| machine-1-5 | 0.0042643923 | lstm_f | 0.43139814 | 0.92848565 | 101.16286 | 0.85714286 | 2.8571429 | 0.14285714 | 0.011905782 | 119.05782 | 106.20985 | 15.857143 | 0 | False |
| machine-1-5 | 0.0042643923 | last_value | 0.071248623 | 0.73027366 | 16.707802 | 0.85714286 | 4.2857143 | 0.14285714 | 0.01267666 | 126.7666 | 78.800857 | 10 | 0 | False |
| machine-1-5 | 0.0042643923 | moving_median | 0.44406187 | 0.86458544 | 104.13251 | 0.85714286 | 2.7142857 | 0.14285714 | 0.013062099 | 130.62099 | 111.7773 | 19.428571 | 0 | False |
| machine-1-5 | 0.0042643923 | var1 | 0.25219828 | 0.85686467 | 59.140497 | 0.71428571 | 2.8571429 | 0.28571429 | 0.0090364026 | 90.364026 | 88.650964 | 10 | 0 | False |
| machine-2-4 | 0.072291213 | r_native_window | 0.33815324 | 0.7452136 | 4.6776534 | 0.8 | 4.8 | 0.2 | 0.64584388 | 6458.4388 | 10.580063 | 643.85 | 11 | False |
| machine-2-4 | 0.072291213 | r_endpoint | 0.34014416 | 0.74724497 | 4.7051937 | 1 | 1 | 0 | 0.54542527 | 5454.2527 | 292.10175 | 522.45 | 8 | False |
| machine-2-4 | 0.072291213 | control_fusion | 0.12820359 | 0.71582099 | 1.7734325 | 1 | 0.95 | 0 | 0.54367726 | 5436.7726 | 293.48176 | 529.85 | 8 | False |
| machine-2-4 | 0.072291213 | forecast_control_fusion | 0.12838882 | 0.71639711 | 1.7759948 | 1 | 0.85 | 0 | 0.49082294 | 4908.2294 | 309.12185 | 439.85 | 6 | False |
| machine-2-4 | 0.072291213 | xlstmad_f | 0.41953122 | 0.77297468 | 5.8033501 | 1 | 1.85 | 0 | 0.0049680298 | 49.680298 | 38.180229 | 10.65 | 0 | False |
| machine-2-4 | 0.072291213 | lstm_f | 0.43933045 | 0.82538944 | 6.0772317 | 1 | 0.95 | 0 | 0.077970468 | 779.70468 | 243.80146 | 13.55 | 0 | False |
| machine-2-4 | 0.072291213 | last_value | 0.27903495 | 0.68015117 | 3.8598737 | 1 | 2.2 | 0 | 0.0058420351 | 58.420351 | 34.96021 | 10.75 | 0 | False |
| machine-2-4 | 0.072291213 | moving_median | 0.29946415 | 0.73921031 | 4.1424696 | 1 | 2 | 0 | 0.025990156 | 259.90156 | 78.660472 | 14.05 | 0 | False |
| machine-2-4 | 0.072291213 | var1 | 0.42715572 | 0.76667666 | 5.9088193 | 1 | 2 | 0 | 0.028198169 | 281.98169 | 183.0811 | 10.7 | 0 | False |
| machine-2-7 | 0.017790102 | r_native_window | 0.34294155 | 0.90287681 | 19.277098 | 0.05 | 5.6 | 0.95 | 0.012856709 | 128.56709 | 0.86869652 | 23.05 | 0 | False |
| machine-2-7 | 0.017790102 | r_endpoint | 0.82546224 | 0.95426448 | 46.400084 | 0.55 | 3.05 | 0.45 | 0.0031707423 | 31.707423 | 6.5152239 | 11.15 | 0 | False |
| machine-2-7 | 0.017790102 | control_fusion | 0.48948445 | 0.95885571 | 27.514426 | 0.95 | 0.4 | 0.05 | 0.016896147 | 168.96147 | 26.060896 | 22.4 | 0 | False |
| machine-2-7 | 0.017790102 | forecast_control_fusion | 0.48880355 | 0.96009553 | 27.476152 | 0.95 | 0.5 | 0.05 | 0.014420362 | 144.20362 | 16.939582 | 22.4 | 0 | False |
| machine-2-7 | 0.017790102 | xlstmad_f | 0.78418868 | 0.96514975 | 44.080054 | 0.95 | 0.5 | 0.05 | 0.0046909612 | 46.909612 | 22.58611 | 10.25 | 0 | False |
| machine-2-7 | 0.017790102 | lstm_f | 0.78430408 | 0.96656102 | 44.086541 | 0.95 | 1.15 | 0.05 | 0.0023889154 | 23.889154 | 13.899144 | 10.95 | 0 | False |
| machine-2-7 | 0.017790102 | last_value | 0.17440615 | 0.73989747 | 9.8035493 | 0.95 | 0.85 | 0.05 | 0.0094687921 | 94.687921 | 52.121791 | 10.95 | 0 | False |
| machine-2-7 | 0.017790102 | moving_median | 0.43541916 | 0.85586367 | 24.47536 | 0.6 | 2.4 | 0.4 | 0.0001737393 | 1.737393 | 0.43434826 | 10 | 0 | False |
| machine-2-7 | 0.017790102 | var1 | 0.29152473 | 0.8990583 | 16.386906 | 0.95 | 0.85 | 0.05 | 0.0088607045 | 88.607045 | 60.808756 | 11.3 | 0 | False |
| machine-2-8 | 0.0068665501 | r_native_window | 0.19471945 | 0.92564989 | 28.357683 | 1 | 0 | 0 | 0.6103238 | 6103.238 | 2.5766555 | 5962 | 1 | False |
| machine-2-8 | 0.0068665501 | r_endpoint | 0.96169506 | 0.98650777 | 140.05506 | 1 | 0 | 0 | 0.5706433 | 5706.433 | 48.097569 | 5962 | 1 | False |
| machine-2-8 | 0.0068665501 | control_fusion | 0.0094968442 | 0.63944001 | 1.383059 | 1 | 0 | 0 | 0.72111999 | 7211.1999 | 10.736065 | 5962 | 1 | False |
| machine-2-8 | 0.0068665501 | forecast_control_fusion | 0.0094968442 | 0.63944001 | 1.383059 | 1 | 0 | 0 | 0.72111999 | 7211.1999 | 10.736065 | 5962 | 1 | False |
| machine-2-8 | 0.0068665501 | xlstmad_f | 0.95139557 | 0.98968964 | 138.55511 | 1 | 0 | 0 | 0.34909388 | 3490.9388 | 186.80752 | 5962 | 1 | False |
| machine-2-8 | 0.0068665501 | lstm_f | 0.9558671 | 0.98680064 | 139.20631 | 1 | 5 | 0 | 0.25899682 | 2589.9682 | 23.1899 | 5962 | 1 | False |
| machine-2-8 | 0.0068665501 | last_value | 0.48265032 | 0.98081912 | 70.290076 | 1 | 5 | 0 | 0.0077729108 | 77.729108 | 41.655931 | 10 | 0 | False |
| machine-2-8 | 0.0068665501 | moving_median | 0.91286414 | 0.99638121 | 132.94364 | 1 | 5 | 0 | 0.0046379799 | 46.379799 | 3.0060981 | 112 | 0 | False |
| machine-2-8 | 0.0068665501 | var1 | 0.87510494 | 0.98938823 | 127.44463 | 1 | 5 | 0 | 0.22434081 | 2243.4081 | 174.35369 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | r_native_window | 0.11704523 | 0.77614044 | 2.5340347 | 0 | 120.33333 | 1 | 0 | 0 | 0 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | r_endpoint | 0.072353675 | 0.62104915 | 1.5664604 | 0.33333333 | 26.555556 | 0.66666667 | 0.00076015024 | 7.6015024 | 7.6015024 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | control_fusion | 0.046448791 | 0.50292881 | 1.0056185 | 1 | 0 | 0 | 0.99414237 | 9941.4237 | 5.3657664 | 1733 | 7 | False |
| machine-3-2 | 0.046189278 | forecast_control_fusion | 0.046448791 | 0.50292881 | 1.0056185 | 1 | 0 | 0 | 0.99414237 | 9941.4237 | 5.3657664 | 1733 | 7 | False |
| machine-3-2 | 0.046189278 | xlstmad_f | 0.060033187 | 0.59904009 | 1.2997213 | 0.44444444 | 71.444444 | 0.55555556 | 0.00098372384 | 9.8372384 | 9.8372384 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | lstm_f | 0.062406954 | 0.59656596 | 1.3511134 | 0.55555556 | 61.888889 | 0.44444444 | 0.0008942944 | 8.942944 | 8.942944 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | last_value | 0.065411832 | 0.53414978 | 1.4161692 | 0.77777778 | 48 | 0.22222222 | 0.0029958862 | 29.958862 | 19.22733 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | moving_median | 0.056521561 | 0.48716043 | 1.2236944 | 0.77777778 | 48 | 0.22222222 | 0.0020568771 | 20.568771 | 20.121624 | 10 | 0 | False |
| machine-3-2 | 0.046189278 | var1 | 0.042319188 | 0.34190473 | 0.91621237 | 0.44444444 | 62.555556 | 0.55555556 | 0.0011625827 | 11.625827 | 11.625827 | 10 | 0 | False |
| machine-3-11 | 0.0069620253 | r_native_window | 0.018436971 | 0.80310058 | 2.6482194 | 1 | 0 | 0 | 0.89660789 | 8966.0789 | 6.3734863 | 2422.6667 | 3 | False |
| machine-3-11 | 0.0069620253 | r_endpoint | 0.37846816 | 0.88426936 | 54.361791 | 1 | 0 | 0 | 0.61957368 | 6195.7368 | 297.07528 | 2422.6667 | 3 | False |
| machine-3-11 | 0.0069620253 | control_fusion | 0.0081067802 | 0.57109978 | 1.1644284 | 1 | 0 | 0 | 0.87610651 | 8761.0651 | 14.871468 | 2422.6667 | 3 | False |
| machine-3-11 | 0.0069620253 | forecast_control_fusion | 0.0081067802 | 0.57109978 | 1.1644284 | 1 | 0 | 0 | 0.87628355 | 8762.8355 | 16.641881 | 2422.6667 | 3 | False |
| machine-3-11 | 0.0069620253 | xlstmad_f | 0.38382887 | 0.90007325 | 55.131783 | 1 | 0 | 0 | 0.34781531 | 3478.1531 | 457.82877 | 2422.6667 | 3 | False |
| machine-3-11 | 0.0069620253 | lstm_f | 0.38371295 | 0.90132309 | 55.115132 | 1 | 0 | 0 | 0.51232207 | 5123.2207 | 346.64684 | 2422.6667 | 3 | False |
| machine-3-11 | 0.0069620253 | last_value | 0.16453286 | 0.67621617 | 23.632902 | 1 | 1 | 0 | 0.037638977 | 376.38977 | 239.7139 | 15.666667 | 0 | False |
| machine-3-11 | 0.0069620253 | moving_median | 0.39188249 | 0.84010275 | 56.288576 | 1 | 6 | 0 | 0.083775937 | 837.75937 | 350.18766 | 70.333333 | 1 | False |
| machine-3-11 | 0.0069620253 | var1 | 0.1375091 | 0.87961103 | 19.751307 | 1 | 0 | 0 | 0.28928546 | 2892.8546 | 112.24418 | 2422.6667 | 3 | False |
| machine-3-7 | 0.015255369 | r_native_window | 0.0936567 | 0.76674658 | 6.1392614 | 1 | 15.8 | 0 | 0.41720507 | 4172.0507 | 7.1390327 | 1609 | 2 | False |
| machine-3-7 | 0.015255369 | r_endpoint | 0.11767758 | 0.7109687 | 7.7138469 | 1 | 7.6 | 0 | 0.31222559 | 3122.2559 | 128.14564 | 1443.2 | 2 | False |
| machine-3-7 | 0.015255369 | control_fusion | 0.026922903 | 0.71758036 | 1.7648149 | 1 | 6.2 | 0 | 0.51540246 | 5154.0246 | 19.989291 | 1672.4 | 2 | False |
| machine-3-7 | 0.015255369 | forecast_control_fusion | 0.026922483 | 0.71761009 | 1.7647873 | 1 | 6.2 | 0 | 0.51540246 | 5154.0246 | 19.989291 | 1672.4 | 2 | False |
| machine-3-7 | 0.015255369 | xlstmad_f | 0.12319176 | 0.6833084 | 8.0753051 | 1 | 2.2 | 0 | 0.25839729 | 2583.9729 | 136.71248 | 1443.2 | 2 | False |
| machine-3-7 | 0.015255369 | lstm_f | 0.12428552 | 0.67848322 | 8.1470018 | 1 | 2.2 | 0 | 0.26467964 | 2646.7964 | 81.741924 | 1443.2 | 2 | False |
| machine-3-7 | 0.015255369 | last_value | 0.064330119 | 0.59385106 | 4.2168838 | 1 | 4.6 | 0 | 0.0052114938 | 52.114938 | 28.913082 | 10 | 0 | False |
| machine-3-7 | 0.015255369 | moving_median | 0.25147139 | 0.70974585 | 16.484123 | 1 | 3 | 0 | 0.0093878279 | 93.878279 | 93.164376 | 10 | 0 | False |
| machine-3-7 | 0.015255369 | var1 | 0.12339288 | 0.64584986 | 8.0884888 | 1 | 4.6 | 0 | 0.010101731 | 101.01731 | 101.01731 | 10 | 0 | False |

## Standalone xLSTMAD-F route

Status: `FINAL_STANDALONE_ROUTE_IMPOSSIBLE`
High-FPR machines: ['machine-2-8', 'machine-3-11', 'machine-3-7']
Best-case 28-machine macro FPR: 0.036220173

## Complement-route feasibility bounds

```json
{
  "audit_kind": "logical_feasibility_only_no_efficacy_decision",
  "bounds": {
    "ap_above_prevalence_count": {
      "impossible": false,
      "maximum_achievable": 28,
      "observed_count": 9,
      "required": 20
    },
    "bootstrap_lower_95": {
      "best_case_lower_95": 0.4999518485981565,
      "impossible": false,
      "required_strictly_greater_than": 0.0,
      "resampling_unit": "paired machine",
      "samples": 10000,
      "seed": 901
    },
    "catastrophic_count": {
      "impossible": false,
      "maximum": 2,
      "observed_count": 0,
      "observed_machines": []
    },
    "high_fpr_count": {
      "impossible": true,
      "maximum": 2,
      "observed_count": 7,
      "observed_machines": [
        "machine-1-7",
        "machine-1-5",
        "machine-2-4",
        "machine-2-8",
        "machine-3-2",
        "machine-3-11",
        "machine-3-7"
      ]
    },
    "macro_event_detection": {
      "best_case": 0.9892857142857142,
      "impossible": false,
      "minimum": 0.5,
      "unopened_assumption": "all 19 event detection rates equal one"
    },
    "macro_normal_point_fpr": {
      "best_case": 0.14044195120613803,
      "impossible": true,
      "maximum": 0.02,
      "unopened_assumption": "all 19 FPRs equal zero"
    },
    "mean_delta_ap": {
      "best_case": 0.6785441537688943,
      "impossible": false,
      "minimum": 0.02,
      "unopened_delta_upper_bound": 1.0
    },
    "median_ap_over_prevalence": {
      "best_case": 23436.0,
      "impossible": false,
      "minimum": 1.5,
      "unopened_ratio_upper_bounds": {
        "machine-1-1": 28223,
        "machine-1-2": 23438,
        "machine-1-4": 23451,
        "machine-1-6": 23433,
        "machine-1-8": 23443,
        "machine-2-1": 23438,
        "machine-2-2": 23444,
        "machine-2-3": 23433,
        "machine-2-5": 23433,
        "machine-2-6": 28487,
        "machine-2-9": 28466,
        "machine-3-1": 28444,
        "machine-3-10": 23437,
        "machine-3-3": 23447,
        "machine-3-4": 23431,
        "machine-3-5": 23435,
        "machine-3-6": 28470,
        "machine-3-8": 28448,
        "machine-3-9": 28457
      }
    },
    "positive_delta_count": {
      "impossible": false,
      "maximum_achievable": 21,
      "observed_count": 2,
      "required": 20
    }
  },
  "decision": "FINAL_COMPLEMENT_ROUTE_IMPOSSIBLE",
  "impossible_components": [
    "high_fpr_count",
    "macro_normal_point_fpr"
  ],
  "observed_catastrophic_machines": [],
  "observed_delta_AP": [
    -0.00030589793191759806,
    4.8099432698248124e-05,
    -9.809140328278024e-06,
    0.00018523036666584503,
    -0.000680897310626094,
    0.0,
    0.0,
    0.0,
    -4.198874507081729e-07
  ],
  "observed_high_fpr_machines": [
    "machine-1-7",
    "machine-1-5",
    "machine-2-4",
    "machine-2-8",
    "machine-3-2",
    "machine-3-11",
    "machine-3-7"
  ],
  "observed_machines": [
    "machine-1-7",
    "machine-1-3",
    "machine-1-5",
    "machine-2-4",
    "machine-2-7",
    "machine-2-8",
    "machine-3-2",
    "machine-3-11",
    "machine-3-7"
  ],
  "optimistic_bootstrap_mean_delta_AP": 0.6785441537688943,
  "stage1_pass_permitted": false,
  "unopened_eligible_label_lengths": {
    "machine-1-1": 28223,
    "machine-1-2": 23438,
    "machine-1-4": 23451,
    "machine-1-6": 23433,
    "machine-1-8": 23443,
    "machine-2-1": 23438,
    "machine-2-2": 23444,
    "machine-2-3": 23433,
    "machine-2-5": 23433,
    "machine-2-6": 28487,
    "machine-2-9": 28466,
    "machine-3-1": 28444,
    "machine-3-10": 23437,
    "machine-3-3": 23447,
    "machine-3-4": 23431,
    "machine-3-5": 23435,
    "machine-3-6": 28470,
    "machine-3-8": 28448,
    "machine-3-9": 28457
  },
  "unopened_machines": [
    "machine-1-1",
    "machine-1-2",
    "machine-1-4",
    "machine-1-6",
    "machine-1-8",
    "machine-2-1",
    "machine-2-2",
    "machine-2-3",
    "machine-2-5",
    "machine-2-6",
    "machine-2-9",
    "machine-3-1",
    "machine-3-3",
    "machine-3-4",
    "machine-3-5",
    "machine-3-6",
    "machine-3-8",
    "machine-3-9",
    "machine-3-10"
  ]
}
```

## xLSTM-F versus LSTM-F diagnostic

Mean paired AP difference: -0.0014374517
Machines with positive xLSTM-F minus LSTM-F AP: 2/9
This comparison is descriptive and does not support an xLSTM-specific superiority claim.

## Execution accounting

```json
{
  "anomaly_metrics_computed": false,
  "execution_manifest": "reports/adaptive_normality_m1_smd/stage1b_r/execution_calibration_manifest.json",
  "machines": [
    "machine-1-7",
    "machine-1-3",
    "machine-1-5",
    "machine-2-4",
    "machine-2-7",
    "machine-2-8",
    "machine-3-2",
    "machine-3-11",
    "machine-3-7"
  ],
  "peak_allocated_bytes": {
    "machine-1-3": 3775808000,
    "machine-1-5": 3775808000,
    "machine-1-7": 3775744512,
    "machine-2-4": 3775808000,
    "machine-2-7": 3775744512,
    "machine-2-8": 3775744512,
    "machine-3-11": 3775808000,
    "machine-3-2": 3775808000,
    "machine-3-7": 3775808000
  },
  "peak_reserved_bytes": {
    "machine-1-3": 3854565376,
    "machine-1-5": 3854565376,
    "machine-1-7": 3854565376,
    "machine-2-4": 3854565376,
    "machine-2-7": 3854565376,
    "machine-2-8": 3854565376,
    "machine-3-11": 3854565376,
    "machine-3-2": 3854565376,
    "machine-3-7": 3860856832
  },
  "resumed_machines": [
    "machine-1-7",
    "machine-1-3",
    "machine-1-5",
    "machine-2-4",
    "machine-2-7"
  ],
  "schema": "adaptive-normality-m1-stage1b-r-execution-summary-v1",
  "score_manifest": "reports/adaptive_normality_m1_smd/stage1b_r/score_manifest.json",
  "selected_epochs": {
    "machine-1-3": 49,
    "machine-1-5": 48,
    "machine-1-7": 49,
    "machine-2-4": 49,
    "machine-2-7": 48,
    "machine-2-8": 47,
    "machine-3-11": 13,
    "machine-3-2": 50,
    "machine-3-7": 47
  },
  "source_commit": "2eda60d024d2a9149d62de5161ca76916a085942",
  "test_labels_read": false,
  "training_seconds": 53703.74699993804,
  "wall_time_seconds": 25429.857301197946
}
```
