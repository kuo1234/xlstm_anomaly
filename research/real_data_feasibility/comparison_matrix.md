# Role matrix (feasibility, not performance)

`Available` means raw bytes are locally inspectable, not that an experiment is authorized. A conditional candidate needs acquisition, license and a frozen split/label protocol. See [label semantics](label_semantics.md).

### Tier 1 — standard real-world TSAD comparison

| Candidate | Real multivariate signal / anomaly truth | Availability and caveat |
|---|---|---|
| SMD 1-8 strict anchor, M2N2 1-4/2-1 | 38 raw metrics, binary test points | M2N2 pair acquired; strict 1-8 sealed historically but bytes absent. No timestamps or drift truth. |
| MSL P-15 / SMAP T-3 | NASA per-series multivariate arrays and expert test intervals | Labels only; archive 403, exact dimensions pending. |
| SWaT Dec 2015 | 51 industrial variables, attack labels | Manual iTrust permission. |
| PSM (optional) | Approximately 25 metrics and test anomaly labels | Canonical package/terms not yet verified; no reason to expand minimal suite now. |

### Tier 2 — M2N2's explicit distribution-shift/new-normal set

| Exact series/release | Prior-work shift rationale | Current feasibility |
|---|---|---|
| SMD machine-1-4, machine-2-1 | M2N2 selects these two specifically for train/test shift | Acquired, original raw split, independently hashed; strongest low-friction pair. |
| MSL P-15, SMAP T-3 | Selected shifted NASA series | Official interval metadata acquired, arrays 403 at legacy S3; retain only if author-linked archive identity verified. |
| SWaT A1/A2 Dec 2015, WADI A2 Nov 2019 | Industrial train/test/new-normal examples; WADI substantial shift | Both manual iTrust; versions non-interchangeable with AnDri SWaT. |
| Yahoo A1-R20, A1-R55 | Two real univariate shifted series | Webscope manual; may complement but cannot establish multivariate recurrent-state claim alone. |
| CreditCard | Explicit low-shift control in M2N2 | Kaggle terms; irregular transaction events, not a regular sensor stream. |

M2N2's KLD/figures motivate the selection; they are not independent drift-onset annotations. Its benchmark results are not reused as this audit's scientific results. Source: [paper](https://ojs.aaai.org/index.php/AAAI/article/view/29210/30283) and [code README](https://github.com/carrtesy/M2N2).

### Tier 3 — drift/anomaly semantic validation

| AnDri family | Type of change/anomaly annotation | Suitability for exact four-way drift-active estimand |
|---|---|---|
| v2 ECG/IOPS | Native anomalies + **injected** transitions; generated schedules absent in current tree | No, until exact compositions/schedules and mixed labels recovered; then semi-synthetic, not independent real drift. |
| v2 Elec/Weather | Natural variation + **injected** anomalies, no independent drift intervals | No. |
| Current Sensor `real iot` | Upstream anomaly_point/pattern and change_point columns, paper-asserted expert annotation | Partial **onset-level** only; 3 changes across two univariate series, no duration/overlap class. |
| Current Climate/Traffic | Threshold-derived precipitation events / EWMA-calendar-derived traffic labels | No adjudicated benign drift-active ground truth. |
| Current SMD/SWaT | Binary anomaly/attack; VIF/crops | No. |

### Tier 4 — industrial anomaly external validation

| Candidate | Source-native attack label | Legitimate-drift ground truth |
|---|---|---|
| HAI 22.04 | `Attack` per second; 58 attack intervals in four tests (7+17+10+24) | **No**; ~730 MB + Git LFS setup. |
| SWaT Dec 2015 | Attack flag and physical run metadata | **No**. |
| WADI Nov 2019 | Attack-labeled test | **No**. |

HAI is a useful distinct industrial domain after acquisition, but none of Tier 4 may be sold as a true drift-vs-anomaly benchmark. [Official HAI README](https://github.com/icsdataset/hai) distinguishes `Attack` from normal operation, not planned benign regime shifts.
