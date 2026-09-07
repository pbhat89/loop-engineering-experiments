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
"""
from __future__ import annotations

import json
from pathlib import Path

from src.utils import ARTIFACTS_DIR, ensure_dir, utc_now

MEMORY_ROOT = ARTIFACTS_DIR / "memory"  # <run_id>/<condition>.jsonl
DETAIL_MAX_CHARS = 240
RECALL_LIMIT = 30


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
