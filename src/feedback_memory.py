"""Raw cross-task memory for the experiment-4 memory arms (decision D-22).

A ``FeedbackMemory`` is a plain append-only JSONL log per run and condition at
``artifacts/memory/<run_id>/<condition>.jsonl``. After each task the arm appends
the findings it was shown verbatim - the checker's for ``feedback_memory``, the
operator's own review findings for ``self_refine_memory`` - and before planning a
later task the whole log is recalled, most recent first, capped.

This is deliberately dumber than the skill loop: nothing is distilled, rewritten,
scored for relevance or deduplicated. It is the control that separates "carrying
comments forward" from "learning a reusable procedure". No IO beyond that one
file, no secrets, no network.

Experiment 5 (decision D-23) adds :meth:`FeedbackMemory.seed`: a new run's log can start
from an earlier run's records so a *warm* arm can be compared against a cold one. The
caller redacts the records first (see :func:`redact_numbers`, which is what the runner and
``scripts/seed_audit.py`` both use) and each seeded record is stamped with ``seeded_from``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from src.utils import ARTIFACTS_DIR, ensure_dir, utc_now

MEMORY_ROOT = ARTIFACTS_DIR / "memory"  # <run_id>/<condition>.jsonl
DETAIL_MAX_CHARS = 240
RECALL_LIMIT = 30

# Redaction for seeded memory (experiment 5, D-23). Every numeric token in a carried-over note is replaced by
# `[n]`, so a warm arm inherits the *conventions* the checker taught it and never a value from a held-out
# golden. Task ids (`T3`, `T10`) and the quantile names `p90` / `p99` survive: they name things, not results.
# The rule is `\d[\d,]*(?:\.\d+)?%?`, with two refinements: a percent sign one space after the number is
# swallowed with it ("10.42 %" -> "[n]", not "[n] %"), and a trailing comma is not ("n: 241," keeps its comma).
NUMBER_RE = re.compile(r"\d(?:[\d,]*\d)?(?:\.\d+)?(?:\s?%)?")
PROTECTED_RE = re.compile(r"T\d+|p90|p99")
REDACTION = "[n]"
SEEDED_TEXT_FIELDS = ("text", "detail")


def _protected_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in PROTECTED_RE.finditer(text)]


def number_tokens(text: object) -> list[str]:
    """Every numeric token in ``text``, skipping task ids and p90/p99 - the redaction rule's own alphabet."""
    if text is None:
        return []
    s = str(text)
    spans = _protected_spans(s)
    return [m.group(0) for m in NUMBER_RE.finditer(s) if not any(a <= m.start() < b for a, b in spans)]


def redact_numbers(text: object) -> tuple[object, int]:
    """Replace every numeric token in ``text`` with ``[n]``; returns (redacted, tokens replaced)."""
    if text is None:
        return None, 0
    s = str(text)
    spans = _protected_spans(s)
    out: list[str] = []
    cursor = replaced = 0
    for m in NUMBER_RE.finditer(s):
        if any(a <= m.start() < b for a, b in spans):
            continue
        out.append(s[cursor:m.start()])
        out.append(REDACTION)
        cursor = m.end()
        replaced += 1
    out.append(s[cursor:])
    return "".join(out), replaced


def redact_record(record: dict) -> tuple[dict, int]:
    """A copy of ``record`` with ``text`` and ``detail`` redacted; returns (record, tokens replaced)."""
    out = dict(record)
    replaced = 0
    for field in SEEDED_TEXT_FIELDS:
        if out.get(field) is not None:
            out[field], k = redact_numbers(out[field])
            replaced += k
    return out, replaced


class FeedbackMemory:
    """Append-only per-condition log of past findings, stored as JSONL."""

    def __init__(self, root: Path | str, run_id: str, condition: str):
        self.root = Path(root)
        self.run_id = run_id
        self.condition = condition
        self.path = self.root / run_id / f"{condition}.jsonl"

    # ---- write -----------------------------------------------------------------------
    def append(self, task_id: str, task_title: str, items: list[dict]) -> int:
        """Append one compact record per finding; returns how many were written."""
        records = [self._record(task_id, task_title, item) for item in items or []]
        if not records:
            return 0
        ensure_dir(self.path.parent)
        with open(self.path, "a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return len(records)

    @staticmethod
    def _record(task_id: str, task_title: str, item: dict) -> dict:
        """One finding, verbatim apart from the truncated ``detail``."""
        source = "self" if item.get("source") == "self" else "checker"
        record = {
            "task_id": task_id,
            "task_title": task_title,
            "attempt": item.get("attempt") or item.get("first_seen_attempt"),
            "source": source,
            "severity": item.get("severity"),
            "criterion": item.get("criterion"),
            "text": item.get("remediation") if source == "checker" else item.get("issue"),
            "detail": _trim(item.get("detail")),
            "written_at": utc_now(),
        }
        if item.get("verdict") is not None:
            record["verdict"] = item["verdict"]
        return record

    def seed(self, records: list[dict]) -> int:
        """Append already-redacted records from an earlier run, each stamped ``seeded_from: <run_id>``.

        The caller owns the redaction (``redact_record``); this method only records provenance and writes.
        Returns how many records were written.
        """
        rows = [{**r, "seeded_from": str(r.get("seeded_from") or r.get("source_run") or "unknown")} for r in records or []]
        if not rows:
            return 0
        ensure_dir(self.path.parent)
        with open(self.path, "a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        return len(rows)

    # ---- read ------------------------------------------------------------------------
    def read_all(self) -> list[dict]:
        """Every record in write order; a missing or unreadable line is skipped, never fatal."""
        if not self.path.is_file():
            return []
        out: list[dict] = []
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                out.append(record)
        return out

    def recall(self, exclude_task_id: str, limit: int = RECALL_LIMIT) -> list[dict]:
        """Records from tasks other than ``exclude_task_id``, most recent first, capped at ``limit``."""
        others = [r for r in self.read_all() if r.get("task_id") != exclude_task_id]
        return list(reversed(others))[: max(int(limit), 0)]


def _trim(value: object, limit: int = DETAIL_MAX_CHARS) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"
