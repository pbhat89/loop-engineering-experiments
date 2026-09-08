"""Executor tests (A6): default and expert plans for T1-T8 against the real data snapshot,
determinism, produced-key shapes, required artifacts and the structured error paths, plus the
experiment-5 v2 held-out chain T11 -> T12 -> T13 (D-24).

Data-dependent tests skip with a reason when ``data/raw`` is absent. No network, no goldens.
"""
from __future__ import annotations

import copy
import json
import time
from pathlib import Path

import pytest

from src.analyses.catalogue import TASK_CATALOGUE, default_plan
from src.task_runner import execute
from src.utils import REPO_ROOT

DATA_PRESENT = (REPO_ROOT / "data" / "raw" / "medical_claims.csv").is_file() and (REPO_ROOT / "data" / "raw" / "members.csv").is_file()
pytestmark = pytest.mark.skipif(not DATA_PRESENT, reason="data/raw is empty - run `uv run python -m src.download_data` first")

TASKS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
RUN_ID = "test_a6"

ALL_KEYS = TASK_CATALOGUE["T1"]["components"][3]["params"]["keys"]["options"]
ALL_PAIRS = TASK_CATALOGUE["T1"]["components"][5]["params"]["pairs"]["options"]

# Expert choices per the skeleton's golden conventions (leakage-free features, adjudicated denominators,
# service_date_from, stratified split, train_only fitting, all relevant caveats, denominators and citations).
FULL: dict[str, dict[str, dict]] = {
    "T1": {
        "load_tables": {}, "schema_summary": {}, "missingness": {"scope": "all_columns"},
        "duplicate_check": {"keys": ALL_KEYS},
        "date_ranges": {"columns": ["medical_claims.service_date_from", "medical_claims.service_date_to", "medical_claims.adjudication_date"], "consistency_checks": True},
        "join_check": {"pairs": ALL_PAIRS},
        "write_report": {"caveats": ["synthetic_data", "sample_preview"], "show_denominators": True, "cite_artifacts": True},
    },
    "T2": {
        "load_tables": {}, "claim_volume": {"by": ["claim_status", "claim_type"], "figure": True},
        "denial_rate": {"denominator": "adjudicated_claims"}, "fraud_prevalence": {"denominator": "all_claims"},
        "financial_summary": {"amount_columns": ["billed_amount", "allowed_amount", "paid_amount"], "statistics": "sum_mean_quantiles"},
        "monthly_trend": {"date_column": "service_date_from", "metrics": ["claim_count", "paid_amount_sum"]},
        "write_report": {"caveats": ["synthetic_data", "descriptive_only"], "show_denominators": True, "cite_artifacts": True},
    },
    "T3": {
        "load_tables": {}, "join_check": {"pairs": ["medical_claims.rendering_npi->providers.provider_npi"]},
        "provider_join": {"provider_key": "rendering_npi", "how": "inner", "validate": "many_to_one"},
        "group_comparison": {"group_by": ["provider_specialty", "network_status", "provider_specialty+network_status"], "metrics": ["claim_count", "paid_amount_sum", "paid_amount_mean", "denial_rate", "fraud_rate"], "denominator": "adjudicated_claims", "min_group_size": 30},
        "provider_ranking": {"metric": "claim_count", "top_n": 10, "min_claims": 30},
        "write_report": {"caveats": ["synthetic_data", "small_groups", "association_not_causation"], "show_denominators": True, "cite_artifacts": True},
    },
    "T4": {
        "load_tables": {}, "denial_code_ranking": {"scope": "denied_claims", "quantify_missing": "by_status"},
        "denial_rate_by_segment": {"segments": ["claim_type", "provider_specialty", "network_status", "place_of_service", "auth_required_flag"], "denominator": "adjudicated_claims", "min_group_size": 30},
        "write_report": {"caveats": ["synthetic_data", "small_groups"], "show_denominators": True, "cite_artifacts": True},
    },
    "T5": {
        "load_tables": {}, "class_prevalence": {},
        "feature_comparison": {"features": ["claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status", "billed_amount", "allowed_amount", "paid_amount", "service_units", "length_of_stay", "er_flag", "auth_required_flag", "high_cost_flag", "member_payer_type"]},
        "leakage_assessment": {},
        "write_report": {"caveats": ["synthetic_data", "class_imbalance", "association_not_causation", "no_operational_use"], "show_denominators": True, "cite_artifacts": True},
    },
    "T6": {
        "load_tables": {},
        "feature_set": {"features": ["claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status", "billed_amount", "allowed_amount", "paid_amount", "service_units", "length_of_stay", "er_flag", "elective_flag", "preventive_flag", "auth_required_flag", "primary_icd10_cm", "drg_present", "high_cost_flag"]},
        "split": {"test_size": 0.25, "stratify": True}, "preprocessing": {"fit_on": "train_only", "scaling": "standard"},
        "models": {"models": ["logistic_regression", "random_forest", "gradient_boosting"], "class_weight": "balanced"},
        "write_report": {"caveats": ["synthetic_data", "class_imbalance", "model_limitations", "no_operational_use"], "show_denominators": True, "cite_artifacts": True},
    },
    "T7": {
        "load_tables": {}, "split": {"test_size": 0.25},
        "target_definition": {"amount_column": "paid_amount", "percentile": 95, "threshold_source": "train_only"},
        "feature_set": {"features": ["claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status", "service_units", "length_of_stay", "er_flag", "elective_flag", "preventive_flag", "auth_required_flag", "primary_icd10_cm", "drg_present"]},
        "preprocessing": {"fit_on": "train_only", "scaling": "standard"},
        "models": {"models": ["logistic_regression", "random_forest", "gradient_boosting"]},
        "write_report": {"caveats": ["synthetic_data", "model_limitations", "no_operational_use"], "show_denominators": True, "cite_artifacts": True},
    },
    "T8": {
        "collect_findings": {"sources": ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]},
        "brief_sections": {"sections": ["key_findings", "model_results", "limitations", "synthetic_caveats", "next_steps", "methodology"], "causal_language": "avoid", "cite_artifacts": True},
        "write_report": {"caveats": ["synthetic_data", "no_operational_use"], "show_denominators": True, "cite_artifacts": True},
    },
}

# component -> (metric key, required sub-keys) ; None = value checked structurally elsewhere
COMPONENT_PRODUCES: dict[str, dict[str, tuple[str, list[str]]]] = {
    "T1": {
        "load_tables": ("tables", []), "schema_summary": ("schema", []),
        "missingness": ("missingness", ["scope", "per_table", "all_null_columns"]),
        "duplicate_check": ("duplicates", []), "date_ranges": ("date_ranges", []), "join_check": ("join_check", []),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T2": {
        "load_tables": ("tables", []), "claim_volume": ("claim_volume", ["total_claims", "by"]),
        "denial_rate": ("denial_rate", ["value", "numerator", "denominator", "numerator_definition", "denominator_definition", "denominator_option"]),
        "fraud_prevalence": ("fraud_prevalence", ["value", "numerator", "denominator", "denominator_option"]),
        "financial_summary": ("financial_summary", []),
        "monthly_trend": ("monthly_trend", ["date_column", "n_months", "first_month", "last_month", "unparseable_dates", "series"]),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T3": {
        "load_tables": ("tables", []), "join_check": ("join_check", []),
        "provider_join": ("provider_join", ["provider_key", "how", "validate", "rows_before", "rows_after", "unmatched", "providers_matched"]),
        "group_comparison": ("group_comparison", ["min_group_size", "denominator_option", "groups"]),
        "provider_ranking": ("provider_ranking", ["metric", "top_n", "min_claims", "rows"]),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T4": {
        "load_tables": ("tables", []),
        "denial_code_ranking": ("denial_code_ranking", ["scope", "codes", "missing_denial_codes"]),
        "denial_rate_by_segment": ("denial_rate_by_segment", ["denominator_option", "min_group_size", "segments"]),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T5": {
        "load_tables": ("tables", []),
        "class_prevalence": ("class_prevalence", ["positives", "negatives", "total", "prevalence", "imbalance_ratio"]),
        "feature_comparison": ("feature_comparison", []),
        "leakage_assessment": ("leakage_risks", ["label_derived_fields", "id_fields", "protected_attributes", "flagged_in_plan"]),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T6": {
        "load_tables": ("tables", []),
        "feature_set": ("feature_set", ["features", "n_categorical", "n_numeric", "id_fields_present", "label_derived_present"]),
        "split": ("split", ["test_size", "stratify", "seed", "n_train", "n_test", "prevalence_train", "prevalence_test"]),
        "preprocessing": ("preprocessing", ["fit_on", "scaling", "n_features_out"]),
        "models": ("models", []),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T7": {
        "load_tables": ("tables", []),
        "split": ("split", ["test_size", "seed", "n_train", "n_test"]),
        "target_definition": ("target_definition", ["amount_column", "percentile", "threshold_source", "threshold_value", "positive_rate_train", "positive_rate_test", "n_positive_train", "n_positive_test"]),
        "feature_set": ("feature_set", ["features", "n_categorical", "n_numeric", "id_fields_present", "target_derived_present"]),
        "preprocessing": ("preprocessing", ["fit_on", "scaling", "n_features_out"]),
        "models": ("models", []),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
    "T8": {
        "collect_findings": ("findings", []),
        "brief_sections": ("brief", ["sections", "causal_language", "cite_artifacts", "word_count", "n_numeric_statements", "n_cited_statements"]),
        "write_report": ("report", ["caveats", "show_denominators", "cite_artifacts", "sections"]),
    },
}
T6_MODEL_KEYS = ["precision", "recall", "f1", "pr_auc", "roc_auc", "confusion_matrix", "threshold", "n_test"]
T7_MODEL_KEYS = ["pr_auc", "roc_auc", "precision_at_top_5pct", "recall_at_top_5pct", "n_test"]
HEAD_KEYS = ["task_id", "run_id", "condition", "attempt", "seed", "generated_at", "plan_sha256", "plan", "tables"]


def full_plan(tid: str) -> dict:
    return {"steps": [{"component": c, "params": copy.deepcopy(p)} for c, p in FULL[tid].items()], "skills_applied": [], "rationale": "expert", "changes_summary": None}


def run_context(root: Path, condition: str, tid: str, attempt: int = 1) -> dict:
    return {
        "run_id": RUN_ID, "condition": condition, "task_id": tid, "attempt": attempt, "seed": 42,
        "output_dir": str(root / RUN_ID / condition / tid / f"attempt_{attempt}"),
        "manifest_path": "data/processed/manifest.json", "data_dir": "data/raw", "timeout_seconds": 600,
    }


def run(root: Path, condition: str, tid: str, plan: dict) -> tuple[dict, float]:
    t0 = time.perf_counter()
    res = execute({"task_id": tid, "components": TASK_CATALOGUE[tid]["components"]}, plan, run_context(root, condition, tid))
    dt = time.perf_counter() - t0
    print(f"[runtime] {tid} {condition}: {dt:.1f}s status={res['status']} errors={len(res['errors'])}")
    return res, dt


def assert_contract(res: dict, tid: str, plan: dict, require_all_artifacts: bool = True) -> None:
    out = Path(res["output_dir"])
    assert res["status"] == "ok", res["errors"]
    assert res["task_id"] == tid and res["seed"] == 42 and res["attempt"] == 1
    assert res["components_failed"] == [] and res["errors"] == []
    assert set(res["components_executed"]) == {s["component"] for s in plan["steps"]}
    # A default (naive) plan may legitimately miss a required artifact whose component is not
    # default_selected (e.g. T3 provider_ranking.csv) - that gap is for the evaluator to penalise.
    required = TASK_CATALOGUE[tid]["required_artifacts"] if require_all_artifacts else ["metrics.json", "report.md"]
    for name in required:
        assert (out / name).is_file(), f"{tid}: missing required artifact {name}"
    names = {Path(a).name for a in res["artifacts"]}
    assert {"metrics.json", "report.md"} <= names
    for a in res["artifacts"]:
        p = Path(a) if Path(a).is_absolute() else REPO_ROOT / a
        assert p.is_file(), a
        assert out.resolve() in p.resolve().parents, f"artifact outside output_dir: {a}"
    on_disk = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert on_disk == res["metrics"]
    assert Path(res["metrics_path"]).name == "metrics.json" and Path(res["report_path"]).name == "report.md"
    m = res["metrics"]
    for k in HEAD_KEYS:
        assert k in m, f"{tid}: metrics head missing {k}"
    assert m["plan"] == plan and len(m["plan_sha256"]) == 64
    for comp in res["components_executed"]:
        key, subkeys = COMPONENT_PRODUCES[tid][comp]
        assert key in m, f"{tid}: {comp} did not produce {key}"
        for sk in subkeys:
            assert sk in m[key], f"{tid}: {key} missing {sk}"
    for name, info in m["tables"].items():
        assert set(info) == {"rows", "columns"}
    report = (out / "report.md").read_text(encoding="utf-8")
    for heading in ("## Summary", "## Results", "## Artifacts", "## Method"):
        assert heading in report
    rp = next(s["params"] for s in plan["steps"] if s["component"] == "write_report")
    assert ("## Caveats" in report) == bool(rp.get("caveats"))
    if rp.get("cite_artifacts"):
        results = report.split("## Results", 1)[1].split("## Artifacts", 1)[0]
        bullets = [ln for ln in results.splitlines() if ln.startswith("- ")]
        assert bullets and all(ln.rstrip().endswith("]") and "[source: " in ln for ln in bullets)
    if rp.get("show_denominators"):
        assert " / " in report and " = " in report


def check_task_specific(res: dict, tid: str, full: bool) -> None:
    m = res["metrics"]
    out = Path(res["output_dir"])
    if tid == "T1":
        assert m["tables"]["medical_claims"]["rows"] == 12845 and m["tables"]["members"]["rows"] == 500
        if full:
            assert m["missingness"]["all_null_columns"]["medical_claims"] == ["dx3", "dx4", "dx5", "modifier1", "modifier2", "denial_reason_desc", "auth_number"]
            assert all(v["is_candidate_key"] for k, v in m["duplicates"].items() if k != "adherence.member_id")
            assert m["date_consistency"]["adjudication_before_service_end"] == 36
            assert m["join_check"]["pharmacy_claims.pharmacy_npi->providers.provider_npi"]["cardinality"] == "no_match"
            assert m["join_check"]["medical_claims.rendering_npi->providers.provider_npi"]["unmatched_left"] == 0
        contract = json.loads((out / "data_contract.json").read_text(encoding="utf-8"))
        assert set(contract) == set(TASK_CATALOGUE["T1"]["input_tables"]) and {"rows", "columns"} <= set(contract["medical_claims"])
    elif tid == "T2":
        assert m["claim_volume"]["total_claims"] == 12845
        assert {k: v["n"] for k, v in m["claim_volume"]["by"]["claim_status"].items()} == {"Paid": 10511, "Denied": 1286, "Adjusted": 542, "Pended": 506}
        dr = m["denial_rate"]
        assert dr["numerator"] == 1286 and dr["denominator"] == (12339 if full else 12845)
        assert abs(dr["value"] - dr["numerator"] / dr["denominator"]) < 1e-12
        # service_date_from spans 2021-01..2023-12 (36 months); the naive adjudication_date runs to 2024-02 (38)
        assert m["monthly_trend"]["n_months"] == (36 if full else 38) and m["monthly_trend"]["unparseable_dates"] == 0
        assert sum(m["monthly_trend"]["series"]["claim_count"].values()) == 12845
        if full:
            assert m["fraud_prevalence"]["numerator"] == 647 and m["fraud_prevalence"]["denominator"] == 12845
            assert m["monthly_trend"]["date_column"] == "service_date_from"
            assert {"median", "p90", "p99"} <= set(m["financial_summary"]["paid_amount"])
        else:
            assert "median" not in m["financial_summary"]["paid_amount"]
    elif tid == "T3":
        gc = m["group_comparison"]
        assert sum(v["n"] for v in gc["groups"]["provider_specialty"].values()) == 12845
        if full:
            ns = gc["groups"]["network_status"]
            assert set(ns) == {"In-Network", "Out-of-Network"} and gc["denominator_option"] == "adjudicated_claims"
            assert sum(v["denial_rate"]["denominator"] for v in ns.values()) == 12339 and sum(v["denial_rate"]["numerator"] for v in ns.values()) == 1286
            assert all("|" in k for k in gc["groups"]["provider_specialty+network_status"])
            assert len(m["provider_ranking"]["rows"]) == 10 and all(r["n"] >= 30 for r in m["provider_ranking"]["rows"])
            assert m["provider_join"]["unmatched"] == 0 and m["provider_join"]["providers_matched"] == 150
    elif tid == "T4":
        dcr = m["denial_code_ranking"]
        assert sum(c["n"] for c in dcr["codes"]) == 1286 and len(dcr["codes"]) == 10
        assert dcr["missing_denial_codes"]["overall"] == 11559 and dcr["missing_denial_codes"]["among_denied"] == 0
        if full:
            assert abs(sum(c["share"] for c in dcr["codes"]) - 1.0) < 1e-9
            assert set(dcr["missing_denial_codes"]["by_status"]) == {"Paid", "Denied", "Adjusted", "Pended"}
            assert set(m["denial_rate_by_segment"]["segments"]) == {"claim_type", "provider_specialty", "network_status", "place_of_service", "auth_required_flag"}
            assert m["denial_rate_by_segment"]["segments"]["network_status"]["In-Network"]["denominator"] == 10370
    elif tid == "T5":
        cp = m["class_prevalence"]
        assert cp["positives"] == 647 and cp["total"] == 12845 and abs(cp["imbalance_ratio"] - 12198 / 647) < 1e-9
        fc = m["feature_comparison"]
        assert fc["claim_type"]["kind"] == "categorical" and abs(sum(fc["claim_type"]["flagged"].values()) - 1.0) < 1e-9
        assert fc["billed_amount"]["kind"] == "numeric" and fc["billed_amount"]["n_flagged"] == 647
        if full:
            assert m["leakage_risks"]["label_derived_fields"] == ["fraud_pattern_type"] and m["leakage_risks"]["flagged_in_plan"] == []
            assert fc["member_payer_type"]["kind"] == "categorical"
        else:
            assert fc["fraud_pattern_type"]["unflagged"] == {"(missing)": 1.0}
    elif tid == "T6":
        sp = m["split"]
        assert sp["n_train"] + sp["n_test"] == 12845 and sp["seed"] == 42
        for name, r in m["models"].items():
            assert set(T6_MODEL_KEYS) <= set(r) and 0.0 <= r["roc_auc"] <= 1.0 and r["n_test"] == sp["n_test"]
            cm = r["confusion_matrix"]
            assert sum(cm[0]) + sum(cm[1]) == sp["n_test"]
        fl = json.loads((out / "feature_list.json").read_text(encoding="utf-8"))
        assert fl["features"] == m["feature_set"]["features"]
        assert json.loads((out / "model_metrics.json").read_text(encoding="utf-8")) == m["models"]
        if full:
            assert sp["stratify"] is True and abs(sp["prevalence_train"] - sp["prevalence_test"]) < 0.002
            assert m["preprocessing"]["fit_on"] == "train_only" and set(m["models"]) == {"logistic_regression", "random_forest", "gradient_boosting"}
            assert m["feature_set"]["label_derived_present"] == [] and m["feature_set"]["id_fields_present"] == []
        else:
            assert m["feature_set"]["label_derived_present"] == ["fraud_pattern_type"]
    elif tid == "T7":
        td, sp = m["target_definition"], m["split"]
        assert sp["n_train"] + sp["n_test"] == 12845
        assert td["n_positive_train"] / sp["n_train"] == pytest.approx(td["positive_rate_train"])
        for name, r in m["models"].items():
            assert set(T7_MODEL_KEYS) <= set(r) and 0.0 <= r["precision_at_top_5pct"] <= 1.0
        thr = json.loads((out / "threshold.json").read_text(encoding="utf-8"))
        assert thr["threshold_value"] == td["threshold_value"]
        if full:
            assert td["threshold_source"] == "train_only" and abs(td["positive_rate_train"] - 0.05) < 0.002
            assert m["feature_set"]["target_derived_present"] == []
        else:
            assert td["threshold_source"] == "all_data" and m["feature_set"]["target_derived_present"] == ["billed_amount", "allowed_amount"]
    elif tid == "T8":
        brief = m["brief"]
        text = (out / "executive_brief.md").read_text(encoding="utf-8")
        assert brief["word_count"] <= 600 and len(text.split()) == brief["word_count"]
        assert not any(f.get("status") == "missing" for f in m["findings"])
        findings = json.loads((out / "findings.json").read_text(encoding="utf-8"))
        assert findings == m["findings"]
        if full:
            assert brief["cite_artifacts"] is True and brief["n_cited_statements"] == brief["n_numeric_statements"] > 0
            low = text.lower()
            assert not any(p in low for p in ("causes", "drives", "leads to", "because of"))
            assert {f["task_id"] for f in findings} == {"T1", "T2", "T3", "T4", "T5", "T6", "T7"}
            for heading in ("## Key findings", "## Model results", "## Limitations", "## Synthetic-data caveats", "## Next steps", "## Methodology"):
                assert heading in text
        else:
            assert brief["n_cited_statements"] == 0 and "drives" in text


# --------------------------------------------------------------------------- #
# Tests                                                                       #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("a6_runs")


@pytest.mark.parametrize("tid", TASKS)
def test_default_plan(root: Path, tid: str) -> None:
    plan = default_plan(tid)
    res, dt = run(root, "default", tid, plan)
    assert dt < 60, f"{tid} default plan took {dt:.1f}s"
    assert_contract(res, tid, plan, require_all_artifacts=False)
    check_task_specific(res, tid, full=False)


@pytest.mark.parametrize("tid", TASKS)
def test_full_plan_and_determinism(root: Path, tid: str) -> None:
    plan = full_plan(tid)
    res, dt = run(root, "full", tid, plan)
    assert dt < 60, f"{tid} full plan took {dt:.1f}s"
    assert_contract(res, tid, plan)
    check_task_specific(res, tid, full=True)
    first = copy.deepcopy(res["metrics"])
    again, _ = run(root, "full", tid, full_plan(tid))  # same output dir: identical paths, fresh run
    second = again["metrics"]
    assert first.pop("generated_at") and second.pop("generated_at")
    assert first == second, f"{tid}: metrics differ between two runs of the same plan"
    assert sorted(res["artifacts"]) == sorted(again["artifacts"])


def test_unknown_component_is_structured_error(root: Path) -> None:
    plan = {"steps": [{"component": "bogus_component", "params": {}}, {"component": "load_tables", "params": {}}, {"component": "write_report", "params": {}}]}
    res = execute({"task_id": "T2"}, plan, run_context(root, "errors_unknown", "T2"))
    assert res["errors"][0]["type"] == "unknown_component" and res["errors"][0]["component"] == "bogus_component"
    assert res["status"] == "partial" and "load_tables" in res["components_executed"]
    assert Path(res["metrics_path"]).is_file() and Path(res["report_path"]).is_file()


def test_models_without_feature_set_is_missing_dependency(root: Path) -> None:
    plan = {"steps": [{"component": "load_tables", "params": {}}, {"component": "split", "params": {}}, {"component": "preprocessing", "params": {}}, {"component": "models", "params": {}}, {"component": "write_report", "params": {}}]}
    res = execute({"task_id": "T6"}, plan, run_context(root, "errors_dependency", "T6"))
    by_component = {e["component"]: e["type"] for e in res["errors"]}
    assert by_component["models"] == "missing_dependency" and by_component["preprocessing"] == "missing_dependency"
    assert res["status"] == "partial" and "split" in res["components_executed"] and "models" in res["components_failed"]
    assert "models" not in res["metrics"] and "split" in res["metrics"]


def test_invalid_param_skips_only_that_component(root: Path) -> None:
    plan = {"steps": [{"component": "load_tables", "params": {}}, {"component": "denial_rate", "params": {"denominator": "everything"}}, {"component": "claim_volume", "params": {"by": ["claim_status"], "figure": "false"}}, {"component": "write_report", "params": {"caveats": ["synthetic_data"]}}]}
    res = execute({"task_id": "T2"}, plan, run_context(root, "errors_param", "T2"))
    assert [e["type"] for e in res["errors"]] == ["invalid_param"] and res["components_failed"] == ["denial_rate"]
    assert res["status"] == "partial" and "claim_volume" in res["components_executed"] and "denial_rate" not in res["metrics"]
    assert res["metrics"]["plan"] == plan  # the plan is recorded as received
    assert not (Path(res["output_dir"]) / "claims_status_distribution.png").exists()  # "false" matched the boolean option


def test_nothing_runnable_is_error_but_files_exist(root: Path) -> None:
    res = execute({"task_id": "T4"}, {"steps": [{"component": "nope", "params": {}}]}, run_context(root, "errors_none", "T4"))
    assert res["status"] == "error" and res["components_executed"] == []
    assert Path(res["metrics_path"]).is_file() and Path(res["report_path"]).is_file()
    assert {Path(a).name for a in res["artifacts"]} == {"metrics.json", "report.md"}


def test_runtime_error_inside_component_is_captured(root: Path, monkeypatch) -> None:
    import src.analyses.t2_portfolio as t2

    def boom(ctx, params):
        raise ValueError("synthetic failure")

    monkeypatch.setitem(t2.HANDLERS, "denial_rate", boom)
    res = execute({"task_id": "T2"}, default_plan("T2"), run_context(root, "errors_runtime", "T2"))
    err = next(e for e in res["errors"] if e["component"] == "denial_rate")
    assert err["type"] == "runtime_error" and "synthetic failure" in err["message"]
    assert res["status"] == "partial" and "financial_summary" in res["components_executed"]


def test_missing_source_task_recorded_not_invented(root: Path) -> None:
    plan = {"steps": [{"component": "collect_findings", "params": {"sources": ["T3", "T7"]}}, {"component": "brief_sections", "params": {"sections": ["key_findings", "model_results"], "cite_artifacts": True}}, {"component": "write_report", "params": {}}]}
    res = execute({"task_id": "T8"}, plan, run_context(root, "isolated_condition", "T8"))
    assert res["status"] == "ok"
    assert res["metrics"]["findings"] == [{"task_id": "T3", "status": "missing"}, {"task_id": "T7", "status": "missing"}]
    brief = res["metrics"]["brief"]
    assert brief["n_cited_statements"] == brief["n_numeric_statements"]


def test_t13_brief_reads_the_final_attempts_of_t11_and_t12(root: Path) -> None:
    """T13 (D-24) sources only the two held-out tasks before it, reading each one's *final* attempt."""
    condition = "heldout_v2"
    t11_plan = {"steps": [
        {"component": "load_tables", "params": {}},
        {"component": "claim_volume", "params": {"by": ["claim_status"], "figure": True}},
        {"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}},
        {"component": "fraud_prevalence", "params": {"denominator": "all_claims"}},
        {"component": "financial_summary", "params": {"amount_columns": ["billed_amount", "allowed_amount", "paid_amount"], "statistics": "sum_mean_quantiles"}},
        {"component": "monthly_trend", "params": {"date_column": "service_date_from", "metrics": ["claim_count", "paid_amount_sum"]}},
        {"component": "write_report", "params": {"caveats": ["synthetic_data", "descriptive_only"], "show_denominators": True, "cite_artifacts": True}},
    ]}
    t12_plan = {"steps": [
        {"component": "load_tables", "params": {}},
        {"component": "split", "params": {"test_size": 0.25}},
        {"component": "target_definition", "params": {"amount_column": "paid_amount", "percentile": 90, "threshold_source": "train_only"}},
        {"component": "feature_set", "params": {"features": ["claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status", "service_units", "length_of_stay", "er_flag", "elective_flag", "preventive_flag", "auth_required_flag", "primary_icd10_cm", "drg_present"]}},
        {"component": "preprocessing", "params": {"fit_on": "train_only", "scaling": "standard"}},
        {"component": "models", "params": {"models": ["logistic_regression", "random_forest"]}},
        {"component": "write_report", "params": {"caveats": ["synthetic_data", "model_limitations", "no_operational_use"], "show_denominators": True, "cite_artifacts": True}},
    ]}

    def spec(tid: str) -> dict:
        return {"task_id": tid, "components": TASK_CATALOGUE[tid]["components"]}

    # a first and then a second T11 attempt: only the second (final) one may reach the brief
    first = execute(spec("T11"), default_plan("T11"), run_context(root, condition, "T11", attempt=1))
    final = execute(spec("T11"), t11_plan, run_context(root, condition, "T11", attempt=2))
    assert first["status"] == "ok" and final["status"] == "ok"
    assert execute(spec("T12"), t12_plan, run_context(root, condition, "T12", attempt=1))["status"] == "ok"

    plan = {"steps": [
        {"component": "collect_findings", "params": {"sources": ["T11", "T12"]}},
        {"component": "brief_sections", "params": {"sections": ["key_findings", "model_results", "limitations", "synthetic_caveats", "next_steps"], "causal_language": "avoid", "cite_artifacts": True}},
        {"component": "write_report", "params": {"caveats": ["synthetic_data", "no_operational_use"], "show_denominators": True, "cite_artifacts": True}},
    ]}
    res = execute(spec("T13"), plan, run_context(root, condition, "T13"))
    assert res["status"] == "ok" and res["errors"] == []
    findings = res["metrics"]["findings"]
    assert {f["task_id"] for f in findings} == {"T11", "T12"}
    assert not any(f.get("status") == "missing" for f in findings)
    keys = {(f["task_id"], f["metric_key"]) for f in findings}
    assert {("T11", "claim_volume.total_claims"), ("T11", "denial_rate"), ("T12", "target_definition.threshold_value")} <= keys
    assert any(t == "T12" and k.endswith(".roc_auc") for t, k in keys)  # the brief must be able to quote the ranking metric
    assert all("attempt_2" in f["source_path"] for f in findings if f["task_id"] == "T11")

    brief = res["metrics"]["brief"]
    assert brief["n_numeric_statements"] > 0 and brief["n_cited_statements"] == brief["n_numeric_statements"]
    assert brief["word_count"] <= 600 and brief["causal_language"] == "avoid"
    text = (Path(res["output_dir"]) / "executive_brief.md").read_text(encoding="utf-8")
    assert "## Key findings" in text and "## Model results" in text
    assert not any(phrase in text.lower() for phrase in ("causes", " drives ", "leads to", "because of"))
