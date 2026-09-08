"""Per-task component tables transcribed from docs/LEAD_CATALOGUE_SKELETON.md.

The executor validates plans against this table (ids, params, options, defaults,
``multi`` flags), runs components in the canonical order listed here and skips a
component whose ``requires`` dependency was not selected. ``config/tasks.yaml``
(A3) is generated from the same skeleton; behaviour never comes from it.
"""
from __future__ import annotations

from typing import Any

JOIN_PAIRS = [
    "medical_claims.member_id->members.member_id",
    "medical_claims.rendering_npi->providers.provider_npi",
    "medical_claims.billing_npi->providers.provider_npi",
    "pharmacy_claims.member_id->members.member_id",
    "pharmacy_claims.pharmacy_npi->providers.provider_npi",
    "adherence.member_id->members.member_id",
]
CAVEAT_IDS = [
    "synthetic_data",
    "sample_preview",
    "descriptive_only",
    "association_not_causation",
    "small_groups",
    "class_imbalance",
    "model_limitations",
    "no_operational_use",
]
BOOL = [True, False]


def P(options: list, default: Any, multi: bool = False) -> dict:
    return {"options": list(options), "default": default, "multi": multi}


def C(cid: str, default_selected: bool = False, params: dict | None = None, requires: list[str] | None = None) -> dict:
    return {"id": cid, "default_selected": default_selected, "params": params or {}, "requires": requires or []}


LOAD_TABLES = C("load_tables", True)
JOIN_CHECK = C("join_check", False, {"pairs": P(JOIN_PAIRS, [], multi=True)})
WRITE_REPORT = C(
    "write_report",
    True,
    {
        "caveats": P(CAVEAT_IDS, [], multi=True),
        "show_denominators": P(BOOL, False),
        "cite_artifacts": P(BOOL, False),
    },
)

T5_FEATURES = [
    "claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status",
    "billed_amount", "allowed_amount", "paid_amount", "service_units", "length_of_stay",
    "er_flag", "auth_required_flag", "fraud_pattern_type", "high_cost_flag",
    "member_sex", "member_race_ethnicity", "member_age_band", "member_payer_type",
]
T6_FEATURES = [
    "claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status",
    "billed_amount", "allowed_amount", "paid_amount", "service_units", "length_of_stay",
    "er_flag", "elective_flag", "preventive_flag", "auth_required_flag", "primary_icd10_cm", "drg_present",
    "high_cost_flag", "fraud_pattern_type", "claim_id", "member_id", "rendering_npi",
]
T7_FEATURES = [
    "claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status",
    "service_units", "length_of_stay", "er_flag", "elective_flag", "preventive_flag", "auth_required_flag",
    "primary_icd10_cm", "drg_present", "billed_amount", "allowed_amount", "paid_amount", "member_oop", "cob_amount",
    "high_cost_flag", "claim_id", "member_id",
]
MODELS = ["logistic_regression", "random_forest", "gradient_boosting"]
PREPROCESSING = C(
    "preprocessing",
    True,
    {"fit_on": P(["train_only", "all_data"], "all_data"), "scaling": P(["none", "standard"], "none")},
    requires=["feature_set", "split"],
)

# Shared by T3 / T10 (provider and specialty analyses) and T4 / T9 (denial analyses): the held-out transfer
# tasks of experiment 5 reuse the same components, option lists and defaults as the tasks they mirror (D-23),
# so the catalogue entries are the same objects and cannot drift apart.
PROVIDER_JOIN = C(
    "provider_join",
    False,
    {
        "provider_key": P(["rendering_npi", "billing_npi"], "rendering_npi"),
        "how": P(["inner", "left"], "inner"),
        "validate": P(["none", "many_to_one"], "none"),
    },
)
GROUP_COMPARISON = C(
    "group_comparison",
    True,
    {
        "group_by": P(["provider_specialty", "network_status", "provider_specialty+network_status"], ["provider_specialty"], multi=True),
        "metrics": P(
            ["claim_count", "paid_amount_sum", "paid_amount_mean", "denial_rate", "fraud_rate"],
            ["claim_count", "paid_amount_sum"],
            multi=True,
        ),
        "denominator": P(["all_claims", "adjudicated_claims"], "all_claims"),
        "min_group_size": P([0, 30, 50, 100], 0),
    },
)
PROVIDER_RANKING = C(
    "provider_ranking",
    False,
    {
        "metric": P(["claim_count", "paid_amount_sum", "denial_rate"], "claim_count"),
        "top_n": P([5, 10, 20], 10),
        "min_claims": P([0, 30], 0),
    },
)
DENIAL_CODE_RANKING = C(
    "denial_code_ranking",
    True,
    {"scope": P(["denied_claims", "all_claims"], "all_claims"), "quantify_missing": P(["none", "overall", "by_status"], "overall")},
)
DENIAL_RATE_BY_SEGMENT = C(
    "denial_rate_by_segment",
    True,
    {
        "segments": P(
            ["claim_type", "provider_specialty", "network_status", "place_of_service", "auth_required_flag"],
            ["claim_type"],
            multi=True,
        ),
        "denominator": P(["all_claims", "adjudicated_claims"], "all_claims"),
        "min_group_size": P([0, 30, 50, 100], 0),
    },
)
# Shared by T2 / T11 (portfolio descriptions), T7 / T12 (high-cost models) and T8 / T13 (executive briefs):
# experiment 5 v2's convention-dense held-out tasks reuse the same components, option lists and defaults as the
# tasks they mirror (D-24), so the catalogue entries are the same objects and cannot drift apart.
PORTFOLIO_COMPONENTS = [
    LOAD_TABLES,
    C(
        "claim_volume",
        True,
        {
            "by": P(
                ["claim_status", "claim_type", "cpt_category", "place_of_service", "network_status", "provider_specialty"],
                ["claim_status"],
                multi=True,
            ),
            "figure": P(BOOL, True),
        },
    ),
    C("denial_rate", True, {"denominator": P(["all_claims", "adjudicated_claims", "paid_and_denied"], "all_claims")}),
    C("fraud_prevalence", False, {"denominator": P(["all_claims", "adjudicated_claims"], "all_claims")}),
    C(
        "financial_summary",
        True,
        {
            "amount_columns": P(
                ["billed_amount", "allowed_amount", "paid_amount", "member_oop", "cob_amount"], ["paid_amount"], multi=True
            ),
            "statistics": P(["sum_mean", "sum_mean_quantiles"], "sum_mean"),
        },
    ),
    C(
        "monthly_trend",
        True,
        {
            "date_column": P(["service_date_from", "service_date_to", "adjudication_date"], "adjudication_date"),
            "metrics": P(["claim_count", "paid_amount_sum"], ["claim_count"], multi=True),
        },
    ),
    WRITE_REPORT,
]
HIGH_COST_COMPONENTS = [
    LOAD_TABLES,
    C("split", True, {"test_size": P([0.2, 0.25, 0.3], 0.25)}),
    C(
        "target_definition",
        True,
        {
            "amount_column": P(["paid_amount", "billed_amount", "allowed_amount"], "paid_amount"),
            "percentile": P([90, 95, 99], 95),
            "threshold_source": P(["train_only", "all_data"], "all_data"),
        },
        requires=["split"],
    ),
    C("feature_set", True, {"features": P(T7_FEATURES, ["claim_type", "billed_amount", "allowed_amount"], multi=True)}),
    PREPROCESSING,
    C(
        "models",
        True,
        {"models": P(MODELS, ["logistic_regression"], multi=True)},
        requires=["split", "target_definition", "feature_set", "preprocessing"],
    ),
    WRITE_REPORT,
]
BRIEF_SECTIONS = C(
    "brief_sections",
    True,
    {
        "sections": P(
            ["key_findings", "model_results", "limitations", "synthetic_caveats", "next_steps", "methodology"],
            ["key_findings", "model_results"],
            multi=True,
        ),
        "causal_language": P(["avoid", "allow"], "allow"),
        "cite_artifacts": P(BOOL, False),
    },
    requires=["collect_findings"],
)
PORTFOLIO_ARTIFACTS = [
    "claims_status_distribution.png", "monthly_claim_volume.png", "financial_summary.csv",
    "monthly_trend.csv", "report.md", "metrics.json",
]
HIGH_COST_ARTIFACTS = [
    "model_metrics.json", "threshold.json", "feature_list.json", "precision_at_k.png", "report.md", "metrics.json",
]
BRIEF_ARTIFACTS = ["executive_brief.md", "findings.json", "report.md", "metrics.json"]
PROVIDER_ARTIFACTS = ["group_comparison.csv", "group_comparison.png", "provider_ranking.csv", "report.md", "metrics.json"]
DENIAL_ARTIFACTS = ["denial_code_ranking.csv", "denial_rates_by_segment.csv", "denial_rate_by_segment.png", "report.md", "metrics.json"]

TASK_CATALOGUE: dict[str, dict] = {
    "T1": {
        "title": "Dataset reconnaissance",
        "input_tables": ["members", "providers", "medical_claims", "pharmacy_claims", "adherence"],
        "required_artifacts": ["data_contract.json", "missingness.csv", "report.md", "metrics.json"],
        "components": [
            LOAD_TABLES,
            C("schema_summary", True),
            C("missingness", True, {"scope": P(["top_10", "all_columns"], "top_10")}),
            C(
                "duplicate_check",
                False,
                {
                    "keys": P(
                        [
                            "medical_claims.claim_id", "pharmacy_claims.rx_claim_id", "members.member_id",
                            "providers.provider_npi", "adherence.member_id", "adherence.member_id+therapeutic_class",
                        ],
                        ["medical_claims.claim_id"],
                        multi=True,
                    )
                },
            ),
            C(
                "date_ranges",
                False,
                {
                    "columns": P(
                        [
                            "medical_claims.service_date_from", "medical_claims.service_date_to",
                            "medical_claims.adjudication_date", "pharmacy_claims.fill_date", "pharmacy_claims.paid_date",
                            "members.enrollment_start", "members.enrollment_end",
                        ],
                        ["medical_claims.service_date_from"],
                        multi=True,
                    ),
                    "consistency_checks": P(BOOL, False),
                },
            ),
            JOIN_CHECK,
            WRITE_REPORT,
        ],
    },
    "T2": {
        "title": "Claims portfolio description",
        "input_tables": ["medical_claims"],
        "required_artifacts": list(PORTFOLIO_ARTIFACTS),
        "components": list(PORTFOLIO_COMPONENTS),
    },
    "T3": {
        "title": "Provider and network patterns",
        "input_tables": ["medical_claims", "providers"],
        "required_artifacts": list(PROVIDER_ARTIFACTS),
        "components": [LOAD_TABLES, JOIN_CHECK, PROVIDER_JOIN, GROUP_COMPARISON, PROVIDER_RANKING, WRITE_REPORT],
    },
    "T4": {
        "title": "Denial analysis",
        "input_tables": ["medical_claims"],
        "required_artifacts": list(DENIAL_ARTIFACTS),
        "components": [LOAD_TABLES, DENIAL_CODE_RANKING, DENIAL_RATE_BY_SEGMENT, WRITE_REPORT],
    },
    "T5": {
        "title": "Fraud-pattern exploration",
        "input_tables": ["medical_claims", "members"],
        "required_artifacts": ["fraud_comparison.csv", "fraud_prevalence.png", "report.md", "metrics.json"],
        "components": [
            LOAD_TABLES,
            C("class_prevalence", True),
            C(
                "feature_comparison",
                True,
                {"features": P(T5_FEATURES, ["claim_type", "billed_amount", "fraud_pattern_type"], multi=True)},
            ),
            C("leakage_assessment", False),
            WRITE_REPORT,
        ],
    },
    "T6": {
        "title": "Baseline fraud model",
        "input_tables": ["medical_claims"],
        "target": "fraud_label",
        "required_artifacts": [
            "model_metrics.json", "confusion_matrices.png", "pr_curves.png", "feature_list.json", "report.md", "metrics.json",
        ],
        "components": [
            LOAD_TABLES,
            C(
                "feature_set",
                True,
                {"features": P(T6_FEATURES, ["claim_type", "billed_amount", "paid_amount", "fraud_pattern_type"], multi=True)},
            ),
            C("split", True, {"test_size": P([0.2, 0.25, 0.3], 0.25), "stratify": P(BOOL, False)}),
            PREPROCESSING,
            C(
                "models",
                True,
                {"models": P(MODELS, ["logistic_regression"], multi=True), "class_weight": P(["none", "balanced"], "none")},
                requires=["feature_set", "split", "preprocessing"],
            ),
            WRITE_REPORT,
        ],
    },
    "T7": {
        "title": "High-cost claim identification",
        "input_tables": ["medical_claims"],
        "required_artifacts": list(HIGH_COST_ARTIFACTS),
        "components": list(HIGH_COST_COMPONENTS),
    },
    "T8": {
        "title": "Executive brief",
        "input_tables": [],
        "required_artifacts": list(BRIEF_ARTIFACTS),
        "components": [
            C("collect_findings", True, {"sources": P(["T1", "T2", "T3", "T4", "T5", "T6", "T7"], ["T2", "T6"], multi=True)}),
            BRIEF_SECTIONS,
            WRITE_REPORT,
        ],
    },
    # Experiment 5 (D-23): two held-out transfer tasks that share T4's and T3's components, option lists and
    # defaults but ask different questions. They are executed by the same handler modules (see TASK_MODULES).
    "T9": {
        "title": "Denial hotspots",
        "input_tables": ["medical_claims"],
        "required_artifacts": list(DENIAL_ARTIFACTS),
        "components": [LOAD_TABLES, DENIAL_CODE_RANKING, DENIAL_RATE_BY_SEGMENT, WRITE_REPORT],
    },
    "T10": {
        "title": "Specialty spend and denials",
        "input_tables": ["medical_claims", "providers"],
        "required_artifacts": list(PROVIDER_ARTIFACTS),
        "components": [LOAD_TABLES, JOIN_CHECK, PROVIDER_JOIN, GROUP_COMPARISON, PROVIDER_RANKING, WRITE_REPORT],
    },
    # Experiment 5 v2 (D-24): three convention-dense held-out tasks sharing T2's, T7's and T8's components, option
    # lists and defaults while asking different questions. They are executed by the same handler modules (see
    # TASK_MODULES). T13's `collect_findings` is the one component whose options differ: its only sources are the
    # two tasks that precede it in this set.
    "T11": {
        "title": "Portfolio deep-dive",
        "input_tables": ["medical_claims"],
        "required_artifacts": list(PORTFOLIO_ARTIFACTS),
        "components": list(PORTFOLIO_COMPONENTS),
    },
    "T12": {
        "title": "High-cost model, wider net",
        "input_tables": ["medical_claims"],
        "required_artifacts": list(HIGH_COST_ARTIFACTS),
        "components": list(HIGH_COST_COMPONENTS),
    },
    "T13": {
        "title": "Brief for the CFO",
        "input_tables": [],
        "required_artifacts": list(BRIEF_ARTIFACTS),
        "components": [
            C("collect_findings", True, {"sources": P(["T11", "T12"], ["T11"], multi=True)}),
            BRIEF_SECTIONS,
            WRITE_REPORT,
        ],
    },
}


def components_of(task_id: str) -> dict[str, dict]:
    return {c["id"]: c for c in TASK_CATALOGUE[task_id]["components"]}


def canonical_order(task_id: str) -> list[str]:
    return [c["id"] for c in TASK_CATALOGUE[task_id]["components"]]


def default_plan(task_id: str) -> dict:
    """Every ``default_selected`` component with its default params (the naive baseline)."""
    steps = []
    for comp in TASK_CATALOGUE[task_id]["components"]:
        if comp["default_selected"]:
            steps.append({"component": comp["id"], "params": {n: s["default"] for n, s in comp["params"].items()}})
    return {"steps": steps, "skills_applied": [], "rationale": "catalogue defaults", "changes_summary": None}
