"""The fourteen house rules - the unwritten practice the apprentice has to learn.

**Never shown to an operator.** The starter manual says where each gap is ("for
combinations of cardiac risk factors, refer to underwriting judgement") and never what
fills it. A request-payload leakage audit (:mod:`src.underwriting.audit`) runs over every
request file the runner writes and fails if a rule id, a rule statement or a
hidden-only point value reaches the operator outside the ask-a-senior answers.

Each rule carries four things:

``trigger(case, ctx)``
    Pure predicate over the case fields (``ctx`` holds the component debits computed so
    far, which is what rule ``HR-04`` needs). A rule *triggers* here; whether it *fires*
    - whether it changes the answer - is derived in :mod:`src.underwriting.engine` by
    leave-one-out, never asserted by hand.
``statement``
    What a senior would say out loud, numbers included. Returned by the ask-a-senior
    oracle and by nothing else.
``markup_sentence``
    What the reviewer's markup says. No digits at all, so a markup teaches the rule
    without handing over the arithmetic.
``oracle_keywords``
    Groups of alternatives; every group must appear in a question before the oracle will
    quote the statement, and the rule must also be relevant to the case in hand.

Rules 1-8 are from the approved design, 9-12 are the lead's additions in the same
spirit, and 13-14 appear only in held-out cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.underwriting.tables import (
    FAMILY_HISTORY_AGE_LIMIT,
    HAZARDOUS_AVOCATIONS,
)

CURRENT_YEAR = 2026  # the frozen "today" of the case file; keeps dx age and DUI recency deterministic

TRAINING_RULE_IDS: tuple[str, ...] = tuple(f"HR-{i:02d}" for i in range(1, 13))
HELDOUT_ONLY_RULE_IDS: tuple[str, ...] = ("HR-13", "HR-14")
ALL_RULE_IDS: tuple[str, ...] = TRAINING_RULE_IDS + HELDOUT_ONLY_RULE_IDS


@dataclass(frozen=True)
class HouseRule:
    rule_id: str
    title: str
    area: str
    trigger: Callable[[dict, dict], bool]
    statement: str
    markup_sentence: str
    oracle_keywords: tuple[tuple[str, ...], ...]
    scope: str = "training"  # training | heldout
    effect: str = ""  # one word for the logs: debits | decision | modifier
    notes: str = ""

    def matches_question(self, question: str) -> bool:
        q = (question or "").lower()
        return all(any(alt in q for alt in group) for group in self.oracle_keywords) and bool(self.oracle_keywords)

    def to_record(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "area": self.area,
            "scope": self.scope,
            "effect": self.effect,
            "statement": self.statement,
            "markup_sentence": self.markup_sentence,
            "oracle_keywords": [list(group) for group in self.oracle_keywords],
            "notes": self.notes,
        }


# --------------------------------------------------------------------------- field helpers


def qualifying_family_events(case: dict) -> list[dict]:
    """Parent/sibling events before the manual's qualifying age - what the manual charges for."""
    return [
        e
        for e in (case.get("family_history") or [])
        if int(e.get("age", 999)) < FAMILY_HISTORY_AGE_LIMIT
    ]


def cardiac_family_history(case: dict) -> bool:
    return any(e.get("condition") in ("MI", "stroke") for e in qualifying_family_events(case))


def age_at_diagnosis(case: dict) -> int | None:
    year = case.get("diabetes_dx_year")
    return None if year is None else int(case["age"]) - (CURRENT_YEAR - int(year))


def years_since_dui(case: dict) -> int | None:
    year = case.get("dui_year")
    return None if year is None else CURRENT_YEAR - int(year)


def avocation_type(case: dict) -> str:
    return str((case.get("avocation") or {}).get("type") or "none")


def weight_lost_lb(case: dict) -> float:
    change = float(case.get("weight_change_lb_12mo") or 0.0)
    return -change if change < 0 else 0.0


# --------------------------------------------------------------------------- triggers


def _t01(case: dict, ctx: dict) -> bool:
    return bool(case.get("bp_treated")) and int(case["bp_systolic"]) <= 145 and int(case["bp_diastolic"]) <= 90


def _t02(case: dict, ctx: dict) -> bool:
    av = case.get("avocation") or {}
    return av.get("type") == "aviation" and int(av.get("hours_per_year", 0)) < 100


def _t03(case: dict, ctx: dict) -> bool:
    return int(case["age"]) > 60 and bool(qualifying_family_events(case))


def _t04(case: dict, ctx: dict) -> bool:
    return int(ctx.get("cardiac_factor_count", 0)) >= 3


def _t05(case: dict, ctx: dict) -> bool:
    dx_age = age_at_diagnosis(case)
    return dx_age is not None and dx_age > 45 and float(case["a1c"]) < 7.0


def _t06(case: dict, ctx: dict) -> bool:
    return case.get("occupation_class") == "C" and avocation_type(case) in HAZARDOUS_AVOCATIONS


def _t07(case: dict, ctx: dict) -> bool:
    return int(ctx.get("tc_band", 0)) != int(ctx.get("ratio_band", 0))


def _t08(case: dict, ctx: dict) -> bool:
    income = float(case.get("annual_income") or 0)
    face = float(case.get("face_amount") or 0)
    return face > 1_000_000 and income > 0 and face > 20 * income


def _t09(case: dict, ctx: dict) -> bool:
    return weight_lost_lb(case) > 0


def _t10(case: dict, ctx: dict) -> bool:
    since = years_since_dui(case)
    return since is not None and since < 3


def _t11(case: dict, ctx: dict) -> bool:
    return bool(case.get("sleep_apnea")) and bool(case.get("cpap_compliant"))


def _t12(case: dict, ctx: dict) -> bool:
    return case.get("liver_enzymes") == "elevated_under_2x" and not case.get("alcohol_treatment")


def _t13(case: dict, ctx: dict) -> bool:
    sites: dict[str, int] = {}
    for e in qualifying_family_events(case):
        if e.get("condition") == "cancer" and e.get("site"):
            sites[str(e["site"])] = sites.get(str(e["site"]), 0) + 1
    return any(n >= 2 for n in sites.values())


def _t14(case: dict, ctx: dict) -> bool:
    av = case.get("avocation") or {}
    if av.get("type") != "scuba":
        return False
    return int(av.get("max_depth_ft", 0)) > 100 or bool(av.get("cave_wreck"))


# --------------------------------------------------------------------------- the rules


HOUSE_RULES: tuple[HouseRule, ...] = (
    HouseRule(
        rule_id="HR-01",
        title="Treated, controlled blood pressure charges the treatment band only",
        area="blood pressure",
        effect="debits",
        trigger=_t01,
        statement=(
            "Where blood pressure is treated and the current reading is at or below 145/90, charge the "
            "treatment debit of 25 only. Do not add the reading band on top."
        ),
        markup_sentence=(
            "Blood pressure that is treated and controlled carries the treatment charge only; the reading "
            "is not charged on top."
        ),
        oracle_keywords=(("blood pressure", "bp", "hypertension"), ("treat", "medicat", "controll")),
    ),
    HouseRule(
        rule_id="HR-02",
        title="Private aviation under a hundred hours a year is a flat extra, never a rating",
        area="avocation",
        effect="modifier",
        trigger=_t02,
        statement=(
            "A private pilot flying fewer than 100 hours a year takes a flat extra of $2.50 per $1,000 and "
            "no rating debits. Private aviation at that level is never declined."
        ),
        markup_sentence=(
            "Private aviation at a modest number of hours a year takes a flat extra rather than rating "
            "debits, and is never declined for the flying alone."
        ),
        oracle_keywords=(("pilot", "aviation", "flying", "aircraft"),),
    ),
    HouseRule(
        rule_id="HR-03",
        title="Family-history debits lapse once the applicant is older than the qualifying age",
        area="family history",
        effect="debits",
        trigger=_t03,
        statement="Family-history debits are dropped entirely once the applicant is over 60.",
        markup_sentence=(
            "Family-history debits are dropped once the applicant is older than the family-history "
            "qualifying age."
        ),
        oracle_keywords=(
            ("family history", "familial", "father", "mother", "sibling", "parent", "family"),
            ("age", "older", "over", "lapse", "expire", "drop", "still"),
        ),
    ),
    HouseRule(
        rule_id="HR-04",
        title="Three or more cardiac risk factors together carry an interaction charge",
        area="cardiac",
        effect="debits",
        trigger=_t04,
        statement=(
            "When three or more of these appear together - a blood pressure debit, a lipid debit, an A1c "
            "debit, BMI of 31 or above, current tobacco use, or a charged family history of cardiac disease "
            "- add a further 25 debits as an interaction charge."
        ),
        markup_sentence=(
            "Several cardiac risk factors appearing together carry an interaction charge on top of the "
            "individual debits."
        ),
        oracle_keywords=(("cardiac", "heart", "risk factor", "combination", "combine", "interact", "together"),),
    ),
    HouseRule(
        rule_id="HR-05",
        title="Late-onset type 2 diabetes with a controlled A1c earns a credit",
        area="diabetes",
        effect="debits",
        trigger=_t05,
        statement=(
            "Type 2 diabetes first diagnosed after age 45 with an A1c below 7.0 earns a credit of 25 debits, "
            "floored at zero."
        ),
        markup_sentence=(
            "Adult-onset diabetes first diagnosed in later middle age, with the A1c well controlled, earns "
            "a credit against the debits."
        ),
        oracle_keywords=(("diabet", "a1c", "t2d"), ("diagnos", "onset", "late", "credit", "age", "allowance")),
    ),
    HouseRule(
        rule_id="HR-06",
        title="Hazardous occupation plus hazardous avocation takes an exclusion rider",
        area="avocation",
        effect="modifier",
        trigger=_t06,
        statement=(
            "An occupation in class C combined with a hazardous avocation takes an exclusion rider for the "
            "avocation rather than a flat extra or avocation debits."
        ),
        markup_sentence=(
            "A hazardous occupation combined with a hazardous avocation takes an exclusion rider for the "
            "avocation, not a flat extra and not debits."
        ),
        oracle_keywords=(
            ("occupation", "class c", "hazardous", "job", "work"),
            ("avocation", "exclusion", "rider", "hobby", "sport", "pastime"),
        ),
    ),
    HouseRule(
        rule_id="HR-07",
        title="Where cholesterol and the ratio disagree, the ratio governs",
        area="lipids",
        effect="debits",
        trigger=_t07,
        statement=(
            "Where the total cholesterol band and the ratio band disagree, the ratio governs. Charge the "
            "ratio band only."
        ),
        markup_sentence=(
            "Where the total cholesterol band and the ratio band disagree, the ratio governs; the "
            "cholesterol band is not charged."
        ),
        oracle_keywords=(
            ("cholesterol", "lipid", "ratio", "hdl"),
            ("disagree", "conflict", "which", "govern", "both", "differ", "apply"),
        ),
    ),
    HouseRule(
        rule_id="HR-08",
        title="A large face amount at a high multiple of income is postponed",
        area="financial",
        effect="decision",
        trigger=_t08,
        statement=(
            "A face amount above $1,000,000 at more than 20 times income is postponed for financial "
            "evidence, not rated."
        ),
        markup_sentence=(
            "A large face amount at a high multiple of income is postponed for financial evidence rather "
            "than rated."
        ),
        oracle_keywords=(
            ("face amount", "face", "income", "financial", "coverage"),
            ("postpone", "refer", "multiple", "large", "limit", "times", "justif"),
        ),
    ),
    HouseRule(
        rule_id="HR-09",
        title="Recent weight loss is added back at half before the build band is read",
        area="build",
        effect="debits",
        trigger=_t09,
        statement="Weight lost in the past 12 months is added back at half before the build band is read.",
        markup_sentence="Weight lost in the past year is added back at half before the build band is read.",
        oracle_keywords=(("weight", "build", "bmi"), ("lost", "loss", "lose", "gain", "change", "reduc", "dropped")),
    ),
    HouseRule(
        rule_id="HR-10",
        title="A recent DUI is a postpone, not a rating",
        area="driving",
        effect="decision",
        trigger=_t10,
        statement="A DUI within the last 3 years is a postpone, not a rating.",
        markup_sentence="A recent DUI is postponed, not rated.",
        oracle_keywords=(("dui", "dwi", "impaired driving", "drink driving", "drunk"),),
    ),
    HouseRule(
        rule_id="HR-11",
        title="Sleep apnea on documented CPAP compliance carries no debit",
        area="sleep apnea",
        effect="debits",
        trigger=_t11,
        statement="Where CPAP compliance is documented, sleep apnea carries no debit at all - the 50 does not apply.",
        markup_sentence="Sleep apnea with documented CPAP compliance carries no debit.",
        oracle_keywords=(("sleep apnea", "apnoea", "apnea", "cpap"),),
    ),
    HouseRule(
        rule_id="HR-12",
        title="Mildly elevated liver enzymes with no alcohol history carry no debit",
        area="liver",
        effect="debits",
        trigger=_t12,
        statement=(
            "Elevated liver enzymes below twice the upper limit of normal, with no alcohol history, carry "
            "no debit."
        ),
        markup_sentence="Mildly elevated liver enzymes with no alcohol history carry no debit.",
        oracle_keywords=(("liver", "enzyme", "alt", "ast", "ggt", "transaminase"),),
    ),
    HouseRule(
        rule_id="HR-13",
        title="Two relatives with the same cancer break the family-history cap",
        area="family history",
        effect="debits",
        scope="heldout",
        trigger=_t13,
        statement=(
            "Two first-degree relatives with the same cancer before 60 add a further 25 debits on top of "
            "the family-history cap."
        ),
        markup_sentence=(
            "Where two first-degree relatives have had the same cancer young, the family-history cap does "
            "not hold and a further charge applies."
        ),
        oracle_keywords=(("cancer",), ("two", "both", "second", "relatives", "cap", "same", "multiple")),
    ),
    HouseRule(
        rule_id="HR-14",
        title="Deep or overhead-environment scuba takes a flat extra",
        area="avocation",
        effect="modifier",
        scope="heldout",
        trigger=_t14,
        statement=(
            "Scuba to a depth greater than 100 feet, or any cave or wreck penetration, takes a flat extra "
            "of $5.00 per $1,000 regardless of the number of dives, and no scuba depth debit."
        ),
        markup_sentence=(
            "Scuba beyond recreational depth, or any cave or wreck penetration, takes a flat extra "
            "regardless of how often the applicant dives."
        ),
        oracle_keywords=(("scuba", "dive", "diving"), ("depth", "deep", "feet", "cave", "wreck", "penetration")),
    ),
)

RULES_BY_ID: dict[str, HouseRule] = {r.rule_id: r for r in HOUSE_RULES}


def house_rules_records() -> list[dict]:
    return [r.to_record() for r in HOUSE_RULES]


# --------------------------------------------------------------------------- manual topics for the oracle

# Topics a question may hit that the manual already answers. The oracle returns the manual
# section verbatim - the question was wasted, which is the point of the ask-a-senior arm.
MANUAL_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Decision vocabulary": ("decision", "vocabulary", "accept", "decline", "postpone", "what decisions"),
    "Rating classes and the debit bands": ("debit band", "rating class", "which class", "class band", "table 2", "how many debits"),
    "Preferred eligibility": ("preferred", "pref plus", "std+", "standard plus", "best class"),
    "Build": ("bmi", "build", "height", "weight"),
    "Blood pressure": ("blood pressure", "bp", "systolic", "diastolic", "hypertension"),
    "Lipids": ("cholesterol", "lipid", "hdl", "ratio"),
    "Diabetes and A1c": ("a1c", "diabet", "glucose"),
    "Tobacco": ("tobacco", "smok", "nicotine", "cigarette", "vape"),
    "Family history": ("family history", "father", "mother", "sibling", "parent"),
    "Occupation": ("occupation", "class a", "class b", "class c", "job"),
    "Avocations": ("avocation", "aviation", "pilot", "scuba", "dive", "climb", "motorsport", "racing", "hobby"),
    "Driving record": ("mvr", "driving", "violation", "speeding", "dui", "licence", "license"),
    "Alcohol and liver": ("liver", "enzyme", "alcohol", "drink"),
    "Sleep apnea": ("apnea", "apnoea", "cpap"),
    "Financial underwriting": ("income", "face amount", "financial", "in force", "inforce", "multiple"),
    "Modifiers": ("flat extra", "exclusion", "rider", "modifier"),
}

ORACLE_FALLBACK = "Not something I can answer from here; use the manual."
