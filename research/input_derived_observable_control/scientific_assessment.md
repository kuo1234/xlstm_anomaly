# Scientific assessment — P1r

## Outcome (frozen wording from `protocol.md`)

- **xLSTM — `NO_RESOLVED_ADDITIONAL_UTILITY`.** Under the frozen HGB decoder, no additional
  predictive/decodable utility of `internal234` beyond the input-derived observable summary P1r
  is resolved for xLSTM: source-level ΔAP −0.00023259 [−0.00076128, +0.00029149].
- **Matched LSTM — `NO_RESOLVED_ADDITIONAL_UTILITY`.** Under the frozen HGB decoder, no
  additional predictive/decodable utility of `internal234` beyond the input-derived observable
  summary P1r is resolved for matched LSTM: source-level ΔAP +0.00028937
  [−0.00041494, +0.00095887].

The evidence is exploratory: three detector seeds and one synthetic generator.

## What this does and does not establish

- **Scope.** The result concerns only additional predictive/decodable utility beyond the
  temporally matched, bounded input-derived summary P1r under the frozen decoder. It is not
  information-theoretic. `internal234` is a deterministic function of the causal input window,
  so information-theoretic superiority over the full observation was out of scope in principle,
  whatever the outcome.
- **One summary only.** P1r closes the predeclared synthetic input-derived-control stage. It
  does not close every possible observable representation. Another summary, decoder or budget
  could give a different number, and none of these is authorised (see "Last control" below).
- **Relation to the residual-derived results.** They are unchanged as records. Against the
  temporally matched residual-derived summary O1r, `internal234` retained a positive increment
  under the frozen decoder (+0.015165 and +0.011252, 30/30 cells each). Against P1r, no
  increment is resolved. The internal-state increment in this synthetic ladder is therefore
  relative to score/history and residual-derived summaries, and is not resolved relative to a
  bounded summary of the scaled input window.
- **Descriptive only.** `H+P1r` reaches a higher test AP than `H+O1r+internal234` in all six
  runs (see `results.md`). This comparison is not tested, and it carries no inference beyond
  the table.
- **Backbones.** Both backbones give the same classification. No backbone-specific mechanism,
  no ranking of backbones, and no causal, safe-adaptation, contamination or deployment claim
  follows.

## Consequence for the claim ladder

L1c-P ("`internal234` retains additional predictive/decodable utility under the fixed decoder
beyond the temporally matched input-derived observable summary P1r") is **not supported at this
resolution** (`NO_RESOLVED_ADDITIONAL_UTILITY` for both backbones). L1a, L1b, L1c and L1c-NL are
unchanged.

## Last control

As predeclared, P1r is the last synthetic observable-control experiment. None of the following
is authorised from this result:

- a further observable summary;
- a further decoder;
- a further HGB budget;
- an MLP or CNN;
- W128/W256;
- a persistent-state experiment;
- a post-hoc rescue control.

Next steps: interpret P1r, consolidate it, then move to the real-data measurement validation
(R0).
