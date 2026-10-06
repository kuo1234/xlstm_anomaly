# Injection-molding interval feasibility — separate from negative pharma probe

2026-10-06, before any injection prediction outcomes. Existing Ridge + split-conformal measurement, no new network. Goal: confirm that an independent physical-quality prediction/evaluation task is executable and characterize future-cycle precision/coverage; not claim method novelty or safety of skipping metrology.

Fixed asset: author-linked dataset1.zip at scatimdata7bd35941d75c97a3f276439377dc430ab47402be. Primarytarget weight; exclude distanceA, weight, cycle_counter from inputs. Join only physical-labelled cycle IDs to both curves; all1167labelledcycles have curves; seven curveswithoutquality remain reported, excluded by label availability, not outcomes. Comma-decimal parsing explicit.

Variants: Ridge(alpha=10), scalar-only vs scalar+curve mean/std/max/integral. No HPO. Two evaluation protocols: sortedcyclecounter60/20/20% propertrain/calibration/test; seededrandom permutation ofcycles(seed20261007) at same fractions as retrospectivediagnostic ofcommonrandombenchmark. Testpopulationsdiffer, so difference is descriptive, not causal estimate ofsplit harm. Fullcurves are post-cycle data: no within-cycle leadtime claim. Scaler/imputationtrain-only; no targetnormalization.

Nominalsplit-conformalcoverage90%; radius kthabsresidual, k=ceil((ncal+1)*0.90), cappedonlyifneeded via infinity. Report originalscaleRMSE,MAE,R²,coverage,intervalwidth; scientificunit cycle with oneequipment/sourcefamily. Row-order supportsfuture-cyclevalidation, not recoveredwall-clock days/DoEcondition IDs. No exchangeability guarantee fororderedcycle/drift; empiricalcoverage only.

Exactly4Ridgefits,0neural; no dataset/target/alpha/policy replacement afterresults. Mean/trainbaseline forpredictionfeasibility. Anyasset/join/nonfinite failureSTOP. A positive fit onlydemonstratesboundedtaskfeasibility, not novelarchitecture or operationalcostsavings. Commit/pushmanifest+scriptbeforefit, recordexecution andall4arms. Pharmaresults/seal remain unchanged.
