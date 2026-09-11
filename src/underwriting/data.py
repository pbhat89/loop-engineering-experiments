"""Build, freeze and load the experiment-7 data pack.

    python -m src.underwriting.data build    # regenerate data/underwriting/* and the freeze manifest
    python -m src.underwriting.data verify   # re-derive and compare; exits 1 on any drift

Four files are frozen, hashed the same way the claims experiment hashes its golden pack
(``src/run_experiment.py::build_freeze_manifest``):

    starter_manual.md     what every arm is handed, every request
    house_rules.json      never shown to an operator
    cases.json            the 38 applications, no golden fields
    goldens.json          the answers, the fired rule ids and the derived tiers

``cases.json`` and ``goldens.json`` are separate files on purpose: the runner loads the
cases to build a request and the goldens only after the answer is in.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.underwriting.cases import build_dataset, sanity
from src.underwriting.house_rules import house_rules_records
from src.underwriting.manual import build_manual
from src.utils import DATA_DIR, atomic_write_json, atomic_write_text, read_json, sha256_file, sha256_text, utc_now

UW_DATA_DIR = DATA_DIR / "underwriting"
MANUAL_PATH = UW_DATA_DIR / "starter_manual.md"
HOUSE_RULES_PATH = UW_DATA_DIR / "house_rules.json"
CASES_PATH = UW_DATA_DIR / "cases.json"
GOLDENS_PATH = UW_DATA_DIR / "goldens.json"
FREEZE_PATH = UW_DATA_DIR / "freeze_manifest.json"

FROZEN_FILES: tuple[Path, ...] = (MANUAL_PATH, HOUSE_RULES_PATH, CASES_PATH, GOLDENS_PATH)


# --------------------------------------------------------------------------- build


def build(write: bool = True) -> dict:
    """Regenerate every frozen file from code. Returns the freeze manifest."""
    cases, goldens = build_dataset()
    problems = sanity(cases, goldens)
    if problems:
        raise RuntimeError("case schedule violated:\n  " + "\n  ".join(problems))
    if write:
        UW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write_text(MANUAL_PATH, build_manual())
        atomic_write_json(HOUSE_RULES_PATH, {"rules": house_rules_records()})
        atomic_write_json(CASES_PATH, {"seed": 42, "cases": cases})
        atomic_write_json(GOLDENS_PATH, {"goldens": goldens})
    return build_freeze_manifest(write=write)


def build_freeze_manifest(write: bool = True) -> dict:
    entries = {p.name: sha256_file(p) for p in FROZEN_FILES if p.exists()}
    manifest = {
        "experiment": "experiment-7-underwriting-apprentice",
        "frozen_at": utc_now(),
        "files": entries,
        "freeze_sha256": sha256_text(json.dumps(entries, sort_keys=True)),
    }
    if write:
        atomic_write_json(FREEZE_PATH, manifest)
    return manifest


def verify_freeze() -> tuple[str, list[str]]:
    """(freeze_sha256, drift messages). Drift = a missing manifest, or any changed/added/removed file."""
    stored = read_json(FREEZE_PATH, default=None)
    if not stored:
        return "", [f"{FREEZE_PATH.name} does not exist - run `python -m src.underwriting.data build`"]
    current = build_freeze_manifest(write=False)["files"]
    drift = [f"changed or added: {name}" for name, digest in current.items() if stored["files"].get(name) != digest]
    drift += [f"removed: {name}" for name in stored["files"] if name not in current]
    return stored.get("freeze_sha256", ""), drift


def verify_regeneration() -> list[str]:
    """Re-derive everything from code and compare with what is on disk."""
    problems: list[str] = []
    if build_manual() != MANUAL_PATH.read_text(encoding="utf-8"):
        problems.append("starter_manual.md differs from build_manual()")
    if {"rules": house_rules_records()} != read_json(HOUSE_RULES_PATH, default={}):
        problems.append("house_rules.json differs from house_rules_records()")
    cases, goldens = build_dataset()
    if cases != (read_json(CASES_PATH, default={}) or {}).get("cases"):
        problems.append("cases.json differs from build_dataset()")
    if goldens != (read_json(GOLDENS_PATH, default={}) or {}).get("goldens"):
        problems.append("goldens.json differs from build_dataset()")
    problems.extend(sanity(cases, goldens))
    return problems


# --------------------------------------------------------------------------- load


def load_manual() -> str:
    return MANUAL_PATH.read_text(encoding="utf-8")


def load_house_rules() -> list[dict]:
    return list((read_json(HOUSE_RULES_PATH, default={}) or {}).get("rules") or [])


def load_cases(phase: str | None = None) -> list[dict]:
    cases = list((read_json(CASES_PATH, default={}) or {}).get("cases") or [])
    return [c for c in cases if phase is None or c["phase"] == phase]


def load_goldens(phase: str | None = None) -> list[dict]:
    goldens = list((read_json(GOLDENS_PATH, default={}) or {}).get("goldens") or [])
    return [g for g in goldens if phase is None or g["phase"] == phase]


def goldens_by_case_id() -> dict[str, dict]:
    return {g["case_id"]: g for g in load_goldens()}


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("build", "verify"))
    args = ap.parse_args(argv)
    if args.command == "build":
        manifest = build(write=True)
        cases = load_cases()
        print(f"wrote {len(FROZEN_FILES)} files to {UW_DATA_DIR.as_posix()}")
        print(f"cases: {sum(1 for c in cases if c['phase'] == 'train')} train, "
              f"{sum(1 for c in cases if c['phase'] == 'holdout')} holdout")
        print(f"freeze_sha256: {manifest['freeze_sha256']}")
        return 0
    digest, drift = verify_freeze()
    problems = verify_regeneration()
    for line in drift + problems:
        print(f"DRIFT: {line}")
    print(f"freeze_sha256: {digest}")
    print("underwriting data pack clean" if not (drift or problems) else f"{len(drift) + len(problems)} problem(s)")
    return 1 if (drift or problems) else 0


if __name__ == "__main__":
    sys.exit(main())
