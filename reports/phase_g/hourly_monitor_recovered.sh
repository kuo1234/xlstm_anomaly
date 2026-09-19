#!/usr/bin/env bash
set -u

# Read-only hourly monitor for the single authorized recovered Phase-G1
# continuation.  This script never starts, retries, audits, or mutates the
# scientific execution; it records only process/ledger/artifact metadata.
root="/home/p76141495/home/xlstm_anomaly"
seal="069cdd227e26c1c4e3633bc6088b31fd71a3ae92"
output_dir="$root/reports/phase_g1_recovered_execution_v1"
ledger="$output_dir/g1_continuation_ledger.jsonl"
timestamp="$(date --iso-8601=seconds)"

pid=""
while read -r candidate_pid candidate_args; do
  if [[ "$candidate_args" == *"scripts/phase_g1_continue_from_cache.py"* && "$candidate_args" == *"$seal"* && "$candidate_args" != rtk\ * ]]; then
    pid="$candidate_pid"
    break
  fi
done < <(ps -eo pid=,args=)

if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
  process_state="running"
else
  process_state="not_running"
  pid="-"
fi

if [[ -f "$ledger" ]]; then
  ledger_lines="$(wc -l < "$ledger" | tr -d ' ')"
  continuation_starts="$(awk '/"event": "continuation_start"/ {n++} END {print n+0}' "$ledger")"
  continuation_completes="$(awk '/"event": "continuation_complete"/ {n++} END {print n+0}' "$ledger")"
  failures="$(awk '/"event": "process_exception"|"event": "continuation_failure"/ {n++} END {print n+0}' "$ledger")"
  last_event="$(awk -F'"event": "' 'NF > 1 {split($2,a,"\""); event=a[1]} END {print event}' "$ledger")"
  last_event="${last_event:-unknown}"
else
  ledger_lines="0"
  continuation_starts="0"
  continuation_completes="0"
  failures="0"
  last_event="ledger_missing"
fi

if [[ -d "$output_dir" ]]; then
  output_bytes="$(du -sb "$output_dir" 2>/dev/null | awk '{print $1}')"
  output_files="$(find "$output_dir" -type f -printf '.' 2>/dev/null | wc -c | tr -d ' ')"
else
  output_bytes="0"
  output_files="0"
fi

head="$(git -C "$root" rev-parse HEAD 2>/dev/null || printf 'unavailable')"
if [[ "$head" == "$seal" ]]; then
  head_state="expected"
else
  head_state="changed"
fi
disk_free="$(df -P -h "$root" | awk 'NR==2 {print $4}')"

printf '%s process=%s pid=%s seal=%s head=%s head_state=%s output_bytes=%s output_files=%s ledger_lines=%s starts=%s completes=%s failures=%s last_event=%s disk_free=%s\n' \
  "$timestamp" "$process_state" "$pid" "$seal" "$head" "$head_state" \
  "$output_bytes" "$output_files" "$ledger_lines" "$continuation_starts" \
  "$continuation_completes" "$failures" "$last_event" "$disk_free"
