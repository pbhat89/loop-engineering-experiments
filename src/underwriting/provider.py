"""How an answer reaches the graph.

The graph never calls a model. At every decision it hands a request to a provider and
takes back a JSON object:

``manual``
    The real mode. :class:`ManualProvider` raises a LangGraph ``interrupt`` carrying the
    request, so the runner stops, writes the request to a file and returns. Whatever you
    use to answer it (a Claude Code subagent, a script against any model API, a person
    with a text editor) writes the response file, and the runner resumes with
    ``Command(resume=...)``. Nothing here knows or cares which model answered; the
    identifier recorded in the logs comes from ``config/underwriting.yaml``.

``stub``
    Deterministic stand-ins in :mod:`src.underwriting.stub`, for tests and smoke runs.
    Always labelled stub wherever its output appears.

Keeping the provider this thin is deliberate. It is what lets the same experiment run on
a subscription, on a hosted API, or on a local model, without the graph changing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.utils import sha256_text

VALID_MODES: tuple[str, ...] = ("manual", "stub")
DEFAULT_MODE = "manual"

# Recorded in every case record so a reader can tell what produced an answer. Override in
# config/underwriting.yaml; the value is a label, never a client configuration.
DEFAULT_MODEL_BY_MODE = {"manual": "unspecified-manual-operator", "stub": "deterministic-fixture-v1"}
DEFAULT_OPERATOR_BY_MODE = {"manual": "manual-file-protocol", "stub": "deterministic-fixture"}


class ProviderError(RuntimeError):
    """An operator response was missing, unparseable, or not a JSON object."""


class ProviderConfigurationError(ProviderError):
    """A mode cannot start with the settings given."""


class ProviderSettings(BaseModel):
    mode: str = DEFAULT_MODE
    model_identifier: str | None = None
    operator: str | None = None

    def validated(self) -> "ProviderSettings":
        if self.mode not in VALID_MODES:
            raise ProviderConfigurationError(f"mode {self.mode!r} is not one of {VALID_MODES}")
        return self


def read_response_file(path: Path | str) -> tuple[dict, str]:
    """Load an operator response and return ``(response, sha256_of_file_text)``.

    The hash goes into the run log, so a response cannot be quietly edited after the fact.
    """
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


class BaseProvider:
    mode: str = ""
    operator: str = ""
    model_identifier: str = ""

    def __init__(self, settings: ProviderSettings):
        settings = settings.validated()
        self.mode = settings.mode
        self.operator = settings.operator or DEFAULT_OPERATOR_BY_MODE[settings.mode]
        self.model_identifier = settings.model_identifier or DEFAULT_MODEL_BY_MODE[settings.mode]

    def describe(self) -> dict[str, str]:
        return {"provider_mode": self.mode, "operator": self.operator, "model_identifier": self.model_identifier}

    def decide(self, request: Any) -> dict:  # pragma: no cover - abstract
        raise NotImplementedError


class ManualProvider(BaseProvider):
    """Pauses the graph; the answer arrives later through ``Command(resume=...)``."""

    def decide(self, request: Any) -> dict:
        from langgraph.types import interrupt  # local import keeps this module importable without a graph

        payload = request.model_dump(mode="json") if hasattr(request, "model_dump") else dict(request)
        response = interrupt(payload)
        if not isinstance(response, dict):
            raise ProviderError("operator response must be a JSON object")
        return response
