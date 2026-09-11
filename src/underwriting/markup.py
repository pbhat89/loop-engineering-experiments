"""The reviewer's markup: what a senior writes on the file after the apprentice has rated it.

Templated from the golden and the rules that fired. It names the correct decision, class
and modifiers, the material factors, and the practice behind each rule that fired - and
**never a threshold and never a point value**. The only digits it may contain are the
case id and the rating-class names ("Table 2"); a test asserts exactly that over every
markup the generator can produce.

This is the whole of what the notebook and written-rules arms carry forward, so the
constraint is not cosmetic: it is what keeps the house rules learnable without being
copyable.
"""
from __future__ import annotations

import re

from src.underwriting.house_rules import RULES_BY_ID
from src.underwriting.tables import FLAT_EXTRA_BAND_WORDS, LADDER, LADDER_INDEX

DECISION_WORDS = {
    "accept": "accept",
    "accept_with_modification": "accept with modification",
    "postpone": "postpone",
    "decline": "decline",
}
STEP_WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight")

# What a markup is allowed to contain digits for: the case id, the rating-class names
# ("Table 2"), and the lab name "A1c" - which names a test, not a threshold or a value.
ALLOWED_DIGIT_PATTERNS = (r"UW-[TH]\d{2}", r"A1c") + tuple(
    re.escape(name) for name in LADDER if any(ch.isdigit() for ch in name)
)


def _join(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def modifier_words(modifier: dict) -> str:
    if modifier.get("type") == "exclusion":
        return f"an exclusion rider for the {modifier.get('detail')}"
    band = FLAT_EXTRA_BAND_WORDS.get(float(modifier.get("amount_per_1000") or 0), "a flat-extra band")
    return f"a flat extra at {band} for the {modifier.get('detail')}"


def answer_in_words(golden: dict) -> str:
    decision = DECISION_WORDS.get(str(golden.get("decision")), str(golden.get("decision")))
    if golden.get("decision") == "postpone":
        text = "the file should have been postponed"
    elif golden.get("decision") == "decline":
        text = "the file should have been declined"
    else:
        text = f"the decision is {decision} at {golden.get('rating_class')}"
    mods = [modifier_words(m) for m in (golden.get("modifiers") or [])]
    if mods:
        text += f", with {_join(mods)}"
    return text


def direction_phrase(agent: dict | None, golden: dict) -> str:
    """Direction and size of the miss, in words - never a number."""
    a_decision = (agent or {}).get("decision")
    g_decision = golden.get("decision")
    a_post, g_post = a_decision == "postpone", g_decision == "postpone"
    if g_post and not a_post:
        return "This one needed postponing rather than rating."
    if a_post and not g_post:
        return "This one did not need postponing; it rates on the evidence to hand."
    a_class, g_class = (agent or {}).get("rating_class"), golden.get("rating_class")
    if a_class not in LADDER_INDEX or g_class not in LADDER_INDEX:
        return "The rating class you returned could not be read against the ladder."
    delta = LADDER_INDEX[a_class] - LADDER_INDEX[g_class]
    if delta == 0:
        return "The rating class was right."
    word = STEP_WORDS[min(abs(delta), len(STEP_WORDS) - 1)]
    step = "step" if abs(delta) == 1 else "steps"
    return f"The rating was {word} {step} too {'severe' if delta > 0 else 'lenient'}."


def _misread_factor(agent: dict | None, golden: dict) -> str:
    agent_drivers = {str(d).strip().lower() for d in ((agent or {}).get("drivers") or [])}
    golden_drivers = [str(d) for d in (golden.get("drivers") or [])]
    missed = [d for d in golden_drivers if d.lower() not in agent_drivers]
    if missed:
        return missed[0]
    if golden_drivers:
        return golden_drivers[0]
    return "preferred-eligibility"


def build_markup(golden: dict, agent: dict | None, scores: dict) -> str:
    """The markup shown after one training case. Correct answers get a one-line confirmation."""
    case_id = golden.get("case_id", "")
    drivers = _join([str(d) for d in (golden.get("drivers") or [])])
    correct = bool(scores.get("decision_match")) and int(scores.get("ladder_distance", 99)) == 0

    if correct:
        return f"{case_id}: correct. The material factors were {drivers}."

    lines = [f"{case_id}: {direction_phrase(agent, golden)}"]
    lines.append(f"On review {answer_in_words(golden)}.")
    lines.append(f"The material factors are {drivers}.")

    fired = [rid for rid in (golden.get("fired_rule_ids") or []) if rid in RULES_BY_ID]
    if fired:
        lines.extend(RULES_BY_ID[rid].markup_sentence for rid in fired)
    else:
        lines.append(f"The manual covers this case; the {_misread_factor(agent, golden)} band was misread.")
    return " ".join(lines)


# --------------------------------------------------------------------------- the digit rule


def forbidden_digits(text: str) -> list[str]:
    """Digit runs in ``text`` that are neither a case id nor part of a rating-class name."""
    stripped = text
    for pattern in ALLOWED_DIGIT_PATTERNS:
        stripped = re.sub(pattern, " ", stripped)
    return re.findall(r"\d+", stripped)
