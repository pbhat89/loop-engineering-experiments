"""Validate a skill proposal before it is persisted (structure, safety, generality, duplicates).

``validate(proposal, existing_skills, task_id, remaining_task_ids)`` returns::

    {"decision": "accepted" | "rejected" | "retry_revision",
     "checks": [{"check_id", "passed", "detail", "severity"}],
     "reasons": [str],                     # details of every failed check
     "duplicate_of": str | None,           # skill_id when the duplicate check fails
     "similarity": float | None}           # highest token-Jaccard against existing skills

Decision rule: any failed check with severity ``reject`` -> ``rejected``; otherwise any failed
check with severity ``revise`` -> ``retry_revision`` (structural gaps the operator can fix in
one revision; the graph converts a second ``retry_revision`` into ``rejected``); otherwise
``accepted``. Every check always runs so the ``checks`` list is complete for the log.

Thresholds (all module constants, tuned to the six foundational skills):

* ``MIN_TEXT_CHARS = 10``      trigger and objective must each be at least this long   (revise)
* ``MIN_PROCEDURE_STEPS = 2``  procedure needs at least this many steps                 (revise)
* ``MIN_STEP_WORDS = 3``       every step must be concrete: at least this many words    (revise)
* ``MIN_EXAMPLE_CHARS = 10``   example shorter than this is a structural gap            (revise)
* ``MIN_FUTURE_TASKS = 2``     ``applicable_task_ids`` must intersect the remaining tasks
                               (excluding the current task) in at least this many ids   (reject)
* ``DUPLICATE_JACCARD = 0.6``  token-Jaccard over ``objective + procedure`` (tokens as in
                               ``skill_store.keywords``: alphanumeric, length >= 4, stop words
                               removed) against every existing skill; >= threshold is a
                               duplicate                                                (reject)

Safety (reject): the proposal text must not instruct shell/command execution, package
installation, network or URL access, credential/API-key/token use, ``eval``/``exec``, file or
directory deletion, or edits to the rubric, goldens, or evaluator. Patterns are listed in
``SAFETY_PATTERNS``.

Generality (reject, applied to trigger/objective/procedure/required_checks only, never to the
example): no hard-coded numeric findings ("denial rate is 10.4%", "12% of claims were denied"),
no scope limited to a single task id, and no ungrounded language ("proves", "guarantees",
"definitively", or direct causal claims about fraud/denials). Thresholds such as "n < 30" or
"95% interval" are not findings and pass.

Provenance (reject): ``source_feedback_ids`` must be non-empty.
"""
from __future__ import annotations

import re
from typing import Any

from src.skill_store import keywords

MIN_TEXT_CHARS = 10
MIN_PROCEDURE_STEPS = 2
MIN_STEP_WORDS = 3
MIN_EXAMPLE_CHARS = 10
MIN_FUTURE_TASKS = 2
DUPLICATE_JACCARD = 0.6

REJECT = "reject"
REVISE = "revise"

TEXT_FIELDS: tuple[str, ...] = (
    "name",
    "trigger",
    "objective",
    "procedure",
    "required_checks",
    "expected_artifacts",
    "failure_modes",
    "example",
)
GENERALITY_FIELDS: tuple[str, ...] = ("trigger", "objective", "procedure", "required_checks")
OPTIONAL_LIST_FIELDS: tuple[str, ...] = ("required_checks", "expected_artifacts", "failure_modes")

SAFETY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("shell_execution", r"\b(subprocess|os\.system|popen|powershell|cmd\.exe|/bin/sh|bash\b|zsh\b|\bsudo\b|chmod\b|chown\b)"),
    ("shell_execution", r"\b(run|execute|invoke|launch|spawn)\b(\s+\w+){0,3}\s+(shell|terminal|command line|command|commands|script|scripts|binary|executable)\b"),
    ("shell_execution", r"\b(shell|terminal)\s+(command|commands|script|access)\b"),
    ("package_install", r"\b(pip|pip3|conda|npm|apt(-get)?|brew|uv)\s+(install|add)\b"),
    ("network_access", r"\b(https?|ftp|ssh|sftp)://"),
    ("network_access", r"\b(curl|wget|urllib|requests\.(get|post|put)|httpx|socket|websocket)\b"),
    ("network_access", r"\b(download|upload|fetch|retrieve|pull|post|send|query|call)\b(\s+\w+){0,4}\s+(from|to|via|over)\s+(the\s+)?(internet|web|network|url|urls|api|apis|endpoint|endpoints|remote server|cloud)\b"),
    ("network_access", r"\b(api|http|https|rest|web)\s+(call|calls|request|requests|endpoint|endpoints)\b"),
    ("network_access", r"\b(internet|external network|network connection|web service)\b"),
    ("credential_use", r"\b(credential|credentials|password|passwords|passphrase|secret key|secrets?\b|api[ _-]?keys?|access[ _-]?tokens?|auth[ _-]?tokens?|bearer tokens?|private keys?|ssh keys?|service account|\.env\b|environment variables?)"),
    ("dynamic_code", r"\b(eval|exec|compile|__import__)\s*\("),
    ("dynamic_code", r"\b(eval|exec)\b"),
    ("file_deletion", r"\b(delete|remove|erase|wipe|purge|unlink|destroy)\b(\s+\w+){0,3}\s+(file|files|directory|directories|folder|folders|disk|drive|repository|repo)\b"),
    ("file_deletion", r"\b(rm\s+-rf?|rmdir|shutil\.rmtree|os\.remove|os\.unlink|\.unlink\(|del\s+/[a-z])"),
    ("evaluation_tampering", r"\b(edit|modify|change|update|rewrite|alter|patch|tweak|adjust|delete|remove|replace|bypass|skip|disable)\b(\s+\w+){0,3}\s+(rubric|rubrics|golden|goldens|golden pack|evaluator|grader|grading|freeze|pass threshold)\b"),
)

_METRIC_NOUNS = r"(rate|rates|share|shares|percentage|percentages|prevalence|proportion|proportions|ratio|ratios|mean|median|average|total|count|counts|volume|amount|amounts|frequency)"
GENERALITY_PATTERNS: tuple[tuple[str, str], ...] = (
    # "denial rate is 10.4%", "the median paid amount was 420", "total count = 12,800"
    ("hard_coded_finding", rf"\b{_METRIC_NOUNS}\b(\s+\w+){{0,2}}\s+(is|was|were|are|equals|equal to|=|came to|stands at|reached|sits at)\s+(about |approximately |roughly |around |~)?\$?\d"),
    # "10.4% denial rate", "12% of claims were denied", "1,150 denied claims"
    ("hard_coded_finding", rf"\d[\d,]*(\.\d+)?\s?%\s+(denial|fraud|denied|paid|approval|prevalence|of (the )?(claims|members|providers|rows|records|population|sample))\b"),
    ("hard_coded_finding", r"\b\d[\d,]*(\.\d+)?\s+(denied|paid|pending|fraudulent|flagged)\s+(claims|records|rows|members|providers)\b"),
    ("ungrounded_claim", r"\b(proves?|proven|guarantees?|guaranteed|definitively|certainly|undeniably|beyond doubt|without doubt)\b"),
    ("ungrounded_claim", r"\b(fraud|denials?)\b\s+(is|are|was|were)\s+caused\s+by\b"),
    ("ungrounded_claim", r"\bcauses?\s+(fraud|denials?|claim denials?)\b"),
)
_TASK_ID_RE = re.compile(r"\bT\d{1,3}\b")
_SINGLE_TASK_SCOPE_RE = re.compile(r"\b(only|specifically|just|solely|exclusively)\s+(for|in|to|during)\s+(task\s+)?T\d{1,3}\b|\bfor\s+task\s+T\d{1,3}\s+only\b", re.IGNORECASE)


# --------------------------------------------------------------------------- helpers


def _field(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return str(value or "")


def _existing_skill_text(skill: Any) -> str:
    sections = _field(skill, "sections") or {}
    return f"{_text(sections.get('objective'))} {_text(sections.get('procedure'))}"


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def nearest_existing(proposal: dict, existing_skills: list) -> tuple[str | None, float | None]:
    """(skill_id, similarity) of the most similar existing skill; ties by skill_id."""
    proposal_tokens = keywords(f"{_text(proposal.get('objective'))} {_text(proposal.get('procedure'))}")
    best_id: str | None = None
    best_sim: float | None = None
    for skill in sorted(existing_skills or [], key=lambda s: str(_field(s, "skill_id") or "")):
        sim = jaccard(proposal_tokens, keywords(_existing_skill_text(skill)))
        if best_sim is None or sim > best_sim:
            best_id, best_sim = str(_field(skill, "skill_id") or ""), sim
    return best_id, (None if best_sim is None else round(best_sim, 3))


def _scan(patterns: tuple[tuple[str, str], ...], text: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for label, pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            hits.append((label, m.group(0).strip()))
    return hits


class _Checks:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, check_id: str, passed: bool, detail: str, severity: str) -> None:
        self.items.append({"check_id": check_id, "passed": bool(passed), "detail": detail, "severity": severity})


# --------------------------------------------------------------------------- public API


def validate(proposal: dict, existing_skills: list, task_id: str, remaining_task_ids: list[str]) -> dict:
    """Validate one proposal against the content rules in ``skills/SKILL_SCHEMA.md``."""
    if hasattr(proposal, "model_dump"):
        proposal = proposal.model_dump()
    proposal = dict(proposal or {})
    checks = _Checks()

    # --- required fields (structural) ---------------------------------------------------
    name = _text(proposal.get("name")).strip()
    trigger = _text(proposal.get("trigger")).strip()
    objective = _text(proposal.get("objective")).strip()
    procedure = [str(s).strip() for s in _as_list(proposal.get("procedure")) if str(s).strip()]
    problems: list[str] = []
    if len(name) < 3:
        problems.append("name shorter than 3 characters")
    if len(trigger) < MIN_TEXT_CHARS:
        problems.append(f"trigger shorter than {MIN_TEXT_CHARS} characters")
    if len(objective) < MIN_TEXT_CHARS:
        problems.append(f"objective shorter than {MIN_TEXT_CHARS} characters")
    if len(procedure) < MIN_PROCEDURE_STEPS:
        problems.append(f"procedure has {len(procedure)} step(s); needs at least {MIN_PROCEDURE_STEPS}")
    checks.add("required_fields", not problems, "; ".join(problems) or "name, trigger, objective and procedure present", REVISE)

    vague = [s for s in procedure if len(s.split()) < MIN_STEP_WORDS]
    checks.add(
        "procedure_concrete",
        not vague,
        f"steps with fewer than {MIN_STEP_WORDS} words: {vague}" if vague else "every step names what to compute, compare, record, or check",
        REVISE,
    )

    tags = [str(t).strip() for t in _as_list(proposal.get("tags")) if str(t).strip()]
    checks.add("tags_present", bool(tags), "tags are used for retrieval and must be non-empty" if not tags else f"{len(tags)} tag(s)", REVISE)

    missing_optional = [f for f in OPTIONAL_LIST_FIELDS if not [x for x in _as_list(proposal.get(f)) if str(x).strip()]]
    checks.add(
        "optional_sections",
        not missing_optional,
        f"empty sections: {missing_optional}" if missing_optional else "required_checks, expected_artifacts and failure_modes present",
        REVISE,
    )

    example = _text(proposal.get("example")).strip()
    checks.add(
        "example_present",
        len(example) >= MIN_EXAMPLE_CHARS,
        f"example has {len(example)} characters; needs at least {MIN_EXAMPLE_CHARS}" if len(example) < MIN_EXAMPLE_CHARS else "example present",
        REVISE,
    )

    # --- provenance ------------------------------------------------------------------
    feedback_ids = [f for f in _as_list(proposal.get("source_feedback_ids")) if f.strip()]
    checks.add(
        "provenance",
        bool(feedback_ids),
        "source_feedback_ids is empty; an evolved skill must cite the feedback it was learned from" if not feedback_ids else f"cites feedback ids {feedback_ids}",
        REJECT,
    )

    # --- applicability -----------------------------------------------------------------
    applicable = {a.strip() for a in _as_list(proposal.get("applicable_task_ids")) if a.strip()}
    remaining = {r.strip() for r in _as_list(remaining_task_ids) if r.strip()} - {str(task_id)}
    future = sorted(applicable & remaining)
    checks.add(
        "applicability",
        len(future) >= MIN_FUTURE_TASKS,
        f"applies to {len(future)} remaining task(s) {future}; needs at least {MIN_FUTURE_TASKS} of {sorted(remaining)}",
        REJECT,
    )

    # --- safety ------------------------------------------------------------------------
    all_text = " \n ".join(_text(proposal.get(f)) for f in TEXT_FIELDS)
    safety_hits = _scan(SAFETY_PATTERNS, all_text)
    checks.add(
        "safety",
        not safety_hits,
        "unsafe instructions: " + "; ".join(f"{label} ({snippet!r})" for label, snippet in safety_hits) if safety_hits else "no shell, network, credential, dynamic-code, deletion, or evaluation-tampering instructions",
        REJECT,
    )

    # --- generality ----------------------------------------------------------------------
    scoped_text = " \n ".join(_text(proposal.get(f)) for f in GENERALITY_FIELDS)
    generality_hits = _scan(GENERALITY_PATTERNS, scoped_text)
    task_refs = sorted(set(_TASK_ID_RE.findall(f"{trigger} {objective}")))
    if len(task_refs) == 1 or _SINGLE_TASK_SCOPE_RE.search(scoped_text):
        generality_hits.append(("single_task_scope", f"trigger/objective scoped to task {task_refs or ['a single task id']}"))
    if len(applicable) == 1:
        generality_hits.append(("single_task_scope", f"applicable_task_ids names a single task {sorted(applicable)}"))
    checks.add(
        "generality",
        not generality_hits,
        "not a general skill: " + "; ".join(f"{label} ({snippet!r})" for label, snippet in generality_hits) if generality_hits else "no hard-coded findings, single-task scope, or ungrounded claims",
        REJECT,
    )

    # --- duplicate -----------------------------------------------------------------------
    nearest_id, similarity = nearest_existing(proposal, existing_skills)
    is_duplicate = similarity is not None and similarity >= DUPLICATE_JACCARD
    checks.add(
        "duplicate",
        not is_duplicate,
        f"token-Jaccard {similarity} vs {nearest_id} (threshold {DUPLICATE_JACCARD})" if nearest_id else "no existing skills to compare against",
        REJECT,
    )

    # --- decision ------------------------------------------------------------------------
    failed = [c for c in checks.items if not c["passed"]]
    if any(c["severity"] == REJECT for c in failed):
        decision = "rejected"
    elif failed:
        decision = "retry_revision"
    else:
        decision = "accepted"
    return {
        "decision": decision,
        "checks": checks.items,
        "reasons": [f"{c['check_id']}: {c['detail']}" for c in failed],
        "duplicate_of": nearest_id if is_duplicate else None,
        "similarity": similarity,
        "nearest_skill_id": nearest_id,
    }
