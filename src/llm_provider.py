"""Provider adapter for the LLM-decision nodes.

Three modes, selected by ``CLAIMS_SKILL_LOOP_LLM_MODE``:

* ``manual`` (default) - the study mode. No model call is made by this process.
  ``decide()`` raises a LangGraph ``interrupt`` carrying the operator request; the
  graph checkpoints and pauses. The lead writes the request to a JSON file, a
  stateless ``experiment-operator`` subagent writes the response file, and the
  runner resumes the thread with ``Command(resume=<response dict>)``.
* ``stub`` - ``FixtureProvider`` answers the same requests deterministically from
  the request payload with simple rules. It exists to test the graph, logs,
  dashboard, and file lifecycle without any model; every record it produces is
  labelled ``deterministic-fixture`` and must never be reported as an LLM result.
* ``anthropic_api`` - optional, not used in this study. Instantiates
  ``langchain_anthropic.ChatAnthropic`` only in this mode and fails closed with
  a clear error when ``ANTHROPIC_API_KEY`` is absent.

This module never reads Claude Code session credentials, never spawns the
``claude`` CLI, and never logs an API key.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.graph_state import LLM_DECISION_NODES, response_schema_for
from src.utils import ARTIFACTS_DIR, atomic_write_json, ensure_dir, read_json, sha256_text, utc_now

MODE_ENV = "CLAIMS_SKILL_LOOP_LLM_MODE"
MODEL_ENV = "CLAIMS_SKILL_LOOP_MODEL"
OPERATOR_ENV = "CLAIMS_SKILL_LOOP_OPERATOR"
API_KEY_ENV = "ANTHROPIC_API_KEY"

VALID_MODES: tuple[str, ...] = ("manual", "stub", "anthropic_api")
DEFAULT_MODE = "manual"
DEFAULT_MODEL_BY_MODE = {
    "manual": "claude-fable-5-1",  # the Claude Code session model that answers operator requests
    "stub": "deterministic-fixture-v1",
    "anthropic_api": "claude-opus-5",
}
DEFAULT_OPERATOR_BY_MODE = {
    "manual": "claude-code-subagent",
    "stub": "deterministic-fixture",
    "anthropic_api": "anthropic-api",
}
MANUAL_ROOT = ARTIFACTS_DIR / "manual"


class ProviderError(RuntimeError):
    """Raised for invalid operator responses or provider failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when a mode cannot start (e.g. anthropic_api without an API key)."""


class ProviderSettings(BaseModel):
    mode: str = DEFAULT_MODE
    model_identifier: str | None = None
    operator: str | None = None

    @classmethod
    def from_env(cls, **overrides: Any) -> "ProviderSettings":
        values: dict[str, Any] = {
            "mode": os.environ.get(MODE_ENV) or DEFAULT_MODE,
            "model_identifier": os.environ.get(MODEL_ENV) or None,
            "operator": os.environ.get(OPERATOR_ENV) or None,
        }
        values.update({k: v for k, v in overrides.items() if v is not None})
        settings = cls(**values)
        if settings.mode not in VALID_MODES:
            raise ProviderConfigurationError(f"{MODE_ENV}={settings.mode!r} is not one of {VALID_MODES}")
        return settings


class OperatorRequest(BaseModel):
    """What an operator needs to make one decision. Contains no secrets and no raw dataset text."""

    request_id: str
    run_id: str
    condition: str
    task_id: str
    attempt: int
    node: str
    seq: int
    created_at: str = Field(default_factory=utc_now)
    instructions: str
    payload: dict
    response_schema: dict

    @classmethod
    def build(
        cls,
        *,
        run_id: str,
        condition: str,
        task_id: str,
        attempt: int,
        node: str,
        seq: int,
        instructions: str,
        payload: dict,
    ) -> "OperatorRequest":
        if node not in LLM_DECISION_NODES:
            raise ValueError(f"{node!r} is not an LLM-decision node")
        return cls(
            request_id=f"{run_id}:{condition}:{task_id}:a{attempt}:{node}:{seq}",
            run_id=run_id,
            condition=condition,
            task_id=task_id,
            attempt=attempt,
            node=node,
            seq=seq,
            instructions=instructions,
            payload=payload,
            response_schema=response_schema_for(node),
        )

    # ---- manual-mode file protocol ---------------------------------------------------
    def file_stem(self) -> str:
        return f"{self.task_id}_a{self.attempt}_{self.node}_{self.seq}"

    def request_path(self, root: Path | None = None) -> Path:
        return (root or MANUAL_ROOT) / self.run_id / self.condition / f"{self.file_stem()}.request.json"

    def response_path(self, root: Path | None = None) -> Path:
        return (root or MANUAL_ROOT) / self.run_id / self.condition / f"{self.file_stem()}.response.json"

    def write_request_file(self, root: Path | None = None) -> Path:
        return atomic_write_json(self.request_path(root), self.model_dump(mode="json"))


def read_response_file(path: Path | str) -> tuple[dict, str]:
    """Load an operator response and return ``(response, sha256_of_file_text)``."""
    p = Path(path)
    if not p.exists():
        raise ProviderError(f"response file not found: {p}")
    text = p.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"response file is not valid JSON ({exc}): {p}") from exc
    if not isinstance(data, dict):
        raise ProviderError(f"response must be a JSON object: {p}")
    return data, sha256_text(text)


# --------------------------------------------------------------------------- providers


class BaseProvider:
    mode: str = ""
    operator: str = ""
    model_identifier: str = ""

    def __init__(self, settings: ProviderSettings):
        self.mode = settings.mode
        self.operator = settings.operator or DEFAULT_OPERATOR_BY_MODE[settings.mode]
        self.model_identifier = settings.model_identifier or DEFAULT_MODEL_BY_MODE[settings.mode]

    def describe(self) -> dict[str, str]:
        return {"provider_mode": self.mode, "operator": self.operator, "model_identifier": self.model_identifier}

    def decide(self, request: OperatorRequest) -> dict:  # pragma: no cover - abstract
        raise NotImplementedError


class ManualProvider(BaseProvider):
    """Pauses the graph with a LangGraph interrupt; the response arrives via ``Command(resume=...)``."""

    def decide(self, request: OperatorRequest) -> dict:
        from langgraph.types import interrupt  # local import keeps this module importable without a graph

        response = interrupt(request.model_dump(mode="json"))
        if not isinstance(response, dict):
            raise ProviderError("operator response must be a JSON object")
        return response


class FixtureProvider(BaseProvider):
    """Deterministic rule-based stand-in used only in ``stub`` mode.

    Rules (documented so nobody mistakes them for reasoning):
    * plan: start from the catalogue's ``default_selected`` components with default
      params; add any component whose id appears verbatim in a retrieved skill and
      apply ``component.param=value`` tokens found in skill text; on revision,
      apply the ``related_components`` recommended by evaluator feedback.
    * reflect: every feedback item with ``reusable: true`` becomes a lesson; every
      item becomes a current-task correction.
    * propose: the first lesson applicable to >= 2 remaining tasks becomes a
      proposal; otherwise ``proposal`` is null with a reason.
    """

    # component.param=value ; values may contain inner dots (0.25) but a trailing period is sentence punctuation
    _TOKEN = re.compile(r"\b([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)=([A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+)*)")

    def decide(self, request: OperatorRequest) -> dict:
        node, payload = request.node, request.payload
        if node == "plan_task":
            return self._plan(payload, revise=False)
        if node == "revise_plan":
            return self._plan(payload, revise=True)
        if node == "reflect_on_feedback":
            return self._reflect(payload)
        if node == "propose_skill":
            return self._propose(payload)
        if node == "revise_skill_proposal":
            return self._revise_proposal(payload)
        raise ProviderError(f"fixture has no rule for node {node!r}")

    # ---- helpers -------------------------------------------------------------------
    @staticmethod
    def _catalogue(payload: dict) -> dict[str, dict]:
        return {c["id"]: c for c in payload.get("component_catalogue", []) if isinstance(c, dict) and "id" in c}

    @staticmethod
    def _default_params(component: dict) -> dict:
        return {name: spec.get("default") for name, spec in (component.get("params") or {}).items() if "default" in spec}

    @staticmethod
    def _skill_text(skill: dict) -> str:
        sections = skill.get("sections") or {}
        parts = [str(skill.get("name", "")), " ".join(skill.get("tags") or [])]
        for value in sections.values():
            parts.append(" ".join(value) if isinstance(value, list) else str(value))
        return "\n".join(parts)

    def _plan(self, payload: dict, *, revise: bool) -> dict:
        catalogue = self._catalogue(payload)
        selected: dict[str, dict] = {}
        for cid, comp in catalogue.items():
            if comp.get("default_selected"):
                selected[cid] = self._default_params(comp)
        if revise and payload.get("prior_plan"):
            for step in payload["prior_plan"].get("steps", []):
                if step.get("component") in catalogue:
                    selected[step["component"]] = dict(step.get("params") or {})
        skills_applied: list[str] = []
        for skill in payload.get("retrieved_skills", []) or []:
            text = self._skill_text(skill)
            applied = False
            for cid, comp in catalogue.items():
                if re.search(rf"\b{re.escape(cid)}\b", text):
                    selected.setdefault(cid, self._default_params(comp))
                    applied = True
            for cid, pname, value in self._TOKEN.findall(text):
                if cid in catalogue and pname in (catalogue[cid].get("params") or {}):
                    spec = catalogue[cid]["params"][pname]
                    params = selected.setdefault(cid, self._default_params(catalogue[cid]))
                    coerced = _coerce_option(spec, value)
                    if spec.get("multi"):  # list-valued parameter: tokens add items
                        current = list(params.get(pname) or [])
                        if coerced not in current:
                            current.append(coerced)
                        params[pname] = current
                    else:
                        params[pname] = coerced
                    applied = True
            if applied and skill.get("skill_id"):
                skills_applied.append(skill["skill_id"])
        changes: list[str] = []
        if revise:
            recommendations = list(payload.get("feedback", []) or [])
            for item in recommendations:
                for rec in item.get("related_components", []) or []:
                    cid = rec.get("component")
                    if cid in catalogue:
                        params = selected.setdefault(cid, self._default_params(catalogue[cid]))
                        declared = catalogue[cid].get("params") or {}
                        for k, v in (rec.get("params") or {}).items():
                            if k not in declared:
                                continue
                            if declared[k].get("multi") and isinstance(v, list):
                                params[k] = list(dict.fromkeys(list(params.get(k) or []) + v))
                            else:
                                params[k] = v
                        changes.append(f"{cid} <- {item.get('feedback_id')}")
        steps = [{"component": cid, "params": params} for cid, params in selected.items()]
        return {
            "steps": steps,
            "skills_applied": sorted(set(skills_applied)),
            "rationale": "deterministic fixture: catalogue defaults"
            + (" + skill-referenced components" if skills_applied else "")
            + (" + feedback-recommended components" if changes else ""),
            "changes_summary": ("; ".join(changes) or "no feedback recommendations applied") if revise else None,
        }

    def _reflect(self, payload: dict) -> dict:
        feedback = payload.get("feedback", []) or []
        lessons = [
            {
                "lesson": item.get("remediation", ""),
                "applicable_task_ids": list(item.get("applicable_task_ids") or []),
                "source_feedback_ids": [item.get("feedback_id", "")],
            }
            for item in feedback
            if item.get("reusable")
        ]
        corrections = [
            {"feedback_id": item.get("feedback_id", ""), "correction": item.get("remediation", "")} for item in feedback
        ]
        return {"reusable_lessons": lessons, "current_task_corrections": corrections}

    def _propose(self, payload: dict) -> dict:
        remaining = set(payload.get("remaining_task_ids", []) or [])
        lessons = (payload.get("reflection") or {}).get("reusable_lessons", []) or []
        feedback_by_id = {f.get("feedback_id"): f for f in payload.get("feedback", []) or []}
        for lesson in lessons:
            applicable = [t for t in lesson.get("applicable_task_ids", []) if t in remaining]
            if len(applicable) < 2:
                continue
            fb = feedback_by_id.get((lesson.get("source_feedback_ids") or [None])[0]) or {}
            tokens = [
                f"{rec.get('component')}.{k}={v}"
                for rec in fb.get("related_components", []) or []
                for k, v in (rec.get("params") or {}).items()
            ]
            components = sorted({rec.get("component") for rec in fb.get("related_components", []) or [] if rec.get("component")})
            issue = fb.get("issue_type") or "lesson"
            name = re.sub(r"[^a-z0-9]+", "_", f"{issue}_{fb.get('criterion', 'general')}".lower()).strip("_")
            return {
                "proposal": {
                    "name": name[:60],
                    "tags": sorted(set((payload.get("task_spec") or {}).get("tags", []) + [fb.get("criterion", "general")])),
                    "trigger": f"When a task involves {', '.join(components) or 'this kind of analysis'} on claims data.",
                    "objective": lesson.get("lesson", ""),
                    "procedure": [
                        lesson.get("lesson", ""),
                        "Apply catalogue components: " + (", ".join(components) or "n/a") + ".",
                        "Set parameters: " + (", ".join(tokens) or "defaults") + ".",
                    ],
                    "required_checks": [f"Plan includes {c}" for c in components] or ["Lesson reflected in the plan"],
                    "expected_artifacts": list((payload.get("task_spec") or {}).get("required_artifacts", []))[:3],
                    "failure_modes": ["Applying the convention without stating it in the report."],
                    "example": f"Fixture-generated from {fb.get('feedback_id', 'feedback')} on {payload.get('task_id')}.",
                    "applicable_task_ids": applicable,
                    "source_feedback_ids": list(lesson.get("source_feedback_ids") or []),
                },
                "reason_if_null": None,
            }
        return {"proposal": None, "reason_if_null": "no lesson applies to at least two remaining tasks"}

    def _revise_proposal(self, payload: dict) -> dict:
        proposal = dict(payload.get("proposal") or {})
        validation = payload.get("validation") or {}
        if not proposal or validation.get("duplicate_of"):
            return {"proposal": None, "reason_if_null": "fixture withdraws duplicate or empty proposal"}
        for key, filler in (
            ("trigger", "When a comparable claims-analysis task is planned."),
            ("objective", "Apply a validated reusable procedure."),
            ("example", "Generic claims-data example."),
        ):
            if len(str(proposal.get(key) or "")) < 10:
                proposal[key] = filler
        if len(proposal.get("procedure") or []) < 2:
            proposal["procedure"] = list(proposal.get("procedure") or []) + ["Record the check in the report."]
        return {"proposal": proposal, "reason_if_null": None}


def _coerce_option(param_spec: dict, value: str) -> Any:
    """Map a text token onto the declared option with the same string form (keeps ints/bools typed)."""
    for option in param_spec.get("options", []) or []:
        if str(option) == value:
            return option
    return value


class AnthropicAPIProvider(BaseProvider):
    """Optional live adapter (not used in this study). Fails closed without an API key."""

    def __init__(self, settings: ProviderSettings):
        super().__init__(settings)
        if not os.environ.get(API_KEY_ENV):
            raise ProviderConfigurationError(
                f"mode anthropic_api requires {API_KEY_ENV} to be set explicitly (separate Anthropic Console billing); "
                "it never reuses Claude Code session credentials. Use mode 'manual' or 'stub' instead."
            )
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:  # pragma: no cover - optional extra
            raise ProviderConfigurationError("install the optional extra: uv sync --extra anthropic") from exc
        self._llm = ChatAnthropic(model=self.model_identifier, max_tokens=16000)

    def decide(self, request: OperatorRequest) -> dict:
        structured = self._llm.with_structured_output(request.response_schema)
        prompt = (
            f"{request.instructions}\n\nRespond with JSON only, matching the provided schema.\n\n"
            f"REQUEST PAYLOAD (JSON):\n{json.dumps(request.payload, ensure_ascii=False)}"
        )
        result = structured.invoke(prompt)
        if isinstance(result, BaseModel):
            return result.model_dump()
        if not isinstance(result, dict):
            raise ProviderError("anthropic_api returned a non-object result")
        return result


def get_provider(settings: ProviderSettings | None = None) -> BaseProvider:
    settings = settings or ProviderSettings.from_env()
    if settings.mode == "manual":
        return ManualProvider(settings)
    if settings.mode == "stub":
        return FixtureProvider(settings)
    if settings.mode == "anthropic_api":
        return AnthropicAPIProvider(settings)
    raise ProviderConfigurationError(f"unknown mode {settings.mode!r}")


def manual_dir(run_id: str, condition: str, root: Path | None = None) -> Path:
    return ensure_dir((root or MANUAL_ROOT) / run_id / condition)


def pending_requests(run_id: str, condition: str, root: Path | None = None) -> list[Path]:
    """Request files that have no response file yet (manual mode bookkeeping)."""
    folder = (root or MANUAL_ROOT) / run_id / condition
    if not folder.exists():
        return []
    pending = []
    for req in sorted(folder.glob("*.request.json")):
        if not req.with_name(req.name.replace(".request.json", ".response.json")).exists():
            pending.append(req)
    return pending


def load_request(path: Path | str) -> OperatorRequest:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ProviderError(f"request file unreadable: {path}")
    return OperatorRequest(**data)
