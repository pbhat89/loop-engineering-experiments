"""What the notebook and written-rules arms keep between cases.

Both stores follow the raw-log shape of ``src/feedback_memory.py``: one append-only file
per run and arm under ``artifacts/uw/<run_id>/``, nothing distilled by code.

``Notebook``  the markups as written, newest first, all of them (thirty at most).
``RuleBook``  one markdown file the operator rewrites itself, plus a version history.

Neither store reads a golden, and neither writes anything in the held-out phase.
"""
from __future__ import annotations

from pathlib import Path

from src.utils import append_jsonl, atomic_write_text, ensure_dir, read_jsonl

RULEBOOK_MAX_ENTRIES = 25
EMPTY_RULEBOOK = (
    "# House rule book\n\n"
    "_Nothing written yet. Add an entry only when a reviewer has corrected you._\n"
)


class Notebook:
    """Every markup this arm has been given, appended verbatim."""

    def __init__(self, root: Path | str):
        self.path = Path(root) / "notebook" / "markups.jsonl"

    def append(self, case_index: int, case_id: str, markup: str, written_at: str) -> int:
        append_jsonl(self.path, {"case_index": int(case_index), "case_id": case_id, "markup": markup, "written_at": written_at})
        return 1

    def read_all(self) -> list[dict]:
        return read_jsonl(self.path)

    def recall(self, exclude_case_id: str | None = None) -> list[dict]:
        """Newest first; the case being decided is never in its own memory."""
        records = [r for r in self.read_all() if r.get("case_id") != exclude_case_id]
        return list(reversed(records))

    def memory_block(self, exclude_case_id: str | None = None) -> dict:
        records = self.recall(exclude_case_id)
        return {
            "kind": "notebook",
            "note": (
                "Reviewer markups from earlier applications in this run, newest first, exactly as written. "
                "They may or may not apply to the file in front of you."
            ),
            "entries": [{"markup": r["markup"]} for r in records],
            "size": len(records),
        }


class RuleBook:
    """The written-rules arm's own house-rule book, rewritten by a reflection call each case."""

    def __init__(self, root: Path | str):
        self.dir = Path(root) / "written_rules"
        self.path = self.dir / "rulebook.md"
        self.history = self.dir / "history"

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8") if self.path.is_file() else EMPTY_RULEBOOK

    def version(self) -> int:
        return len(sorted(self.history.glob("v*.md"))) if self.history.is_dir() else 0

    def write(self, markdown: str) -> int:
        text = (markdown or "").strip() or EMPTY_RULEBOOK
        ensure_dir(self.dir)
        ensure_dir(self.history)
        version = self.version() + 1
        atomic_write_text(self.history / f"v{version:02d}.md", text + "\n")
        atomic_write_text(self.path, text + "\n")
        return version

    def memory_block(self) -> dict:
        text = self.read()
        return {
            "kind": "written_rules",
            "note": (
                "Your own house-rule book, as you last rewrote it. Everything in it came from reviewer "
                f"corrections on earlier applications in this run. At most {RULEBOOK_MAX_ENTRIES} entries."
            ),
            "rulebook_markdown": text,
            "size": len([line for line in text.splitlines() if line.strip().startswith(("-", "*", "#"))]),
        }
