"""T8 — Executive brief: collect findings from the final attempts of source tasks and write a <= 600-word brief.

Values are read from each source task's ``metrics.json`` (highest ``attempt_<n>`` under the same
``artifacts/tasks/<run_id>/<condition>/``); nothing is recomputed and nothing is invented - a missing
source is recorded as ``{"task_id": ..., "status": "missing"}``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.analyses.common import Ctx, rate
from src.utils import rel

SECTION_ORDER = ["key_findings", "model_results", "limitations", "synthetic_caveats", "next_steps", "methodology"]
SECTION_TITLES = {
    "key_findings": "Key findings",
    "model_results": "Model results",
    "limitations": "Limitations",
    "synthetic_caveats": "Synthetic-data caveats",
    "next_steps": "Next steps",
    "methodology": "Methodology",
}
WORD_LIMIT = 600
DIGIT = re.compile(r"\d")


# --------------------------------------------------------------------------- #
# Source discovery and extraction                                             #
# --------------------------------------------------------------------------- #
def final_attempt_metrics(condition_dir: Path, task_id: str) -> tuple[dict | None, Path | None]:
    tdir = condition_dir / task_id
    if not tdir.is_dir():
        return None, None
    best: tuple[int, Path] | None = None
    for p in tdir.iterdir():
        if p.is_dir() and p.name.startswith("attempt_") and (p / "metrics.json").is_file():
            try:
                n = int(p.name[len("attempt_"):])
            except ValueError:
                continue
            if best is None or n > best[0]:
                best = (n, p / "metrics.json")
    if best is None:
        return None, None
    with open(best[1], "r", encoding="utf-8") as fh:
        return json.load(fh), best[1]


def _get(d: Any, *keys: str) -> Any:
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def _finding(task_id: str, key: str, label: str, value: Any, src: str, numerator: int | None = None, denominator: int | None = None) -> dict:
    f = {"task_id": task_id, "metric_key": key, "label": label, "value": value, "source_path": f"{src}#{key}"}
    if numerator is not None and denominator is not None:
        f["numerator"], f["denominator"] = int(numerator), int(denominator)
    return f


def _rate_finding(task_id: str, key: str, label: str, d: dict | None, src: str) -> list[dict]:
    if not isinstance(d, dict) or d.get("value") is None:
        return []
    return [_finding(task_id, key, label, d["value"], src, d.get("numerator"), d.get("denominator"))]


def extract(task_id: str, m: dict, src: str) -> list[dict]:
    out: list[dict] = []
    if task_id == "T1":
        for name, info in (m.get("tables") or {}).items():
            if isinstance(info, dict) and info.get("rows") is not None:
                out.append(_finding("T1", f"tables.{name}.rows", f"{name} row count", info["rows"], src))
    elif task_id == "T2":
        dr = m.get("denial_rate")
        out += _rate_finding("T2", "denial_rate", f"Denial rate (denominator: {_get(dr, 'denominator_option') or 'unspecified'})", dr, src)
        total = _get(m, "claim_volume", "total_claims")
        if total is not None:
            out.append(_finding("T2", "claim_volume.total_claims", "Total medical claims", total, src))
        paid = _get(m, "financial_summary", "paid_amount", "sum")
        if paid is not None:
            out.append(_finding("T2", "financial_summary.paid_amount.sum", "Total paid amount", paid, src))
        fp = m.get("fraud_prevalence")
        out += _rate_finding("T2", "fraud_prevalence", f"Fraud prevalence (denominator: {_get(fp, 'denominator_option') or 'unspecified'})", fp, src)
    elif task_id == "T3":
        groups = _get(m, "group_comparison", "groups", "network_status") or {}
        for value, info in groups.items():
            out += _rate_finding("T3", f"group_comparison.groups.network_status.{value}.denial_rate", f"Denial rate, network_status = {value}", _get(info, "denial_rate"), src)
    elif task_id == "T4":
        codes = _get(m, "denial_code_ranking", "codes") or []
        if codes:
            top = codes[0]
            share, n = top.get("share"), top.get("n")
            den = int(round(n / share)) if share and n is not None else None
            out.append(_finding("T4", "denial_code_ranking.codes[0]", f"Top denial code {top.get('code')} (scope: {_get(m, 'denial_code_ranking', 'scope')})", share, src, n, den))
    elif task_id == "T5":
        cp = m.get("class_prevalence")
        if isinstance(cp, dict) and cp.get("prevalence") is not None:
            out.append(_finding("T5", "class_prevalence.prevalence", "Fraud label prevalence", cp["prevalence"], src, cp.get("positives"), cp.get("total")))
    elif task_id == "T6":
        for name, r in (m.get("models") or {}).items():
            for metric in ("roc_auc", "pr_auc"):
                if isinstance(r, dict) and r.get(metric) is not None:
                    out.append(_finding("T6", f"models.{name}.{metric}", f"Fraud model {name} {metric.replace('_', '-').upper()}", r[metric], src))
        feats = _get(m, "feature_set", "features")
        if isinstance(feats, list):
            out.append(_finding("T6", "feature_set.features", "Fraud model feature count", len(feats), src))
    elif task_id == "T7":
        td = m.get("target_definition")
        if isinstance(td, dict) and td.get("threshold_value") is not None:
            out.append(_finding("T7", "target_definition.threshold_value", f"High-cost threshold ({td.get('amount_column')} p{td.get('percentile')}, {td.get('threshold_source')})", td["threshold_value"], src))
        for name, r in (m.get("models") or {}).items():
            if isinstance(r, dict) and r.get("pr_auc") is not None:
                out.append(_finding("T7", f"models.{name}.pr_auc", f"High-cost model {name} PR-AUC", r["pr_auc"], src))
    return out


def collect_findings(ctx: Ctx, params: dict) -> None:
    condition_dir = ctx.output_dir.parent.parent
    findings: list[dict] = []
    missing: list[str] = []
    for tid in params["sources"]:
        m, path = final_attempt_metrics(condition_dir, tid)
        if m is None:
            findings.append({"task_id": tid, "status": "missing"})
            missing.append(tid)
            continue
        findings += extract(tid, m, rel(path))
    ctx.state["findings"] = findings
    ctx.state["missing_sources"] = missing
    ctx.metrics["findings"] = findings
    ctx.write_json("findings.json", findings)
    n_values = sum(1 for f in findings if "value" in f)
    ctx.result("collect_findings", f"Sources requested: {', '.join(params['sources'])}; missing: {', '.join(missing) or 'none'}", source=ctx.artifact_rel("findings.json"))
    ctx.result("collect_findings", "Findings with values extracted", value=n_values, source=ctx.artifact_rel("findings.json"))


# --------------------------------------------------------------------------- #
# Brief                                                                        #
# --------------------------------------------------------------------------- #
def _fmt(f: dict) -> str:
    v, label = f["value"], f["label"]
    if v is None:
        return f"{label}: not available"
    if "numerator" in f and "denominator" in f:
        return f"{label}: {v * 100:.2f}% ({f['numerator']:,} / {f['denominator']:,})"
    if isinstance(v, bool):
        return f"{label}: {v}"
    if isinstance(v, int):
        return f"{label}: {v:,}"
    if "amount" in label.lower() or "threshold" in label.lower():
        return f"{label}: {v:,.2f}"
    return f"{label}: {v:.3f}"


def _priority(f: dict) -> int:
    key, tid = f["metric_key"], f["task_id"]
    if tid == "T1" or key == "feature_set.features":
        return 3
    if tid in ("T3", "T4") or key.startswith("financial_summary"):
        return 2
    return 1


def _causal(mode: str, subject: str, obj: str) -> str:
    return f"{subject} drives {obj}." if mode == "allow" else f"{subject} is associated with {obj}."


def _build_statements(findings: list[dict], missing: list[str], sections: list[str], mode: str, cite: bool, findings_src: str) -> dict[str, list[dict]]:
    """Section -> list of {text, source, priority}. Numeric statements carry the finding's source."""
    by_section: dict[str, list[dict]] = {s: [] for s in sections}
    valued = [f for f in findings if "value" in f]
    if "key_findings" in sections:
        for f in valued:
            if f["task_id"] in ("T1", "T2", "T3", "T4", "T5"):
                by_section["key_findings"].append({"text": _fmt(f), "source": f["source_path"], "priority": _priority(f)})
        net = [f for f in valued if f["metric_key"].startswith("group_comparison.groups.network_status.")]
        if len(net) >= 2:
            hi = max(net, key=lambda f: (f["value"], f["label"]))
            status = hi["metric_key"].split(".")[3]
            by_section["key_findings"].append({"text": _causal(mode, f"{status} status", "a higher denial rate in this sample"), "source": None, "priority": 2})
        if missing:
            by_section["key_findings"].append({"text": f"Sources without a completed attempt: {', '.join(missing)}; their values are not reported.", "source": findings_src, "priority": 0})
        if not by_section["key_findings"]:
            by_section["key_findings"].append({"text": "No descriptive findings were available from the selected source tasks.", "source": None, "priority": 0})
    if "model_results" in sections:
        for f in valued:
            if f["task_id"] in ("T6", "T7"):
                by_section["model_results"].append({"text": _fmt(f), "source": f["source_path"], "priority": _priority(f)})
        if by_section["model_results"]:
            by_section["model_results"].append({"text": _causal(mode, "The selected claim attribute set", "the fraud and high-cost scores reported above; the models are baselines fitted on one random split"), "source": None, "priority": 2})
        else:
            by_section["model_results"].append({"text": "No model results were available from the selected source tasks.", "source": None, "priority": 0})
    if "limitations" in sections:
        by_section["limitations"] = [
            {"text": "Every model is an untuned baseline evaluated on a single random hold-out split; no temporal validation, calibration or confidence intervals were produced.", "source": None, "priority": 0},
            {"text": "Rates depend on the denominators chosen by the source tasks and are only comparable when the denominator definitions match.", "source": None, "priority": 0},
            {"text": "Group differences are descriptive associations; the analyses do not identify mechanisms or effects.", "source": None, "priority": 0},
        ]
    if "synthetic_caveats" in sections:
        by_section["synthetic_caveats"] = [
            {"text": "All records are synthetic (the HLT sample preview); no real members, providers or claims are described and no PHI is present.", "source": None, "priority": 0},
            {"text": "Distributions reflect the data generator, so magnitudes must not be quoted as real-world benchmarks or used for operational decisions.", "source": None, "priority": 0},
        ]
    if "next_steps" in sections:
        by_section["next_steps"] = [
            {"text": "Re-run the fraud and high-cost baselines with a temporal split and calibrated thresholds before any comparison across models.", "source": None, "priority": 0},
            {"text": "Extend the denial analysis to code-by-segment breakdowns with minimum group sizes and explicit denominators.", "source": None, "priority": 0},
            {"text": "Confirm the data contract (all-null columns, label-derived fields, unmatched pharmacy NPIs) with the data owner before further modelling.", "source": None, "priority": 0},
        ]
    if "methodology" in sections:
        by_section["methodology"] = [
            {"text": "Values are read from the final attempt of each source task's metrics file; nothing is recomputed or estimated in this brief.", "source": None, "priority": 0},
            {"text": "Source tasks used fixed seeds, recorded plan hashes and wrote their artifacts next to their metrics for traceability.", "source": None, "priority": 0},
        ]
    return by_section


def _render(ctx: Ctx, by_section: dict[str, list[dict]], sections: list[str], cite: bool) -> tuple[str, list[str]]:
    lines = [f"# Executive brief — run {ctx.run_context.get('run_id')} ({ctx.run_context.get('condition')})", ""]
    bullets: list[str] = []
    for s in [s for s in SECTION_ORDER if s in sections]:
        lines += [f"## {SECTION_TITLES[s]}", ""]
        for st in by_section.get(s, []):
            text = st["text"]
            if cite and st.get("source"):
                text = f"{text} [source: {st['source']}]"
            lines.append(f"- {text}")
            bullets.append(text)
        lines.append("")
    return "\n".join(lines), bullets


def brief_sections(ctx: Ctx, params: dict) -> None:
    sections = [s for s in SECTION_ORDER if s in params["sections"]]
    mode, cite = params["causal_language"], bool(params["cite_artifacts"])
    findings = ctx.state.get("findings") or []
    missing = ctx.state.get("missing_sources") or []
    by_section = _build_statements(findings, missing, sections, mode, cite, ctx.artifact_rel("findings.json"))
    text, bullets = _render(ctx, by_section, sections, cite)
    # trim lowest-priority numeric statements until the brief fits the word limit
    while len(text.split()) > WORD_LIMIT:
        candidates = [(st["priority"], s, i) for s in ("key_findings", "model_results") for i, st in enumerate(by_section.get(s, [])) if st["priority"] > 0]
        if not candidates:
            break
        _, s, i = max(candidates, key=lambda c: (c[0], c[2]))
        del by_section[s][i]
        text, bullets = _render(ctx, by_section, sections, cite)
    numeric = [b for b in bullets if DIGIT.search(b)]
    cited = [b for b in numeric if b.rstrip().endswith("]") and "[source: " in b]
    out = {
        "sections": sections,
        "causal_language": mode,
        "cite_artifacts": cite,
        "word_count": len(text.split()),
        "n_numeric_statements": len(numeric),
        "n_cited_statements": len(cited),
    }
    ctx.metrics["brief"] = out
    ctx.write_text("executive_brief.md", text)
    ctx.result("brief_sections", f"Sections: {', '.join(sections)}; causal_language={mode}; cite_artifacts={cite}", source=ctx.artifact_rel("executive_brief.md"))
    ctx.result("brief_sections", "Word count", value=out["word_count"], source="metrics.json#brief.word_count")
    ctx.result("brief_sections", "Numeric statements cited", value=rate(out["n_cited_statements"], out["n_numeric_statements"]), numerator=out["n_cited_statements"], denominator=out["n_numeric_statements"], source="metrics.json#brief")


HANDLERS = {"collect_findings": collect_findings, "brief_sections": brief_sections}
