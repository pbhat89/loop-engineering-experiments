"""The precedent arm: attribute-matched nearest neighbours, with their correct answers.

Matching is on attributes, not meaning - a weighted sum of band differences over the
fifteen features an underwriter actually searches on. Deterministic, explainable, and
symmetric; the distance of a case to itself is zero. Ties are broken by recency, so the
most recently filed of two equally near cases wins.

The nearest distance is logged for every case, held-out included, so the write-up can
say whether precedent is doing real work or has found a near-twin.
"""
from __future__ import annotations

from pathlib import Path

from src.underwriting.house_rules import CURRENT_YEAR, qualifying_family_events
from src.underwriting.tables import (
    A1C_BANDS,
    BUILD_BANDS,
    DIASTOLIC_BANDS,
    LIPID_RATIO_BANDS,
    MVR_VIOLATION_BANDS,
    SYSTOLIC_BANDS,
    TOBACCO_STATUSES,
    TOTAL_CHOLESTEROL_BANDS,
    band_value,
    income_multiple,
)
from src.utils import append_jsonl, read_jsonl

DEFAULT_K = 3

# Feature -> weight. Ordinal features contribute |band difference| x weight; flags contribute
# the weight when they differ. The scale is arbitrary but fixed: what matters is the ordering.
WEIGHTS: dict[str, float] = {
    "age_band": 1.0,
    "bmi_band": 1.5,
    "tobacco": 2.0,
    "bp_band": 1.5,
    "bp_treated": 1.0,
    "lipid_band": 1.5,
    "a1c_band": 2.0,
    "diabetes": 1.5,
    "family_history": 1.0,
    "occupation_class": 1.5,
    "avocation": 2.5,
    "mvr_band": 1.0,
    "dui_recent": 1.5,
    "sleep_apnea": 1.0,
    "liver": 1.0,
    "face_multiple_band": 1.5,
}
ORDINAL: tuple[str, ...] = (
    "age_band", "bmi_band", "bp_band", "lipid_band", "a1c_band", "occupation_class", "mvr_band",
    "face_multiple_band", "tobacco",
)

AGE_BANDS: tuple[tuple[int, int | None], ...] = ((0, 29), (30, 39), (40, 49), (50, 59), (60, None))
FACE_MULTIPLE_BANDS: tuple[float, ...] = (5.0, 10.0, 15.0, 20.0)


def _band_index(bands, value) -> int:
    for i, band in enumerate(bands):
        low, high = band[0], band[1]
        if (low is None or value >= low) and (high is None or value <= high):
            return i
    return len(bands) - 1


def feature_vector(case: dict) -> dict:
    """The fifteen attributes precedent matches on, as band indices and flags."""
    av = case.get("avocation") or {}
    multiple = float(case["face_amount"]) / max(float(case.get("annual_income") or 1), 1.0)
    return {
        "age_band": _band_index(AGE_BANDS, int(case["age"])),
        "bmi_band": _band_index(BUILD_BANDS, float(case["bmi"])),
        "tobacco": TOBACCO_STATUSES.index(str(case.get("tobacco_declared") or "never")),
        "bp_band": max(
            _band_index(SYSTOLIC_BANDS, int(case["bp_systolic"])),
            _band_index(DIASTOLIC_BANDS, int(case["bp_diastolic"])),
        ),
        "bp_treated": bool(case.get("bp_treated")),
        "lipid_band": max(
            _band_index(TOTAL_CHOLESTEROL_BANDS, int(case["total_cholesterol"])),
            _band_index(LIPID_RATIO_BANDS, float(case["lipid_ratio"])),
        ),
        "a1c_band": _band_index(A1C_BANDS, float(case["a1c"])),
        "diabetes": case.get("diabetes_dx_year") is not None,
        "family_history": bool(qualifying_family_events(case)),
        "occupation_class": "ABC".index(str(case.get("occupation_class") or "A")),
        "avocation": str(av.get("type") or "none"),
        "mvr_band": _band_index(MVR_VIOLATION_BANDS, int(case.get("mvr_violations") or 0)),
        "dui_recent": case.get("dui_year") is not None and (CURRENT_YEAR - int(case["dui_year"])) < 5,
        "sleep_apnea": bool(case.get("sleep_apnea")),
        "liver": str(case.get("liver_enzymes") or "normal") != "normal",
        "face_multiple_band": sum(1 for edge in FACE_MULTIPLE_BANDS if multiple > edge),
    }


def distance(a: dict, b: dict) -> float:
    """Weighted band distance between two feature vectors. Symmetric; zero on self."""
    total = 0.0
    for name, weight in WEIGHTS.items():
        x, y = a.get(name), b.get(name)
        if name in ORDINAL:
            total += weight * abs(int(x) - int(y))
        else:
            total += weight * (0.0 if x == y else 1.0)
    return round(total, 3)


def summarise(case: dict) -> str:
    """A one-line description of a filed case, so the operator can see why it is near."""
    av = str((case.get("avocation") or {}).get("type") or "none")
    bits = [
        f"{case['sex']} {case['age']}",
        f"BMI {float(case['bmi']):.1f}",
        f"BP {case['bp_systolic']}/{case['bp_diastolic']}{' treated' if case.get('bp_treated') else ''}",
        f"TC {case['total_cholesterol']} ratio {float(case['lipid_ratio']):.1f}",
        f"A1c {float(case['a1c']):.1f}{' (T2D)' if case.get('diabetes_dx_year') else ''}",
        f"class {case['occupation_class']}",
        f"avocation {av}",
    ]
    if case.get("sleep_apnea"):
        bits.append("sleep apnea")
    if str(case.get("liver_enzymes") or "normal") != "normal":
        bits.append("raised liver enzymes")
    if case.get("dui_year"):
        bits.append(f"DUI {case['dui_year']}")
    return "; ".join(bits)


class PrecedentFile:
    """Past cases with their correct answers, filed automatically after each training case."""

    # The brief calls this file ``precedent/cases.jsonl``; that collides with the per-arm run log
    # ``<arm>/cases.jsonl`` (also in the brief), because the arm is itself called ``precedent``.
    # Renamed to ``filed_cases.jsonl``; recorded as a deviation in decision D-01.
    FILENAME = "filed_cases.jsonl"

    def __init__(self, root: Path | str):
        self.path = Path(root) / "precedent" / self.FILENAME

    def append(self, case: dict, golden: dict) -> int:
        append_jsonl(
            self.path,
            {
                "case_id": case["case_id"],
                "case_index": int(case["case_index"]),
                "summary": summarise(case),
                "features": feature_vector(case),
                "answer": {
                    "decision": golden["decision"],
                    "rating_class": golden["rating_class"],
                    "modifiers": golden["modifiers"],
                    "drivers": golden["drivers"],
                },
            },
        )
        return 1

    def read_all(self) -> list[dict]:
        return read_jsonl(self.path)

    def nearest(self, case: dict, k: int = DEFAULT_K) -> list[dict]:
        """The ``k`` nearest filed cases. Ties broken by recency (higher case_index first)."""
        target = feature_vector(case)
        scored = [
            {**record, "distance": distance(target, record["features"])}
            for record in self.read_all()
            if record.get("case_id") != case.get("case_id")
        ]
        scored.sort(key=lambda r: (r["distance"], -int(r["case_index"])))
        return scored[: max(int(k), 0)]

    def memory_block(self, case: dict, k: int = DEFAULT_K) -> dict:
        neighbours = self.nearest(case, k)
        return {
            "kind": "precedent",
            "note": (
                "The nearest applications you have already rated, matched on attributes, with the answer the "
                "reviewer settled on. Distance is a weighted count of band differences: lower is nearer."
            ),
            "entries": [
                {"summary": n["summary"], "distance": n["distance"], "correct_answer": n["answer"]}
                for n in neighbours
            ],
            "size": len(neighbours),
            "nearest_distance": neighbours[0]["distance"] if neighbours else None,
        }
