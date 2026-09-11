"""The request-payload leakage audit.

Run over **every** request file a run writes. It fails if anything the operator is not
allowed to see has reached a payload:

1. a forbidden key anywhere in the payload (``tier``, ``golden``, ``fired_rule_ids``, ...);
2. a house-rule id (``HR-07``) anywhere in the serialised request;
3. a tier word (``clean`` / ``judgement`` / ``compound``) used as a value;
4. the case's own golden - its decision phrasing, its class, its modifier keys, or the
   markup written about it;
5. a house-rule statement, or a numeric token that appears **only** in a house-rule
   statement and nowhere in the starter manual.

Two exemptions, both deliberate and both narrow:

``senior_answers``
    the ask-a-senior oracle quotes a rule out loud on purpose - that is the arm.
``memory.rulebook_markdown``
    the written-rules book is the operator's own prose. Whatever numbers it contains the
    operator inferred; flagging them would be flagging the arm's output, not a leak.

Everything else - the case, the manual, the instructions, the notebook entries, the
precedent entries - is system-authored and is checked in full.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from src.underwriting.engine import TIER_WORDS, modifier_key
from src.underwriting.house_rules import ALL_RULE_IDS, HOUSE_RULES
from src.underwriting.manual import build_manual

# Anything rule-shaped or tier-shaped is banned everywhere, memory blocks included.
FORBIDDEN_KEYS_ANYWHERE: frozenset[str] = frozenset(
    {
        "tier", "tiers", "case_tier",
        "golden", "goldens", "golden_answer",
        "fired_rule_ids", "fired_rules", "rule_id", "rule_ids",
        "house_rule", "house_rules", "markup_sentence", "statement",
        "manual_only",
    }
)
# Answer-shaped keys are banned outside the memory block. Inside it they are the design:
# the precedent arm exists to show past cases with the answer the reviewer settled on.
FORBIDDEN_KEYS_OUTSIDE_MEMORY: frozenset[str] = frozenset(
    {"correct_answer", "answer_key", "expected", "debit_breakdown", "total_debits", "debits"}
)
EXEMPT_PATHS: tuple[tuple[str, ...], ...] = (("senior_answers",), ("memory", "rulebook_markdown"))
MEMORY_PATH: tuple[str, ...] = ("memory",)

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_STATEMENT_FRAGMENT_WORDS = 6


def _manual_numbers() -> set[str]:
    return set(_NUMBER.findall(build_manual()))


def hidden_point_values() -> set[str]:
    """Numeric tokens that appear in a house-rule statement and nowhere in the manual."""
    manual = _manual_numbers()
    hidden: set[str] = set()
    for rule in HOUSE_RULES:
        hidden |= {t for t in _NUMBER.findall(rule.statement) if t not in manual}
    return hidden


def statement_fragments() -> dict[str, str]:
    """A fragment of each rule statement that does **not** also occur in its markup sentence.

    The markup sentence is allowed to travel (that is how the notebook arm works); the spoken
    statement is not. Sliding the window until the two differ keeps the check from firing on a
    legitimate markup whose wording happens to open the same way.
    """
    out: dict[str, str] = {}
    for rule in HOUSE_RULES:
        words = rule.statement.split()
        markup = rule.markup_sentence.lower()
        chosen = " ".join(words[:_STATEMENT_FRAGMENT_WORDS]).rstrip(",.")
        for start in range(0, max(len(words) - _STATEMENT_FRAGMENT_WORDS + 1, 1)):
            candidate = " ".join(words[start : start + _STATEMENT_FRAGMENT_WORDS]).rstrip(",.")
            if candidate.lower() not in markup:
                chosen = candidate
                break
        out[rule.rule_id] = chosen
    return out


def _walk(node: object, path: tuple[str, ...] = ()):
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, path + (str(key),))
    elif isinstance(node, (list, tuple)):
        for i, value in enumerate(node):
            yield from _walk(value, path + (f"[{i}]",))


def _is_exempt(path: tuple[str, ...]) -> bool:
    return any(path[: len(prefix)] == prefix for prefix in EXEMPT_PATHS)


def _text_of(node: object) -> str:
    return json.dumps(node, ensure_ascii=False, default=str)


def audit_payload(request: dict, golden: dict | None = None, markup: str | None = None) -> list[str]:
    """Every leak in one request. Empty list means clean."""
    problems: list[str] = []
    payload = request.get("payload") or {}
    whole = _text_of(request)

    for rule_id in ALL_RULE_IDS:
        if rule_id in whole:
            problems.append(f"house-rule id {rule_id} appears in the request")

    for path, node in _walk(payload):
        if not path:
            continue
        in_memory = path[: len(MEMORY_PATH)] == MEMORY_PATH
        banned = FORBIDDEN_KEYS_ANYWHERE if in_memory else (FORBIDDEN_KEYS_ANYWHERE | FORBIDDEN_KEYS_OUTSIDE_MEMORY)
        if path[-1] in banned:
            problems.append(f"forbidden key {'.'.join(path)}")
        if isinstance(node, str) and node.strip().lower() in TIER_WORDS:
            problems.append(f"tier word {node!r} as a value at {'.'.join(path)}")

    hidden = hidden_point_values()
    fragments = statement_fragments()
    for path, node in _walk(payload):
        if not isinstance(node, str) or _is_exempt(path):
            continue
        for rule_id, fragment in fragments.items():
            if fragment.lower() in node.lower():
                problems.append(f"house-rule statement ({rule_id}) at {'.'.join(path) or 'payload'}")
        for token in _NUMBER.findall(node):
            if token in hidden:
                problems.append(f"hidden point value {token!r} at {'.'.join(path) or 'payload'}")

    if golden:
        # The reflect step is handed this case's markup on purpose - rewriting the rule book from
        # the correction is the whole of that arm. Every other step must never see it.
        if request.get("step") != "reflect" and markup and markup.strip() and markup.strip() in whole:
            problems.append("the markup for this case appears in its own request")
        for key, label in (("tier", "tier"), ("fired_rule_ids", "fired rule ids")):
            value = golden.get(key)
            if value and _text_of(value) in whole:
                problems.append(f"golden {label} appears in the request")
        wanted = sorted(modifier_key(m) for m in (golden.get("modifiers") or []))
        if wanted and _text_of(wanted) in whole:
            problems.append("golden modifier keys appear in the request")
    return problems


def audit_request_file(path: Path | str, goldens: dict[str, dict] | None = None, markups: dict[str, str] | None = None) -> list[str]:
    request = json.loads(Path(path).read_text(encoding="utf-8"))
    case_id = request.get("case_id")
    golden = (goldens or {}).get(case_id)
    markup = (markups or {}).get(case_id)
    return [f"{Path(path).name}: {p}" for p in audit_payload(request, golden, markup)]


def audit_run(root: Path | str, goldens: dict[str, dict] | None = None, markups: dict[str, str] | None = None) -> list[str]:
    """Audit every request file under ``artifacts/uw/<run_id>/requests/``."""
    problems: list[str] = []
    requests_dir = Path(root) / "requests"
    for path in sorted(requests_dir.rglob("*.json")):
        problems.extend(audit_request_file(path, goldens, markups))
    return problems


def request_files(root: Path | str) -> list[Path]:
    return sorted((Path(root) / "requests").rglob("*.json"))
