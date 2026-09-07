"""Tests for the task suite, rubric, golden pack and deterministic evaluator (A3).

Config-level tests parse and cross-reference config/tasks.yaml, config/rubric.yaml and goldens/*; kind-level
unit tests use small synthetic rubrics/goldens; the T2 scenario tests build an "ideal" and a "naive" execution
result from the committed golden (skipped when the golden pack has not been built).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.evaluator import EVALUATOR_VERSION, evaluate, mismatches, resolve_all
from src.graph_nodes import _NO_MATCH, match_option
from src.utils import REPO_ROOT

CONFIG = REPO_ROOT / "config"
GOLDENS = REPO_ROOT / "goldens"
KINDS = {"exact", "tolerance", "artifact_exists", "field_excluded", "contract", "caveat_keywords", "metric_range", "report_structure", "component_executed"}
TOP_LEVEL_METRIC_KEYS = {"task_id", "run_id", "condition", "attempt", "seed", "generated_at", "plan_sha256", "plan", "tables"}


# --------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def suite() -> dict:
    return yaml.safe_load((CONFIG / "tasks.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tasks(suite) -> dict[str, dict]:
    return {t["task_id"]: t for t in suite["tasks"]}


@pytest.fixture(scope="module")
def rubric() -> dict:
    return yaml.safe_load((CONFIG / "rubric.yaml").read_text(encoding="utf-8"))


def load_golden(task_spec: dict) -> dict | None:
    path = REPO_ROOT / task_spec["golden_file"]
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) if path.suffix in (".yaml", ".yml") else json.loads(text)


@pytest.fixture(scope="module")
def goldens(tasks) -> dict[str, dict]:
    out = {tid: load_golden(spec) for tid, spec in tasks.items()}
    if any(g is None for g in out.values()):
        pytest.skip("golden pack not built - run `uv run python -m src.build_goldens`")
    return out


def mini_rubric(*checks: dict, threshold: float = 3.5) -> dict:
    base = {"check_id": "TX.c", "dimension": "correctness", "weight": 1, "critical": False, "remediation": "fix it",
            "related_components": [{"component": "x", "params": {"p": "v"}}], "reusable": True, "applicable_task_ids": ["T9"]}
    return {"rubric_version": "test", "pass_threshold": threshold,
            "dimensions": [{"id": d} for d in ("correctness", "completeness", "reproducibility", "statistical_discipline", "communication")],
            "tasks": {"TX": {"checks": [{**base, **c} for c in checks]}}}


SPEC = {"task_id": "TX", "components": [{"id": "denial_rate", "produces": [{"key": "denial_rate"}]}]}


def run(check: dict, golden: dict, result: dict, threshold: float = 3.5) -> dict:
    return evaluate(SPEC, result, mini_rubric(check, threshold=threshold), golden)


def one(evaluation: dict) -> dict:
    assert len(evaluation["checks"]) == 1
    return evaluation["checks"][0]


# --------------------------------------------------------------------------- config parsing and cross-references
def test_suite_shape(suite, tasks):
    assert suite["suite_version"] == "1"
    assert list(tasks) == ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
    # experiment 4 runs the six-task suite T1 -> T2 -> T4 -> T3 -> T7 -> T8 (D-22); the order must be a subset of the specs and match experiment.yaml
    assert suite["task_order"] == ["T1", "T2", "T4", "T3", "T7", "T8"] and set(suite["task_order"]) <= set(tasks)
    from src.utils import CONFIG_DIR, read_yaml
    assert read_yaml(CONFIG_DIR / "experiment.yaml")["task_order"] == suite["task_order"]
    for tid, spec in tasks.items():
        for key in ("title", "objective", "tags", "input_tables", "golden_file", "required_artifacts", "components"):
            assert key in spec, (tid, key)
        assert {"report.md", "metrics.json"} <= set(spec["required_artifacts"])
        ids = [c["id"] for c in spec["components"]]
        assert len(ids) == len(set(ids)), tid
        for comp in spec["components"]:
            assert comp["description"] and "default_selected" in comp and comp["produces"], (tid, comp["id"])
            for pname, p in (comp.get("params") or {}).items():
                assert p["description"] and "options" in p and "default" in p, (tid, comp["id"], pname)
                defaults = p["default"] if p.get("multi") else [p["default"]]
                assert all(match_option(p["options"], d) is not _NO_MATCH for d in defaults), (tid, comp["id"], pname)


def test_objectives_do_not_name_options_as_correct(tasks):
    for tid, spec in tasks.items():
        text = spec["objective"].lower()
        for word in ("adjudicated_claims", "train_only", "denied_claims", "all_columns", "correct option", "recommended"):
            assert word not in text, (tid, word)


def test_rubric_shape_and_cross_references(tasks, rubric):
    assert rubric["rubric_version"] == "1" and rubric["pass_threshold"] == 3.5
    dims = {d["id"] for d in rubric["dimensions"]}
    assert dims == {"correctness", "completeness", "reproducibility", "statistical_discipline", "communication"}
    assert set(rubric["tasks"]) == set(tasks)
    seen: set[str] = set()
    for tid, block in rubric["tasks"].items():
        spec = tasks[tid]
        catalogue = {c["id"]: c for c in spec["components"]}
        produced = {p["key"] for c in spec["components"] for p in c["produces"]} | TOP_LEVEL_METRIC_KEYS
        assert 8 <= len(block["checks"]), tid
        assert any(c["critical"] for c in block["checks"]), tid
        for chk in block["checks"]:
            cid = chk["check_id"]
            assert cid.startswith(f"{tid}.") and cid not in seen, cid
            seen.add(cid)
            assert chk["kind"] in KINDS and chk["dimension"] in dims, cid
            assert chk["weight"] > 0 and isinstance(chk["critical"], bool) and chk["remediation"], cid
            assert isinstance(chk["reusable"], bool) and isinstance(chk["applicable_task_ids"], list), cid
            assert all(t in tasks and t > tid for t in chk["applicable_task_ids"]), cid
            target = str(chk["target"])
            if chk["kind"] in {"exact", "tolerance", "contract", "metric_range", "field_excluded"} and not target.startswith("plan:"):
                assert target.split(".")[0].split("*")[0] in produced, (cid, target)
            if chk["kind"] == "artifact_exists":
                assert target in spec["required_artifacts"], cid
            if chk["kind"] == "component_executed":
                assert target in catalogue, cid
            assert chk["related_components"], cid
            for rc in chk["related_components"]:
                comp = catalogue[rc["component"]]
                for pname, pval in (rc.get("params") or {}).items():
                    p = comp["params"][pname]
                    values = pval if p.get("multi") else [pval]
                    assert (not p.get("multi")) or isinstance(pval, list), (cid, pname)
                    assert all(match_option(p["options"], v) is not _NO_MATCH for v in values), (cid, pname, pval)
        covered = {c["target"] for c in block["checks"] if c["kind"] == "artifact_exists"}
        assert set(spec["required_artifacts"]) <= covered, tid


def test_each_check_kind_used_in_rubric(rubric):
    used = {c["kind"] for block in rubric["tasks"].values() for c in block["checks"]}
    assert used == KINDS


def test_goldens_exist_and_reference_check_targets(tasks, rubric, goldens):
    for tid, golden in goldens.items():
        assert golden["task_id"] == tid and golden["golden_version"] == "1" and golden["builder"] == "src/build_goldens.py"
        assert golden["dataset_revision"] and golden["built_at"] and isinstance(golden["data_sha256"], dict)
        assert set(golden["required_artifacts"]) == set(tasks[tid]["required_artifacts"])
        for key in ("expected_exact", "expected_metrics", "contracts", "metric_ranges", "prohibited_fields", "required_caveats"):
            assert key in golden, (tid, key)
        caveat_ids = {c["id"] for c in golden["required_caveats"]}
        for chk in rubric["tasks"][tid]["checks"]:
            key = chk.get("golden_key") or chk["target"]
            section = {"exact": "expected_exact", "tolerance": "expected_metrics", "contract": "contracts", "metric_range": "metric_ranges"}.get(chk["kind"])
            if section:
                assert key in golden[section], (chk["check_id"], section, key)
            if chk["kind"] == "caveat_keywords":
                assert chk["target"] in caveat_ids, chk["check_id"]
            if chk["kind"] == "field_excluded":
                assert golden["prohibited_fields"], chk["check_id"]
        for spec in golden["expected_metrics"].values():
            assert "tolerance" in spec and "definition" in spec and ("value" in spec or "values" in spec)


def test_headline_golden_values(goldens):
    t2, t7 = goldens["T2"], goldens["T7"]
    assert t2["expected_exact"]["claim_volume.total_claims"] == 12845
    assert t2["expected_exact"]["claim_volume.by.claim_status"]["Paid"]["n"] == 10511
    assert abs(t2["expected_metrics"]["denial_rate"]["value"] - 1286 / 12339) < 1e-12
    assert abs(t2["expected_metrics"]["fraud_prevalence"]["value"] - 647 / 12845) < 1e-12
    assert t2["expected_exact"]["monthly_trend.n_months"] == 36
    assert sum(t2["expected_exact"]["monthly_trend.series.claim_count"].values()) == 12845
    codes = goldens["T4"]["expected_exact"]["denial_code_ranking.codes"]
    assert sum(c["n"] for c in codes) == 1286 and abs(sum(c["share"] for c in codes) - 1) < 1e-9
    assert goldens["T4"]["expected_exact"]["denial_code_ranking.missing_denial_codes"] == {"overall": 11559, "overall_denominator": 12845, "among_denied": 0, "among_denied_denominator": 1286}
    assert t7["expected_metrics"]["target_definition.threshold_value"]["definition"]["threshold_source"] == "train_only"
    assert abs(t7["expected_metrics"]["target_definition.threshold_value"]["value"] - t7["reference"]["all_data_threshold"]) > 0.01
    assert t7["expected_exact"]["split"] == {"n_train": 9633, "n_test": 3212}
    assert set(t7["prohibited_fields"]) >= {"billed_amount", "allowed_amount", "paid_amount", "member_oop", "cob_amount", "high_cost_flag", "claim_id", "member_id"}
    assert goldens["T1"]["expected_exact"]["missingness.all_null_columns.medical_claims"] == ["auth_number", "denial_reason_desc", "dx3", "dx4", "dx5", "modifier1", "modifier2"]


@pytest.mark.skipif(not (REPO_ROOT / "data" / "raw" / "medical_claims.csv").is_file(), reason="raw data not downloaded")
def test_build_goldens_check_is_clean(goldens):
    from src.build_goldens import main

    assert main(["--check"]) == 0


# --------------------------------------------------------------------------- path resolution and exact semantics
def test_resolve_all_handles_dotted_keys_and_wildcards():
    metrics = {"join_check": {"medical_claims.rendering_npi->providers.provider_npi": {"unmatched_left": 0}},
               "models": {"lr": {"roc_auc": 0.8}, "rf": {"roc_auc": 0.9}}, "auth": {0: {"n": 1}}}
    assert resolve_all(metrics, "join_check.medical_claims.rendering_npi->providers.provider_npi.unmatched_left") == [("join_check.medical_claims.rendering_npi->providers.provider_npi.unmatched_left", 0)]
    assert sorted(v for _, v in resolve_all(metrics, "models.*.roc_auc")) == [0.8, 0.9]
    assert resolve_all(metrics, "auth.0.n") == [("auth.0.n", 1)]
    assert resolve_all(metrics, "models.gb.roc_auc") == []


def test_mismatch_semantics():
    assert mismatches({"a": {"n": 1}}, {"a": {"n": 1, "share": 0.5}, "b": 2}) == []
    assert mismatches([1, 2, 3], [3, 2, 1]) == []
    assert mismatches([{"npi": "1", "n": 5}, {"npi": "2", "n": 5}], [{"npi": "2", "n": 5, "x": 1}, {"npi": "1", "n": 5}]) == []
    assert mismatches(0.1 + 0.2, 0.3) == []
    assert mismatches(True, True) == [] and mismatches(True, 1) != []  # bools compare by lower-cased string form, not numerically
    assert mismatches(30, "30") == [] and mismatches("Paid", "Paid") == []
    assert mismatches({"a": 1}, {"b": 1}) == ["value.a: missing"]
    assert mismatches([1, 2], [1, 2, 3])


# --------------------------------------------------------------------------- one unit test per kind
def test_kind_exact(tmp_path):
    golden = {"expected_exact": {"claim_volume.by.claim_status": {"Paid": {"n": 3}, "Denied": {"n": 1}}}}
    good = {"metrics": {"claim_volume": {"by": {"claim_status": {"Paid": {"n": 3, "share": 0.75}, "Denied": {"n": 1, "share": 0.25}}}}}}
    bad = {"metrics": {"claim_volume": {"by": {"claim_status": {"Paid": {"n": 2}, "Denied": {"n": 1}}}}}}
    chk = {"kind": "exact", "target": "claim_volume.by.claim_status"}
    assert one(run(chk, golden, good))["passed"]
    rec = one(run(chk, golden, bad))
    assert not rec["passed"] and "Paid.n" in rec["detail"]
    missing = one(run(chk, golden, {"metrics": {}}))
    assert not missing["passed"] and missing["observed"] is None


def test_kind_tolerance():
    golden = {"expected_metrics": {"denial_rate": {"value": 0.1042, "tolerance": 1e-6, "definition": {"numerator": "denied"}},
                                   "shares": {"values": {"A": 0.25, "B": 0.75}, "tolerance": 1e-6, "definition": {}}}}
    chk = {"kind": "tolerance", "target": "denial_rate"}
    assert one(run(chk, golden, {"metrics": {"denial_rate": {"value": 0.1042 + 5e-7}}}))["passed"]
    rec = one(run(chk, golden, {"metrics": {"denial_rate": {"value": 0.10}}}))
    assert not rec["passed"] and rec["observed"] == 0.10 and rec["expected"] == 0.1042
    assert one(run(chk, golden, {"metrics": {}}))["observed"] is None
    values_chk = {"kind": "tolerance", "target": "shares"}
    assert one(run(values_chk, golden, {"metrics": {"shares": {"A": 0.25, "B": 0.75}}}))["passed"]
    assert not one(run(values_chk, golden, {"metrics": {"shares": {"A": 0.30, "B": 0.70}}}))["passed"]
    assert not one(run(values_chk, golden, {"metrics": {"shares": {"A": 0.25}}}))["passed"]


def test_kind_artifact_exists(tmp_path):
    (tmp_path / "financial_summary.csv").write_text("a,b\n", encoding="utf-8")
    chk = {"kind": "artifact_exists", "target": "financial_summary.csv"}
    listed = {"artifacts": [str(tmp_path / "financial_summary.csv")], "output_dir": str(tmp_path)}
    assert one(run(chk, {}, listed))["passed"]
    unlisted = one(run(chk, {}, {"artifacts": [], "output_dir": str(tmp_path)}))
    assert unlisted["passed"] and "not listed" in unlisted["detail"]
    ghost = one(run(chk, {}, {"artifacts": [str(tmp_path / "missing" / "financial_summary.csv")], "output_dir": str(tmp_path / "missing")}))
    assert not ghost["passed"] and ghost["observed"] is None


def test_kind_field_excluded():
    golden = {"prohibited_fields": ["fraud_pattern_type", "claim_id", "member_sex"]}
    chk = {"kind": "field_excluded", "target": "feature_set.features"}
    assert one(run(chk, golden, {"metrics": {"feature_set": {"features": ["claim_type", "billed_amount"]}}}))["passed"]
    rec = one(run(chk, golden, {"metrics": {"feature_set": {"features": ["claim_type", "fraud_pattern_type", "claim_id"]}}}))
    assert not rec["passed"] and rec["observed"] == ["fraud_pattern_type", "claim_id"]
    assert one(run(chk, golden, {"metrics": {}}))["observed"] is None
    keys_chk = {"kind": "field_excluded", "target": "feature_comparison"}
    assert not one(run(keys_chk, golden, {"metrics": {"feature_comparison": {"member_sex": {}, "claim_type": {}}}}))["passed"]
    plan_chk = {"kind": "field_excluded", "target": "plan:feature_set.features"}
    plan_result = {"metrics": {"plan": {"steps": [{"component": "feature_set", "params": {"features": ["claim_id"]}}]}}}
    assert not one(run(plan_chk, golden, plan_result))["passed"]
    narrowed = {"kind": "field_excluded", "target": "feature_set.features", "fields": ["member_sex"]}
    assert one(run(narrowed, golden, {"metrics": {"feature_set": {"features": ["claim_id"]}}}))["passed"]


def test_kind_contract():
    golden = {"contracts": {
        "group_comparison.min_group_size": 30, "report.show_denominators": True, "split.test_size": 0.25,
        "models_logistic": {"includes": ["logistic_regression"]}, "models_tree": {"any_of": ["random_forest", "gradient_boosting"]},
        "models_metrics": {"each_has": ["roc_auc", "pr_auc"]}, "feature_comparison": {"min_count": 2, "from": ["a", "b", "c"]},
        "brief.n_cited_statements": {"equals_metric": "brief.n_numeric_statements"},
        "findings_core": {"includes": ["T2", "T6"], "field": "task_id"}, "plan_sha256": {"present": True},
    }}
    metrics = {"group_comparison": {"min_group_size": "30"}, "report": {"show_denominators": "true"}, "split": {"test_size": 0.25},
               "models": {"logistic_regression": {"roc_auc": 0.8, "pr_auc": 0.2}, "random_forest": {"roc_auc": 0.9}},
               "feature_comparison": {"a": {}, "z": {}, "c": {}}, "brief": {"n_cited_statements": 4, "n_numeric_statements": 5},
               "findings": [{"task_id": "T2"}, {"task_id": "T6", "status": "missing"}], "plan_sha256": "abc"}
    result = {"metrics": metrics}

    def contract(target, key=None):
        return one(run({"kind": "contract", "target": target, **({"golden_key": key} if key else {})}, golden, result))

    assert contract("group_comparison.min_group_size")["passed"]  # string form "30" matches 30
    assert contract("report.show_denominators")["passed"]  # "true" matches True
    assert contract("split.test_size")["passed"]
    assert contract("models", "models_logistic")["passed"]
    assert contract("models", "models_tree")["passed"]
    rec = contract("models", "models_metrics")
    assert not rec["passed"] and "random_forest lacks ['pr_auc']" in rec["detail"]
    assert contract("feature_comparison")["passed"]
    rec = contract("brief.n_cited_statements")
    assert not rec["passed"] and "n_numeric_statements" in rec["detail"]
    assert contract("findings", "findings_core")["passed"]
    assert contract("plan_sha256")["passed"]
    missing = one(run({"kind": "contract", "target": "preprocessing.fit_on"}, {"contracts": {"preprocessing.fit_on": "train_only"}}, result))
    assert not missing["passed"] and missing["observed"] is None
    wrong = one(run({"kind": "contract", "target": "preprocessing.fit_on"}, {"contracts": {"preprocessing.fit_on": "train_only"}}, {"metrics": {"preprocessing": {"fit_on": "all_data"}}}))
    assert not wrong["passed"] and wrong["observed"] == "all_data" and wrong["expected"] == "train_only"


def test_kind_caveat_keywords(tmp_path):
    golden = {"required_caveats": [{"id": "synthetic_data", "any_of": ["synthetic", "simulated"]}]}
    chk = {"kind": "caveat_keywords", "target": "synthetic_data"}
    assert one(run(chk, golden, {"metrics": {"report": {"caveats": ["synthetic_data"]}}}))["passed"]
    (tmp_path / "report.md").write_text("# T\n\n## Caveats\n- All records are SYNTHETIC.\n", encoding="utf-8")
    via_text = one(run(chk, golden, {"metrics": {"report": {"caveats": []}}, "output_dir": str(tmp_path)}))
    assert via_text["passed"] and via_text["observed"]["keywords_found"] == ["synthetic"]
    (tmp_path / "report.md").write_text("# T\n\nNothing to see.\n", encoding="utf-8")
    rec = one(run(chk, golden, {"metrics": {"report": {"caveats": []}}, "output_dir": str(tmp_path)}))
    assert not rec["passed"] and rec["observed"]["keywords_found"] == []


def test_kind_metric_range():
    golden = {"metric_ranges": {"models.*.pr_auc": {"min": "split.prevalence_test", "max": 1.0}, "split.prevalence_test": {"min": 0.03, "max": 0.07}}}
    metrics = {"split": {"prevalence_test": 0.05}, "models": {"lr": {"pr_auc": 0.3}, "rf": {"pr_auc": 0.04}}}
    rec = one(run({"kind": "metric_range", "target": "models.*.pr_auc"}, golden, {"metrics": metrics}))
    assert not rec["passed"] and "models.rf.pr_auc = 0.04" in rec["detail"] and rec["expected"]["resolved"]["min"] == 0.05
    metrics["models"]["rf"]["pr_auc"] = 0.5
    assert one(run({"kind": "metric_range", "target": "models.*.pr_auc"}, golden, {"metrics": metrics}))["passed"]
    assert one(run({"kind": "metric_range", "target": "split.prevalence_test"}, golden, {"metrics": metrics}))["passed"]
    no_bound = one(run({"kind": "metric_range", "target": "models.*.pr_auc"}, golden, {"metrics": {"models": metrics["models"]}}))
    assert not no_bound["passed"] and "missing metric" in no_bound["detail"]
    assert one(run({"kind": "metric_range", "target": "models.*.pr_auc"}, golden, {"metrics": {"split": {"prevalence_test": 0.05}}}))["observed"] is None


def test_kind_report_structure(tmp_path):
    (tmp_path / "report.md").write_text("# Title\n\n## Results\n- denial rate 1,286 / 12,339 = 0.1042 [source: metrics.json#denial_rate]\n\n## Method\n", encoding="utf-8")
    (tmp_path / "executive_brief.md").write_text("Higher volume drives denials. " + "word " * 10, encoding="utf-8")
    golden = {"forbidden_phrases": ["causes", "drives", "leads to", "because of"]}
    result = {"output_dir": str(tmp_path)}

    def structure(target):
        return one(run({"kind": "report_structure", "target": target}, golden, result))

    assert structure("report.md#section:Method")["passed"]
    assert not structure("report.md#section:Caveats")["passed"]
    assert structure("report.md#pattern:denominator_format")["observed"] == 1
    assert structure("report.md#pattern:source_citation")["passed"]
    forbidden = structure("executive_brief.md#forbidden_phrases")
    assert not forbidden["passed"] and forbidden["observed"] == ["drives"]
    assert structure("executive_brief.md#max_words:600")["passed"]
    assert not structure("executive_brief.md#max_words:5")["passed"]
    assert not structure("missing.md#section:X")["passed"]


def test_kind_component_executed():
    chk = {"kind": "component_executed", "target": "denial_rate"}
    assert one(run(chk, {}, {"components_executed": ["load_tables", "denial_rate"]}))["passed"]
    assert not one(run(chk, {}, {"components_executed": ["load_tables"]}))["passed"]
    inferred = one(run(chk, {}, {"metrics": {"denial_rate": {"value": 0.1}}}))
    assert inferred["passed"] and "inferred" in inferred["detail"]


# --------------------------------------------------------------------------- scoring and feedback
def test_scoring_formula_and_null_dimensions():
    rubric = mini_rubric(
        {"check_id": "TX.a", "dimension": "correctness", "weight": 3, "kind": "contract", "target": "x.a"},
        {"check_id": "TX.b", "dimension": "correctness", "weight": 1, "kind": "contract", "target": "x.b"},
        {"check_id": "TX.c", "dimension": "communication", "weight": 2, "kind": "contract", "target": "x.c", "critical": True},
    )
    golden = {"contracts": {"x.a": "yes", "x.b": "yes", "x.c": "yes"}}
    ev = evaluate(SPEC, {"metrics": {"x": {"a": "yes", "b": "no", "c": "yes"}}}, rubric, golden)
    assert ev["scores"] == {"correctness": 3.0, "completeness": None, "reproducibility": None, "statistical_discipline": None, "communication": 4.0}
    assert ev["score_total"] == 3.5 and ev["passed"] is True
    ev2 = evaluate(SPEC, {"metrics": {"x": {"a": "yes", "b": "yes", "c": "no"}}}, rubric, golden)
    assert ev2["scores"]["correctness"] == 4.0 and ev2["score_total"] == 2.0 and ev2["passed"] is False
    assert ev2["critical_failures"] == ["TX.c"]
    ev3 = evaluate(SPEC, {"metrics": {"x": {"a": "yes", "b": "yes", "c": "no"}}}, rubric, golden)
    assert ev3["score_total"] == 2.0  # deterministic


def test_feedback_items_and_metadata():
    rubric = mini_rubric({"check_id": "TX.denial_rate_value", "dimension": "correctness", "kind": "contract", "target": "denial_rate.denominator_option",
                          "critical": True, "issue_type": "wrong_denominator", "related_components": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
                          "applicable_task_ids": ["T3", "T4"]})
    golden = {"contracts": {"denial_rate.denominator_option": "adjudicated_claims"}, "golden_version": "1"}
    ev = evaluate(SPEC, {"metrics": {"denial_rate": {"denominator_option": "all_claims"}}}, rubric, golden)
    assert ev["evaluator_version"] == EVALUATOR_VERSION and ev["rubric_version"] == "test" and ev["golden_version"] == "1"
    assert len(ev["rubric_sha256"]) == 64 and len(ev["golden_sha256"]) == 64 and "freeze_sha256" in ev
    item = ev["feedback"][0]
    assert item["feedback_id"] == "TX-denial_rate_value" and item["check_id"] == "TX.denial_rate_value"
    assert item["criterion"] == "correctness" and item["issue_type"] == "wrong_denominator" and item["severity"] == "high"
    assert item["related_components"] == [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}]
    assert item["reusable"] is True and item["applicable_task_ids"] == ["T3", "T4"]
    assert item["observed"] == "all_claims" and item["expected"] == "adjudicated_claims" and item["remediation"] == "fix it"
    passing = evaluate(SPEC, {"metrics": {"denial_rate": {"denominator_option": "adjudicated_claims"}}}, rubric, golden)
    assert passing["feedback"] == [] and passing["passed"]


def test_empty_execution_result_fails_every_check_without_raising(tasks, rubric, goldens):
    ev = evaluate(tasks["T2"], {}, rubric, goldens["T2"])
    assert ev["passed"] is False and ev["score_total"] == 0.0 and ev["n_passed"] == 0
    assert len(ev["feedback"]) == len(rubric["tasks"]["T2"]["checks"])
    assert all(item["observed"] in (None, [], False) or isinstance(item["observed"], dict) for item in ev["feedback"])
    json.dumps(ev)  # log-safe


# --------------------------------------------------------------------------- T2 scenarios built from the golden
def _touch_all(tmp_path: Path, names: list[str]) -> list[str]:
    out = []
    for name in names:
        p = tmp_path / name
        if not p.exists():
            p.write_bytes(b"x")
        out.append(str(p))
    return out


def ideal_t2(golden: dict, tmp_path: Path) -> dict:
    ee, em = golden["expected_exact"], golden["expected_metrics"]
    cols = ["billed_amount", "allowed_amount", "paid_amount"]
    metrics = {
        "task_id": "T2", "run_id": "test", "condition": "baseline", "attempt": 1, "seed": 42, "generated_at": "x", "plan_sha256": "y",
        "plan": {"steps": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}]},
        "tables": {"medical_claims": {"rows": 12845, "columns": 54}},
        "claim_volume": {"total_claims": ee["claim_volume.total_claims"],
                         "by": {"claim_status": {k: {"n": v["n"], "share": v["n"] / 12845} for k, v in ee["claim_volume.by.claim_status"].items()}}},
        "denial_rate": {"value": em["denial_rate"]["value"], "numerator": ee["denial_rate.numerator"], "denominator": ee["denial_rate.denominator"],
                        "numerator_definition": "claim_status == Denied", "denominator_definition": "Paid, Denied, Adjusted", "denominator_option": "adjudicated_claims"},
        "fraud_prevalence": {"value": em["fraud_prevalence"]["value"], "numerator": 647, "denominator": 12845, "denominator_option": "all_claims"},
        "financial_summary": {c: {"n": 12845, **{s: em[f"financial_summary.{c}.{s}"]["value"] for s in ("sum", "mean", "median", "p90", "p99")}} for c in cols},
        "monthly_trend": {"date_column": "service_date_from", "n_months": ee["monthly_trend.n_months"], "first_month": ee["monthly_trend.first_month"],
                          "last_month": ee["monthly_trend.last_month"], "unparseable_dates": 0, "series": {"claim_count": dict(ee["monthly_trend.series.claim_count"])}},
        "report": {"caveats": ["synthetic_data", "descriptive_only"], "show_denominators": True, "cite_artifacts": False, "sections": ["Summary", "Results", "Artifacts", "Caveats", "Method"]},
    }
    (tmp_path / "report.md").write_text(
        "# T2\n\n## Summary\n\n## Results\n- Denial rate: 1286 / 12339 = 0.1042\n\n## Artifacts\n\n## Caveats\n- Synthetic data.\n- Descriptive analysis only.\n\n## Method\n", encoding="utf-8")
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    artifacts = _touch_all(tmp_path, golden["required_artifacts"])
    return {"status": "ok", "task_id": "T2", "attempt": 1, "output_dir": str(tmp_path), "artifacts": artifacts,
            "metrics_path": str(tmp_path / "metrics.json"), "report_path": str(tmp_path / "report.md"), "metrics": metrics,
            "components_executed": ["load_tables", "claim_volume", "denial_rate", "fraud_prevalence", "financial_summary", "monthly_trend", "write_report"],
            "components_failed": [], "errors": [], "seed": 42, "duration_seconds": 0.1}


def naive_t2(golden: dict, tmp_path: Path) -> dict:
    """Catalogue defaults: all_claims denominator, adjudication_date trend, paid sum/mean only, no caveats."""
    ee = golden["expected_exact"]
    series = {k: v + (1 if i % 2 else -1) for i, (k, v) in enumerate(ee["monthly_trend.series.claim_count"].items())}
    metrics = {
        "task_id": "T2", "seed": 42, "plan_sha256": "y", "plan": {"steps": [{"component": "denial_rate", "params": {"denominator": "all_claims"}}]},
        "tables": {"medical_claims": {"rows": 12845, "columns": 54}},
        "claim_volume": {"total_claims": 12845, "by": {"claim_status": {k: {"n": v["n"], "share": v["n"] / 12845} for k, v in ee["claim_volume.by.claim_status"].items()}}},
        "denial_rate": {"value": 1286 / 12845, "numerator": 1286, "denominator": 12845, "numerator_definition": "Denied", "denominator_definition": "all claims", "denominator_option": "all_claims"},
        "financial_summary": {"paid_amount": {"n": 12845, "sum": golden["expected_metrics"]["financial_summary.paid_amount.sum"]["value"], "mean": golden["expected_metrics"]["financial_summary.paid_amount.mean"]["value"]}},
        "monthly_trend": {"date_column": "adjudication_date", "n_months": 38, "first_month": "2021-01", "last_month": "2024-02", "unparseable_dates": 0, "series": {"claim_count": series}},
        "report": {"caveats": [], "show_denominators": False, "cite_artifacts": False, "sections": ["Summary", "Results", "Artifacts", "Method"]},
    }
    (tmp_path / "report.md").write_text("# T2\n\n## Summary\n\n## Results\n- Denial rate: 0.1001\n\n## Artifacts\n\n## Method\n", encoding="utf-8")
    (tmp_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    artifacts = _touch_all(tmp_path, golden["required_artifacts"])
    return {"status": "ok", "task_id": "T2", "attempt": 1, "output_dir": str(tmp_path), "artifacts": artifacts, "metrics_path": str(tmp_path / "metrics.json"),
            "report_path": str(tmp_path / "report.md"), "metrics": metrics,
            "components_executed": ["load_tables", "claim_volume", "denial_rate", "financial_summary", "monthly_trend", "write_report"], "components_failed": [], "errors": [], "seed": 42}


def test_ideal_t2_scores_four(tasks, rubric, goldens, tmp_path):
    ev = evaluate(tasks["T2"], ideal_t2(goldens["T2"], tmp_path), rubric, goldens["T2"])
    failed = [c for c in ev["checks"] if not c["passed"]]
    assert failed == [], failed
    assert ev["score_total"] == 4.0 and ev["passed"] is True and ev["feedback"] == []
    assert all(v == 4.0 for v in ev["scores"].values())


def test_naive_t2_fails_with_exact_fixes(tasks, rubric, goldens, tmp_path):
    ev = evaluate(tasks["T2"], naive_t2(goldens["T2"], tmp_path), rubric, goldens["T2"])
    assert ev["passed"] is False and ev["score_total"] < 3.5, ev["score_total"]
    assert {"T2.denial_rate_value", "T2.denial_rate_denominator"} <= set(ev["critical_failures"])
    by_id = {f["feedback_id"]: f for f in ev["feedback"]}
    assert by_id["T2-denial_rate_value"]["related_components"] == [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}]
    assert by_id["T2-denial_rate_value"]["severity"] == "high" and by_id["T2-denial_rate_value"]["applicable_task_ids"] == ["T3", "T4"]
    assert by_id["T2-monthly_date_column"]["related_components"][0]["params"]["date_column"] == "service_date_from"
    assert by_id["T2-fraud_prevalence_executed"]["observed"] is False
    assert "synthetic_data" in by_id["T2-caveat_synthetic"]["related_components"][0]["params"]["caveats"]
    assert by_id["T2-show_denominators"]["related_components"] == [{"component": "write_report", "params": {"show_denominators": True}}]
    assert [f["feedback_id"] for f in ev["feedback"]] == [c["check_id"].replace(".", "-", 1) for c in ev["checks"] if not c["passed"]]  # rubric order
    # passing checks still credited: the artifacts exist and the status mix is right
    assert ev["scores"]["reproducibility"] == 4.0
    passed_ids = {c["check_id"] for c in ev["checks"] if c["passed"]}
    assert {"T2.total_claims", "T2.status_mix", "T2.paid_amount_sum"} <= passed_ids


def test_single_critical_convention_lands_below_threshold(tasks, rubric, goldens, tmp_path):
    """Everything right except the headline denominator must still fail and score clearly below 3.5."""
    result = ideal_t2(goldens["T2"], tmp_path)
    result["metrics"]["denial_rate"] = {"value": 1286 / 12845, "numerator": 1286, "denominator": 12845, "numerator_definition": "Denied",
                                        "denominator_definition": "all claims", "denominator_option": "all_claims"}
    ev = evaluate(tasks["T2"], result, rubric, goldens["T2"])
    assert ev["passed"] is False and ev["score_total"] <= 3.3, ev["score_total"]
    assert ev["critical_failures"] == ["T2.denial_rate_value", "T2.denial_rate_denominator"]
