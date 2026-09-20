# Standalone LSTM diagnostic results

Status: **POST-HOC / EXPLORATORY**

## Reconstructed primary effect

```text
mean Delta_L_own       0.14296629419144774
median                  0.14348919951372090
minimum                 0.12343624704555345
maximum                 0.16518666527010928
positive units          50 / 50
units >= +0.02          50 / 50
positive detector seeds 5 / 5
seed means >= +0.02     5 / 5
positive sources        10 / 10
source means >= +0.02   10 / 10
```

The aggregate algebra check is:

```text
0.14251889179304736 - (-0.00044740239840040496)
= 0.14296629419144774
```

The values above are reconstructed from the authoritative arrays, not entered
as a target.

## Detector-seed means

| seed | Delta_L_own |
|---:|---:|
| 11 | 0.1403079385 |
| 22 | 0.1449215702 |
| 33 | 0.1394592059 |
| 44 | 0.1405850634 |
| 55 | 0.1495576930 |

## Test-source means

| source | Delta_L_own |
|---:|---:|
| 3000 | 0.1364330142 |
| 3001 | 0.1504317202 |
| 3002 | 0.1420621901 |
| 3003 | 0.1505905960 |
| 3004 | 0.1406777565 |
| 3005 | 0.1369698626 |
| 3006 | 0.1495220808 |
| 3007 | 0.1520776366 |
| 3008 | 0.1281451972 |
| 3009 | 0.1427528876 |

## Exploratory uncertainty

- Hierarchical bootstrap: 95% CI `[0.1379040881, 0.1477015553]`, 10,000
  draws, seed 901.
- Source-cluster sign-flip: raw p `0.001953125`, exact enumeration over the
  10 source clusters, seed metadata 902.

These quantities are descriptive post-hoc summaries. They were not added to
Holm correction and do not create a new GO/STOP rule.

## Recovery limits

Scenario-level arrays in the committed audit are shape metadata only, so
standalone LSTM scenario effects are
`NOT_RECOVERABLE_FROM_CONSOLIDATED_ARTIFACTS`.

The committed audit likewise lacks the two standalone shared-CANDI AP arms;
`Delta_L_shared` is
`NOT_RECOVERABLE_FROM_CONSOLIDATED_ARTIFACTS`. Duration/severity standalone
AP arrays are unavailable for the same reason. No inference or re-extraction
was performed to fill these gaps.
