"""Leakage audit for a seeded run (experiment 5, decision D-23).

    uv run python scripts/seed_audit.py --run-id run_007 --holdout T9,T10,T5,T6

A warm arm may inherit the *conventions* an earlier run learned; it must never inherit a value from a golden
file of a task it has not attempted yet. This script is that check:

1. It loads everything the new run was seeded with -- every record carrying ``seeded_from`` in
   ``artifacts/memory/<run_id>/*.jsonl``, and the full text of every evolved skill file the run can read from
   its seed run (``skills/evolved/<seed_run>/*.md``; the seed run comes from the ``seeding`` block of
   ``logs/runs/<run_id>.json``). It also loads the seed run's *unredacted* memory as the "before" state.
2. It extracts numeric tokens with the redaction rule's own regex (``src.feedback_memory.number_tokens``) from
   both states, so a bug in the redaction shows up as a token that survived into the seeded text.
3. It compares them against every number in the holdout goldens, each rendered with and without thousands
   separators and rounded to 2-6 decimal places.

Materiality: a golden pack contains 0, 1, 30, 42 and 0.25, and a skill's frontmatter contains ``version: 1``,
so a bare "any digit matches" comparison is all noise. A golden number counts as leakable when it carries at
least ``MIN_SIGNIFICANT_DIGITS`` significant digits -- when reproducing it would mean reproducing a *result*
rather than restating a convention or a parameter. The rule is printed with the report so a reader can judge it.

Exit code 1 with the offending items printed if any material golden number is reachable from the seeded
material; otherwise "seed audit clean". Read-only: this script never writes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.feedback_memory import MEMORY_ROOT, number_tokens  # noqa: E402
from src.utils import GOLDENS_DIR, LOGS_DIR, SKILLS_DIR, read_json, read_yaml, rel  # noqa: E402

MIN_SIGNIFICANT_DIGITS = 3
ROUNDINGS = range(2, 7)
TEXT_FIELDS = ("text", "detail")
# provenance of the golden file itself, not analysis results
SKIPPED_GOLDEN_KEYS = frozenset({"built_at", "builder", "data_sha256", "dataset_revision", "golden_version", "task_id"})


# --------------------------------------------------------------------------- numbers
def significant_digits(value: float) -> int:
    value = float(value)
    if value.is_integer():
        digits = str(abs(int(value)))
    else:
        digits = f"{abs(value):.10f}".rstrip("0").replace(".", "")
    return len(digits.lstrip("0").rstrip("0")) or 1


def is_material(value: float) -> bool:
    v = float(value)
    if v != v or v in (float("inf"), float("-inf")):  # NaN / inf
        return False
    return significant_digits(v) >= MIN_SIGNIFICANT_DIGITS


def parse_token(token: str) -> float | None:
    try:
        return float(token.replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


def golden_numbers(path: Path) -> dict[float, list[str]]:
    """Every material number in one golden file, mapped to where it appears."""
    data = read_yaml(path) if path.suffix in (".yaml", ".yml") else read_json(path, default={})
    out: dict[float, list[str]] = {}

    def add(value: float, where: str) -> None:
        if is_material(value):
            out.setdefault(float(value), []).append(where)

    def walk(node: object, where: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in SKIPPED_GOLDEN_KEYS:
                    continue
                path_here = f"{where}.{k}" if where else str(k)
                for token in number_tokens(k):  # numbers used as keys (segment values, place-of-service codes)
                    parsed = parse_token(token)
                    if parsed is not None:
                        add(parsed, f"{path_here} (key)")
                walk(v, path_here)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")
        elif isinstance(node, bool):
            return
        elif isinstance(node, (int, float)):
            add(float(node), where)
        elif isinstance(node, str):
            for token in number_tokens(node):  # numbers spelled out inside definitions
                parsed = parse_token(token)
                if parsed is not None:
                    add(parsed, f"{where} (in text)")

    walk(data, "")
    return out


def renderings(value: float) -> set[str]:
    """The string forms a note could plausibly use for ``value``: plain, thousands-separated, 2-6 dp."""
    forms: set[str] = set()
    candidates = [float(value)] + ([] if float(value).is_integer() else [round(float(value), dp) for dp in ROUNDINGS])
    for v in candidates:
        forms.add(str(int(v)) if float(v).is_integer() else repr(float(v)))
        forms.add(f"{v:,.0f}" if float(v).is_integer() else f"{v:,}")
        for dp in ROUNDINGS:
            forms.add(f"{v:.{dp}f}")
            forms.add(f"{v:,.{dp}f}")
    return {f for f in forms if f}


# --------------------------------------------------------------------------- seeded material
def _note_texts(path: Path, *, seeded_only: bool, warnings: list[str]) -> list[dict]:
    items: list[dict] = []
    kept = 0
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            warnings.append(f"{rel(path)}:{i} is not valid JSON; skipped")
            continue
        if not isinstance(record, dict):
            continue
        if seeded_only and not record.get("seeded_from"):
            continue  # notes this run wrote itself are not carried-over material
        kept += 1
        for field in TEXT_FIELDS:
            if record.get(field):
                items.append({"origin": f"{rel(path)}:{i}", "field": field, "text": str(record[field])})
    if seeded_only and kept == 0:
        warnings.append(f"{rel(path)} holds no seeded records")
    return items


def collect(run_id: str) -> tuple[list[dict], list[dict], list[str]]:
    """(as-seeded items, pre-redaction items, warnings). Each item: {origin, field, text}."""
    warnings: list[str] = []
    manifest = LOGS_DIR / "runs" / f"{run_id}.json"
    run = read_json(manifest, default=None) or {}
    if not run:
        warnings.append(f"no run manifest at {rel(manifest)}; auditing the files on disk only")
    seeding = run.get("seeding") or {}
    seed_run = seeding.get("source_run") or (run.get("config") or {}).get("seed_from_run")

    seeded: list[dict] = []
    memory_dir = MEMORY_ROOT / run_id
    for path in sorted(memory_dir.glob("*.jsonl")) if memory_dir.is_dir() else []:
        seeded += _note_texts(path, seeded_only=True, warnings=warnings)
    if not memory_dir.is_dir():
        warnings.append(f"no memory directory at {rel(memory_dir)}")

    before: list[dict] = []
    if seed_run:
        source_dir = MEMORY_ROOT / seed_run
        # only the logs this run actually seeded from; the seed run's other arms were not carried over
        seeded_conditions = sorted((seeding.get("memory") or {}).keys())
        sources = [source_dir / f"{c}.jsonl" for c in seeded_conditions] or sorted(source_dir.glob("*.jsonl"))
        for path in sources:
            if path.is_file():
                before += _note_texts(path, seeded_only=False, warnings=warnings)
            else:
                warnings.append(f"seed source {rel(path)} does not exist")

    excluded = set((seeding.get("skills") or {}).get("excluded_skill_ids") or [])
    skill_dir = SKILLS_DIR / "evolved" / seed_run if seed_run else None
    if skill_dir is not None and skill_dir.is_dir():
        for path in sorted(skill_dir.glob("*.md")):
            if any(path.stem.startswith(sid) for sid in excluded):
                warnings.append(f"{rel(path)} is excluded from seeding by seed_skill_exclude; not audited")
                continue
            seeded.append({"origin": rel(path), "field": "skill file", "text": path.read_text(encoding="utf-8", errors="replace")})
    elif seed_run:
        warnings.append(f"no seeded skill directory at skills/evolved/{seed_run}")
    else:
        warnings.append("no seed run recorded; no skill files audited")
    return seeded, before, warnings


# --------------------------------------------------------------------------- audit
def _matches(items: list[dict], lookup: dict[str, list[tuple[float, str, str]]]) -> tuple[list[str], int]:
    found: list[str] = []
    n_tokens = 0
    for item in items:
        for token in number_tokens(item["text"]):
            n_tokens += 1
            parsed = parse_token(token)
            keys = {token, token.replace("%", "").strip()}
            if parsed is not None:
                keys.add(str(int(parsed)) if float(parsed).is_integer() else repr(parsed))
            for key in keys:
                for value, gpath, where in lookup.get(key, []):
                    found.append(f"{item['origin']} [{item['field']}]: token {token!r} matches {gpath} {where} = {value!r}")
    return list(dict.fromkeys(found)), n_tokens


def audit(run_id: str, holdout: list[str]) -> int:
    goldens: dict[str, dict[float, list[str]]] = {}
    missing: list[str] = []
    for tid in holdout:
        paths = sorted(GOLDENS_DIR.glob(f"{tid}_*.json")) + sorted(GOLDENS_DIR.glob(f"{tid}_*.yaml"))
        if not paths:
            missing.append(tid)
        for path in paths:
            goldens[rel(path)] = golden_numbers(path)
    if missing:
        print(f"seed audit cannot run: no golden file for {', '.join(missing)}")
        return 1

    lookup: dict[str, list[tuple[float, str, str]]] = {}
    n_numbers = 0
    for gpath, numbers in goldens.items():
        n_numbers += len(numbers)
        for value, wheres in numbers.items():
            for form in renderings(value):
                lookup.setdefault(form, []).append((value, gpath, wheres[0]))

    seeded, before, warnings = collect(run_id)
    offences, n_seeded_tokens = _matches(seeded, lookup)
    prevented, n_before_tokens = _matches(before, lookup)

    print(f"seed audit for run {run_id}")
    print(f"  holdout goldens        : {', '.join(sorted(goldens))}")
    print(f"  material golden numbers: {n_numbers} (at least {MIN_SIGNIFICANT_DIGITS} significant digits)")
    print(f"  string forms compared  : {len(lookup)} (plain, thousands-separated, rounded to "
          f"{ROUNDINGS.start}-{ROUNDINGS.stop - 1} dp)")
    print(f"  seeded material        : {sum(1 for i in seeded if i['field'] == 'skill file')} skill file(s), "
          f"{sum(1 for i in seeded if i['field'] != 'skill file')} seeded note field(s); "
          f"{n_seeded_tokens} numeric tokens")
    print(f"  seed run before redaction: {len(before)} note field(s); {n_before_tokens} numeric tokens, "
          f"{len(prevented)} of which reach a holdout golden")
    for w in warnings:
        print(f"  note: {w}")
    if prevented:
        print("\n  golden numbers the redaction removed (informational, not a failure):")
        for o in prevented[:20]:
            print(f"    {o}")
        if len(prevented) > 20:
            print(f"    ... and {len(prevented) - 20} more")
    if offences:
        print(f"\nSEED AUDIT FAILED - {len(offences)} golden number(s) reachable from the seeded material:")
        for o in offences:
            print(f"  {o}")
        return 1
    print("\nseed audit clean")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--holdout", required=True, help="comma-separated task ids whose goldens must not be reachable")
    args = ap.parse_args(argv)
    holdout = [t.strip() for t in args.holdout.split(",") if t.strip()]
    return audit(args.run_id, holdout)


if __name__ == "__main__":
    raise SystemExit(main())
