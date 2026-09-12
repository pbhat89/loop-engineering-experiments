"""The seeded case generator and the frozen case file.

Thirty training applications and eight held-out ones, drawn from one seeded RNG
(``seed 42``). Roughly sixteen structured fields each, about 150 words when rendered,
and one detail per case that does not matter.

**Tiers are derived, never assigned.** The generator proposes a case by injecting the
attributes a target rule needs, then runs *both* engines and reads the tier and the
fired-rule list off the result (:func:`src.underwriting.engine.derive`). A proposal
whose derived fired set is not exactly the target is thrown away and redrawn. The
targets below are therefore a search objective, not a label.

The training schedule (section 5 of the build brief) asks for 9 clean / 14 judgement /
7 compound *and* every rule firing in at least three training cases in at least two
shapes. Those two are arithmetically incompatible: twelve rules at three firings needs
36 firings, and 14 judgement cases (one firing each) plus 7 compound cases (at most
three each) supply at most 35. The mix is therefore **9 clean / 13 judgement / 8
compound** - one case moved from judgement to compound, the smallest change that makes
the set satisfiable - and every other constraint in section 5 is met as written. See
decision D-01.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from src.underwriting.engine import derive, rate_house, rate_manual_only
from src.underwriting.house_rules import CURRENT_YEAR
from src.underwriting.tables import OCCUPATION_EXAMPLES, bmi_from

SEED = 42
TRAINING_CASES = 30
HELDOUT_CASES = 8

# --------------------------------------------------------------------------- the schedule

TRAINING_CLEAN_COUNT = 9
TRAINING_JUDGEMENT_TARGETS: tuple[frozenset[str], ...] = tuple(
    frozenset({rid}) for rid in (
        "HR-01", "HR-02", "HR-03", "HR-04", "HR-05", "HR-06",
        "HR-07", "HR-08", "HR-09", "HR-10", "HR-11", "HR-12", "HR-04",
    )
)
TRAINING_COMPOUND_TARGETS: tuple[frozenset[str], ...] = (
    frozenset({"HR-08", "HR-01", "HR-12"}),
    frozenset({"HR-08", "HR-03", "HR-11"}),
    frozenset({"HR-10", "HR-02", "HR-04"}),
    frozenset({"HR-10", "HR-07", "HR-06"}),
    frozenset({"HR-01", "HR-05", "HR-09"}),
    frozenset({"HR-02", "HR-05", "HR-09"}),
    frozenset({"HR-03", "HR-04", "HR-07"}),
    frozenset({"HR-06", "HR-11", "HR-12"}),
)

HELDOUT_CLEAN_COUNT = 2
HELDOUT_JUDGEMENT_TARGETS: tuple[frozenset[str], ...] = (
    frozenset({"HR-13"}),
    frozenset({"HR-14"}),
    frozenset({"HR-07"}),
    frozenset({"HR-10"}),
)
HELDOUT_COMPOUND_TARGETS: tuple[frozenset[str], ...] = (
    frozenset({"HR-01", "HR-04", "HR-07"}),
    frozenset({"HR-06", "HR-09", "HR-11"}),
)

# Window mix (every 10 consecutive training cases)
WINDOW = 10
WINDOW_CLEAN = (2, 4)
WINDOW_JUDGEMENT = (4, 5)
WINDOW_COMPOUND = (2, 3)

MAX_DRAWS_PER_SLOT = 4000
CANDIDATE_POOL = 120       # matching candidates to look at before choosing one
CANDIDATE_QUANTILE = 0.80  # where in the naive-error distribution the kept candidate sits

PRODUCTS: tuple[str, ...] = ("10-year term", "20-year term", "30-year term", "whole life")
FACE_AMOUNTS: tuple[int, ...] = (250_000, 400_000, 500_000, 750_000, 1_000_000)
IRRELEVANT_DETAILS: tuple[str, ...] = (
    "keeps tropical fish",
    "plays in a pub quiz league",
    "restores vintage radios",
    "sings in a community choir",
    "collects first-edition crime novels",
    "volunteers at a food bank on Saturdays",
    "has run the same book club for nine years",
    "grows chillies on a balcony",
    "is learning classical guitar",
    "keeps bees at an allotment",
    "coaches a junior chess club",
    "bakes sourdough every weekend",
    "is a season-ticket holder at the local rugby club",
    "has a long-haired cat named after a composer",
    "walks a neighbour's greyhound each morning",
    "makes stained glass in a garage workshop",
)
CANCER_SITES: tuple[str, ...] = ("breast", "colon", "lung", "pancreas", "prostate")


# --------------------------------------------------------------------------- base draw


def _weight_for(height_in: int, target_bmi: float) -> int:
    return int(round(target_bmi * height_in * height_in / 703.0))


def set_build(case: dict, height_in: int, target_bmi: float) -> None:
    case["height_in"] = int(height_in)
    case["weight_lb"] = _weight_for(height_in, target_bmi)
    case["bmi"] = bmi_from(case["height_in"], case["weight_lb"])


def draw_base_case(rng: random.Random) -> dict:
    """A plausible applicant before any rule is suppressed or injected."""
    sex = rng.choice(("M", "F"))
    age = rng.randint(29, 58)
    height_in = rng.randint(62, 75) if sex == "M" else rng.randint(60, 70)
    case: dict = {
        "sex": sex,
        "age": age,
        "product": rng.choice(PRODUCTS),
        "face_amount": rng.choice(FACE_AMOUNTS),
        "weight_change_lb_12mo": 0,
        "tobacco_declared": rng.choices(("never", "quit_over_5y", "quit_1_5y"), weights=(0.7, 0.2, 0.1))[0],
        "nicotine_lab": "negative",
        "bp_systolic": rng.randint(108, 136),
        "bp_diastolic": rng.randint(66, 86),
        "bp_treated": False,
        "bp_treatment_since": None,
        "total_cholesterol": rng.randint(165, 235),
        "hdl": rng.randint(42, 68),
        "a1c": round(rng.uniform(4.9, 6.2), 1),
        "diabetes_dx_year": None,
        "diabetes_medication": None,
        "family_history": [],
        "occupation_class": "A",
        "occupation": rng.choice(OCCUPATION_EXAMPLES["A"]),
        "avocation": {"type": "none"},
        "mvr_violations": rng.choices((0, 1), weights=(0.75, 0.25))[0],
        "dui_year": None,
        "liver_enzymes": "normal",
        "alcohol_treatment": False,
        "sleep_apnea": False,
        "cpap_compliant": False,
        "annual_income": rng.choice((85_000, 110_000, 140_000, 175_000, 210_000, 260_000)),
        "inforce_coverage": rng.choice((0, 100_000, 150_000, 250_000, 400_000)),
        "irrelevant_detail": rng.choice(IRRELEVANT_DETAILS),
    }
    set_build(case, height_in, round(rng.uniform(21.0, 27.0), 1))
    _reconcile_lipids(case)
    return case


def _reconcile_lipids(case: dict) -> None:
    case["lipid_ratio"] = round(float(case["total_cholesterol"]) / float(case["hdl"]), 1)


def set_lipids(case: dict, total_cholesterol: int, ratio: float) -> None:
    """Choose an HDL that produces (close to) the wanted ratio, then recompute the ratio from it."""
    case["total_cholesterol"] = int(total_cholesterol)
    case["hdl"] = max(25, int(round(total_cholesterol / ratio)))
    _reconcile_lipids(case)


# --------------------------------------------------------------------------- neutral filler debits

# Debit sources that trigger no house rule, used to move a case across a class band so a
# target rule's effect is visible in the answer. Each returns the field edit it makes.
def _filler_occupation_b(case: dict, rng: random.Random) -> None:
    case["occupation_class"] = "B"
    case["occupation"] = rng.choice(OCCUPATION_EXAMPLES["B"])


def _filler_occupation_c(case: dict, rng: random.Random) -> None:
    if (case.get("avocation") or {}).get("type", "none") != "none":
        return  # class C + a hazardous avocation is HR-06; leave it alone
    case["occupation_class"] = "C"
    case["occupation"] = rng.choice(OCCUPATION_EXAMPLES["C"])


def _filler_violations(case: dict, rng: random.Random) -> None:
    case["mvr_violations"] = rng.choice((2, 3))


def _filler_tobacco_quit(case: dict, rng: random.Random) -> None:
    if case["tobacco_declared"] == "never":
        case["tobacco_declared"] = "quit_1_5y"


def _filler_liver_over(case: dict, rng: random.Random) -> None:
    if case["liver_enzymes"] == "normal":
        case["liver_enzymes"] = "elevated_over_2x"


def _filler_apnea_untreated(case: dict, rng: random.Random) -> None:
    if not case["sleep_apnea"]:
        case["sleep_apnea"] = True
        case["cpap_compliant"] = False


def _filler_family(case: dict, rng: random.Random) -> None:
    if case["family_history"] or int(case["age"]) > 60:
        return
    case["family_history"] = [
        {
            "relation": rng.choice(("father", "mother", "brother", "sister")),
            "condition": rng.choice(("MI", "stroke")),
            "site": None,
            "age": rng.randint(44, 58),
        }
    ]


def _filler_build(case: dict, rng: random.Random) -> None:
    if case["weight_change_lb_12mo"]:
        return  # HR-09 owns the build on this case
    set_build(case, case["height_in"], round(rng.uniform(28.2, 30.6), 1))


FILLERS = (
    _filler_occupation_b,
    _filler_occupation_c,
    _filler_violations,
    _filler_tobacco_quit,
    _filler_liver_over,
    _filler_apnea_untreated,
    _filler_family,
    _filler_build,
)


def apply_fillers(case: dict, rng: random.Random, k: int) -> None:
    for filler in rng.sample(FILLERS, k=min(k, len(FILLERS))):
        filler(case, rng)


# --------------------------------------------------------------------------- injectors


def _inject_01(case: dict, rng: random.Random) -> None:
    case["bp_treated"] = True
    case["bp_treatment_since"] = rng.randint(2014, 2023)
    case["bp_systolic"] = rng.randint(139, 145)
    case["bp_diastolic"] = rng.randint(80, 90)


def _inject_02(case: dict, rng: random.Random) -> None:
    case["avocation"] = {
        "type": "aviation",
        "hours_per_year": rng.randint(35, 95),
        "total_hours": rng.randint(280, 1400),
        "aerobatics": False,
    }


def _inject_03(case: dict, rng: random.Random) -> None:
    case["age"] = rng.randint(62, 70)
    case["family_history"] = [
        {
            "relation": rng.choice(("father", "brother")),
            "condition": rng.choice(("MI", "stroke")),
            "site": None,
            "age": rng.randint(45, 58),
        }
    ]
    if rng.random() < 0.5:
        case["family_history"].append(
            {"relation": "mother", "condition": "cancer", "site": rng.choice(CANCER_SITES), "age": rng.randint(48, 59)}
        )


def _inject_04(case: dict, rng: random.Random) -> None:
    """Three cardiac factors without tipping HR-01 or HR-07: untreated BP, a matched lipid pair, an A1c band."""
    case["bp_treated"] = False
    case["bp_systolic"] = rng.randint(139, 148)
    case["bp_diastolic"] = rng.randint(80, 88)
    set_lipids(case, rng.randint(245, 275), round(rng.uniform(5.3, 6.3), 1))
    case["a1c"] = round(rng.uniform(6.5, 6.9), 1)


def _inject_05(case: dict, rng: random.Random) -> None:
    case["age"] = rng.randint(52, 60)
    dx_age = rng.randint(46, case["age"] - 2)
    case["diabetes_dx_year"] = CURRENT_YEAR - (case["age"] - dx_age)
    case["diabetes_medication"] = rng.choice(("metformin", "metformin and a GLP-1 agonist", "diet controlled"))
    case["a1c"] = round(rng.uniform(6.5, 6.9), 1)


def _inject_06(case: dict, rng: random.Random) -> None:
    case["occupation_class"] = "C"
    case["occupation"] = rng.choice(OCCUPATION_EXAMPLES["C"])
    if rng.random() < 0.5:
        case["avocation"] = {"type": "climbing", "discipline": "technical trad rock", "days_per_year": rng.randint(12, 40)}
    else:
        case["avocation"] = {"type": "motorsport", "series": "club saloon racing", "events_per_year": rng.randint(4, 14)}


def _inject_07(case: dict, rng: random.Random) -> None:
    """Total cholesterol lands in a worse band than the ratio, so the two tables disagree.

    Two shapes: a ratio inside the free band (the charge disappears entirely) and a ratio one
    band better than the cholesterol (the charge drops but stays, which is what a compound case
    with the cardiac-interaction rule needs).
    """
    if rng.random() < 0.5:
        set_lipids(case, rng.randint(246, 315), round(rng.uniform(3.6, 4.8), 1))
    else:
        set_lipids(case, rng.randint(286, 340), round(rng.uniform(5.3, 6.3), 1))


def _inject_08(case: dict, rng: random.Random) -> None:
    case["annual_income"] = rng.choice((45_000, 52_000, 60_000, 68_000))
    case["face_amount"] = rng.choice((1_500_000, 1_750_000, 2_000_000, 2_500_000))


def _inject_09(case: dict, rng: random.Random) -> None:
    """Weight lost recently, sized so half of it back crosses a build band."""
    edge = rng.choice((28.0, 31.0, 34.0))
    height = case["height_in"]
    start = round(edge - rng.uniform(0.6, 1.6), 1)
    set_build(case, height, start)
    per_lb = 703.0 / (height * height)
    need = (edge + 0.4 - case["bmi"]) / per_lb
    lost = int(round(max(need * 2.0, 12.0))) + rng.randint(0, 6)
    case["weight_change_lb_12mo"] = -lost


def _inject_10(case: dict, rng: random.Random) -> None:
    case["dui_year"] = rng.choice((CURRENT_YEAR - 1, CURRENT_YEAR - 2))


def _inject_11(case: dict, rng: random.Random) -> None:
    case["sleep_apnea"] = True
    case["cpap_compliant"] = True


def _inject_12(case: dict, rng: random.Random) -> None:
    case["liver_enzymes"] = "elevated_under_2x"
    case["alcohol_treatment"] = False


def _inject_13(case: dict, rng: random.Random) -> None:
    site = rng.choice(CANCER_SITES)
    case["family_history"] = [
        {"relation": "mother", "condition": "cancer", "site": site, "age": rng.randint(46, 57)},
        {"relation": "sister", "condition": "cancer", "site": site, "age": rng.randint(46, 57)},
    ]
    case["age"] = rng.randint(38, 56)


def _inject_14(case: dict, rng: random.Random) -> None:
    deep = rng.random() < 0.5
    case["avocation"] = {
        "type": "scuba",
        "max_depth_ft": rng.randint(105, 160) if deep else rng.randint(55, 95),
        "dives_per_year": rng.randint(8, 45),
        "cave_wreck": (not deep) or rng.random() < 0.4,
    }


INJECTORS = {
    "HR-01": _inject_01,
    "HR-02": _inject_02,
    "HR-03": _inject_03,
    "HR-04": _inject_04,
    "HR-05": _inject_05,
    "HR-06": _inject_06,
    "HR-07": _inject_07,
    "HR-08": _inject_08,
    "HR-09": _inject_09,
    "HR-10": _inject_10,
    "HR-11": _inject_11,
    "HR-12": _inject_12,
    "HR-13": _inject_13,
    "HR-14": _inject_14,
}

# Injection order matters where two rules touch the same fields (build, lipids, age).
INJECTION_ORDER = ("HR-03", "HR-05", "HR-13", "HR-04", "HR-07", "HR-09", "HR-01", "HR-02", "HR-06", "HR-14",
                   "HR-08", "HR-10", "HR-11", "HR-12")


def _suppress(case: dict, rng: random.Random) -> None:
    """Turn every rule trigger off, so only the injected ones can be on."""
    case["bp_treated"] = False
    case["bp_treatment_since"] = None
    case["bp_systolic"] = min(int(case["bp_systolic"]), 136)
    case["bp_diastolic"] = min(int(case["bp_diastolic"]), 86)
    case["avocation"] = {"type": "none"}
    case["diabetes_dx_year"] = None
    case["diabetes_medication"] = None
    case["weight_change_lb_12mo"] = 0
    case["dui_year"] = None
    case["sleep_apnea"] = False
    case["cpap_compliant"] = False
    case["liver_enzymes"] = "normal"
    case["alcohol_treatment"] = False
    case["family_history"] = []
    case["age"] = min(int(case["age"]), 58)
    case["occupation_class"] = "A"
    case["occupation"] = rng.choice(OCCUPATION_EXAMPLES["A"])
    # lipids: put both tables in the same band so HR-07 cannot trigger
    set_lipids(case, rng.randint(170, 230), round(rng.uniform(3.4, 4.8), 1))
    if float(case["a1c"]) >= 6.5:
        case["a1c"] = round(rng.uniform(5.0, 6.2), 1)
    if float(case["bmi"]) >= 28.0:
        set_build(case, case["height_in"], round(rng.uniform(21.0, 27.4), 1))
    case["annual_income"] = max(int(case["annual_income"]), 85_000)
    if case["face_amount"] > 1_000_000:
        case["face_amount"] = 1_000_000


def propose(rng: random.Random, targets: frozenset[str], filler_k: int) -> dict:
    case = draw_base_case(rng)
    _suppress(case, rng)
    for rule_id in INJECTION_ORDER:
        if rule_id in targets:
            INJECTORS[rule_id](case, rng)
    apply_fillers(case, rng, filler_k)
    return case


# --------------------------------------------------------------------------- rendering


def _money(value: int | float) -> str:
    return f"${int(value):,}"


def render_case(case: dict) -> str:
    """The applicant as the operator sees it. About 150 words, ASCII only, no golden fields."""
    av = case.get("avocation") or {}
    av_type = str(av.get("type") or "none")
    if av_type == "aviation":
        avocation = (
            f"private pilot, {av['hours_per_year']} hrs/yr, {av['total_hours']} total, "
            f"{'aerobatics' if av.get('aerobatics') else 'no aerobatics'}"
        )
    elif av_type == "scuba":
        avocation = (
            f"recreational scuba, max depth {av['max_depth_ft']} ft, {av['dives_per_year']} dives/yr, "
            f"{'cave and wreck penetration' if av.get('cave_wreck') else 'open water only'}"
        )
    elif av_type == "climbing":
        avocation = f"{av['discipline']} climbing, {av['days_per_year']} days/yr"
    elif av_type == "motorsport":
        avocation = f"{av['series']}, {av['events_per_year']} events/yr"
    else:
        avocation = "none declared"

    weight_change = int(case["weight_change_lb_12mo"])
    if weight_change < 0:
        change = f"down {abs(weight_change)} lb in the last 12 months"
    elif weight_change > 0:
        change = f"up {weight_change} lb in the last 12 months"
    else:
        change = "stable over the last 12 months"

    tobacco = {
        "never": "never used",
        "quit_over_5y": "quit more than 5 years ago",
        "quit_1_5y": "quit within the last 5 years",
        "current": "current user",
    }[str(case["tobacco_declared"])]
    tobacco += f"; nicotine screen {case['nicotine_lab']}"

    bp = f"{case['bp_systolic']}/{case['bp_diastolic']}"
    bp += f", on treatment since {case['bp_treatment_since']}" if case.get("bp_treated") else ", untreated"

    if case.get("diabetes_dx_year"):
        diabetes = f"type 2 diabetes diagnosed {case['diabetes_dx_year']}, {case['diabetes_medication']}"
    else:
        diabetes = "no diabetes diagnosis"

    if case["family_history"]:
        events = ", ".join(
            f"{e['relation']} {e['condition']}{' (' + e['site'] + ')' if e.get('site') else ''} at {e['age']}"
            for e in case["family_history"]
        )
    else:
        events = "nothing before age 60 in parents or siblings"

    apnea = "none reported"
    if case.get("sleep_apnea"):
        apnea = "diagnosed, " + ("documented CPAP compliance" if case.get("cpap_compliant") else "no CPAP in use")

    liver = {
        "normal": "liver enzymes normal",
        "elevated_under_2x": "liver enzymes elevated, below twice the upper limit of normal",
        "elevated_over_2x": "liver enzymes elevated, above twice the upper limit of normal",
    }[str(case["liver_enzymes"])]
    liver += "; treated for alcohol use in the past" if case.get("alcohol_treatment") else "; no alcohol history"

    mvr = f"{case['mvr_violations']} moving violation(s) in the last 3 years"
    mvr += f"; DUI conviction {case['dui_year']}" if case.get("dui_year") else "; no DUI"

    lines = [
        f"Applicant: {case['sex']}, age {case['age']}.",
        f"Product: {case['product']}, face {_money(case['face_amount'])}.",
        f"Build: {case['height_in'] // 12}'{case['height_in'] % 12}\", {case['weight_lb']} lb, BMI "
        f"{case['bmi']:.1f}; weight {change}.",
        f"Tobacco: {tobacco}.",
        f"Blood pressure: {bp}.",
        f"Lipids: total cholesterol {case['total_cholesterol']}, HDL {case['hdl']}, ratio "
        f"{case['lipid_ratio']:.1f}.",
        f"A1c: {case['a1c']:.1f}; {diabetes}.",
        f"Family history: {events}.",
        f"Occupation: {case['occupation']}, class {case['occupation_class']}.",
        f"Avocation: {avocation}.",
        f"Driving: {mvr}.",
        f"Alcohol and liver: {liver}.",
        f"Sleep apnea: {apnea}.",
        f"Financial: income {_money(case['annual_income'])}, {_money(case['inforce_coverage'])} already in "
        f"force.",
        f"Also on file: {case['irrelevant_detail']}.",
    ]
    return "\n".join(lines)


CASE_FIELDS: tuple[str, ...] = (
    "sex", "age", "product", "face_amount", "height_in", "weight_lb", "bmi", "weight_change_lb_12mo",
    "tobacco_declared", "nicotine_lab", "bp_systolic", "bp_diastolic", "bp_treated", "bp_treatment_since",
    "total_cholesterol", "hdl", "lipid_ratio", "a1c", "diabetes_dx_year", "diabetes_medication",
    "family_history", "occupation", "occupation_class", "avocation", "mvr_violations", "dui_year",
    "liver_enzymes", "alcohol_treatment", "sleep_apnea", "cpap_compliant", "annual_income",
    "inforce_coverage", "irrelevant_detail",
)


def operator_fields(case: dict) -> dict:
    """The structured view handed to the operator - the case fields and nothing else."""
    return {k: case[k] for k in CASE_FIELDS if k in case}


# --------------------------------------------------------------------------- ordering


@dataclass
class Slot:
    tier: str
    targets: frozenset[str]


def _window_ok(tiers: list[str]) -> bool:
    for start in range(0, len(tiers) - WINDOW + 1):
        w = tiers[start : start + WINDOW]
        if not WINDOW_CLEAN[0] <= w.count("clean") <= WINDOW_CLEAN[1]:
            return False
        if not WINDOW_JUDGEMENT[0] <= w.count("judgement") <= WINDOW_JUDGEMENT[1]:
            return False
        if not WINDOW_COMPOUND[0] <= w.count("compound") <= WINDOW_COMPOUND[1]:
            return False
    return True


def find_tier_order(rng: random.Random, counts: dict[str, int], attempts: int = 200_000) -> list[str]:
    """A tier sequence with the given counts, case 1 not clean, and every window inside the mix."""
    pool = ["clean"] * counts["clean"] + ["judgement"] * counts["judgement"] + ["compound"] * counts["compound"]
    for _ in range(attempts):
        candidate = pool[:]
        rng.shuffle(candidate)
        if candidate[0] == "clean":
            continue
        if _window_ok(candidate):
            return candidate
    raise RuntimeError(f"no tier order found for {counts}")


# --------------------------------------------------------------------------- generation


def naive_ladder_distance(result: dict) -> int:
    """How many ladder steps a careful reader of the manual alone lands away from the golden."""
    from src.underwriting.scorer import ladder_distance

    manual, golden = result["manual_only"], result["golden"]
    return ladder_distance(manual.decision, manual.rating_class, golden.decision, golden.rating_class)


def _generate_for(rng: random.Random, targets: frozenset[str], case_id: str, index: int, phase: str) -> dict:
    """Draw candidates until the *derived* fired set equals ``targets``, then pick one with headroom.

    The tier is read off the engines, never set. Among the matching candidates the generator keeps
    the one at :data:`CANDIDATE_QUANTILE` of the naive-reader ladder distance: a judgement or
    compound case that the manual alone happens to get right teaches nothing, and picking the
    median would leave the headline metric almost no room to move.
    """
    matches: list[tuple[int, int, dict]] = []
    for draw in range(MAX_DRAWS_PER_SLOT):
        # Vary how many neutral debits ride along, so the same rule fires at different
        # points on the ladder instead of always at the same total.
        filler_k = rng.choice((0, 0, 1, 1, 2, 2, 3))
        case = propose(rng, targets, filler_k)
        result = derive(case)
        if not result["consistent"] or result["tier"] is None:
            continue
        if frozenset(result["fired_rule_ids"]) != targets:
            continue
        matches.append((naive_ladder_distance(result), draw, case))
        if len(matches) >= CANDIDATE_POOL:
            break
    if not matches:
        raise RuntimeError(f"could not generate a case firing exactly {sorted(targets)} in {MAX_DRAWS_PER_SLOT} draws")
    matches.sort(key=lambda m: (m[0], -m[1]))
    case = matches[int(CANDIDATE_QUANTILE * (len(matches) - 1))][2]
    case["case_id"] = case_id
    case["case_index"] = index
    case["phase"] = phase
    return case


def _golden_for(case: dict) -> dict:
    result = derive(case)
    golden = result["golden"].to_record()
    golden.update(
        {
            "case_id": case["case_id"],
            "case_index": case["case_index"],
            "phase": case["phase"],
            "fired_rule_ids": list(result["fired_rule_ids"]),
            "tier": result["tier"],
            "manual_only": result["manual_only"].to_record(),
        }
    )
    return golden


def _slots(rng: random.Random, counts: dict[str, int], judgement, compound) -> list[Slot]:
    order = find_tier_order(rng, counts)
    buckets = {
        "clean": [frozenset()] * counts["clean"],
        "judgement": list(judgement),
        "compound": list(compound),
    }
    rng.shuffle(buckets["judgement"])
    rng.shuffle(buckets["compound"])
    cursor = {k: 0 for k in buckets}
    slots: list[Slot] = []
    for tier in order:
        slots.append(Slot(tier=tier, targets=buckets[tier][cursor[tier]]))
        cursor[tier] += 1
    return slots


def build_dataset(seed: int = SEED) -> tuple[list[dict], list[dict]]:
    """Generate the frozen case list and the golden list. Deterministic for a given seed."""
    rng = random.Random(seed)

    train_counts = {
        "clean": TRAINING_CLEAN_COUNT,
        "judgement": len(TRAINING_JUDGEMENT_TARGETS),
        "compound": len(TRAINING_COMPOUND_TARGETS),
    }
    train_slots = _slots(rng, train_counts, TRAINING_JUDGEMENT_TARGETS, TRAINING_COMPOUND_TARGETS)

    held_counts = {
        "clean": HELDOUT_CLEAN_COUNT,
        "judgement": len(HELDOUT_JUDGEMENT_TARGETS),
        "compound": len(HELDOUT_COMPOUND_TARGETS),
    }
    held_order = ["judgement", "compound", "clean", "judgement", "judgement", "compound", "clean", "judgement"]
    held_buckets = {
        "clean": [frozenset()] * held_counts["clean"],
        "judgement": list(HELDOUT_JUDGEMENT_TARGETS),
        "compound": list(HELDOUT_COMPOUND_TARGETS),
    }
    rng.shuffle(held_buckets["judgement"])
    rng.shuffle(held_buckets["compound"])
    cursor = {k: 0 for k in held_buckets}
    held_slots: list[Slot] = []
    for tier in held_order:
        held_slots.append(Slot(tier=tier, targets=held_buckets[tier][cursor[tier]]))
        cursor[tier] += 1

    cases: list[dict] = []
    goldens: list[dict] = []
    for i, slot in enumerate(train_slots, start=1):
        case = _generate_for(rng, slot.targets, f"UW-T{i:02d}", i, "train")
        cases.append(case)
        goldens.append(_golden_for(case))
    for i, slot in enumerate(held_slots, start=1):
        case = _generate_for(rng, slot.targets, f"UW-H{i:02d}", i, "holdout")
        cases.append(case)
        goldens.append(_golden_for(case))
    return cases, goldens


def split(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    return ([c for c in cases if c["phase"] == "train"], [c for c in cases if c["phase"] == "holdout"])


def sanity(cases: list[dict], goldens: list[dict]) -> list[str]:
    """Every schedule constraint from section 5, checked against the derived goldens."""
    problems: list[str] = []
    by_phase = {"train": [], "holdout": []}
    for g in goldens:
        by_phase[g["phase"]].append(g)
    train, held = by_phase["train"], by_phase["holdout"]

    if len(train) != TRAINING_CASES:
        problems.append(f"training cases: {len(train)} != {TRAINING_CASES}")
    if len(held) != HELDOUT_CASES:
        problems.append(f"held-out cases: {len(held)} != {HELDOUT_CASES}")

    tiers = [g["tier"] for g in train]
    for tier, want in (("clean", TRAINING_CLEAN_COUNT), ("judgement", len(TRAINING_JUDGEMENT_TARGETS)),
                       ("compound", len(TRAINING_COMPOUND_TARGETS))):
        if tiers.count(tier) != want:
            problems.append(f"training {tier}: {tiers.count(tier)} != {want}")
    if tiers and tiers[0] == "clean":
        problems.append("case 1 is clean")
    if not _window_ok(tiers):
        problems.append("training window mix violated")

    firings: dict[str, list[frozenset]] = {}
    for g in train:
        for rid in g["fired_rule_ids"]:
            firings.setdefault(rid, []).append(frozenset(set(g["fired_rule_ids"]) - {rid}))
    for rid in (f"HR-{i:02d}" for i in range(1, 13)):
        shapes = firings.get(rid, [])
        if len(shapes) < 3:
            problems.append(f"{rid} fires in {len(shapes)} training cases (< 3)")
        if len(set(shapes)) < 2:
            problems.append(f"{rid} fires in {len(set(shapes))} distinct shapes (< 2)")
    for rid in ("HR-13", "HR-14"):
        if rid in firings:
            problems.append(f"{rid} fires in training")

    heldout_novel = [g for g in held if set(g["fired_rule_ids"]) & {"HR-13", "HR-14"}]
    if len(heldout_novel) != 2:
        problems.append(f"held-out novel-rule cases: {len(heldout_novel)} != 2")

    for g in train + held:
        if g["tier"] == "clean":
            manual = g["manual_only"]
            same = (
                manual["decision"] == g["decision"]
                and manual["rating_class"] == g["rating_class"]
                and manual["modifiers"] == g["modifiers"]
                and sorted(manual["drivers"]) == sorted(g["drivers"])
            )
            if not same:
                problems.append(f"{g['case_id']}: clean tier but manual-only != golden")
    return problems


def verify_engines(case: dict) -> tuple[dict, dict]:
    return rate_manual_only(case).to_record(), rate_house(case).to_record()
