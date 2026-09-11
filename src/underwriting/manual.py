"""Render the starter manual from the rating tables.

Every arm is handed this text, unchanged, on every request. It is generated from
:mod:`src.underwriting.tables`, so the manual and the engines cannot drift apart - a
test asserts every number in every table appears in the rendered text.

The manual is honest about its own gaps the way a real one is: each hidden-rule area
carries a line saying *where* the gap is and never what fills it. ASCII only, so it
prints on a cp1252 console without a codec dance.
"""
from __future__ import annotations

from src.underwriting.tables import (
    A1C_BANDS,
    ALCOHOL_TREATMENT_DEBITS,
    AVIATION_DEFAULT_DEBITS,
    BP_TREATMENT_DEBITS,
    BUILD_BANDS,
    CLIMBING_DEBITS,
    DEBIT_BANDS,
    DECLINE,
    DIASTOLIC_BANDS,
    DUI_DEBITS,
    FAMILY_HISTORY_AGE_LIMIT,
    FAMILY_HISTORY_DEBITS_CAP,
    FAMILY_HISTORY_DEBITS_PER_EVENT,
    FLAT_EXTRA_BANDS,
    INCOME_MULTIPLE_BANDS,
    LIPID_RATIO_BANDS,
    LIVER_ENZYME_DEBITS,
    MOTORSPORT_FLAT_EXTRA,
    MVR_VIOLATION_BANDS,
    OCCUPATION_CLASS_DEBITS,
    OCCUPATION_EXAMPLES,
    PREFERRED_CRITERIA,
    SCUBA_DEPTH_BANDS,
    SLEEP_APNEA_DEBITS,
    SYSTOLIC_BANDS,
    TOBACCO_DEBITS,
    TOTAL_CHOLESTEROL_BANDS,
)

GAP_LINES: dict[str, str] = {
    "cardiac": "For combinations of cardiac risk factors, refer to underwriting judgement.",
    "treated_bp": "For a treated condition whose reading is now at target, refer to underwriting judgement.",
    "family_age": "For applicants well past the family-history qualifying age, refer to underwriting judgement.",
    "late_onset": "For late-onset metabolic disease that is well controlled, refer to underwriting judgement.",
    "two_tables": "Where two tables in this manual point at different bands, refer to underwriting judgement.",
    "aviation": "For private aviation, refer to underwriting judgement.",
    "occ_avoc": "Where a hazardous occupation and a hazardous avocation appear together, refer to underwriting judgement.",
    "build_change": "For a recent change in build, refer to underwriting judgement.",
    "recent_mvr": "For a recent motoring conviction, refer to underwriting judgement.",
    "treated_apnea": "For treated sleep-disordered breathing, refer to underwriting judgement.",
    "liver": "For borderline liver chemistry, refer to underwriting judgement.",
    "financial": "Where the face amount is large relative to income, refer to underwriting judgement.",
}


def fmt_int(value) -> str:
    return "decline" if value == DECLINE else str(int(value))


def fmt_one_dp(value) -> str:
    return "decline" if value == DECLINE else f"{float(value):.1f}"


def _span(low, high, fmt) -> str:
    if low is None:
        return f"up to {fmt(high)}"
    if high is None:
        return f"{fmt(low)}+"
    if low == high:
        return f"{fmt(low)}"
    return f"{fmt(low)}-{fmt(high)}"


def render_bands(bands, bound_fmt=fmt_int, result_fmt=fmt_int, unit: str = "") -> str:
    return " | ".join(f"{_span(lo, hi, bound_fmt)}{unit} {result_fmt(res)}" for lo, hi, res in bands)


def _preferred_line(tier: str) -> str:
    c = PREFERRED_CRITERIA[tier]
    tobacco = "never" if c["tobacco_allowed"] == ("never",) else "never or quit over 5 yr"
    dui = "no DUI ever" if c["dui_within_years"] is None else f"no DUI in {c['dui_within_years']} yr"
    family = (
        "no qualifying family history"
        if int(c["family_history_events_max"]) == 0
        else f"at most {c['family_history_events_max']} family-history event"
    )
    return (
        f"**{tier}**: BMI {fmt_one_dp(c['bmi_max'])} or under; BP {c['systolic_max']}/{c['diastolic_max']} "
        f"or under and untreated; TC {c['total_cholesterol_max']} or under with ratio "
        f"{fmt_one_dp(c['ratio_max'])} or under; A1c {fmt_one_dp(c['a1c_max'])} or under with no diabetes "
        f"diagnosis; tobacco {tobacco}; {c['violations_max']} moving violations and {dui}; occupation class "
        f"{' or '.join(c['occupation_classes'])}; no hazardous avocation; {family}; no sleep apnea, no "
        f"alcohol history, normal liver chemistry."
    )


def build_manual() -> str:
    """The starter manual, in markdown."""
    flat = " / ".join(f"${b:.2f}" for b in FLAT_EXTRA_BANDS)
    income = " | ".join(
        f"{lo}-{hi} {mult}x" if hi is not None else f"{lo}+ {mult}x" for lo, hi, mult in INCOME_MULTIPLE_BANDS
    )
    debit_bands = " | ".join(
        f"{lo}-{hi} {name}" if hi is not None else f"{lo}+ {name}" for lo, hi, name in DEBIT_BANDS
    )
    occupations = " ".join(
        f"Class {c} ({OCCUPATION_CLASS_DEBITS[c]}{', hazardous' if c == 'C' else ''}): "
        f"{', '.join(OCCUPATION_EXAMPLES[c])}."
        for c in ("A", "B", "C")
    )
    parts = [
        "# Individual life underwriting manual (starter edition)",
        "",
        "This is the whole of the written practice. Rate every application from it. Where it says *refer to "
        "underwriting judgement*, the manual has nothing more to give you.",
        "",
        "## 1. Decision vocabulary",
        "",
        "Four decisions and no others: **accept**; **accept with modification** (a flat extra and/or an "
        "exclusion rider); **postpone** (do not decide yet); **decline**.",
        "",
        "## 2. Rating classes and the debit bands",
        "",
        f"Add the debits from sections 3-14 and read the class off the total: {debit_bands}.",
        "",
        "A decline band in any single table declines the file whatever the total comes to. Three preferred "
        "classes sit above Standard. Each needs **zero debits** and, in addition:",
        "",
        "- " + _preferred_line("Standard Plus"),
        "- " + _preferred_line("Preferred"),
        "- " + _preferred_line("Preferred Plus"),
        "",
        "Zero debits meeting none of the three is **Standard**.",
        "",
        "## 3. Build",
        "",
        f"Height, weight and BMI are on the file. Read the BMI: {render_bands(BUILD_BANDS, fmt_one_dp)}.",
        "",
        GAP_LINES["build_change"],
        "",
        "## 4. Blood pressure",
        "",
        f"Untreated reading, systolic: {render_bands(SYSTOLIC_BANDS)}. Diastolic: "
        f"{render_bands(DIASTOLIC_BANDS)}. Charge the worse of the two bands. On treatment: "
        f"{BP_TREATMENT_DEBITS}.",
        "",
        GAP_LINES["treated_bp"],
        "",
        "## 5. Lipids",
        "",
        f"Total cholesterol: {render_bands(TOTAL_CHOLESTEROL_BANDS)}. Total cholesterol to HDL ratio: "
        f"{render_bands(LIPID_RATIO_BANDS, fmt_one_dp)}. Both tables are in force.",
        "",
        GAP_LINES["two_tables"],
        "",
        "## 6. Diabetes and A1c",
        "",
        f"A1c: {render_bands(A1C_BANDS, fmt_one_dp)}. Type 2 diabetes is rated on the A1c. The year of "
        "diagnosis and any medication are on the file.",
        "",
        GAP_LINES["late_onset"],
        "",
        "## 7. Tobacco",
        "",
        f"Never used, or quit more than 5 years ago: non-smoker, {TOBACCO_DEBITS['never']}. Quit 1 to 5 years "
        f"ago: {TOBACCO_DEBITS['quit_1_5y']}. Current use: smoker rates - in this manual the smoker class "
        f"runs on the same debit ladder, so add {TOBACCO_DEBITS['current']} and cap the best available class "
        "at Standard. A nicotine-positive laboratory result against a declared *never* makes the applicant a "
        "current user.",
        "",
        "## 8. Family history",
        "",
        f"A parent or sibling with myocardial infarction, stroke or cancer before age "
        f"{FAMILY_HISTORY_AGE_LIMIT}: {FAMILY_HISTORY_DEBITS_PER_EVENT} per event, capped at "
        f"{FAMILY_HISTORY_DEBITS_CAP}. The applicant's own age does not change the charge.",
        "",
        GAP_LINES["family_age"],
        "",
        "## 9. Occupation",
        "",
        occupations,
        "",
        "## 10. Avocations",
        "",
        f"{GAP_LINES['aviation']} Where no referral is available, rate private aviation as a hazardous "
        f"avocation: {AVIATION_DEFAULT_DEBITS}. Scuba, by maximum depth: "
        f"{render_bands(SCUBA_DEPTH_BANDS, unit=' ft')}. Technical rock or ice climbing: {CLIMBING_DEBITS}. "
        f"Amateur motorsport competition: a flat extra of ${MOTORSPORT_FLAT_EXTRA:.2f} per $1,000.",
        "",
        GAP_LINES["occ_avoc"],
        "",
        "## 11. Driving record",
        "",
        f"Moving violations in the last 3 years: {render_bands(MVR_VIOLATION_BANDS)}. A DUI conviction: rate "
        f"{DUI_DEBITS}.",
        "",
        GAP_LINES["recent_mvr"],
        "",
        "## 12. Alcohol and liver",
        "",
        f"Elevated liver enzymes: {LIVER_ENZYME_DEBITS}. A history of treatment for alcohol use: "
        f"{ALCOHOL_TREATMENT_DEBITS}.",
        "",
        GAP_LINES["liver"],
        "",
        "## 13. Sleep apnea",
        "",
        f"Diagnosed sleep apnea: {SLEEP_APNEA_DEBITS}.",
        "",
        GAP_LINES["treated_apnea"],
        "",
        "## 14. Financial underwriting",
        "",
        f"The face amount applied for, plus cover already in force, should sit within the income multiple for "
        f"the applicant's age: {income}.",
        "",
        GAP_LINES["financial"],
        "",
        "## 15. Modifiers",
        "",
        f"A flat extra is charged per $1,000 of face amount in one of three bands: {flat}. An exclusion rider "
        "removes one named hazard from cover and carries no charge; name the hazard excluded. Either "
        "modifier makes the decision *accept with modification*.",
        "",
        "## 16. Where this manual stops",
        "",
        f"{GAP_LINES['cardiac']} A referral line means the manual has reached the edge of what it can tell "
        "you. Rate the file on what the tables do say, and expect the reviewer to correct you.",
        "",
    ]
    return "\n".join(parts)


def manual_sections() -> dict[str, str]:
    """The manual split by heading, for the ask-a-senior oracle's verbatim quoting."""
    sections: dict[str, str] = {}
    title: str | None = None
    buffer: list[str] = []
    for line in build_manual().splitlines():
        if line.startswith("## "):
            if title:
                sections[title] = "\n".join(buffer).strip()
            title = line[3:].split(". ", 1)[-1].strip()
            buffer = []
        elif title:
            buffer.append(line)
    if title:
        sections[title] = "\n".join(buffer).strip()
    return sections


def word_count(text: str | None = None) -> int:
    return len((text if text is not None else build_manual()).split())
