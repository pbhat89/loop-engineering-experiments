"""Deterministic rule-based learner ("naive analyst") behind the ``rule_learner`` runtime mode.

Experiment 2 (D-18). The planner starts every task from the catalogue's textbook defaults and
changes a choice only when (a) evaluator feedback on the *current* task recommends it, or
(b) a retrieved skill carries a machine-readable convention that applies to the current
catalogue. The skills it proposes encode conventions as tokens in ``required_checks``::

    param:<name>=<value>               set parameter <name> on every selected component that has it
    param:<component>.<name>=<value>   set it on one specific component
    component:<id>                     include component <id> (with its default parameters)
    list:<name>+=<value>               add <value> to every multi-valued parameter <name>
    list:<name>-=<value>               remove <value> from every multi-valued parameter <name>

A convention is generalised by *parameter name*, which is exactly what a house convention
is ("denominator means adjudicated claims", "small groups are < 30"). It never reads task
briefs or goldens; foundational (prose) skills carry no tokens and are inert for this
learner. Over-generalisation is possible and is part of the experiment: a list addition
learned on one task may be wrong on another, and the evaluator's feedback on that task then
overrides it. Nothing here is an LLM; every record it produces is labelled
``rule-learner-v1`` / ``deterministic-rule-learner``.
"""
from __future__ import annotations

import re
from typing import Any

from src.graph_nodes import _NO_MATCH, match_option
from src.llm_provider import FixtureProvider, ProviderSettings

COMPONENT_RULE = re.compile(r"component:([a-z][a-z0-9_]*)")
PARAM_RULE = re.compile(r"param:(?:([a-z][a-z0-9_]*)\.)?([a-z][a-z0-9_]*)=([A-Za-z0-9_.\-]+)")
LIST_RULE = re.compile(r"list:([a-z][a-z0-9_]*)(\+=|-=)(\S+)")
_TRAILING = ".,;:)]"

# Tags attached to a learned skill by the parameter/component it governs, so tag-based retrieval
# surfaces it on tasks of the same kind (task tags come from config/tasks.yaml).
RULE_TAGS: dict[str, list[str]] = {
    "denominator": ["rates", "denominators", "denials"],
    "min_group_size": ["small_groups", "segments", "group_comparison"],
    "date_column": ["trends", "descriptive"],
    "statistics": ["financial", "descriptive"],
    "scope": ["denials", "denial_codes"],
    "quantify_missing": ["denials", "missingness"],
    "caveats": ["communication", "caveats", "descriptive", "rates", "modeling", "fraud", "denials", "providers"],
    "show_denominators": ["communication", "rates", "denominators", "denials", "providers"],
    "cite_artifacts": ["communication", "caveats", "executive_brief"],
    "features": ["modeling", "leakage", "classification", "high_cost"],
    "fit_on": ["modeling", "splits", "leakage"],
    "stratify": ["modeling", "splits", "class_imbalance"],
    "test_size": ["modeling", "splits"],
    "threshold_source": ["modeling", "threshold", "leakage"],
    "amount_column": ["high_cost", "threshold"],
    "percentile": ["high_cost", "threshold"],
    "models": ["modeling", "metrics"],
    "class_weight": ["modeling", "class_imbalance"],
    "pairs": ["joins", "cardinality", "keys"],
    "keys": ["keys", "duplicates", "data_contract"],
    "columns": ["dates", "data_contract"],
    "consistency_checks": ["dates", "data_quality"],
    "segments": ["segments", "denials"],
    "group_by": ["group_comparison", "providers", "network"],
    "metrics": ["group_comparison", "metrics"],
    "sources": ["executive_brief", "synthesis"],
    "sections": ["executive_brief", "communication"],
    "causal_language": ["communication", "association"],
    "join_check": ["joins", "cardinality"],
    "leakage_assessment": ["leakage", "fraud", "protected_attributes"],
    "fraud_prevalence": ["fraud", "prevalence", "rates"],
    "provider_ranking": ["providers"],
    "duplicate_check": ["duplicates", "keys", "data_contract"],
    "date_ranges": ["dates", "data_contract"],
}


# --------------------------------------------------------------------------- tokens


def parse_rules(text: str) -> list[tuple]:
    """Extract ordered rule tuples from skill text: ("component", id) | ("param", comp|None, name, value) | ("list", name, op, value)."""
    rules: list[tuple] = []
    for m in COMPONENT_RULE.finditer(text):
        rules.append(("component", m.group(1)))
    for m in PARAM_RULE.finditer(text):
        rules.append(("param", m.group(1), m.group(2), m.group(3).rstrip(_TRAILING)))
    for m in LIST_RULE.finditer(text):
        rules.append(("list", m.group(1), m.group(2), m.group(3).rstrip(_TRAILING)))
    return rules


def rule_token(rule: tuple) -> str:
    if rule[0] == "component":
        return f"component:{rule[1]}"
    if rule[0] == "param":
        return f"param:{rule[1] + '.' if rule[1] else ''}{rule[2]}={rule[3]}"
    return f"list:{rule[1]}{rule[2]}{rule[3]}"


def describe_rule(rule: tuple) -> str:
    if rule[0] == "component":
        return f"Include the `{rule[1]}` component."
    if rule[0] == "param":
        scope = f"on `{rule[1]}`" if rule[1] else "on any component that has it"
        return f"`{rule[2]}` = `{rule[3]}` {scope}."
    verb = "Add" if rule[2] == "+=" else "Remove"
    prep = "to" if rule[2] == "+=" else "from"
    return f"{verb} `{rule[3]}` {prep} any `{rule[1]}` list."


def _fmt(value: Any) -> str:
    return "true" if value is True else "false" if value is False else str(value)


def _match(options: list | None, value: str) -> Any:
    """Declared option equal to the token value; booleans and other options compare case-insensitively by string form."""
    opt = match_option(options, value)
    if opt is not _NO_MATCH or options is None:
        return opt
    for option in options:
        if not isinstance(option, (list, dict)) and _fmt(option).lower() == str(value).lower():
            return option
    return _NO_MATCH


# --------------------------------------------------------------------------- provider


class RuleLearnerProvider(FixtureProvider):
    """Textbook-default planner that learns house conventions from feedback and reuses them by parameter name."""

    def __init__(self, settings: ProviderSettings):
        super().__init__(settings)

    # ---- plan --------------------------------------------------------------------------
    def _plan(self, payload: dict, *, revise: bool) -> dict:
        catalogue = self._catalogue(payload)
        selected: dict[str, dict] = {}
        if revise and payload.get("prior_plan"):
            for step in payload["prior_plan"].get("steps", []):
                if step.get("component") in catalogue:
                    selected[step["component"]] = dict(step.get("params") or {})
        else:
            for cid, comp in catalogue.items():
                if comp.get("default_selected"):
                    selected[cid] = self._default_params(comp)
        applied: list[str] = []
        for skill in payload.get("retrieved_skills", []) or []:
            rules = parse_rules(self._skill_text(skill))
            if rules and self._apply_rules(rules, catalogue, selected) and skill.get("skill_id"):
                applied.append(skill["skill_id"])
        changes: list[str] = []
        if revise:
            for item in payload.get("feedback", []) or []:
                for rec in item.get("related_components", []) or []:
                    cid = rec.get("component")
                    if cid not in catalogue:
                        continue
                    params = selected.setdefault(cid, self._default_params(catalogue[cid]))
                    declared = catalogue[cid].get("params") or {}
                    for k, v in (rec.get("params") or {}).items():
                        if k in declared:
                            params[k] = list(dict.fromkeys(v)) if isinstance(v, list) else v
                    changes.append(f"{cid} <- {item.get('feedback_id')}")
        return {
            "steps": [{"component": cid, "params": params} for cid, params in selected.items()],
            "skills_applied": list(dict.fromkeys(applied)),
            "rationale": "rule learner: textbook catalogue defaults"
            + (f" + conventions from {len(applied)} skill(s)" if applied else "")
            + (" + evaluator feedback fixes" if changes else ""),
            "changes_summary": ("; ".join(changes) or "no feedback recommendations applied") if revise else None,
        }

    @staticmethod
    def _apply_rules(rules: list[tuple], catalogue: dict[str, dict], selected: dict[str, dict]) -> bool:
        fired = False
        for rule in rules:
            if rule[0] != "component":
                continue
            cid = rule[1]
            if cid in catalogue and cid not in selected:
                selected[cid] = {n: s.get("default") for n, s in (catalogue[cid].get("params") or {}).items() if "default" in s}
                fired = True
        for rule in rules:
            if rule[0] == "param":
                _, target, name, value = rule
                for cid, params in selected.items():
                    if target and cid != target:
                        continue
                    spec = (catalogue.get(cid, {}).get("params") or {}).get(name)
                    if spec is None or spec.get("multi"):
                        continue
                    opt = _match(spec.get("options"), value)
                    if opt is _NO_MATCH or params.get(name) == opt:
                        continue
                    params[name] = opt
                    fired = True
            elif rule[0] == "list":
                _, name, op, value = rule
                for cid, params in selected.items():
                    spec = (catalogue.get(cid, {}).get("params") or {}).get(name)
                    if spec is None or not spec.get("multi"):
                        continue
                    current = list(params.get(name) or [])
                    if op == "+=":
                        opt = _match(spec.get("options"), value)
                        if opt is _NO_MATCH or opt in current:
                            continue
                        params[name] = current + [opt]
                        fired = True
                    else:
                        kept = [v for v in current if _fmt(v).lower() != value.lower()]
                        if len(kept) != len(current):
                            params[name] = kept
                            fired = True
        return fired

    # ---- reflect -----------------------------------------------------------------------
    @staticmethod
    def _tokens_from_feedback(item: dict, first_plan: dict | None) -> list[str]:
        """Convention tokens implied by one feedback item's recommended fix, generalised by parameter name.

        The diff is taken against the task's *first* plan (the naive one the feedback was issued
        for), so lessons survive even when the current plan already contains the fix.
        """
        plan_params = {s["component"]: dict(s.get("params") or {}) for s in (first_plan or {}).get("steps", [])}
        # Removals are learned only from exclusion-type feedback (leakage, prohibited or protected fields).
        # Other list checks are "at least these" requirements, so dropping unlisted items would be over-fitting.
        marker = f"{item.get('issue_type', '')} {item.get('feedback_id', '')} {item.get('check_id', '')}".lower()
        learn_removals = any(w in marker for w in ("leak", "exclud", "prohibit", "protected"))
        tokens: list[str] = []
        for rec in item.get("related_components", []) or []:
            cid = rec.get("component")
            if not cid:
                continue
            tokens.append(f"component:{cid}")  # idempotent at apply time: only adds the component when missing
            current = plan_params.get(cid, {})
            for name, value in (rec.get("params") or {}).items():
                if isinstance(value, list):
                    before = list(current.get(name) or [])
                    tokens += [f"list:{name}+={_fmt(v)}" for v in value if v not in before]
                    if learn_removals:
                        tokens += [f"list:{name}-={_fmt(v)}" for v in before if v not in value]
                else:
                    tokens.append(f"param:{name}={_fmt(value)}")
        return list(dict.fromkeys(tokens))

    def _reflect(self, payload: dict) -> dict:
        feedback = payload.get("feedback", []) or []
        remaining = list(payload.get("remaining_task_ids", []) or [])
        history = payload.get("plan_history") or []
        first_plan = history[0] if history else payload.get("plan")
        lessons, corrections = [], []
        for item in feedback:
            fid = item.get("feedback_id", "")
            corrections.append({"feedback_id": fid, "correction": item.get("remediation", "")})
            tokens = self._tokens_from_feedback(item, first_plan)
            if tokens:
                lessons.append(
                    {
                        "lesson": f"House convention from {fid}: " + " ".join(tokens),
                        "applicable_task_ids": remaining,  # applies wherever the parameter exists; reuse is logged, not assumed
                        "source_feedback_ids": [fid],
                    }
                )
        return {"reusable_lessons": lessons, "current_task_corrections": corrections}

    # ---- propose -----------------------------------------------------------------------
    @staticmethod
    def _known_tokens(existing: list[dict]) -> set[str]:
        known: set[str] = set()
        for s in existing or []:
            text = " ".join(
                " ".join(v) if isinstance(v, list) else str(v)
                for v in (s.get("required_checks"), s.get("procedure"), s.get("objective"))
                if v
            )
            known.update(rule_token(r) for r in parse_rules(text))
        return known

    def _propose(self, payload: dict) -> dict:
        remaining = set(payload.get("remaining_task_ids", []) or [])
        lessons = (payload.get("reflection") or {}).get("reusable_lessons", []) or []
        known = self._known_tokens(payload.get("existing_skills") or [])
        rules: list[tuple] = []
        sources: list[str] = []
        for lesson in lessons:
            if len(set(lesson.get("applicable_task_ids") or []) & remaining) < 2:
                continue
            for rule in parse_rules(lesson.get("lesson", "")):
                if rule_token(rule) not in known and rule not in rules:
                    rules.append(rule)
            sources += [f for f in lesson.get("source_feedback_ids") or [] if f]
        if not rules:
            return {"proposal": None, "reason_if_null": "no new convention: every lesson is already captured by an existing skill or applies to fewer than two remaining tasks"}
        # Task ids stay out of the skill text (the validator treats them as single-task scope);
        # provenance travels in source_feedback_ids and the store's Provenance section.
        task_tags = list((payload.get("task_spec") or {}).get("tags") or [])
        keys = [r[1] if r[0] == "component" else (r[2] if r[0] == "param" else r[1]) for r in rules]
        tags: list[str] = []
        for key in keys:
            tags += RULE_TAGS.get(key, [])
        tokens = [rule_token(r) for r in rules]
        procedure = [describe_rule(r) for r in rules]
        if len(procedure) < 2:
            procedure.append("State the convention in the report's Method section.")
        return {
            "proposal": {
                "name": ("conventions_" + "_".join(dict.fromkeys(keys)))[:60].rstrip("_"),
                "tags": list(dict.fromkeys(task_tags + tags)),
                "trigger": f"The task catalogue offers {', '.join(sorted(set(keys)))}.",
                "objective": "House conventions learned from evaluator feedback: " + "; ".join(tokens),
                "procedure": procedure,
                "required_checks": tokens,
                "expected_artifacts": list((payload.get("task_spec") or {}).get("required_artifacts") or [])[:3],
                "failure_modes": [
                    "A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.",
                    "List additions may name fields or pairs a later task does not load.",
                ],
                "example": describe_rule(rules[0]),
                "applicable_task_ids": sorted(remaining),
                "source_feedback_ids": list(dict.fromkeys(sources)),
            },
            "reason_if_null": None,
        }

    def _revise_proposal(self, payload: dict) -> dict:
        validation = payload.get("validation") or {}
        if validation.get("duplicate_of"):
            return {"proposal": None, "reason_if_null": f"withdrawn: duplicate of {validation['duplicate_of']}"}
        return super()._revise_proposal(payload)
