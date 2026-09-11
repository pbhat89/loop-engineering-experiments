"""The starter manual's rating tables, as Python data.

Single source of truth: :mod:`src.underwriting.manual` renders the manual text from these
tables and :mod:`src.underwriting.engine` rates from them, so the manual and the engines
cannot disagree (a test asserts every number in a table appears in the manual text).

Nothing here is hidden from the operator: every value below is printed in the starter
manual that every arm receives. The unwritten practice lives in
:mod:`src.underwriting.house_rules`.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- the ladder

LADDER: tuple[str, ...] = (
    "Preferred Plus",
    "Preferred",
    "Standard Plus",
    "Standard",
    "Table 2",
    "Table 4",
    "Table 6",
    "Table 8",
    "Decline",
)
LADDER_INDEX: dict[str, int] = {name: i for i, name in enumerate(LADDER)}

# Short forms an operator may plausibly write; normalised by the scorer.
CLASS_ALIASES: dict[str, str] = {
    "pref+": "Preferred Plus",
    "pref +": "Preferred Plus",
    "preferred+": "Preferred Plus",
    "preferred plus": "Preferred Plus",
    "super preferred": "Preferred Plus",
    "pref": "Preferred",
    "preferred": "Preferred",
    "std+": "Standard Plus",
    "std +": "Standard Plus",
    "standard+": "Standard Plus",
    "standard plus": "Standard Plus",
    "std": "Standard",
    "standard": "Standard",
    "tab 2": "Table 2",
    "table2": "Table 2",
    "table 2": "Table 2",
    "tab 4": "Table 4",
    "table4": "Table 4",
    "table 4": "Table 4",
    "tab 6": "Table 6",
    "table6": "Table 6",
    "table 6": "Table 6",
    "tab 8": "Table 8",
    "table8": "Table 8",
    "table 8": "Table 8",
    "decline": "Decline",
    "declined": "Decline",
}

DECISIONS: tuple[str, ...] = ("accept", "accept_with_modification", "postpone", "decline")
DECISION_ALIASES: dict[str, str] = {
    "accept": "accept",
    "accept with modification": "accept_with_modification",
    "accept_with_modification": "accept_with_modification",
    "accept-with-modification": "accept_with_modification",
    "accept with modifications": "accept_with_modification",
    "modify": "accept_with_modification",
    "postpone": "postpone",
    "postponed": "postpone",
    "decline": "decline",
    "declined": "decline",
}

DECLINE = "decline"  # sentinel debit value: the band itself declines the file

# --------------------------------------------------------------------------- debit -> class

# (low, high_inclusive_or_None, class)
DEBIT_BANDS: tuple[tuple[int, int | None, str], ...] = (
    (0, 49, "Standard"),
    (50, 99, "Table 2"),
    (100, 149, "Table 4"),
    (150, 199, "Table 6"),
    (200, 249, "Table 8"),
    (250, None, "Decline"),
)

# --------------------------------------------------------------------------- build

# (low_bmi, high_bmi_inclusive, debits) - BMI rounded to one decimal
BUILD_BANDS: tuple[tuple[float | None, float | None, int | str], ...] = (
    (None, 18.9, 25),
    (19.0, 27.9, 0),
    (28.0, 30.9, 25),
    (31.0, 33.9, 50),
    (34.0, 36.9, 100),
    (37.0, 39.9, 150),
    (40.0, None, DECLINE),
)

# --------------------------------------------------------------------------- blood pressure

SYSTOLIC_BANDS: tuple[tuple[int | None, int | None, int | str], ...] = (
    (None, 138, 0),
    (139, 148, 25),
    (149, 158, 50),
    (159, 168, 100),
    (169, None, DECLINE),
)
DIASTOLIC_BANDS: tuple[tuple[int | None, int | None, int | str], ...] = (
    (None, 88, 0),
    (89, 94, 25),
    (95, 99, 50),
    (100, 104, 100),
    (105, None, DECLINE),
)
BP_TREATMENT_DEBITS = 25

# --------------------------------------------------------------------------- lipids

TOTAL_CHOLESTEROL_BANDS: tuple[tuple[int | None, int | None, int], ...] = (
    (None, 240, 0),
    (241, 280, 25),
    (281, 320, 50),
    (321, None, 75),
)
# TC / HDL ratio, one decimal
LIPID_RATIO_BANDS: tuple[tuple[float | None, float | None, int], ...] = (
    (None, 5.0, 0),
    (5.1, 6.5, 25),
    (6.6, None, 50),
)

# --------------------------------------------------------------------------- A1c

A1C_BANDS: tuple[tuple[float | None, float | None, int | str], ...] = (
    (None, 6.4, 0),
    (6.5, 6.9, 50),
    (7.0, 7.9, 75),
    (8.0, 8.9, 125),
    (9.0, None, DECLINE),
)

# --------------------------------------------------------------------------- tobacco

TOBACCO_STATUSES: tuple[str, ...] = ("never", "quit_over_5y", "quit_1_5y", "current")
TOBACCO_DEBITS: dict[str, int] = {"never": 0, "quit_over_5y": 0, "quit_1_5y": 25, "current": 75}
NON_SMOKER_STATUSES: tuple[str, ...] = ("never", "quit_over_5y")

# --------------------------------------------------------------------------- family history

FAMILY_HISTORY_CONDITIONS: tuple[str, ...] = ("MI", "stroke", "cancer")
FAMILY_HISTORY_RELATIONS: tuple[str, ...] = ("father", "mother", "brother", "sister")
FAMILY_HISTORY_AGE_LIMIT = 60
FAMILY_HISTORY_DEBITS_PER_EVENT = 25
FAMILY_HISTORY_DEBITS_CAP = 50

# --------------------------------------------------------------------------- occupation

OCCUPATION_CLASS_DEBITS: dict[str, int] = {"A": 0, "B": 25, "C": 50}
OCCUPATION_EXAMPLES: dict[str, tuple[str, ...]] = {
    "A": ("office administrator", "regional sales manager", "software engineer", "schoolteacher", "pharmacist"),
    "B": ("delivery driver", "site foreman", "welder", "commercial fisher's deckhand", "warehouse supervisor"),
    "C": ("structural steel erector", "underground miner", "offshore rig hand", "logging feller", "high-voltage lineman"),
}

# --------------------------------------------------------------------------- avocations

AVOCATION_TYPES: tuple[str, ...] = ("none", "aviation", "scuba", "climbing", "motorsport")
HAZARDOUS_AVOCATIONS: tuple[str, ...] = ("aviation", "scuba", "climbing", "motorsport")
AVIATION_DEFAULT_DEBITS = 50  # the manual refers; absent a referral the file is rated as a hazardous avocation
SCUBA_DEPTH_BANDS: tuple[tuple[int | None, int | None, int], ...] = (
    (None, 60, 0),
    (61, 100, 25),
    (101, None, 50),
)
CLIMBING_DEBITS = 50
MOTORSPORT_FLAT_EXTRA = 5.00  # per $1,000 - stated in the manual, not a house rule

# --------------------------------------------------------------------------- driving record

MVR_VIOLATION_BANDS: tuple[tuple[int, int | None, int], ...] = (
    (0, 1, 0),
    (2, 2, 25),
    (3, None, 50),
)
DUI_DEBITS = 50

# --------------------------------------------------------------------------- alcohol and liver

LIVER_STATUSES: tuple[str, ...] = ("normal", "elevated_under_2x", "elevated_over_2x")
LIVER_ENZYME_DEBITS = 25
ALCOHOL_TREATMENT_DEBITS = 50

# --------------------------------------------------------------------------- sleep apnea

SLEEP_APNEA_DEBITS = 50

# --------------------------------------------------------------------------- financial

# (low_age, high_age_inclusive, income multiple)
INCOME_MULTIPLE_BANDS: tuple[tuple[int, int | None, int], ...] = (
    (18, 30, 30),
    (31, 40, 25),
    (41, 50, 20),
    (51, 60, 15),
    (61, None, 10),
)

# --------------------------------------------------------------------------- modifiers

FLAT_EXTRA_BANDS: tuple[float, ...] = (2.50, 5.00, 7.50)
FLAT_EXTRA_BAND_WORDS: dict[float, str] = {
    2.50: "the first flat-extra band",
    5.00: "the second flat-extra band",
    7.50: "the third flat-extra band",
}
MODIFIER_TYPES: tuple[str, ...] = ("flat_extra", "exclusion")

# --------------------------------------------------------------------------- preferred eligibility

# Nested: Preferred Plus implies Preferred implies Standard Plus. Every threshold is printed
# in the manual, so all three tiers are decidable from the manual alone.
PREFERRED_CRITERIA: dict[str, dict[str, object]] = {
    "Standard Plus": {
        "bmi_max": 27.9,
        "systolic_max": 138,
        "diastolic_max": 88,
        "total_cholesterol_max": 240,
        "ratio_max": 5.0,
        "a1c_max": 6.4,
        "tobacco_allowed": ("never", "quit_over_5y"),
        "violations_max": 0,
        "dui_within_years": 5,       # no DUI in the last 5 years
        "occupation_classes": ("A", "B"),
        "avocation_allowed": False,  # every avocation the case file records is a hazardous one
        "family_history_events_max": 1,
    },
    "Preferred": {
        "bmi_max": 27.0,
        "systolic_max": 134,
        "diastolic_max": 84,
        "total_cholesterol_max": 220,
        "ratio_max": 4.5,
        "a1c_max": 6.0,
        "tobacco_allowed": ("never", "quit_over_5y"),
        "violations_max": 0,
        "dui_within_years": None,    # no DUI ever
        "occupation_classes": ("A",),
        "avocation_allowed": False,
        "family_history_events_max": 0,
    },
    "Preferred Plus": {
        "bmi_max": 26.0,
        "systolic_max": 128,
        "diastolic_max": 80,
        "total_cholesterol_max": 200,
        "ratio_max": 4.0,
        "a1c_max": 5.6,
        "tobacco_allowed": ("never",),
        "violations_max": 0,
        "dui_within_years": None,
        "occupation_classes": ("A",),
        "avocation_allowed": False,
        "family_history_events_max": 0,
    },
}
PREFERRED_ORDER: tuple[str, ...] = ("Preferred Plus", "Preferred", "Standard Plus")


# --------------------------------------------------------------------------- helpers


def band_value(bands, value):
    """First band whose [low, high] contains ``value``; ``None`` when no band matches."""
    for low, high, result in bands:
        if (low is None or value >= low) and (high is None or value <= high):
            return result
    return None


def class_for_debits(debits: int) -> str:
    total = max(int(debits), 0)
    for low, high, name in DEBIT_BANDS:
        if total >= low and (high is None or total <= high):
            return name
    return "Decline"


def bmi_from(height_in: float, weight_lb: float) -> float:
    return round(703.0 * float(weight_lb) / (float(height_in) ** 2), 1)


def income_multiple(age: int) -> int:
    return int(band_value(INCOME_MULTIPLE_BANDS, int(age)) or 10)
