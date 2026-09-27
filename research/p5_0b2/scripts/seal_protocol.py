"""Build the deterministic P5-0B2 artifact hash manifest.

This script reads only protocol files and the committed P5-0B1R structural
artifacts listed in the protocol. It does not access project data or labels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SEAL_PATH = Path("research/p5_0b2/protocol_seal.json")
ARTIFACTS = (
    "research/p5_0b2/README.md",
    "research/p5_0b2/structural_inputs_seal.json",
    "research/p5_0b2/feature_projection.json",
    "research/p5_0b2/detector_backbone_audit.md",
    "research/p5_0b2/detector_contract.md",
    "research/p5_0b2/preprocessing_contract.md",
    "research/p5_0b2/source_development_protocol.md",
    "research/p5_0b2/source_label_firewall.md",
    "research/p5_0b2/target_prefix_adjudication_contract.md",
    "research/p5_0b2/readiness_rule_contract.md",
    "research/p5_0b2/threshold_contract.md",
    "research/p5_0b2/evaluation_contract.md",
    "research/p5_0b2/canonical_sequence.md",
    "research/p5_0b2/final_gate.md",
    "research/p5_0b2/scripts/source_label_firewall.py",
    "research/p5_0b2/scripts/validate_protocol.py",
    "research/p5_0b2/scripts/seal_protocol.py",
    "research/p5_0b2/tests/test_source_label_firewall.py",
    "research/p5_0b2/tests/test_protocol_invariants.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_seal() -> dict[str, object]:
    paths = [ROOT / name for name in ARTIFACTS]
    missing = [name for name, path in zip(ARTIFACTS, paths) if not path.is_file()]
    if missing:
        raise SystemExit("PROTOCOL_SEAL_INPUT_MISSING")

    artifact_hashes = [
        {"path": name, "sha256": sha256(path)}
        for name, path in zip(ARTIFACTS, paths)
    ]
    firewall_hash = next(
        row["sha256"] for row in artifact_hashes
        if row["path"] == "research/p5_0b2/scripts/source_label_firewall.py"
    )
    return {
        "schema_version": "p5-0b2-protocol-seal-v1",
        "status": "P5_0B2_PROTOCOL_SEALED",
        "base_commit": "96e7afa9696303d31e5b7f0163349a97d53ce029",
        "branch": "research/p5-0b2-prelabel-protocol-seal",
        "role_seal_sha256": "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f",
        "energy_fault_detector": {
            "repository": "AEFDI/EnergyFaultDetector",
            "selected_version": "v0.7.1",
            "selected_commit": "ced470e1386066931bad32f3cb6e24bac9c5bb89",
            "paper_cited_version": "v0.3.0",
            "paper_cited_commit": "9e0d65074c88e51e180e3bf37f580280bbb54496",
            "decision": "generic dense MultilayerAutoencoder with external per-row RMSE; PreDist loader and event-specific procedure excluded",
        },
        "source_development": {
            "fold_algorithm": "SHA256(UTF8(P5-0B2-SOURCE-FOLD-v1|role_digest)); within exact strata, sorted by fold_digest then role_digest, assigned round-robin to five folds",
            "seed": 17,
            "source_label_firewall_version": "p5-0b2-source-label-firewall-v1",
            "source_label_firewall_sha256": firewall_hash,
            "detector_selection": "macro source-OOF AP, then AUROC, bottleneck width, learning rate, candidate ID",
            "readiness_scale": "selected detector candidate OOF SOURCE scores outside known fault/disturbance intervals; float64 type-7 IQR",
        },
        "threshold": {
            "estimator": "cumulative finite prefix empirical q99",
            "quantile": "NumPy quantile(method=linear), type 7, float64",
            "minimum_finite_scores": 200,
            "post_ready": "freeze first READY look threshold",
            "future_fpr_certificate": False,
        },
        "readiness_selection": {
            "candidate_families": [
                "fixed-N at each scheduled look",
                "always-ready at first supported look",
                "maximum-horizon at raw look 2304",
                "threshold stability",
                "score-distribution stability",
                "prefix-internal hold-forward exceedance",
                "marginal-gain plateau",
                "pairwise AND conjunctions",
                "never-ready",
            ],
            "primary_fixed_n_reference": 2304,
            "source_only_margin_selection": True,
            "selection_objective": "joint success fraction, acquisition cost, event recall, pointwise FPR, conjunct count, lexical candidate ID",
        },
        "evaluation": {
            "fixed_target_counts_ascii_stratum_order": [5, 1, 4, 4, 2],
            "pooled_success_denominator": 16,
            "minimum_suffix_evaluable_per_stratum": 0,
            "unavailable_outcomes_count_as_failure": True,
            "unavailable_source_model_or_margins_prohibit_pooled_claim": True,
        },
        "target_access": {
            "target_label_access": "NOT_AUTHORIZED",
            "target_raw_values_or_scores_accessed": False,
            "target_prefix_adjudication_performed": False,
            "suffix_evaluation_performed": False,
            "predist_training_performed": False,
            "next_stage": "P5-0B3 SOURCE-only development and source model/readiness-parameter seal",
        },
        "information_boundary": {
            "next_authorized_stage": "P5-0B3 SOURCE-only development only",
            "allowed_source_method_inputs": [
                "pinned protocol and public EnergyFaultDetector v0.7.1 source",
                "SOURCE role digests and exact SOURCE strata",
                "value-free automated_common_feature_intersection lists",
                "fixed global look and acquisition constants",
                "the 74 SOURCE operational files selected by a SOURCE-only manifest projection",
                "canonical SOURCE-only label intervals and released SOURCE audit fields",
            ],
            "target_label_access": "NOT_AUTHORIZED",
            "target_raw_paths_opened": False,
            "target_values_scores_missingness_or_eligibility_released": False,
            "source_label_csv_access": "sealed firewall process only; method receives SOURCE-only artifact",
            "source_raw_file_gate": "SOURCE-only manifest projection; one unique raw_path per role entry; open/hash only SOURCE paths",
        },
        "verification": {
            "synthetic_firewall_test_command": "python3 -m unittest research.p5_0b2.tests.test_source_label_firewall -v",
            "synthetic_firewall_tests": 19,
            "protocol_validator_command": "python3 -m research.p5_0b2.scripts.validate_protocol",
            "combined_test_count": 20,
            "astra_review": "PASS",
        },
        "sealed_artifacts": artifact_hashes,
    }


def main() -> None:
    payload = json.dumps(build_seal(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (ROOT / SEAL_PATH).write_text(payload, encoding="utf-8", newline="\n")
    print("PROTOCOL_SEAL_WRITTEN")


if __name__ == "__main__":
    main()
