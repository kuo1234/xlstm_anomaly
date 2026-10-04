# User clarification — source disturbance versus operational safety

During P2, the user explicitly chose: separate “source fault/disturbance occurred” from “operation is unsafe”. A controller may compensate a disturbance, and measured53channels may not expose harmful consequences. This is a possible identifiability issue, not a verified assertion about any selected fault.

P2 source-label detection targets remain frozen and unchanged: report FAULT recall/ranking and benign source NORMAL_B false alarms. These are SOURCE DISTURBANCE detection metrics, not unsafe-operation recall, safe-admission evidence or a hazard probability. Unsafe-operation ground truth is unavailable here; mark it NOT_EVALUABLE. No hindsight relabeling of weak faults as safe. No removal of source faults from primary metrics.

For subsequent #16 decisions, verified source health/operating labels, disturbance activation and independently justified operational risk must remain distinct. External command/alarm/context may change assumptions; source fault IDs/states must not silently become model inputs.
