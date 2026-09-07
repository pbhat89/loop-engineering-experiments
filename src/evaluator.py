"""Deterministic evaluator: compares an execution result with the frozen rubric and golden pack (A3).

``evaluate(task_spec, execution_result, rubric, golden) -> dict`` (LEAD §7 / plan §15). No LLM judging: every
check is a rule over ``metrics.json`` content, artifact files, and the text of ``report.md`` /
``executive_brief.md``. Check kinds, the ``target`` grammar and the golden sections they read are documented
in the header of ``config/rubric.yaml``; the summary is:

    exact              metrics[target]  vs golden.expected_exact[golden_key]   (subset / multiset semantics)
    tolerance          metrics[target]  vs golden.expected_metrics[golden_key] {value|values, tolerance}
    artifact_exists    target file listed in the result (or in output_dir) and present on disk
    field_excluded     metrics[target] (list or dict keys, or plan:<component>.<param>) disjoint from golden.prohibited_fields
    contract           metrics[target]  vs golden.contracts[golden_key]  (scalar | includes | any_of | each_has | min_count/from | equals_metric | present)
    caveat_keywords    caveat id in metrics.report.caveats OR any golden keyword in report text
    metric_range       metrics[target] (``*`` expands) within golden.metric_ranges[golden_key] {min, max}; bounds may be metric paths
    report_structure   <file>#section:<H> | <file>#pattern:<name> | <file>#forbidden_phrases | <file>#max_words:<n>
    component_executed target in execution_result.components_executed

Scoring: dimension = 4 * sum(weight * passed) / sum(weight) (2 dp, null when a task has no checks in that dimension);
score_total = mean of non-null dimensions (2 dp); passed = all critical checks passed and score_total >= pass_threshold.
A missing metric fails its check with ``observed: null``. Output ordering follows the rubric, so results are stable.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import mean
from typing import Any

from src.utils import REPO_ROOT, read_json, rel, sha256_file

EVALUATOR_VERSION = "1.3"  # 1.1: caveat keywords matched only in caveat/limitation sections or path-stripped text (D-19); 1.2: self_refine added to the stripped condition names (D-21); 1.3: feedback_memory and self_refine_memory added to them (D-22) - condition names only, scoring unchanged
FREEZE_MANIFEST_PATH = REPO_ROOT / "config" / "freeze_manifest.json"
FLOAT_TOL = 1e-9
MAX_MISMATCHES = 5

DEFAULT_ISSUE_TYPE = {
    "exact": "wrong_value",
    "tolerance": "wrong_value",
    "artifact_exists": "missing_artifact",
    "field_excluded": "leakage",
    "contract": "wrong_convention",
    "caveat_keywords": "missing_caveat",
    "metric_range": "metric_out_of_range",
    "report_structure": "report_structure",
    "component_executed": "missing_component",
}
PATTERNS = {
    "denominator_format": re.compile(r"\d[\d,]*\s*/\s*\d[\d,]*\s*=\s*\d"),
    "source_citation": re.compile(r"\[source:\s*[^\]]+\]", re.IGNORECASE),
}


# --------------------------------------------------------------------------- generic helpers
def _jsonable(v: Any) -> Any:
    if v is None or isinstance(v, (bool, int, float, str)):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return str(v)
        return v
    if hasattr(v, "item") and callable(v.item):  # numpy scalar
        try:
            return _jsonable(v.item())
        except Exception:  # pragma: no cover - defensive
            return str(v)
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_jsonable(x) for x in v]
    return str(v)


def _as_float(v: Any) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if hasattr(v, "item"):
        try:
            return _as_float(v.item())
        except Exception:
            return None
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _scalar_eq(expected: Any, observed: Any) -> bool:
    if isinstance(expected, bool) or isinstance(observed, bool):
        return str(expected).lower() == str(observed).lower()
    fe, fo = _as_float(expected), _as_float(observed)
    if fe is not None and fo is not None and not (isinstance(expected, str) and isinstance(observed, str)):
        return math.isclose(fe, fo, rel_tol=FLOAT_TOL, abs_tol=FLOAT_TOL)
    if expected is None or observed is None:
        return expected is None and observed is None
    return str(expected) == str(observed)


def resolve_all(obj: Any, path: str) -> list[tuple[str, Any]]:
    """Resolve a dotted path against nested dicts, allowing keys that themselves contain dots (longest key wins)
    and ``*`` segments that expand over every key. Returns ``[(concrete_path, value), ...]``; empty when absent."""
    if path == "":
        return [("", obj)]
    if not isinstance(obj, dict):
        return []
    if path == "*" or path.startswith("*."):
        rest = path[1:].lstrip(".")
        out: list[tuple[str, Any]] = []
        for k, v in obj.items():
            for p, val in resolve_all(v, rest):
                out.append((f"{k}.{p}" if p else str(k), val))
        return out
    keys = {str(k): k for k in obj}
    candidates = [ks for ks in keys if path == ks or path.startswith(ks + ".")]
    if not candidates:
        return []
    ks = max(candidates, key=len)
    rest = path[len(ks):].lstrip(".")
    return [((f"{ks}.{p}" if p else ks), val) for p, val in resolve_all(obj[keys[ks]], rest)]


def resolve(obj: Any, path: str) -> tuple[bool, Any]:
    hits = resolve_all(obj, path)
    if not hits:
        return False, None
    return True, hits[0][1]


def mismatches(expected: Any, observed: Any, path: str = "") -> list[str]:
    """Exact-match semantics: dict subset, scalar-list multiset, dict-list multiset of subset matches, numbers ~1e-9."""
    where = path or "value"
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return [f"{where}: expected a mapping, observed {type(observed).__name__}"]
        keys = {str(k): k for k in observed}
        out: list[str] = []
        for k, ev in expected.items():
            if str(k) not in keys:
                out.append(f"{where}.{k}: missing")
            else:
                out += mismatches(ev, observed[keys[str(k)]], f"{where}.{k}")
        return out
    if isinstance(expected, list):
        if not isinstance(observed, list):
            return [f"{where}: expected a list, observed {type(observed).__name__}"]
        if len(expected) != len(observed):
            return [f"{where}: expected {len(expected)} items, observed {len(observed)}"]
        if all(not isinstance(e, (dict, list)) for e in expected):
            exp_sorted = sorted(str(e) for e in expected)
            obs_sorted = sorted(str(o) for o in observed)
            return [] if exp_sorted == obs_sorted else [f"{where}: items differ (missing {sorted(set(exp_sorted) - set(obs_sorted))[:MAX_MISMATCHES]}, unexpected {sorted(set(obs_sorted) - set(exp_sorted))[:MAX_MISMATCHES]})"]
        remaining = list(observed)
        out = []
        for i, e in enumerate(expected):
            match = next((o for o in remaining if not mismatches(e, o)), None)
            if match is None:
                out.append(f"{where}[{i}]: no matching element for {json.dumps(_jsonable(e), sort_keys=True)[:160]}")
            else:
                remaining.remove(match)
        return out
    return [] if _scalar_eq(expected, observed) else [f"{where}: expected {json.dumps(_jsonable(expected))}, observed {json.dumps(_jsonable(observed))[:160]}"]


def _items(observed: Any, field: str | None) -> list[str] | None:
    """Project an observed collection to a list of string items (dict -> keys; list of dicts + field -> that field)."""
    if isinstance(observed, dict):
        return [str(k) for k in observed]
    if isinstance(observed, list):
        if field:
            return [str(e.get(field)) for e in observed if isinstance(e, dict) and e.get(field) is not None]
        return [str(e) for e in observed]
    return None


def _compact(v: Any) -> Any:
    """Keep observed values small enough for logs."""
    j = _jsonable(v)
    if isinstance(j, (dict, list)) and len(json.dumps(j)) > 600:
        return {"_truncated": True, "_type": type(v).__name__, "_size": len(v) if hasattr(v, "__len__") else None}
    return j


# --------------------------------------------------------------------------- evaluation context
class _Context:
    def __init__(self, task_spec: dict, execution_result: dict, golden: dict):
        self.task_spec = task_spec
        self.result = execution_result or {}
        self.golden = golden or {}
        metrics = self.result.get("metrics")
        if not isinstance(metrics, dict) or not metrics:
            metrics = read_json(self._abs(self.result.get("metrics_path")), default={}) if self.result.get("metrics_path") else {}
        self.metrics: dict = metrics if isinstance(metrics, dict) else {}
        self.output_dir = self.result.get("output_dir")
        self.artifacts = [str(a) for a in (self.result.get("artifacts") or [])]
        self._text_cache: dict[str, str | None] = {}

    @staticmethod
    def _abs(p: str | None) -> Path | None:
        if not p:
            return None
        path = Path(p)
        return path if path.is_absolute() else REPO_ROOT / path

    def locate(self, name: str) -> tuple[Path | None, str]:
        """Find an artifact by file name: listed artifacts, metrics/report paths, then output_dir. Returns (path, how)."""
        candidates: list[tuple[str, str]] = [(a, "listed") for a in self.artifacts if Path(a).name == name]
        if name == "metrics.json" and self.result.get("metrics_path"):
            candidates.append((str(self.result["metrics_path"]), "metrics_path"))
        if name == "report.md" and self.result.get("report_path"):
            candidates.append((str(self.result["report_path"]), "report_path"))
        if self.output_dir:
            candidates.append((f"{self.output_dir}/{name}", "output_dir (not listed)"))
        for p, how in candidates:
            ap = self._abs(p)
            if ap is not None and ap.is_file():
                return ap, how
        return None, "not found"

    def text(self, name: str) -> str | None:
        if name not in self._text_cache:
            path, _ = self.locate(name)
            try:
                self._text_cache[name] = path.read_text(encoding="utf-8", errors="replace") if path else None
            except OSError:
                self._text_cache[name] = None
        return self._text_cache[name]

    def plan_param(self, component: str, param: str) -> tuple[bool, Any]:
        plan = self.metrics.get("plan") if isinstance(self.metrics.get("plan"), dict) else self.result.get("plan")
        for step in (plan or {}).get("steps", []) if isinstance(plan, dict) else []:
            if step.get("component") == component:
                params = step.get("params") or {}
                return (param in params), params.get(param)
        return False, None

    def resolve(self, path: str) -> tuple[bool, Any]:
        if path.startswith("plan:"):
            comp, _, param = path[5:].partition(".")
            return self.plan_param(comp, param)
        return resolve(self.metrics, path)


# --------------------------------------------------------------------------- check kinds
def _check_exact(chk: dict, ctx: _Context, key: str) -> dict:
    expected_all = ctx.golden.get("expected_exact") or {}
    if key not in expected_all:
        return {"passed": False, "observed": None, "expected": None, "detail": f"golden has no expected_exact[{key!r}]"}
    expected = expected_all[key]
    found, observed = ctx.resolve(chk["target"])
    if not found:
        return {"passed": False, "observed": None, "expected": _compact(expected), "detail": f"metric {chk['target']!r} missing"}
    mm = mismatches(expected, observed)
    detail = "matches golden" if not mm else "; ".join(mm[:MAX_MISMATCHES]) + (f" (+{len(mm) - MAX_MISMATCHES} more)" if len(mm) > MAX_MISMATCHES else "")
    return {"passed": not mm, "observed": _compact(observed), "expected": _compact(expected), "detail": detail}


def _check_tolerance(chk: dict, ctx: _Context, key: str) -> dict:
    spec = (ctx.golden.get("expected_metrics") or {}).get(key)
    if not isinstance(spec, dict):
        return {"passed": False, "observed": None, "expected": None, "detail": f"golden has no expected_metrics[{key!r}]"}
    tol = float(spec.get("tolerance", 0.0))
    found, observed = ctx.resolve(chk["target"])
    if not found:
        return {"passed": False, "observed": None, "expected": _compact(spec.get("value", spec.get("values"))), "detail": f"metric {chk['target']!r} missing"}
    if "values" in spec:
        expected = spec["values"]
        if not isinstance(observed, dict):
            return {"passed": False, "observed": _compact(observed), "expected": _compact(expected), "detail": "expected a mapping of values"}
        keys = {str(k): k for k in observed}
        bad = []
        for k, ev in expected.items():
            ov = _as_float(observed.get(keys.get(str(k)))) if str(k) in keys else None
            if ov is None or abs(ov - float(ev)) > tol:
                bad.append(f"{k}: expected {ev}, observed {ov}")
        return {"passed": not bad, "observed": _compact(observed), "expected": _compact(expected),
                "detail": "all values within tolerance" if not bad else "; ".join(bad[:MAX_MISMATCHES])}
    if isinstance(observed, dict) and "value" in observed:
        observed = observed["value"]
    ov = _as_float(observed)
    expected = float(spec["value"])
    if ov is None:
        return {"passed": False, "observed": _compact(observed), "expected": expected, "detail": "observed value is not numeric"}
    diff = abs(ov - expected)
    return {"passed": diff <= tol, "observed": ov, "expected": expected,
            "detail": f"|observed - expected| = {diff:.6g} {'<=' if diff <= tol else '>'} tolerance {tol:g}; golden definition: {json.dumps(spec.get('definition', {}), sort_keys=True)[:240]}"}


def _check_artifact(chk: dict, ctx: _Context, key: str) -> dict:
    path, how = ctx.locate(chk["target"])
    return {"passed": path is not None, "observed": rel(path) if path else None, "expected": chk["target"],
            "detail": f"{chk['target']} {how}" if path else f"{chk['target']} not found in listed artifacts, metrics/report paths or output_dir"}


def _check_field_excluded(chk: dict, ctx: _Context, key: str) -> dict:
    prohibited = [str(f) for f in (ctx.golden.get("prohibited_fields") or [])]
    if chk.get("fields"):
        prohibited = [f for f in prohibited if f in set(map(str, chk["fields"]))]
    found, observed = ctx.resolve(chk["target"])
    items = _items(observed, None) if found else None
    if items is None:
        return {"passed": False, "observed": None, "expected": f"none of {prohibited}", "detail": f"feature list {chk['target']!r} missing"}
    overlap = [f for f in prohibited if f in set(items)]
    return {"passed": not overlap, "observed": overlap, "expected": f"none of {prohibited}",
            "detail": "no prohibited fields present" if not overlap else f"prohibited fields present: {overlap}"}


def _check_contract(chk: dict, ctx: _Context, key: str) -> dict:
    contracts = ctx.golden.get("contracts") or {}
    if key not in contracts:
        return {"passed": False, "observed": None, "expected": None, "detail": f"golden has no contracts[{key!r}]"}
    expected = contracts[key]
    found, observed = ctx.resolve(chk["target"])
    rule_keys = {"includes", "any_of", "each_has", "min_count", "from", "equals_metric", "present", "field"}
    if isinstance(expected, dict) and set(expected) & rule_keys:
        if not found:
            return {"passed": False, "observed": None, "expected": _compact(expected), "detail": f"metric {chk['target']!r} missing"}
        field = expected.get("field")
        problems: list[str] = []
        items = _items(observed, field)
        if "present" in expected and (observed is None) == bool(expected["present"]):
            problems.append("value absent")
        if "includes" in expected:
            missing = [x for x in expected["includes"] if str(x) not in set(items or [])]
            if missing:
                problems.append(f"missing {missing}")
        if "any_of" in expected and not (set(map(str, expected["any_of"])) & set(items or [])):
            problems.append(f"none of {expected['any_of']} present")
        if "each_has" in expected:
            elems = list(observed.values()) if isinstance(observed, dict) else (observed if isinstance(observed, list) else [])
            if not elems:
                problems.append("no elements to inspect")
            for name, e in (observed.items() if isinstance(observed, dict) else enumerate(elems)):
                if not isinstance(e, dict):
                    problems.append(f"{name}: not a mapping")
                    continue
                lacking = [f for f in expected["each_has"] if f not in e]
                if lacking:
                    problems.append(f"{name} lacks {lacking}")
        if "min_count" in expected:
            allowed = set(map(str, expected.get("from") or []))
            hits = [i for i in (items or []) if not allowed or i in allowed]
            if len(hits) < int(expected["min_count"]):
                problems.append(f"only {len(hits)} of the required {expected['min_count']} items present ({hits})")
        if "equals_metric" in expected:
            ok2, other = ctx.resolve(str(expected["equals_metric"]))
            if not ok2:
                problems.append(f"reference metric {expected['equals_metric']!r} missing")
            elif not _scalar_eq(other, observed):
                problems.append(f"{chk['target']} = {_jsonable(observed)} but {expected['equals_metric']} = {_jsonable(other)}")
        summary = items if items is not None else observed
        return {"passed": not problems, "observed": _compact(summary), "expected": _compact(expected),
                "detail": "contract satisfied" if not problems else "; ".join(problems[:MAX_MISMATCHES])}
    if not found:
        return {"passed": False, "observed": None, "expected": _jsonable(expected), "detail": f"metric {chk['target']!r} missing"}
    passed = _scalar_eq(expected, observed)
    return {"passed": passed, "observed": _compact(observed), "expected": _jsonable(expected),
            "detail": "contract satisfied" if passed else f"{chk['target']} is {_jsonable(observed)!r}, expected {_jsonable(expected)!r}"}


_SECTION_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


_CONDITION_NAMES = (
    "baseline",
    "reflection_only",
    "skill_learning",
    "foundational_only",
    "self_refine",
    "feedback_memory",
    "self_refine_memory",
)


def _caveat_scope(text: str, identifiers: tuple[str, ...] = ()) -> str:
    """Text in which caveat keywords may be matched (evaluator 1.1).

    Only the bodies of sections whose heading mentions caveats/limitations count; when a report has no
    such section, the whole text is used. In both cases artifact paths, ``[source: …]`` citations, the
    run id, the condition name and every known condition name are removed first — a report that says
    "condition `baseline`" must never satisfy a *model_limitations* caveat whose keywords include
    "baseline".
    """
    headings = list(_SECTION_RE.finditer(text))
    bodies: list[str] = []
    for i, m in enumerate(headings):
        title = m.group(2).lower()
        if "caveat" in title or "limitation" in title:
            end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
            bodies.append(text[m.end():end])
    scoped = "\n".join(bodies) if bodies else text
    scoped = re.sub(r"\[source:[^\]]*\]", " ", scoped, flags=re.IGNORECASE)  # citations first: they contain paths
    scoped = re.sub(r"artifacts/\S+", " ", scoped)
    scoped = re.sub(r"(?i)(?:run|condition)\s*`[^`]*`", " ", scoped)
    for ident in tuple(identifiers) + _CONDITION_NAMES:
        if ident:
            scoped = re.sub(rf"(?i)`?{re.escape(str(ident))}`?", " ", scoped)
    return scoped


def _check_caveat(chk: dict, ctx: _Context, key: str) -> dict:
    entry = next((c for c in (ctx.golden.get("required_caveats") or []) if str(c.get("id")) == chk["target"]), None)
    if entry is None:
        return {"passed": False, "observed": None, "expected": None, "detail": f"golden has no required_caveats entry {chk['target']!r}"}
    keywords = [str(k) for k in (entry.get("any_of") or [])]
    found, listed = ctx.resolve("report.caveats")
    in_metrics = found and isinstance(listed, list) and chk["target"] in [str(c) for c in listed]
    texts = [t for t in (ctx.text("report.md"), ctx.text("executive_brief.md")) if t]
    identifiers = tuple(str(ctx.metrics.get(k)) for k in ("run_id", "condition") if ctx.metrics.get(k))
    blob = "\n".join(_caveat_scope(t, identifiers) for t in texts).lower()
    hits = [k for k in keywords if k.lower() in blob]
    passed = bool(in_metrics or hits)
    return {"passed": passed, "observed": {"in_report_caveats": bool(in_metrics), "keywords_found": hits, "report_text_available": bool(texts)},
            "expected": {"caveat_id": chk["target"], "any_of": keywords},
            "detail": ("caveat present" if passed else f"caveat {chk['target']!r} neither listed in report.caveats nor phrased in the report text (keywords {keywords})")}


def _check_range(chk: dict, ctx: _Context, key: str) -> dict:
    rng = (ctx.golden.get("metric_ranges") or {}).get(key)
    if not isinstance(rng, dict):
        return {"passed": False, "observed": None, "expected": None, "detail": f"golden has no metric_ranges[{key!r}]"}
    bounds: dict[str, float | None] = {}
    for b in ("min", "max"):
        raw = rng.get(b)
        # a bound may be a number, a metric path, or {"ref": <metric path>, "factor": <float>} (ref x factor)
        ref, factor = (raw.get("ref"), float(raw.get("factor", 1.0))) if isinstance(raw, dict) else (raw if isinstance(raw, str) else None, 1.0)
        if ref is not None:
            ok2, val = ctx.resolve(ref)
            resolved = _as_float(val) if ok2 else None
            if resolved is None:
                return {"passed": False, "observed": None, "expected": _jsonable(rng), "detail": f"bound {b} refers to missing metric {ref!r}"}
            bounds[b] = resolved * factor
        else:
            bounds[b] = _as_float(raw)
    hits = resolve_all(ctx.metrics, chk["target"])
    if not hits:
        return {"passed": False, "observed": None, "expected": _jsonable({**rng, "resolved": bounds}), "detail": f"metric {chk['target']!r} missing"}
    observed = {p: _jsonable(v) for p, v in hits}
    bad = []
    for p, v in hits:
        fv = _as_float(v)
        if fv is None or (bounds["min"] is not None and fv < bounds["min"]) or (bounds["max"] is not None and fv > bounds["max"]):
            bad.append(f"{p} = {_jsonable(v)}")
    return {"passed": not bad, "observed": observed, "expected": _jsonable({**rng, "resolved": bounds}),
            "detail": f"all within [{bounds['min']}, {bounds['max']}]" if not bad else f"outside [{bounds['min']}, {bounds['max']}]: {'; '.join(bad[:MAX_MISMATCHES])}"}


def _check_report_structure(chk: dict, ctx: _Context, key: str) -> dict:
    file, _, rule = str(chk["target"]).partition("#")
    text = ctx.text(file)
    if text is None:
        return {"passed": False, "observed": None, "expected": rule, "detail": f"{file} not found"}
    kind, _, arg = rule.partition(":")
    if kind == "section":
        passed = re.search(rf"^#{{1,6}}\s+{re.escape(arg)}\s*$", text, re.IGNORECASE | re.MULTILINE) is not None
        return {"passed": passed, "observed": passed, "expected": f"heading {arg!r}", "detail": f"{file}: heading {arg!r} {'found' if passed else 'missing'}"}
    if kind == "pattern":
        pat = PATTERNS.get(arg)
        if pat is None:
            return {"passed": False, "observed": None, "expected": arg, "detail": f"unknown pattern {arg!r}"}
        n = len(pat.findall(text))
        return {"passed": n > 0, "observed": n, "expected": f">= 1 match of {arg}", "detail": f"{file}: {n} match(es) of {arg}"}
    if kind == "forbidden_phrases":
        phrases = [str(p) for p in (ctx.golden.get("forbidden_phrases") or [])]
        hits = [p for p in phrases if re.search(rf"\b{re.escape(p)}\b", text, re.IGNORECASE)]
        return {"passed": not hits, "observed": hits, "expected": f"none of {phrases}", "detail": f"{file}: forbidden phrases present {hits}" if hits else f"{file}: no forbidden phrases"}
    if kind == "max_words":
        limit = int(arg)
        words = len(text.split())
        return {"passed": words <= limit, "observed": words, "expected": f"<= {limit} words", "detail": f"{file}: {words} words (limit {limit})"}
    return {"passed": False, "observed": None, "expected": rule, "detail": f"unknown report_structure rule {rule!r}"}


def _check_component(chk: dict, ctx: _Context, key: str) -> dict:
    executed = ctx.result.get("components_executed")
    if isinstance(executed, list):
        passed = chk["target"] in executed
        return {"passed": passed, "observed": passed, "expected": f"{chk['target']} executed", "detail": f"components_executed = {executed}"}
    produced = [p.get("key") for c in ctx.task_spec.get("components", []) if c.get("id") == chk["target"] for p in (c.get("produces") or [])]
    present = [k for k in produced if k in ctx.metrics]
    return {"passed": bool(present), "observed": present, "expected": f"{chk['target']} executed", "detail": "components_executed absent; inferred from produced metric keys"}


CHECKERS = {
    "exact": _check_exact,
    "tolerance": _check_tolerance,
    "artifact_exists": _check_artifact,
    "field_excluded": _check_field_excluded,
    "contract": _check_contract,
    "caveat_keywords": _check_caveat,
    "metric_range": _check_range,
    "report_structure": _check_report_structure,
    "component_executed": _check_component,
}


# --------------------------------------------------------------------------- public API
def canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(json.dumps(_jsonable(obj), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def freeze_sha256() -> str | None:
    if not FREEZE_MANIFEST_PATH.is_file():
        return None
    stored = read_json(FREEZE_MANIFEST_PATH, default={}) or {}
    return stored.get("freeze_sha256") or sha256_file(FREEZE_MANIFEST_PATH)


def run_check(chk: dict, ctx: _Context) -> dict:
    kind = chk.get("kind")
    key = chk.get("golden_key") or chk.get("target")
    checker = CHECKERS.get(kind)
    if checker is None:
        outcome = {"passed": False, "observed": None, "expected": None, "detail": f"unknown check kind {kind!r}"}
    else:
        try:
            outcome = checker(chk, ctx, str(key))
        except Exception as exc:  # a broken result must fail the check, never the evaluation
            outcome = {"passed": False, "observed": None, "expected": None, "detail": f"evaluator error while checking: {type(exc).__name__}: {exc}"}
    return {
        "check_id": chk["check_id"], "dimension": chk["dimension"], "weight": chk.get("weight", 1), "critical": bool(chk.get("critical")),
        "kind": kind, "target": chk.get("target"), "passed": bool(outcome["passed"]),
        "observed": _jsonable(outcome.get("observed")), "expected": _jsonable(outcome.get("expected")), "detail": str(outcome.get("detail", "")),
    }


def feedback_item(chk: dict, record: dict, task_id: str) -> dict:
    name = chk["check_id"].split(".", 1)[1] if "." in chk["check_id"] else chk["check_id"]
    weight = float(chk.get("weight", 1))
    severity = "high" if chk.get("critical") else ("medium" if weight >= 2 else "low")
    return {
        "feedback_id": f"{task_id}-{name}",
        "check_id": chk["check_id"],
        "criterion": chk["dimension"],
        "issue_type": chk.get("issue_type") or DEFAULT_ISSUE_TYPE.get(chk.get("kind"), "check_failed"),
        "severity": severity,
        "remediation": chk.get("remediation", ""),
        "related_components": copy.deepcopy(chk.get("related_components") or []),
        "reusable": bool(chk.get("reusable")),
        "applicable_task_ids": list(chk.get("applicable_task_ids") or []),
        "observed": record["observed"],
        "expected": record["expected"],
        "detail": record["detail"],
    }


def evaluate(task_spec: dict, execution_result: dict, rubric: dict, golden: dict) -> dict:
    """Score one execution result against the frozen rubric and golden for ``task_spec['task_id']``."""
    task_id = task_spec.get("task_id")
    task_rubric = ((rubric or {}).get("tasks") or {}).get(task_id) or {}
    checks_spec = list(task_rubric.get("checks") or [])
    dimensions = [d["id"] if isinstance(d, dict) else str(d) for d in (rubric or {}).get("dimensions") or []]
    threshold = float((rubric or {}).get("pass_threshold", 3.5))
    ctx = _Context(task_spec, execution_result, golden)

    records = [run_check(chk, ctx) for chk in checks_spec]
    totals = {d: [0.0, 0.0] for d in dimensions}
    for rec in records:
        w = float(rec["weight"])
        totals.setdefault(rec["dimension"], [0.0, 0.0])
        totals[rec["dimension"]][0] += w
        if rec["passed"]:
            totals[rec["dimension"]][1] += w
    scores = {d: (round(4.0 * got / total, 2) if total > 0 else None) for d, (total, got) in totals.items()}
    valid = [s for s in scores.values() if s is not None]
    score_total = round(mean(valid), 2) if valid else 0.0
    criticals_ok = all(rec["passed"] for rec in records if rec["critical"])
    passed = bool(records) and criticals_ok and score_total >= threshold
    feedback = [feedback_item(chk, rec, task_id) for chk, rec in zip(checks_spec, records) if not rec["passed"]]
    return {
        "evaluator_version": EVALUATOR_VERSION,
        "rubric_version": str((rubric or {}).get("rubric_version", "")),
        "golden_version": str((golden or {}).get("golden_version", "")),
        "rubric_sha256": canonical_sha256(rubric or {}),
        "golden_sha256": canonical_sha256(golden or {}),
        "freeze_sha256": freeze_sha256(),
        "task_id": task_id,
        "pass_threshold": threshold,
        "scores": scores,
        "score_total": score_total,
        "passed": passed,
        "critical_failures": [rec["check_id"] for rec in records if rec["critical"] and not rec["passed"]],
        "n_checks": len(records),
        "n_passed": sum(1 for rec in records if rec["passed"]),
        "checks": records,
        "feedback": feedback,
    }
