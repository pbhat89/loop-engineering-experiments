"""Scoring one answer against the golden.

Headline metric: **rating distance in ladder steps**. Postpone sits off the ladder - if
exactly one of (agent, golden) postpones the distance is a fixed 2, and both postponing
is 0. Also scored per case: decision exact match, modifier F1 (flat extras and exclusion
riders, the band included) and driver recall.

An answer the runner could not parse after its re-request budget is scored at
:data:`POSTPONE_DISTANCE` and flagged, so a broken operator costs the arm the same as a
wrong-but-parseable postpone rather than silently disappearing from the mean.
"""
from __future__ import annotations

from src.underwriting.engine import modifier_key
from src.underwriting.tables import CLASS_ALIASES, DECISION_ALIASES, LADDER, LADDER_INDEX

POSTPONE_DISTANCE = 2
UNPARSEABLE_DISTANCE = 2

# Canonical driver -> the words an operator might use for it.
DRIVER_SYNONYMS: dict[str, tuple[str, ...]] = {
    "build": ("build", "bmi", "weight", "obesity", "body mass"),
    "blood pressure reading": ("blood pressure reading", "bp reading", "systolic", "diastolic", "reading"),
    "blood pressure treatment": ("blood pressure treatment", "bp treatment", "antihypertensive", "on treatment", "treated blood pressure", "bp medication"),
    "total cholesterol": ("total cholesterol", "cholesterol", "tc"),
    "lipid ratio": ("lipid ratio", "cholesterol ratio", "tc/hdl", "tc to hdl", "ratio"),
    "A1c": ("a1c", "hba1c", "glycaemic", "glycemic", "diabetes control"),
    "late-onset diabetes credit": ("diabetes credit", "late-onset credit", "late onset credit", "t2d credit"),
    "tobacco": ("tobacco", "smok", "nicotine", "cigarette"),
    "family history": ("family history", "familial", "father", "mother", "sibling"),
    "cardiac risk interaction": ("cardiac risk interaction", "cardiac interaction", "risk factor interaction", "combined cardiac", "multiple cardiac"),
    "occupation class": ("occupation", "occupational class", "job class"),
    "aviation": ("aviation", "pilot", "flying", "aircraft"),
    "scuba": ("scuba", "diving", "dive"),
    "climbing": ("climbing", "mountaineering"),
    "motorsport": ("motorsport", "racing", "motor racing"),
    "moving violations": ("moving violation", "mvr", "speeding", "driving record", "traffic violation"),
    "DUI": ("dui", "dwi", "impaired driving"),
    "liver enzymes": ("liver", "enzyme", "transaminase"),
    "alcohol history": ("alcohol",),
    "sleep apnea": ("sleep apnea", "sleep apnoea", "apnea", "apnoea", "cpap", "osa"),
    "face amount to income": ("face amount to income", "face to income", "income multiple", "financial", "face amount"),
}
# Longest synonyms first, so "blood pressure treatment" is not eaten by "reading" etc.
_SYNONYM_INDEX: tuple[tuple[str, str], ...] = tuple(
    sorted(
        ((syn, canon) for canon, syns in DRIVER_SYNONYMS.items() for syn in syns),
        key=lambda pair: -len(pair[0]),
    )
)


# --------------------------------------------------------------------------- normalisation


def normalise_decision(value: object) -> str | None:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    return DECISION_ALIASES.get(text) or DECISION_ALIASES.get(text.replace(" ", "_"))


def normalise_class(value: object) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().lower().split())
    if text in ("", "none", "null", "n/a", "postpone", "postponed"):
        return None
    return CLASS_ALIASES.get(text)


def normalise_driver(value: object) -> str:
    text = " ".join(str(value or "").strip().lower().split())
    if not text:
        return ""
    for canon in DRIVER_SYNONYMS:
        if text == canon.lower():
            return canon
    for synonym, canon in _SYNONYM_INDEX:
        if synonym in text:
            return canon
    return text


def normalise_modifier(modifier: object) -> str | None:
    """An operator modifier -> the same key shape the engine uses, or None if unreadable."""
    if not isinstance(modifier, dict):
        return None
    kind = str(modifier.get("type") or "").strip().lower().replace(" ", "_").replace("-", "_")
    detail = normalise_driver(modifier.get("detail"))
    if kind in ("exclusion", "exclusion_rider", "rider"):
        return f"exclusion|{detail}"
    if kind in ("flat_extra", "flatextra", "flat"):
        amount = modifier.get("amount_per_1000", modifier.get("amount"))
        if amount is None:
            amount = _amount_from_text(str(modifier.get("detail") or ""))
        try:
            return f"flat_extra|{float(amount):.2f}|{detail}"
        except (TypeError, ValueError):
            return f"flat_extra|?|{detail}"
    return None


def _amount_from_text(text: str) -> float | None:
    import re

    m = re.search(r"\$?\s*(\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None


# --------------------------------------------------------------------------- the metrics


def ladder_distance(
    agent_decision: object, agent_class: object, golden_decision: object, golden_class: object
) -> int:
    """Rating distance in ladder steps; postpone is off the ladder and costs a fixed 2."""
    a_dec = normalise_decision(agent_decision)
    g_dec = normalise_decision(golden_decision)
    a_post, g_post = a_dec == "postpone", g_dec == "postpone"
    if a_post and g_post:
        return 0
    if a_post or g_post:
        return POSTPONE_DISTANCE
    a_cls = normalise_class(agent_class)
    g_cls = normalise_class(golden_class)
    if g_cls is None:
        return 0 if a_cls is None else UNPARSEABLE_DISTANCE
    if a_cls is None:
        return UNPARSEABLE_DISTANCE
    return abs(LADDER_INDEX[a_cls] - LADDER_INDEX[g_cls])


def _prf(agent: set[str], golden: set[str]) -> dict:
    if not agent and not golden:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "matched": 0, "expected": 0, "given": 0}
    hit = len(agent & golden)
    precision = hit / len(agent) if agent else 0.0
    recall = hit / len(golden) if golden else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "matched": hit,
        "expected": len(golden),
        "given": len(agent),
    }


def modifier_scores(agent_modifiers: list | None, golden_modifiers: list | None) -> dict:
    agent = {k for k in (normalise_modifier(m) for m in (agent_modifiers or [])) if k}
    golden = {modifier_key(m) for m in (golden_modifiers or [])}
    return _prf(agent, golden)


def driver_scores(agent_drivers: list | None, golden_drivers: list | None) -> dict:
    agent = {d for d in (normalise_driver(d) for d in (agent_drivers or [])) if d}
    golden = {normalise_driver(d) for d in (golden_drivers or [])}
    return _prf(agent, golden)


def score_answer(answer: dict | None, golden: dict, *, unparseable: bool = False) -> dict:
    """Score one operator answer. ``unparseable`` records a response the runner gave up on."""
    if unparseable or not isinstance(answer, dict):
        return {
            "ladder_distance": UNPARSEABLE_DISTANCE,
            "decision_match": False,
            "agent_decision": None,
            "agent_rating_class": None,
            "modifier": _prf(set(), {modifier_key(m) for m in (golden.get("modifiers") or [])}),
            "driver": _prf(set(), {normalise_driver(d) for d in (golden.get("drivers") or [])}),
            "unparseable": True,
        }
    a_dec = normalise_decision(answer.get("decision"))
    a_cls = normalise_class(answer.get("rating_class"))
    return {
        "ladder_distance": ladder_distance(
            answer.get("decision"), answer.get("rating_class"), golden.get("decision"), golden.get("rating_class")
        ),
        "decision_match": a_dec == normalise_decision(golden.get("decision")),
        "agent_decision": a_dec,
        "agent_rating_class": a_cls,
        "modifier": modifier_scores(answer.get("modifiers"), golden.get("modifiers")),
        "driver": driver_scores(answer.get("drivers"), golden.get("drivers")),
        "unparseable": False,
    }


# --------------------------------------------------------------------------- series


def trailing_mean(values: list[float], window: int = 5) -> list[float]:
    """Trailing ``window``-case mean; the first cases use what is available so far."""
    out: list[float] = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1) : i + 1]
        out.append(round(sum(chunk) / len(chunk), 4))
    return out


def ladder_names() -> tuple[str, ...]:
    return LADDER
