"""The two rating engines and the derivation of a case's tier.

``rate(case, enabled)`` is the only rating code. With ``enabled`` empty it is
:func:`rate_manual_only` - what a careful reader of the starter manual alone produces.
With every rule enabled it is :func:`rate_house` - the golden.

A rule **triggers** when its predicate is true. A rule **fires** when switching it off
alone changes the scored answer (decision, rating class, modifiers, drivers). Firing,
not triggering, is what the tier is derived from::

    clean      no rule fires        manual-only answer == golden answer
    judgement  exactly one fires
    compound   two or three fire

Nothing here assigns a tier; :func:`derive` runs the engines and reads the result off.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.underwriting.house_rules import (
    ALL_RULE_IDS,
    RULES_BY_ID,
    cardiac_family_history,
    qualifying_family_events,
    weight_lost_lb,
)
from src.underwriting.tables import (
    A1C_BANDS,
    ALCOHOL_TREATMENT_DEBITS,
    AVIATION_DEFAULT_DEBITS,
    BP_TREATMENT_DEBITS,
    BUILD_BANDS,
    CLIMBING_DEBITS,
    DECLINE,
    DIASTOLIC_BANDS,
    DUI_DEBITS,
    FAMILY_HISTORY_DEBITS_CAP,
    FAMILY_HISTORY_DEBITS_PER_EVENT,
    HAZARDOUS_AVOCATIONS,
    LIPID_RATIO_BANDS,
    LIVER_ENZYME_DEBITS,
    MOTORSPORT_FLAT_EXTRA,
    MVR_VIOLATION_BANDS,
    NON_SMOKER_STATUSES,
    OCCUPATION_CLASS_DEBITS,
    PREFERRED_CRITERIA,
    PREFERRED_ORDER,
    SCUBA_DEPTH_BANDS,
    SLEEP_APNEA_DEBITS,
    SYSTOLIC_BANDS,
    TOBACCO_DEBITS,
    TOTAL_CHOLESTEROL_BANDS,
    band_value,
    bmi_from,
    class_for_debits,
)

ALL_RULES = frozenset(ALL_RULE_IDS)
NO_RULES: frozenset[str] = frozenset()

CARDIAC_INTERACTION_DEBITS = 25
LATE_ONSET_DIABETES_CREDIT = 25
FAMILY_HISTORY_SECOND_CANCER_DEBITS = 25
AVIATION_FLAT_EXTRA = 2.50
DEEP_SCUBA_FLAT_EXTRA = 5.00
CARDIAC_INTERACTION_MINIMUM_FACTORS = 3

TIER_CLEAN = "clean"
TIER_JUDGEMENT = "judgement"
TIER_COMPOUND = "compound"
TIER_WORDS: tuple[str, ...] = (TIER_CLEAN, TIER_JUDGEMENT, TIER_COMPOUND)


# --------------------------------------------------------------------------- result types


def modifier_key(modifier: dict) -> str:
    """Scoring key for one modifier - the band is part of the identity."""
    if modifier.get("type") == "flat_extra":
        return f"flat_extra|{float(modifier.get('amount_per_1000') or 0):.2f}|{modifier.get('detail')}"
    return f"exclusion|{modifier.get('detail')}"


@dataclass
class Answer:
    decision: str
    rating_class: str | None
    total_debits: int
    debits: dict[str, int] = field(default_factory=dict)
    modifiers: list[dict] = field(default_factory=list)
    drivers: list[str] = field(default_factory=list)
    postpone_reasons: list[str] = field(default_factory=list)
    triggered_rule_ids: list[str] = field(default_factory=list)

    def outcome(self) -> tuple:
        """The scored answer: what a rule has to change before it counts as having fired."""
        return (
            self.decision,
            self.rating_class,
            tuple(sorted(modifier_key(m) for m in self.modifiers)),
            tuple(sorted(self.drivers)),
        )

    def to_record(self) -> dict:
        return {
            "decision": self.decision,
            "rating_class": self.rating_class,
            "total_debits": self.total_debits,
            "debits": dict(self.debits),
            "modifiers": [dict(m) for m in self.modifiers],
            "drivers": list(self.drivers),
            "postpone_reasons": list(self.postpone_reasons),
        }


# --------------------------------------------------------------------------- small helpers


def _debits_or_decline(value) -> tuple[int, bool]:
    return (0, True) if value == DECLINE else (int(value or 0), False)


def effective_tobacco(case: dict) -> str:
    """Nicotine-positive lab overrides a declared non-smoker - the manual says so."""
    declared = str(case.get("tobacco_declared") or "never")
    if case.get("nicotine_lab") == "positive":
        return "current"
    return declared


def _triggers(rule_id: str, case: dict, ctx: dict) -> bool:
    return bool(RULES_BY_ID[rule_id].trigger(case, ctx))


def _on(rule_id: str, enabled: frozenset[str], case: dict, ctx: dict, triggered: list[str]) -> bool:
    """True when the rule is enabled for this run *and* its predicate holds (recording the trigger)."""
    fired = _triggers(rule_id, case, ctx)
    if fired and rule_id not in triggered:
        triggered.append(rule_id)
    return fired and rule_id in enabled


# --------------------------------------------------------------------------- the engine


def rate(case: dict, enabled: frozenset[str] = NO_RULES) -> Answer:
    """Rate ``case`` with the manual's tables plus the house rules in ``enabled``."""
    enabled = frozenset(enabled or ())
    ctx: dict = {}
    triggered: list[str] = []
    debits: dict[str, int] = {}
    drivers: list[str] = []
    modifiers: list[dict] = []
    postpone: list[str] = []
    hard_decline: list[str] = []

    # --- build (HR-09 adds half the recent weight loss back before the band is read) -----
    bmi = float(case["bmi"])
    if _on("HR-09", enabled, case, ctx, triggered):
        bmi = bmi_from(case["height_in"], float(case["weight_lb"]) + weight_lost_lb(case) / 2.0)
    ctx["bmi_used"] = bmi
    build_debits, build_declines = _debits_or_decline(band_value(BUILD_BANDS, bmi))
    if build_declines:
        hard_decline.append("build")
    if build_debits:
        debits["build"] = build_debits
        drivers.append("build")

    # --- blood pressure (HR-01 drops the reading charge when treated and controlled) -----
    sys_debits, sys_decline = _debits_or_decline(band_value(SYSTOLIC_BANDS, int(case["bp_systolic"])))
    dia_debits, dia_decline = _debits_or_decline(band_value(DIASTOLIC_BANDS, int(case["bp_diastolic"])))
    reading_debits = max(sys_debits, dia_debits)
    if sys_decline or dia_decline:
        hard_decline.append("blood pressure")
    if _on("HR-01", enabled, case, ctx, triggered):
        reading_debits = 0
    if reading_debits:
        debits["blood pressure reading"] = reading_debits
        drivers.append("blood pressure reading")
    if case.get("bp_treated"):
        debits["blood pressure treatment"] = BP_TREATMENT_DEBITS
        drivers.append("blood pressure treatment")
    ctx["bp_debits"] = reading_debits + (BP_TREATMENT_DEBITS if case.get("bp_treated") else 0)

    # --- lipids (HR-07: the ratio governs where the two bands disagree) ------------------
    tc_band = int(band_value(TOTAL_CHOLESTEROL_BANDS, int(case["total_cholesterol"])) or 0)
    ratio_band = int(band_value(LIPID_RATIO_BANDS, float(case["lipid_ratio"])) or 0)
    ctx["tc_band"], ctx["ratio_band"] = tc_band, ratio_band
    if _on("HR-07", enabled, case, ctx, triggered):
        lipid_debits = ratio_band
        lipid_drivers = ["lipid ratio"] if ratio_band else []
    else:
        lipid_debits = max(tc_band, ratio_band)
        lipid_drivers = []
        if lipid_debits:
            if tc_band >= ratio_band:
                lipid_drivers.append("total cholesterol")
            if ratio_band >= tc_band:
                lipid_drivers.append("lipid ratio")
    if lipid_debits:
        debits["lipids"] = lipid_debits
    drivers.extend(lipid_drivers)
    ctx["lipid_debits"] = lipid_debits

    # --- A1c ------------------------------------------------------------------------------
    a1c_debits, a1c_decline = _debits_or_decline(band_value(A1C_BANDS, float(case["a1c"])))
    if a1c_decline:
        hard_decline.append("A1c")
    if a1c_debits:
        debits["A1c"] = a1c_debits
        drivers.append("A1c")
    ctx["a1c_debits"] = a1c_debits

    # --- tobacco ---------------------------------------------------------------------------
    tobacco = effective_tobacco(case)
    ctx["tobacco"] = tobacco
    tobacco_debits = int(TOBACCO_DEBITS.get(tobacco, 0))
    if tobacco_debits:
        debits["tobacco"] = tobacco_debits
        drivers.append("tobacco")

    # --- family history (HR-03 lapse, HR-13 second same-site cancer) ------------------------
    events = qualifying_family_events(case)
    family_debits = min(len(events) * FAMILY_HISTORY_DEBITS_PER_EVENT, FAMILY_HISTORY_DEBITS_CAP)
    lapsed = _on("HR-03", enabled, case, ctx, triggered)
    second_cancer = _on("HR-13", enabled, case, ctx, triggered)
    if lapsed:
        family_debits = 0
    elif second_cancer:
        family_debits += FAMILY_HISTORY_SECOND_CANCER_DEBITS
    if family_debits:
        debits["family history"] = family_debits
        drivers.append("family history")
    ctx["family_debits"] = family_debits

    # --- occupation --------------------------------------------------------------------------
    occupation_debits = int(OCCUPATION_CLASS_DEBITS.get(str(case.get("occupation_class") or "A"), 0))
    if occupation_debits:
        debits["occupation class"] = occupation_debits
        drivers.append("occupation class")

    # --- avocation (HR-02 aviation flat extra, HR-14 deep scuba, HR-06 exclusion rider) -------
    av = case.get("avocation") or {}
    av_type = str(av.get("type") or "none")
    av_debits = 0
    av_modifier: dict | None = None
    if av_type == "aviation":
        if _on("HR-02", enabled, case, ctx, triggered):
            av_modifier = {"type": "flat_extra", "detail": "aviation", "amount_per_1000": AVIATION_FLAT_EXTRA}
        else:
            av_debits = AVIATION_DEFAULT_DEBITS
    elif av_type == "scuba":
        if _on("HR-14", enabled, case, ctx, triggered):
            av_modifier = {"type": "flat_extra", "detail": "scuba", "amount_per_1000": DEEP_SCUBA_FLAT_EXTRA}
        else:
            av_debits = int(band_value(SCUBA_DEPTH_BANDS, int(av.get("max_depth_ft", 0))) or 0)
    elif av_type == "climbing":
        av_debits = CLIMBING_DEBITS
    elif av_type == "motorsport":
        av_modifier = {"type": "flat_extra", "detail": "motorsport", "amount_per_1000": MOTORSPORT_FLAT_EXTRA}
    if av_type in HAZARDOUS_AVOCATIONS and _on("HR-06", enabled, case, ctx, triggered):
        av_debits = 0
        av_modifier = {"type": "exclusion", "detail": av_type, "amount_per_1000": None}
    if av_debits:
        debits[av_type] = av_debits
    if av_modifier is not None:
        modifiers.append(av_modifier)
    if av_type != "none" and (av_debits or av_modifier is not None):
        drivers.append(av_type)

    # --- driving record (HR-10 postpones a recent DUI instead of rating it) ---------------------
    violations = int(case.get("mvr_violations") or 0)
    mvr_debits = int(band_value(MVR_VIOLATION_BANDS, violations) or 0)
    if mvr_debits:
        debits["moving violations"] = mvr_debits
        drivers.append("moving violations")
    if case.get("dui_year") is not None:
        if _on("HR-10", enabled, case, ctx, triggered):
            postpone.append("recent DUI")
        else:
            debits["DUI"] = DUI_DEBITS
        drivers.append("DUI")

    # --- alcohol and liver (HR-12) ---------------------------------------------------------------
    if case.get("liver_enzymes") in ("elevated_under_2x", "elevated_over_2x"):
        if not _on("HR-12", enabled, case, ctx, triggered):
            debits["liver enzymes"] = LIVER_ENZYME_DEBITS
            drivers.append("liver enzymes")
    if case.get("alcohol_treatment"):
        debits["alcohol history"] = ALCOHOL_TREATMENT_DEBITS
        drivers.append("alcohol history")

    # --- sleep apnea (HR-11) ----------------------------------------------------------------------
    if case.get("sleep_apnea"):
        if not _on("HR-11", enabled, case, ctx, triggered):
            debits["sleep apnea"] = SLEEP_APNEA_DEBITS
            drivers.append("sleep apnea")

    # --- financial (HR-08) -------------------------------------------------------------------------
    if _on("HR-08", enabled, case, ctx, triggered):
        postpone.append("financial justification")
        drivers.append("face amount to income")

    # --- cardiac interaction (HR-04), read off the house-adjusted component values -----------------
    factors = [
        ctx["bp_debits"] > 0,
        ctx["lipid_debits"] > 0,
        ctx["a1c_debits"] > 0,
        ctx["bmi_used"] >= 31.0,
        ctx["tobacco"] == "current",
        cardiac_family_history(case) and ctx["family_debits"] > 0,
    ]
    ctx["cardiac_factor_count"] = sum(1 for f in factors if f)
    if _on("HR-04", enabled, case, ctx, triggered):
        debits["cardiac risk interaction"] = CARDIAC_INTERACTION_DEBITS
        drivers.append("cardiac risk interaction")

    # --- late-onset diabetes credit (HR-05) ----------------------------------------------------------
    credit = 0
    if _on("HR-05", enabled, case, ctx, triggered):
        credit = LATE_ONSET_DIABETES_CREDIT
        debits["late-onset diabetes credit"] = -credit
        drivers.append("late-onset diabetes credit")

    total = max(sum(v for v in debits.values()), 0)

    # --- decision and class -----------------------------------------------------------------------------
    if hard_decline:
        decision, rating_class = "decline", "Decline"
    elif postpone:
        decision, rating_class = "postpone", None
    elif total >= 250:
        decision, rating_class = "decline", "Decline"
    else:
        rating_class = class_for_debits(total)
        if total == 0:
            rating_class = _preferred_class(case, ctx) or rating_class
        decision = "accept_with_modification" if modifiers else "accept"

    return Answer(
        decision=decision,
        rating_class=rating_class,
        total_debits=total,
        debits=debits,
        modifiers=modifiers,
        drivers=list(dict.fromkeys(drivers)),
        postpone_reasons=postpone,
        triggered_rule_ids=sorted(triggered),
    )


def _preferred_class(case: dict, ctx: dict) -> str | None:
    """Best preferred tier the file qualifies for, or None (then it is Standard)."""
    for tier in PREFERRED_ORDER:
        if _meets(case, ctx, PREFERRED_CRITERIA[tier]):
            return tier
    return None


def _meets(case: dict, ctx: dict, criteria: dict) -> bool:
    from src.underwriting.house_rules import CURRENT_YEAR

    if float(ctx.get("bmi_used", case["bmi"])) > float(criteria["bmi_max"]):
        return False
    if float(ctx.get("bmi_used", case["bmi"])) < 19.0:
        return False
    if int(case["bp_systolic"]) > int(criteria["systolic_max"]) or int(case["bp_diastolic"]) > int(criteria["diastolic_max"]):
        return False
    if case.get("bp_treated"):
        return False
    if int(case["total_cholesterol"]) > int(criteria["total_cholesterol_max"]):
        return False
    if float(case["lipid_ratio"]) > float(criteria["ratio_max"]):
        return False
    if float(case["a1c"]) > float(criteria["a1c_max"]) or case.get("diabetes_dx_year") is not None:
        return False
    if ctx.get("tobacco", effective_tobacco(case)) not in criteria["tobacco_allowed"]:
        return False
    if int(case.get("mvr_violations") or 0) > int(criteria["violations_max"]):
        return False
    dui_year = case.get("dui_year")
    if dui_year is not None:
        window = criteria["dui_within_years"]
        if window is None or (CURRENT_YEAR - int(dui_year)) <= int(window):
            return False
    if str(case.get("occupation_class") or "A") not in criteria["occupation_classes"]:
        return False
    if not criteria["avocation_allowed"] and str((case.get("avocation") or {}).get("type") or "none") != "none":
        return False
    if len(qualifying_family_events(case)) > int(criteria["family_history_events_max"]):
        return False
    if case.get("sleep_apnea") or case.get("alcohol_treatment"):
        return False
    if case.get("liver_enzymes") != "normal":
        return False
    return True


# --------------------------------------------------------------------------- the two named engines


def rate_manual_only(case: dict) -> Answer:
    """What a careful reader of the starter manual alone produces."""
    return rate(case, NO_RULES)


def rate_house(case: dict, scope: frozenset[str] | None = None) -> Answer:
    """The golden: the manual plus every house rule (or a restricted ``scope``)."""
    return rate(case, ALL_RULES if scope is None else frozenset(scope))


# --------------------------------------------------------------------------- tier derivation


def fired_rule_ids(case: dict, scope: frozenset[str] | None = None) -> list[str]:
    """Rules that change the scored answer when switched off alone. Derived, never assigned."""
    active = ALL_RULES if scope is None else frozenset(scope)
    house = rate(case, active)
    baseline = house.outcome()
    return [rid for rid in sorted(active) if rate(case, active - {rid}).outcome() != baseline]


def tier_for(fired: list[str] | tuple[str, ...]) -> str | None:
    n = len(fired)
    if n == 0:
        return TIER_CLEAN
    if n == 1:
        return TIER_JUDGEMENT
    if n in (2, 3):
        return TIER_COMPOUND
    return None  # four or more rules is outside the design's tier vocabulary


def derive(case: dict) -> dict:
    """Run both engines and read the tier, the fired rules and the golden off the result."""
    manual = rate_manual_only(case)
    house = rate_house(case)
    fired = fired_rule_ids(case)
    tier = tier_for(fired)
    return {
        "manual_only": manual,
        "golden": house,
        "fired_rule_ids": fired,
        "tier": tier,
        "consistent": bool(fired) or manual.outcome() == house.outcome(),
    }


def rule_relevance(case: dict) -> set[str]:
    """Rule ids whose predicate holds for this case - what the ask-a-senior oracle calls relevant."""
    return set(rate_house(case).triggered_rule_ids)
