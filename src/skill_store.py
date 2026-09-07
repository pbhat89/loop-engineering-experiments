"""Skill store for claims-skill-loop: parse, list, retrieve, persist, account reuse, archive.

Layout (see ``skills/SKILL_SCHEMA.md``)::

    skills/foundational/*.md                    hand-authored, always visible
    skills/evolved/<run_id>/<skill_id>_v<n>.md  learned skills, visible only to their own run
    skills/archived/<same filename>             archived skills (moved, never edited)
    skills/index.json                           the only mutable record: reuse counts, status

Skill files are immutable: ``persist`` creates files with exclusive-create semantics and
never overwrites; a same-name proposal gets a new ``skill_id`` and the next version number.
``record_reuse`` and ``archive`` touch only ``skills/index.json`` (plus a file *move* for
archive). Index writes take ``skills/.index.lock``.

Retrieval is deterministic and explainable::

    score = TAG_WEIGHT * |task tags ∩ skill tags| + KEYWORD_WEIGHT * |task keywords ∩ skill keywords|

Keywords are lower-cased alphanumeric tokens of length >= ``MIN_KEYWORD_LENGTH`` taken
from the task ``title`` + ``objective`` and from the skill ``trigger`` + ``objective`` +
``tags``, with ``STOP_WORDS`` removed. A term already counted as a tag overlap is not counted
again as a keyword. Ties break on ``skill_id``. Foundational skills are always eligible;
evolved skills only when ``created_after_task_index < current_task_index``. Skills with
score > 0 are returned (top ``k``); if fewer than ``MIN_RESULTS`` qualify the list is padded
with the lowest-id foundational skills at score 0 so the operator always sees two skills.

Nothing in this module executes code, touches the network, or reads credentials.
"""
from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from src.utils import SKILLS_DIR, FileLock, atomic_write_json, ensure_dir, read_json, rel, utc_now

# --------------------------------------------------------------------------- constants

SECTION_ORDER: tuple[str, ...] = (
    "trigger",
    "objective",
    "procedure",
    "required_checks",
    "expected_artifacts",
    "failure_modes",
    "example",
    "provenance",
)
SECTION_HEADINGS: dict[str, str] = {
    "trigger": "Trigger",
    "objective": "Objective",
    "procedure": "Procedure",
    "required_checks": "Required checks",
    "expected_artifacts": "Expected artifacts",
    "failure_modes": "Failure modes",
    "example": "Example",
    "provenance": "Provenance",
}
LIST_SECTIONS: frozenset[str] = frozenset({"procedure", "required_checks", "expected_artifacts", "failure_modes"})
PROSE_SECTIONS: frozenset[str] = frozenset(SECTION_ORDER) - LIST_SECTIONS
OPERATOR_SECTIONS: tuple[str, ...] = SECTION_ORDER[:-1]  # everything but provenance
OPERATOR_SECTION_MAX_CHARS = 1200
REQUIRED_FRONTMATTER: tuple[str, ...] = (
    "skill_id",
    "name",
    "version",
    "status",
    "kind",
    "created_after_task",
    "created_after_task_index",
    "source_feedback_ids",
    "created_at",
    "reuse_count",
    "tags",
    "applicable_task_ids",
)
STATUSES: tuple[str, ...] = ("active", "archived")
KINDS: tuple[str, ...] = ("foundational", "evolved")

TAG_WEIGHT = 2
KEYWORD_WEIGHT = 1
MIN_KEYWORD_LENGTH = 4
MIN_RESULTS = 2
MIN_PROCEDURE_STEPS = 2
MIN_STEP_WORDS = 3

# English function words plus terms that appear in nearly every task and skill of this suite
# (they would add a constant to every score and defeat the "score > 0" filter).
STOP_WORDS: frozenset[str] = frozenset(
    """
    about above after again against almost along already also although always among another
    anything around because been before being below between both cannot could does doing done
    down during each either else even ever every from further have having here hers herself
    himself into itself just least less like made make many might more most much must myself
    need never none only onto other ought ours ourselves over same several shall should since
    some something still such than that their theirs them themselves then there these they this
    those through thus under until upon very were what whatever when whenever where whether
    which while whom whose will with within without would your yours yourself yourselves
    claim claims data dataset datasets task tasks analysis analyses analyse analyze analysed
    analyzed report reports reporting table tables using used uses include includes including
    provide provides produce produces output outputs result results file files column columns
    field fields value values rows record records step steps
    """.split()
)

_ID_RE = re.compile(r"^(foundational_\d{3}|evolved_.+_\d{3})$")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,59}$")
_TAG_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_FRONTMATTER_RE = re.compile(r"\A﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n(.*)\Z", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")
_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*+])\s+(.*\S)\s*$")
_LEADING_MARKER_RE = re.compile(r"^\s*(?:\d+[.)]|[-*+])\s+")
_TOKEN_RE = re.compile(r"[a-z][a-z0-9_]*")
_YAML_BARE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-.]*$")
_YAML_RESERVED = frozenset({"null", "true", "false", "yes", "no", "on", "off", "~"})


class SkillParseError(ValueError):
    """A skill file does not have the frontmatter + sections shape the schema requires."""


# --------------------------------------------------------------------------- data model


@dataclass
class Skill:
    """One parsed skill file. ``sections`` values are prose strings or lists of items."""

    skill_id: str
    name: str
    version: int
    status: str
    kind: str
    created_after_task: str | None
    created_after_task_index: int | None
    source_feedback_ids: list[str]
    created_at: str
    reuse_count: int
    tags: list[str]
    sections: dict[str, str | list[str]]
    path: Path
    applicable_task_ids: list[str] = field(default_factory=list)
    title: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def section_text(self, key: str) -> str:
        value = self.sections.get(key, "")
        return " ".join(value) if isinstance(value, list) else str(value or "")

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "kind": self.kind,
            "created_after_task": self.created_after_task,
            "created_after_task_index": self.created_after_task_index,
            "source_feedback_ids": list(self.source_feedback_ids),
            "created_at": self.created_at,
            "reuse_count": self.reuse_count,
            "tags": list(self.tags),
            "applicable_task_ids": list(self.applicable_task_ids),
            "title": self.title,
            "sections": _copy_sections(self.sections),
            "path": rel(self.path),
            "extra": dict(self.extra),
        }


# --------------------------------------------------------------------------- text helpers


def keywords(text: str) -> set[str]:
    """Lower-cased alphanumeric tokens (length >= MIN_KEYWORD_LENGTH) minus STOP_WORDS."""
    return {t for t in _TOKEN_RE.findall(str(text or "").lower()) if len(t) >= MIN_KEYWORD_LENGTH and t not in STOP_WORDS}


def slugify(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return slug[:60].rstrip("_")


def normalise_tags(tags: Any) -> list[str]:
    """Lower-case snake_case tags, de-duplicated, order preserved."""
    out: list[str] = []
    for tag in tags or []:
        slug = slugify(tag)
        if slug and slug not in out:
            out.append(slug)
    return out


def section_key(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(heading).strip().lower()).strip("_")


def _clean(text: Any) -> str:
    return " ".join(str(text or "").split())


def _clean_item(text: Any) -> str:
    return _clean(_LEADING_MARKER_RE.sub("", str(text or ""), count=1))


def _copy_sections(sections: dict[str, str | list[str]]) -> dict[str, str | list[str]]:
    return {k: (list(v) if isinstance(v, list) else v) for k, v in sections.items()}


def _as_int(value: Any, default: int | None) -> int | None:
    if value is None or isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(v) for v in value]


def _yaml_value(value: Any, *, force_quote: bool = False) -> str:
    """Render one frontmatter value in the flow style used by the foundational skills."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_yaml_value(v) for v in value) + "]"
    text = str(value)
    if not force_quote and _YAML_BARE_RE.match(text) and text.lower() not in _YAML_RESERVED:
        return text
    return json.dumps(text, ensure_ascii=False)


# --------------------------------------------------------------------------- parsing


def parse_sections(body: str) -> tuple[str, dict[str, str | list[str]]]:
    """Split a skill body into (title, sections). ``##`` headings become snake_case keys.

    List sections (``LIST_SECTIONS``) are parsed one item per numbered or bulleted line;
    indented or unmarked continuation lines join the previous item. A list section without
    any item is kept as a prose string (and fails schema validation for ``procedure``).
    Headings inside fenced code blocks are ignored.
    """
    title = ""
    raw: dict[str, list[str]] = {}
    current: str | None = None
    in_fence = False
    for line in body.splitlines():
        stripped = line.rstrip()
        if stripped.lstrip().startswith("```"):
            in_fence = not in_fence
        if not in_fence:
            m2 = _H2_RE.match(stripped)
            if m2:
                current = section_key(m2.group(1))
                raw.setdefault(current, [])
                continue
            m1 = _H1_RE.match(stripped)
            if m1 and current is None:
                if not title:
                    title = m1.group(1).strip()
                continue
        if current is not None:
            raw[current].append(stripped)
    sections: dict[str, str | list[str]] = {}
    for key, lines in raw.items():
        if key in LIST_SECTIONS:
            items = _parse_items(lines)
            sections[key] = items if items else "\n".join(lines).strip()
        else:
            sections[key] = "\n".join(lines).strip()
    return title, sections


def _parse_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        m = _ITEM_RE.match(line)
        if m:
            items.append(m.group(1).strip())
        elif items:
            items[-1] = f"{items[-1]} {line.strip()}"
    return items


def parse_skill_text(text: str, path: Path | str) -> Skill:
    """Parse a skill Markdown document (frontmatter + sections) into a ``Skill``."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise SkillParseError(f"{path}: expected YAML frontmatter between '---' fences followed by a body")
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        raise SkillParseError(f"{path}: invalid YAML frontmatter ({exc})") from exc
    if not isinstance(meta, dict):
        raise SkillParseError(f"{path}: frontmatter must be a mapping")
    title, sections = parse_sections(m.group(2))
    extra = {k: v for k, v in meta.items() if k not in REQUIRED_FRONTMATTER}
    created_after_task = meta.get("created_after_task")
    return Skill(
        skill_id=str(meta.get("skill_id") or ""),
        name=str(meta.get("name") or ""),
        version=_as_int(meta.get("version"), 1) or 1,
        status=str(meta.get("status") or "active"),
        kind=str(meta.get("kind") or ""),
        created_after_task=None if created_after_task is None else str(created_after_task),
        created_after_task_index=_as_int(meta.get("created_after_task_index"), None),
        source_feedback_ids=_as_str_list(meta.get("source_feedback_ids")),
        created_at=str(meta.get("created_at") or ""),
        reuse_count=_as_int(meta.get("reuse_count"), 0) or 0,
        tags=normalise_tags(meta.get("tags")),
        sections=sections,
        path=Path(path),
        applicable_task_ids=_as_str_list(meta.get("applicable_task_ids")),
        title=title,
        extra=extra,
    )


def load_skill_file(path: Path | str) -> Skill:
    p = Path(path)
    return parse_skill_text(p.read_text(encoding="utf-8"), p)


def validate_skill_schema(skill: Skill) -> list[str]:
    """Return schema problems for a parsed skill (empty list means it conforms)."""
    problems: list[str] = []
    if not _ID_RE.match(skill.skill_id):
        problems.append(f"skill_id {skill.skill_id!r} must be foundational_NNN or evolved_<run_id>_NNN")
    if not _NAME_RE.match(skill.name):
        problems.append(f"name {skill.name!r} must be a snake_case slug of 3-60 characters")
    if not isinstance(skill.version, int) or skill.version < 1:
        problems.append(f"version must be an int >= 1, got {skill.version!r}")
    if skill.status not in STATUSES:
        problems.append(f"status must be one of {STATUSES}, got {skill.status!r}")
    if skill.kind not in KINDS:
        problems.append(f"kind must be one of {KINDS}, got {skill.kind!r}")
    if skill.kind == "foundational":
        if skill.created_after_task is not None or skill.created_after_task_index is not None:
            problems.append("foundational skills must have created_after_task and created_after_task_index null")
        if skill.source_feedback_ids:
            problems.append("foundational skills must have empty source_feedback_ids")
    elif skill.kind == "evolved":
        if not skill.created_after_task:
            problems.append("evolved skills must name created_after_task")
        if skill.created_after_task_index is None or skill.created_after_task_index < 0:
            problems.append("evolved skills must have an integer created_after_task_index >= 0")
        if not skill.source_feedback_ids:
            problems.append("evolved skills must cite at least one source feedback id")
    if not skill.created_at:
        problems.append("created_at is required")
    else:
        try:
            datetime.fromisoformat(skill.created_at)
        except ValueError:
            problems.append(f"created_at {skill.created_at!r} is not ISO-8601")
    if not isinstance(skill.reuse_count, int) or skill.reuse_count < 0:
        problems.append("reuse_count must be an int >= 0")
    if not skill.tags:
        problems.append("tags must be a non-empty list")
    bad_tags = [t for t in skill.tags if not _TAG_RE.match(t)]
    if bad_tags:
        problems.append(f"tags must be lower-case snake_case: {bad_tags}")
    for key in SECTION_ORDER:
        value = skill.sections.get(key)
        if value is None:
            problems.append(f"missing section '{SECTION_HEADINGS[key]}'")
            continue
        if key in LIST_SECTIONS:
            if not isinstance(value, list) or not value:
                problems.append(f"section '{SECTION_HEADINGS[key]}' must be a non-empty numbered or bulleted list")
        elif not isinstance(value, str) or not value.strip():
            problems.append(f"section '{SECTION_HEADINGS[key]}' must be non-empty prose")
    procedure = skill.sections.get("procedure")
    if isinstance(procedure, list):
        if len(procedure) < MIN_PROCEDURE_STEPS:
            problems.append(f"procedure needs at least {MIN_PROCEDURE_STEPS} steps, found {len(procedure)}")
        vague = [s for s in procedure if len(s.split()) < MIN_STEP_WORDS]
        if vague:
            problems.append(f"procedure steps must be concrete (>= {MIN_STEP_WORDS} words): {vague}")
    unknown = [k for k in skill.sections if k not in SECTION_ORDER]
    if unknown:
        problems.append(f"unexpected sections: {unknown}")
    return problems


# --------------------------------------------------------------------------- rendering


def render_skill_markdown(
    *,
    skill_id: str,
    name: str,
    version: int,
    tags: list[str],
    proposal: dict,
    provenance: dict,
    created_at: str,
) -> str:
    """Render an evolved skill file in the exact shape ``parse_skill_text`` reads back."""
    run_id = str(provenance.get("run_id") or "")
    task_id = provenance.get("created_after_task") or provenance.get("task_id")
    feedback_ids = _as_str_list(provenance.get("source_feedback_ids")) or _as_str_list(proposal.get("source_feedback_ids"))
    applicable = _as_str_list(proposal.get("applicable_task_ids"))
    frontmatter: list[tuple[str, Any, bool]] = [
        ("skill_id", skill_id, False),
        ("name", name, False),
        ("version", version, False),
        ("status", "active", False),
        ("kind", "evolved", False),
        ("created_after_task", task_id, False),
        ("created_after_task_index", _as_int(provenance.get("created_after_task_index"), None), False),
        ("source_feedback_ids", feedback_ids, False),
        ("created_at", created_at, True),
        ("reuse_count", 0, False),
        ("tags", tags, False),
        ("applicable_task_ids", applicable, False),
        ("run_id", run_id, False),
        ("condition", provenance.get("condition"), False),
    ]
    lines = ["---"]
    for key, value, quote in frontmatter:
        lines.append(f"{key}: {_yaml_value(value, force_quote=quote)}")
    lines += ["---", "", f"# {_title_for(proposal.get('name'), name)}", ""]

    def prose(key: str, fallback: str) -> str:
        return _clean(proposal.get(key)) or fallback

    def items(key: str, fallback: str) -> list[str]:
        cleaned = [_clean_item(x) for x in (proposal.get(key) or []) if _clean_item(x)]
        return cleaned or [fallback]

    score = provenance.get("evaluation_score_total")
    provenance_text = (
        f"Evolved skill learned in run `{run_id}` (condition `{provenance.get('condition')}`) after task "
        f"{task_id} (task index {provenance.get('created_after_task_index')}) from feedback ids "
        f"{', '.join(feedback_ids) if feedback_ids else 'none'}. Evaluation score total at proposal time: "
        f"{'not recorded' if score is None else score}. Proposed by operator `{provenance.get('operator')}` "
        f"via provider mode `{provenance.get('provider_mode')}` (model `{provenance.get('model_identifier')}`). "
        f"Declared applicable task ids: {', '.join(applicable) if applicable else 'none'}."
    )
    body: dict[str, str | list[str]] = {
        "trigger": prose("trigger", "Not provided by the proposer."),
        "objective": prose("objective", "Not provided by the proposer."),
        "procedure": items("procedure", "No procedure steps were provided."),
        "required_checks": items("required_checks", "No required checks were provided by the proposer."),
        "expected_artifacts": items("expected_artifacts", "No expected artifacts were provided by the proposer."),
        "failure_modes": items("failure_modes", "No failure modes were provided by the proposer."),
        "example": prose("example", "No example was provided by the proposer."),
        "provenance": provenance_text,
    }
    for key in SECTION_ORDER:
        lines.append(f"## {SECTION_HEADINGS[key]}")
        value = body[key]
        if isinstance(value, list):
            marker = (lambda i: f"{i}.") if key == "procedure" else (lambda i: "-")
            lines.extend(f"{marker(i)} {item}" for i, item in enumerate(value, 1))
        else:
            lines.append(value)
        lines.append("")
    return "\n".join(lines)


def _title_for(raw_name: Any, slug: str) -> str:
    raw = _clean(raw_name)
    if raw and (" " in raw or raw != raw.lower()):
        return raw
    return slug.replace("_", " ").capitalize()


# --------------------------------------------------------------------------- store


class SkillStore:
    """Read/write access to the skill library for one run (``run_id``) plus the foundational set."""

    def __init__(self, root: Path | str = SKILLS_DIR, run_id: str | None = None, include_foundational: bool = True):
        self.root = Path(root)
        self.run_id = str(run_id) if run_id else None
        # experiment 3 starts from an empty library so every retrieved skill was learned inside the run (D-21)
        self.include_foundational = bool(include_foundational)
        self.foundational_dir = self.root / "foundational"
        self.evolved_dir = self.root / "evolved"
        self.archived_dir = self.root / "archived"
        self.index_path = self.root / "index.json"
        self.lock_path = self.root / ".index.lock"

    # ---- index ----------------------------------------------------------------------
    def read_index(self) -> dict[str, dict]:
        data = read_json(self.index_path, default={})
        return data if isinstance(data, dict) else {}

    def _write_index(self, index: dict[str, dict]) -> None:
        atomic_write_json(self.index_path, dict(sorted(index.items())))

    # ---- loading --------------------------------------------------------------------
    @property
    def run_dir(self) -> Path | None:
        return self.evolved_dir / self.run_id if self.run_id else None

    def skill_files(self) -> list[Path]:
        files: list[Path] = []
        if self.include_foundational and self.foundational_dir.is_dir():
            files.extend(sorted(self.foundational_dir.glob("*.md")))
        if self.run_dir is not None and self.run_dir.is_dir():
            files.extend(sorted(self.run_dir.glob("*.md")))
        return files

    def load(self, path: Path | str, index: dict[str, dict] | None = None) -> Skill:
        """Parse one skill file and overlay the live ``reuse_count``/``status`` from the index."""
        skill = load_skill_file(path)
        entry = (index if index is not None else self.read_index()).get(skill.skill_id)
        if entry:
            skill.reuse_count = _as_int(entry.get("reuse_count"), skill.reuse_count) or 0
            skill.status = str(entry.get("status") or skill.status)
        return skill

    def list_skills(self) -> list[Skill]:
        """Foundational skills plus this run's evolved skills, active only.

        Deterministic order: foundational first, then evolved, each block by ``skill_id``.
        """
        index = self.read_index()
        skills = [self.load(p, index) for p in self.skill_files()]
        return sorted((s for s in skills if s.status != "archived"), key=lambda s: (s.kind != "foundational", s.skill_id))

    def get(self, skill_id: str) -> Skill | None:
        return next((s for s in self.list_skills() if s.skill_id == skill_id), None)

    # ---- retrieval ------------------------------------------------------------------
    @staticmethod
    def is_eligible(skill: Skill, current_task_index: int) -> bool:
        if skill.kind == "foundational":
            return True
        idx = skill.created_after_task_index
        return idx is not None and idx < int(current_task_index)

    @staticmethod
    def score_skill(task_spec: dict, skill: Skill) -> tuple[float, list[str], list[str]]:
        """Return (score, matched_tags, matched_keywords) for one skill against one task."""
        task_tags = set(normalise_tags((task_spec or {}).get("tags")))
        task_terms = keywords(f"{(task_spec or {}).get('title', '')} {(task_spec or {}).get('objective', '')}")
        skill_tags = set(skill.tags)
        matched_tags = sorted(task_tags & skill_tags)
        skill_terms = keywords(f"{skill.section_text('trigger')} {skill.section_text('objective')}") | skill_tags
        matched_keywords = sorted((task_terms & skill_terms) - set(matched_tags))
        score = TAG_WEIGHT * len(matched_tags) + KEYWORD_WEIGHT * len(matched_keywords)
        return float(score), matched_tags, matched_keywords

    def retrieve(self, task_spec: dict, current_task_index: int, k: int = 6) -> list[dict]:
        """Deterministic top-``k`` skills for a task; see the module docstring for the score."""
        ranked: list[tuple[float, Skill, list[str], list[str]]] = []
        for skill in self.list_skills():
            if not self.is_eligible(skill, current_task_index):
                continue
            score, tags_hit, kw_hit = self.score_skill(task_spec, skill)
            ranked.append((score, skill, tags_hit, kw_hit))
        ranked.sort(key=lambda r: (-r[0], r[1].skill_id))
        hits = [self._hit(skill, score, tags_hit, kw_hit) for score, skill, tags_hit, kw_hit in ranked if score > 0][: max(int(k), 0)]
        if len(hits) < MIN_RESULTS:
            seen = {h["skill_id"] for h in hits}
            for _, skill, _, _ in sorted(ranked, key=lambda r: r[1].skill_id):
                if len(hits) >= MIN_RESULTS:
                    break
                if skill.kind == "foundational" and skill.skill_id not in seen:
                    hits.append(self._hit(skill, 0.0, [], []))
                    seen.add(skill.skill_id)
        return hits

    @staticmethod
    def _hit(skill: Skill, score: float, matched_tags: list[str], matched_keywords: list[str]) -> dict:
        return {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "kind": skill.kind,
            "version": skill.version,
            "tags": list(skill.tags),
            "sections": _copy_sections(skill.sections),
            "path": rel(skill.path),
            "score": float(score),
            "matched_terms": list(matched_tags) + list(matched_keywords),
            "matched_tags": list(matched_tags),
            "matched_keywords": list(matched_keywords),
            "created_after_task_index": skill.created_after_task_index,
        }

    @staticmethod
    def render_for_operator(skills: list[dict]) -> list[dict]:
        """Trim retrieval hits to what the operator prompt needs (sections capped per section)."""
        out: list[dict] = []
        for skill in skills or []:
            get = skill.get if isinstance(skill, dict) else (lambda key, _s=skill: getattr(_s, key, None))
            sections = get("sections") or {}
            out.append(
                {
                    "skill_id": get("skill_id"),
                    "name": get("name"),
                    "kind": get("kind"),
                    "version": get("version"),
                    "tags": list(get("tags") or []),
                    "sections": {
                        key: _trim(sections[key], OPERATOR_SECTION_MAX_CHARS) for key in OPERATOR_SECTIONS if key in sections
                    },
                }
            )
        return out

    # ---- persistence ----------------------------------------------------------------
    def next_skill_id(self, run_id: str, index: dict[str, dict] | None = None) -> str:
        return f"evolved_{run_id}_{self._next_sequence(run_id, index if index is not None else self.read_index()):03d}"

    def _next_sequence(self, run_id: str, index: dict[str, dict]) -> int:
        pattern = re.compile(rf"^evolved_{re.escape(run_id)}_(\d{{3}})(?:_v\d+)?$")
        highest = 0
        candidates = list(index.keys())
        run_dir = self.evolved_dir / run_id
        if run_dir.is_dir():
            candidates.extend(p.stem for p in run_dir.glob("*.md"))
        if self.archived_dir.is_dir():
            candidates.extend(p.stem for p in self.archived_dir.glob(f"evolved_{run_id}_*.md"))
        for candidate in candidates:
            m = pattern.match(candidate)
            if m:
                highest = max(highest, int(m.group(1)))
        return highest + 1

    def _next_version(self, run_id: str, name: str, index: dict[str, dict]) -> int:
        highest = 0
        for entry in index.values():
            if entry.get("run_id") == run_id and entry.get("name") == name:
                highest = max(highest, _as_int(entry.get("version"), 0) or 0)
        run_dir = self.evolved_dir / run_id
        if run_dir.is_dir():
            for p in run_dir.glob("*.md"):
                try:
                    existing = load_skill_file(p)
                except (SkillParseError, OSError):
                    continue
                if existing.name == name:
                    highest = max(highest, existing.version)
        return highest + 1

    def persist(self, proposal: dict, provenance: dict) -> Skill:
        """Write an accepted proposal as a new immutable evolved skill file and register it."""
        if hasattr(proposal, "model_dump"):
            proposal = proposal.model_dump()
        provenance = dict(provenance or {})
        run_id = str(provenance.get("run_id") or self.run_id or "").strip()
        if not run_id:
            raise ValueError("persist: a run_id is required (provenance['run_id'] or SkillStore(run_id=...))")
        provenance["run_id"] = run_id
        name = slugify(proposal.get("name"))
        if len(name) < 3:
            raise ValueError(f"persist: proposal name {proposal.get('name')!r} does not yield a usable slug")
        tags = normalise_tags(proposal.get("tags")) or ["evolved"]
        run_dir = ensure_dir(self.evolved_dir / run_id)
        created_at = utc_now()
        with FileLock(self.lock_path):
            index = self.read_index()
            sequence = self._next_sequence(run_id, index)
            version = self._next_version(run_id, name, index)
            skill_id = f"evolved_{run_id}_{sequence:03d}"
            path = run_dir / f"{skill_id}_v{version}.md"
            text = render_skill_markdown(
                skill_id=skill_id,
                name=name,
                version=version,
                tags=tags,
                proposal=proposal,
                provenance=provenance,
                created_at=created_at,
            )
            # Exclusive create: an existing file is never overwritten.
            with open(path, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            index[skill_id] = {
                "reuse_count": 0,
                "reused_in": [],
                "status": "active",
                "path": rel(path),
                "name": name,
                "version": version,
                "kind": "evolved",
                "run_id": run_id,
                "condition": provenance.get("condition"),
                "created_after_task": provenance.get("created_after_task") or provenance.get("task_id"),
                "created_after_task_index": _as_int(provenance.get("created_after_task_index"), None),
                "source_feedback_ids": _as_str_list(provenance.get("source_feedback_ids")) or _as_str_list(proposal.get("source_feedback_ids")),
                "created_at": created_at,
            }
            self._write_index(index)
        return self.load(path, index)

    # ---- reuse accounting and archive -----------------------------------------------
    def record_reuse(self, skill_id: str, task_id: str) -> None:
        """Increment the live reuse count in ``skills/index.json``; the skill file is untouched."""
        with FileLock(self.lock_path):
            index = self.read_index()
            entry = index.setdefault(skill_id, {"reuse_count": 0, "reused_in": [], "status": "active"})
            entry["reuse_count"] = (_as_int(entry.get("reuse_count"), 0) or 0) + 1
            reused_in = list(entry.get("reused_in") or [])
            reused_in.append(str(task_id))
            entry["reused_in"] = reused_in
            entry.setdefault("status", "active")
            if "path" not in entry:
                skill = self.get(skill_id)
                if skill is not None:
                    entry["path"] = rel(skill.path)
                    entry["kind"] = skill.kind
                    entry["name"] = skill.name
                    entry["version"] = skill.version
            entry["last_reused_at"] = utc_now()
            self._write_index(index)

    def archive(self, skill_id: str, reason: str) -> Path:
        """Move a visible skill file to ``skills/archived/`` unchanged and mark the index."""
        skill = self.get(skill_id)
        if skill is None:
            raise KeyError(f"archive: skill {skill_id!r} is not visible to this store (run_id={self.run_id!r})")
        ensure_dir(self.archived_dir)
        destination = self.archived_dir / skill.path.name
        if destination.exists():
            raise FileExistsError(f"archive: {destination} already exists; archived files are never overwritten")
        with FileLock(self.lock_path):
            shutil.move(str(skill.path), str(destination))
            index = self.read_index()
            entry = index.setdefault(skill_id, {"reuse_count": 0, "reused_in": []})
            entry.update(
                {
                    "status": "archived",
                    "previous_path": rel(skill.path),
                    "path": rel(destination),
                    "archived_at": utc_now(),
                    "archive_reason": str(reason),
                    "name": skill.name,
                    "version": skill.version,
                    "kind": skill.kind,
                }
            )
            self._write_index(index)
        return destination

    def purge_run(self, run_id: str) -> list[str]:
        """Housekeeping only: delete a run's evolved directory and drop its index entries.

        Meant for throw-away check runs and test cleanup, never for the experiment itself
        (experiment runs keep their skills; ``archive`` is the in-experiment retirement path).
        """
        prefix = f"evolved_{run_id}_"
        with FileLock(self.lock_path):
            index = self.read_index()
            removed = sorted(sid for sid, entry in index.items() if sid.startswith(prefix) or entry.get("run_id") == run_id)
            for sid in removed:
                index.pop(sid, None)
            self._write_index(index)
            run_dir = self.evolved_dir / run_id
            if run_dir.is_dir():
                shutil.rmtree(run_dir)
        return removed


def _trim(value: str | list[str], limit: int) -> str | list[str]:
    if isinstance(value, list):
        out: list[str] = []
        used = 0
        for item in value:
            item = str(item)
            if used + len(item) > limit:
                remaining = limit - used
                if remaining > 1:
                    out.append(item[: remaining - 1] + "…")
                break
            out.append(item)
            used += len(item)
        return out
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"
