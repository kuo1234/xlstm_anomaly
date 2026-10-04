"""Reporting only; does not fit, run policies, or select thresholds."""
import json,csv,io
import numpy as np
from base import OUT,sha,save,utc
def fmt(x):return "N/A" if x is None else f"{x:.4f}"
def avg(xs):return float(np.mean(xs)) if xs else None
def main():
 m=json.loads((OUT/"results/metrics.json").read_text());cfg=json.loads((OUT/"configs/pilot.json").read_text());manifest=json.loads((OUT/"results/run_manifest.json").read_text());r=m["results"]
 def group(pol,arm):return sorted([x for x in r if x["policy"]==pol and x["arm"]==arm],key=lambda x:x["physical_group"])
 summaries=[]
 for pol in cfg["policies"]:
  b=group(pol,"benign_B_with_anomalies");s=group(pol,"stationary_A_with_anomalies");t=group(pol,"semantic_fault_twin");allp=[x for x in r if x["policy"]==pol];v=[x for x in b if x["valid_before_censor"]]
  summaries.append({"policy":pol,"scientific_N":5,"formal_coverage":len(v)/5 if pol.startswith("QUARANTINE_") or pol=="FROZEN" else None,
   "median_valid_TTA":float(np.median([x["TTAccept"] for x in v])) if v else None,"TTA_values":[x["TTAccept"] for x in b],
   "B_preanomaly_FPR":avg([x["preanomaly_B_FPR"] for x in b]),"B_clean_all_FPR":avg([x["clean_B_FPR"] for x in b]),
   "stationary_FAR":avg([x["FAR_admit"] for x in s]),"stationary_short_admitted":sum(x["events"][0]["admitted"] for x in s),
   "stationary_long_admitted":sum(x["events"][1]["admitted"] for x in s),"stationary_mutations":sum(x["mutations"] for x in s),
   "twin_FAR":avg([x["FAR_admit"] for x in t]),"twin_fault_promotions":sum(x["fault_promotion_count"] for x in t),
   "all_strata_FAR":sum(x["negative_episodes_admitted"] for x in allp)/sum(x["negative_episodes"] for x in allp),
   "all_strata_negative_episodes_admitted":sum(x["negative_episodes_admitted"] for x in allp),"all_strata_negative_episodes":sum(x["negative_episodes"] for x in allp),
   "all_strata_contaminated_purity":sum(x["negative_unique_effective_ids"] for x in allp)/sum(x["unique_effective_ids"] for x in allp) if sum(x["unique_effective_ids"] for x in allp) else None,
   "all_strata_weighted_contamination":sum(x["negative_loss_weight"] for x in allp)/sum(x["loss_weight_total"] for x in allp) if sum(x["loss_weight_total"] for x in allp) else None,
   "B_event_recall":avg([x["all_anomaly_event_recall"] for x in b]),"B_point_recall":avg([x["all_anomaly_point_recall"] for x in b]),
   "oldA_preanomaly_delta":avg([x["common_old_A_snapshots"]["preanomaly_delta_initial"] for x in b]),
   "oldA_delta_range":[min(x["common_old_A_snapshots"]["preanomaly_delta_initial"] for x in b),max(x["common_old_A_snapshots"]["preanomaly_delta_initial"] for x in b)],
   "premature_B_promotions":sum(len(x["premature_formal_times"]) for x in b),"invalid_B_promotions":sum(x["invalid_formal_promotions"] for x in b)})
 save(OUT/"results/summary.json",{"utc":utc(),"gate":m["gate"],"policy_summaries":summaries,"physical_N":5,"technical_replicates":1,"no_iid_p_values":True})
 corrections=json.loads((OUT/"results/reporting_boundary_correction.json").read_text())
 boundary={x["trajectory"]:x for x in corrections["rows"]}
 lines=["# P4-B results","",f"**{m['gate']}** — STOP after Issue #18 review. No Q met the joint safe-delay gate.","",
 "This minimal deterministic rank2 linearAE pilot tests candidate/sample selection under a shared decoder SGD operator, not official M2N2/CANDI performance or universal admission safety. All135 trajectories completed; no architecture/Q/schedule/threshold rescue. Scientific N=5 physical groups; one deterministic fit per group, not135 independent samples.","",
 "## Main result","",
 "Q1 is exactly immediate mutation with a formal endpoint name. It accepts clean settled-B before censor in5/5 groups (latencies18,7,1,3,7; median7), but does not reduce stationary anomaly FAR (both1.0). At the pre-first-anomaly snapshot, oldA probe FPR increases .2051–.2617 above initial. Same-commit deltas are small because earlier/ongoing updates already damage A; initial-vs-horizon comparison was frozen prospectively to avoid hiding cumulative harm.","",
 "Q64/128/256/512 have0/5 valid benign acceptance before firstB anomaly. Q64 blocks stationary anomaly writes completely, but also makes no stationary writes at all; zero-write is not adaptation success. Its five late promotions are on actual B anomalies, not settled-B acceptance. LargerQ families never mutate any stream. No post-hoc shorter/intermediateQ family added.","",
 "Frozen preanomaly cleanB FPR is .3828–.5078: new-normal false-alarm problem is expressed. Immediate/Q1 and M2N2-style reduce it on all five groups but harm oldA; CANDI-style has only small B utility with this fixed bottleneck/reference geometry. Event recall remains1.0, while point recall and written fractions show extensive fault assimilation. High event recall does not certify safe normality.","",
 "## All-policy Pareto table","",
 "Macro values across5 groups, with paired variants retained. Formal coverage/TTA for native-style no-commit arms are N/A_NATIVE; first effective exposure is separate. All-strata FAR includes benign2+stationary2+twin1 negative episodes per group (25 opportunities per policy), not independent repeated checkpoints.","",
 "| Policy | Valid coverage | Median TTA | B FPR preanomaly | Stationary FAR | Twin FAR | All-strata FAR | B event / point recall | OldA FPR delta preanomaly |",
 "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
 for x in summaries:
  lines.append(f"| {x['policy']} | {fmt(x['formal_coverage']) if x['formal_coverage'] is not None else 'N/A_NATIVE'} | {fmt(x['median_valid_TTA'])} | {fmt(x['B_preanomaly_FPR'])} | {fmt(x['stationary_FAR'])} | {fmt(x['twin_FAR'])} | {fmt(x['all_strata_FAR'])} | {fmt(x['B_event_recall'])} / {fmt(x['B_point_recall'])} | {fmt(x['oldA_preanomaly_delta'])} |")
 lines+=["","Coverage0, latency N/A for FROZEN or unreleasedQ means censored failure, not instantaneous successful acceptance. Q64 later all-cleanB FPR may improve after writing anomalous data: this is excluded from preanomaly adaptation utility, not called benign success.","","## Contamination / ledger and duration evidence","","| Policy | Stationary short / long admitted (each /5) | Stationary mutations | All-strata unique negative purity | Weighted negative exposure fraction | Twin fault PROMOTE count | Premature / invalid benign PROMOTE |","|---|---:|---:|---:|---:|---:|---:|"]
 for x in summaries:
  lines.append(f"| {x['policy']} | {x['stationary_short_admitted']} / {x['stationary_long_admitted']} | {x['stationary_mutations']} | {fmt(x['all_strata_contaminated_purity'])} | {fmt(x['all_strata_weighted_contamination'])} | {x['twin_fault_promotions']} | {x['premature_B_promotions']} / {x['invalid_B_promotions']} |")
 lines+=["","Purity and weighted fraction have different denominators: unique effective IDs versus all nonzero optimization weights. Selected/pending not written. No-write purity=N/A. Native arms have zero formal PROMOTE count but can still admit negative data through parameter updates; FAR measures actual mutation, not endpoint labels.","",
 "Stationary long faults do not produce64 consecutive high-score points under this bottleneck, despite lasting512 samples. No claim that Q64 validates a legitimate regime: it filters uninterrupted alarm runs. UnderB, actual anomalies do yield long enough runs to triggerQ64 in5/5; retain both strata. Scores are mutable common-model outputs, not oracle segment truth.","",
 "## Frozen gate checks","","| Q | Coverage | Median latency | Stationary FAR reduction | Improved physical groups | Max event recall drop | Max oldA FPR deterioration | All criteria |","|---|---:|---:|---:|---:|---:|---:|---|"]
 for x in m["Q_gate_checks"]:
  lines.append(f"| {x['Q']} | {fmt(x['coverage'])} | {fmt(x['median_TTA'])} | {fmt(x['stationary_FAR_reduction'])} | {x['stationary_improved_groups']} | {fmt(x['max_event_recall_drop'])} | {fmt(x['max_old_A_FPR_delta'])} | {x['all_pass']} |")
 lines+=["","Stationary-FAR criterion is false forQ≥64 despite lower FAR because stationary writes=0. Retention checks requiring valid acceptance remain N/A/failed when coverage0, not interpreted as perfect retention. Verdict priority was frozen before fits (PROTOCOL/config). This supports neither useful safe delay nor a universally necessary adaptation-harm conclusion beyond this operator.","",
 "## Every benign physical group","","| Group | Policy | Preanomaly B FPR | Valid commit / TTA | First B write / wholly cleanB write | Transition alarms / clean points (corrected endpoint) | Recovery confirmation | OldA preanomaly delta |","|---|---|---:|---|---|---|---|---:|"]
 for gid in cfg["physical_groups"]:
  for pol in cfg["policies"]:
   x=next(q for q in r if q["physical_group"]==gid and q["policy"]==pol and q["arm"]=="benign_B_with_anomalies")
   rec=x["recovery_supplement"];recovery=str(rec.get("confirmation_time","CENSORED"))
   b=boundary[x["trajectory"]]["burden_until_first_in_transition_formal"]
   lines.append(f"| {gid} | {pol} | {fmt(x['preanomaly_B_FPR'])} | {x['valid_commit_time']} / {x['TTAccept']} ({x['formal_status']}) | {x['first_effective_B_exposure']} / {x['first_wholly_clean_settled_B_exposure']} | {b['alarms']} / {b['clean_points']} | {recovery} | {fmt(x['common_old_A_snapshots']['preanomaly_delta_initial'])} |")
 lines+=["","Reporting correction: raw frozen metrics had five negative-duration Q1 burden intervals because first global PROMOTE occurred in A before transition. Those raw values remain in metrics.json; reporting_boundary_correction.json uses the first formal endpoint at/after transition, censors/clips empty intervals, and separately reports burden through valid B commit. No model/policy/gate rerun or cutoff change. Q1 has12 pre-transitionA formal endpoints and40 transition-premature endpoints; the original52 early count combines both. The above formal-burden zero forQ1 is until the first in-transition alarm/commit (exclusive), not zero transition false alarms. Through valid B commit there are46/41/40/39/36 alarms in274/263/257/259/263 clean points. Both endpoint choices are disclosed; this metric correction has no role in the frozen final gate.", "", "Recovery is three original-timeline64-point blocks FPR≤.10,≥32 clean each, censored at firstB anomaly. It is not acceptance. METRICS/config give exact endpoints and valid-payload rules. Formal first commit can be premature/invalid even if a later new candidate has valid current-only payload; both counted.","",
 "## All135 trajectory outcomes","","| Group | Stratum | Policy | FAR | Purity | Weighted contamination | Updates / selected / optimization IDs | Formal PROMOTE / invalid | Event / point recall |","|---|---|---|---:|---:|---:|---|---|---|"]
 for x in r:
  lines.append(f"| {x['physical_group']} | {x['arm']} | {x['policy']} | {fmt(x['FAR_admit'])} | {fmt(x['contaminated_purity'])} | {fmt(x['weighted_contamination'])} | {x['mutations']} / {x['selected']} / {x['loss_exposure_count']} | {x['formal_promotions']} / {x['invalid_formal_promotions']} | {fmt(x['all_anomaly_event_recall'])} / {fmt(x['all_anomaly_point_recall'])} |")
 lines+=["","## Every physical negative episode","","| Group | Stratum | Policy | Episode [start,end) | Effective write fraction | Event / point recall | First alarm delay |","|---|---|---|---|---:|---|---:|"]
 for x in r:
  for e in x["events"]:
   lines.append(f"| {x['physical_group']} | {x['arm']} | {x['policy']} | {e['id']} [{e['start']},{e['end']}) | {fmt(e['written_fraction'])} | {e['event_recall']} / {fmt(e['point_recall'])} | {e['detection_delay']} |")
 lines+=["","## Causality, truth isolation and reproducibility","",
 f"Pre-result freeze commit {manifest['freeze_commit']}; pushed trace commit {m['pushed_trace_commit']}. Each remote SHA was verified before progressing. All runtime observations/model artifacts are hash-checked, no truth paths reach Runtime.step(x,t); runtime model config strips physical/arm IDs. Evaluator logs access only after trace manifest commit is a verified remote ancestor. Historical P4-A truth was already exposed; not strict confirmatory.",
 "",
 "45/45 benign/fault-twin full-ledger and parameter equality;15/15 Q1/immediate parameter parity. Semantic twin failure is mandatory and included above: successful benign actions mirror fault actions. FROZEN/largerQ absence of twin errors arises from no adaptation, not better legitimacy identification.",
 "",
 "16 tests passed before fits;3 additional reporting-boundary regression tests after outcomes (not a policy retune). Post-result independent audit verifies pre-update scores from previous snapshots, exact full-state hashes, weighted decoder SGD arithmetic and every effective ID at all622080 rows; this audit does not refit/run policies/change cutoffs. Full mutation ledger files and every timestep decoder snapshot are ignored onssh kuo; hashes/row counts/schema tracked in run_manifest and postrun_verification. Rollback NOT_IMPLEMENTED. No adapters, momentum state, scaler/EMA/reference/threshold/encoder mutations.",
 "",
 "Exact commands/environment/model/data/config hashes: provenance/environment.json, freeze.json, trace_seal.json and results/run_manifest.json. Complete metrics, oldA score quantiles pre/post/horizon/final, weighted exposures and access logs are JSON artifacts. Reproduce via frozen inputs and raw P4-A files; no local raw acquisition.",
 "",
 "Limitations: rank2 current-point model and gap0 candidate may reject benign intermittently alarming regimes; all Q≥64 censoring demonstrates this. Decoder-only adaptation has no regime partitioning and can trade new-mean utility for forgettingA. CANDI-style references in a fixed2D latent are not official end-to-end learned representations or SANA. One deterministic solver has no technical RNG replication;five source groups cover physical noise/fit variation only. Only this controlled generator/scoring/operator/gap/Q family was tested. Native official paths and TSB NOT_RUN; real timing/unsafe truth NOT_EVALUABLE. No RL, new feature/CV, classifier, generator changes or learned stopping.",
 "",
 "STOP: reviewer should decide whether external/context evidence or post-write verification merits a separately frozen task. Results do not authorize tuning intermediateQ, adding gap tolerance, changing representation, recurrence or RL."
 ]
 (OUT/"RESULTS.md").write_text("\n".join(lines)+"\n")
 # Flat per-trajectory export for review; structured details remain JSON.
 keys=["physical_group","arm","policy","FAR_admit","contaminated_purity","weighted_contamination","mutations","selected","loss_exposure_count","formal_promotions","invalid_formal_promotions","normal_FPR","all_anomaly_event_recall","all_anomaly_point_recall"]
 with (OUT/"results/per_trajectory.csv").open("w") as f:
  w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows([{k:x[k] for k in keys} for x in r])
 print("report/all-policy and all135 rows written",flush=True)
if __name__=="__main__":main()
