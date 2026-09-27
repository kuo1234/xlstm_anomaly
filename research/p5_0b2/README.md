# P5-0B2 pre-label method and protocol seal

**Review state:** Astra review passed; terminal status is
`P5_0B2_PROTOCOL_SEALED` (authorizes only the next SOURCE-only development
phase).

This directory freezes the detector, source-only development procedure, label
firewall, target prefix adjudication contract, readiness selection procedure,
threshold state, acquisition boundary, evaluator outcomes, and next-stage
information boundary before any TARGET prefix eligibility result is exposed.
It does not execute any of those data-dependent stages.

## Frozen structural inputs

The controlling base is commit
`96e7afa9696303d31e5b7f0163349a97d53ce029`. The P5-0B1R role seal is pinned
by SHA-256
`00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f`.
The fixed inventory is 74 SOURCE, 16 TARGET, and 3 unsupported entities in
five exact eligible `(manufacturer, configuration_type)` strata. Target starts
remain the first raw-row timestamps. Acquisition uses raw timestamped rows at
looks 144, 288, 576, 1152, and 2304; `N_max=2304`, elapsed cap 64 days, primary
purge 0, and the common suffix starts strictly after raw observation 2304.
Hashes for the referenced P5-0B1R structural artifacts are recorded in
`structural_inputs_seal.json`.

`feature_projection.json` freezes an ordered continuous-sensor name projection
from each eligible stratum's committed common intersection. It excludes
status/mode and other unapproved columns before strict detector-schema
validation, so raw union-only columns do not create a schema mismatch.

## Selected detector reference

The specified commit `ced470e1386066931bad32f3cb6e24bac9c5bb89` is EnergyFaultDetector
v0.7.1, not v0.3.0. The paper-cited v0.3.0 tag resolves to
`9e0d65074c88e51e180e3bf37f580280bbb54496` and does not contain the later
PreDist loader. The primary reference is explicitly corrected to v0.7.1's
generic dense autoencoder and row-wise RMSE components. The event-specific
PreDist loader/protocol is excluded. See `detector_backbone_audit.md`.

## Phase boundary

No source or target semantic label payload, target raw value, target score,
target prefix eligibility result, or PreDist model was accessed or produced
while sealing this protocol. Public code/docs and committed P5-0B1R structural
artifacts were used. The next authorized stage may run only the sealed source
label firewall and SOURCE-only model/readiness development. It may open the
74 SOURCE operational files from a SOURCE-only projection of the pinned
structural manifest; each manifest row has a unique raw path. It may not open
any TARGET raw path or TARGET label payload. TARGET prefix adjudication and
all later TARGET access remain unauthorized.

The fixed TARGET counts across the five strata are `5, 1, 4, 4, 2`. The
pooled success denominator remains all 16 entities, and unavailable outcomes
count as failures; there is no minimum suffix-evaluable count per stratum.
An unavailable SOURCE model or frozen margin bars a pooled claim.

## Artifact map

The normative documents and their hashes are listed in `protocol_seal.json`.
`canonical_sequence.md` defines the only permitted phase order. `final_gate.md`
records the terminal gate and any protocol correction.
