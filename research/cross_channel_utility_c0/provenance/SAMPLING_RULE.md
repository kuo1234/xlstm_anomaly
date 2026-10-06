# Pre-acquisition data-only rule

2026-10-06, before any model fitting or scores. Phase A may STOP from literature alone; these samples qualify sources, not utility.

Standard candidates: ETTh1 (one ETT source family) and Weather (Jena). MixBench candidates: AQShunyi (single monitoring station, distinct from ETT) and HouseholdPower (single household); chosen for interpretable system/channel identities and modest D, not the size of published model gains. Time-HD candidate: Electricity/energy panel, conditional on official release metadata.

Bounded acquisition: at most one complete ETTh1 CSV <=5MB, plus metadata/README and at most the first 256 rows of each remaining official released candidate if a versioned exact asset can be resolved without restricted-access bypass. Do not substitute another preprocessed release for blocked MixBench/Time-HD files. No forecasts, correlations, source selection, fitting or performance inspection. The literature already disclosed published aggregate outcomes; those are not this audit's results and must not be used to reorder samples.

Exclude pilot eligibility if timestamp/channel identity, exact preprocessing, split/available-covariate cutoffs or raw asset identity cannot be traced. Missing values/structural absent channels and source-family duplication remain explicit. Do not tune a gap into existence. These rules are a data inspection record, not an executable model/pilot seal.

Metadata resolution before prefix reads: the Time-HD energy panel candidate was resolved to the official Meter config / smart_meters_in_london.csv, rather than its separate ECL config. This was chosen from system/channel metadata before reading null counts and without any forecast fit. Weather prefix came from the same author-linked Time-HD release and is explicitly a mirror, not certified original Jena acquisition.
