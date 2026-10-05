# D0 anti-confound audit

Source family is the primary summary unit. Released files are not treated as180/75 iid experiments; unknown native/crop/subject relations remain possible even after the known duplicate group is collapsed. One family’s seven high-D files do not provide seven independent confirmations of a dimensionality effect.

| family | n | origin | portfolio_gap | oracle_streaming_wins | portfolio_streaming_wins |
|---|---|---|---|---|---|
| CATSv2 | 5 | SIMULATED_SOURCE | -0.08191 | 0 | 0 |
| CreditCard | 1 | UNKNOWN_SOURCE | -0.00764 | 0 | 0 |
| Daphnet | 1 | MEASURED_FAMILY_DOCUMENTED | -0.07242 | 0 | 0 |
| Exathlon | 5 | MEASURED_FAMILY_DOCUMENTED | -0.02934 | 1 | 2 |
| GECCO | 1 | MEASURED_FAMILY_DOCUMENTED | -0.11961 | 0 | 0 |
| GHL | 23 | SIMULATED_SOURCE | -0.00304 | 5 | 17 |
| LTDB | 1 | MEASURED_FAMILY_DOCUMENTED | -0.00527 | 0 | 0 |
| MSL | 1 | MEASURED_FAMILY_DOCUMENTED | 0.13246 | 1 | 1 |
| OPPORTUNITY | 7 | MEASURED_FAMILY_DOCUMENTED | 0.03171 | 4 | 5 |
| SMAP | 5 | MEASURED_FAMILY_DOCUMENTED | -0.00160 | 3 | 2 |
| SMD | 15 | MEASURED_FAMILY_DOCUMENTED | -0.04664 | 4 | 7 |
| SWaT | 2 | MEASURED_FAMILY_DOCUMENTED | -0.25569 | 0 | 0 |
| TAO | 8 | MEASURED_FAMILY_DOCUMENTED | -0.16217 | 0 | 1 |

## Required removals

| removed | series | families | equal_family_mean_gap | positive_series | oracle_streaming_wins |
|---|---|---|---|---|---|
| none | 75 | 13 | -0.04778 | 35 | 18 |
| OPPORTUNITY | 68 | 12 | -0.05440 | 30 | 14 |
| GHL | 52 | 12 | -0.05151 | 18 | 13 |
| SMD | 60 | 12 | -0.04788 | 28 | 14 |
| SMAP+MSL | 69 | 11 | -0.06837 | 32 | 14 |
| GHL+CATSv2 | 47 | 11 | -0.04875 | 18 | 13 |

The fixed-portfolio absolute gap remains negative after every required removal, so Online dominance is not reversed by removing OPPORTUNITY, GHL, SMD, combined SMAP/MSL or both simulated families. This does not establish a causal source-independent drift effect. Full individual-family removal rows are in leave_family_out.csv.

The apparent D>80 Streaming region disappears entirely when OPPORTUNITY is removed: there is no remaining high-D sample, not a measured negative-dimensionality effect. Removing simulations reduces the drift set75→47; removing the unresolved CreditCard row additionally gives46 documented measured-family drift cases. ALL_RELEASED and MEASURED_SOURCE_ONLY therefore have different targets/mixtures, never silently pooled.

## Family-conditioned feature support

| contrast | supported_families | material_positive_families | material_negative_families | mean_family_contrast |
|---|---|---|---|---|
| CD | 4 | Exathlon, SMAP | none | 0.06802 |
| highD>80 | 0 | none | none | unknown / unsupported |
| point_flag | 0 | none | none | unknown / unsupported |
| duration>100 | 3 | none | MSL, SMAP, SMD | -0.08732 |
| prevalence>0.05 | 7 | none | MSL, OPPORTUNITY, SMAP, SMD, SVDB | -0.06406 |
| events>10 | 4 | MITDB, SMD | CATSv2 | -0.00263 |
| train_ratio>0.2 | 6 | SMD | CATSv2, MITDB, OPPORTUNITY | -0.04894 |
| length>20000 | 1 | OPPORTUNITY | none | 0.12910 |
| continuous | 3 | SMAP | none | 0.01989 |
| change_point | 4 | Exathlon, SMAP, SMD | none | 0.08179 |
| periodic | 2 | CATSv2, SMD | none | 0.13368 |
| random_walk | 2 | Exathlon, SMD | none | 0.13275 |

Positive change-point associations across three families are retained rather than erased. They still lack>=3 measured families with a supported CP contrast **within drift-only** and raw-score artifact exclusion. The duration claim loses a third consistent family when conditioning on prevalence; high-D and point-flag contrasts have no within-family cells meeting>=2 rows per side. Event-count direction flips under family leave-one-out. Descriptive prevalence associations remain but are label-derived and not a mechanism identification.

results/leave_method_feature_contrasts.csv reports all eight fixed-method removals. For CP, removing CNN/USAD/MemStream/SDOstream reduces material positive support to two families. results/fixed_pair_feature_contrasts.csv records every fixed pair rather than choosing a favorable pair. The failure map is not a best-of-pool selector.

Known-duplicate sensitivity: {'before_equal_family_gap': -0.07486726810281853, 'after_known_group_equal_family_gap': -0.07596613780956891, 'known_duplicate_collapse_only': True, 'unknown_duplicates_not_resolved': True}. Only verified Exathlon duplicates are collapsed; no assumption that unresolved files are native-independent follows.

Winner concentration is an ORACLE_ENVELOPE diagnostic. MCOD/LODA account for11/18 drift oracle wins, with remaining wins across MemStream/RSHash/SWKNN/HSTree/LEAP. Primary robust Streaming-win candidates number4 and span only MSL/SMD. They may motivate reviewer checks, but not D1 GO or a generic Streaming advantage claim.

Prevalence correlations and within-family ranks are in family_feature_associations.json / family_rank_associations.csv without significance tests. No random window split, iid series p-value, result-informed deletion, mutually exclusive drift recoding or architecture selection is used.
