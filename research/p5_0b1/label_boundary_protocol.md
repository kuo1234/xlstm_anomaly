# P5-0B1 label boundary incident record

## Authorized boundary

The handoff authorized the official PreDist v2 download; archive path listing; hash-only handling of label/event tables; and reading raw observations plus entity, timestamp, feature-schema, manufacturer, and configuration metadata. It prohibited semantic access to normal/fault/disturbance/event/anomaly outcomes and required an immediate stop on accidental semantic access.

## Incident

The root `README.md` was opened and printed in full while inspecting allowed data documentation. It contains a table naming known unlabelled anomaly periods by manufacturer, substation, start/end time, and description. Those are anomaly-outcome metadata. Although this was documentation rather than a label CSV and no label/event table payload was opened, we treat the exposure conservatively as a boundary breach.

## Containment

- Recorded `LABEL_BOUNDARY_BREACH` as the terminal status.
- Stopped archive interpretation at once.
- Did not open label/event table payloads or calculate their hashes.
- Did not parse raw operational series or compute entity statistics, schema compatibility, cadence/gaps, horizons, candidate roles, or target splits.
- Did not write parser scripts or run parser tests.
- Kept the downloaded archive under `/tmp`; no archive or observations are tracked in Git.

The breach must be reviewed before any follow-on task. Any new task must decide whether to exclude the README from the allowed boundary, use an independently supplied label-blind structural documentation source, or stop using this archive. No implicit continuation is authorized by this incident record.
