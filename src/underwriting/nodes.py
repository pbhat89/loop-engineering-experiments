"""LangGraph node implementations for the underwriting apprentice.

The nodes are methods on one class so they can share injected :class:`Services`, and every
node is pure up to the ``provider.decide`` call. In manual mode that call raises a LangGraph
interrupt, and on resume the node re-executes from the top - so nothing is written to disk
before the answer is in hand. All the writes live in ``update_memory`` and ``advance``.

One graph invocation handles one application, start to finish.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.underwriting.cases import operator_fields, render_case
from src.underwriting.markup import build_markup
from src.underwriting.memory import Notebook, RuleBook
from src.underwriting.precedent import PrecedentFile
from src.underwriting.scorer import score_answer
from src.underwriting.senior import answer_questions, for_request, usage
from src.underwriting.state import (
    ASKING_CONDITIONS,
    MAX_QUESTIONS,
    MAX_REREQUESTS,
    UwRequest,
    validate_response,
)
from src.utils import rel, utc_now


@dataclass
class Services:
    """Everything the nodes need, injected so tests can use fakes."""

    provider: Any                                   # .decide(UwRequest) -> dict
    manual: str
    goldens: dict[str, dict]                        # case_id -> golden; read only after the answer is in
    run_root: Path                                  # artifacts/uw/<run_id>
    log: Callable[[str, dict], None] = lambda condition, record: None
    max_rerequests: int = MAX_REREQUESTS
    precedent_k: int = 3
    max_questions: int = MAX_QUESTIONS              # cap the senior oracle will answer
    extra_log_fields: dict = field(default_factory=dict)

    def notebook(self) -> Notebook:
        return Notebook(self.run_root)

    def rulebook(self) -> RuleBook:
        return RuleBook(self.run_root)

    def precedent(self) -> PrecedentFile:
        return PrecedentFile(self.run_root)


class UwNodes:
    def __init__(self, services: Services):
        self.s = services

    # ---- pure helpers ------------------------------------------------------------------
    def _case_block(self, state: dict) -> dict:
        case = state["case"]
        return {"rendered": render_case(case), "fields": operator_fields(case)}

    def _memory_block(self, state: dict) -> dict | None:
        condition, case = state["condition"], state["case"]
        if condition == "notebook":
            return self.s.notebook().memory_block(exclude_case_id=case["case_id"])
        if condition == "written_rules":
            return self.s.rulebook().memory_block()
        if condition == "precedent":
            return self.s.precedent().memory_block(case, self.s.precedent_k)
        return None

    def _ask(self, state: dict, step: str, payload: dict) -> tuple[dict | None, int, list[str], list[str], list[str]]:
        """Ask the operator, re-requesting with the validation errors up to the cap.

        Returns ``(answer or None, re-requests used, last errors, request paths, response paths)``.
        """
        errors: list[str] = []
        requests: list[str] = []
        responses: list[str] = []
        for attempt in range(1, self.s.max_rerequests + 2):
            body = dict(payload)
            if errors:
                body["validation_errors"] = errors
            request = UwRequest.build(
                run_id=state["run_id"],
                condition=state["condition"],
                phase=state["phase"],
                case_index=state["case_index"],
                case_id=state["case_id"],
                step=step,
                attempt=attempt,
                payload=body,
            )
            requests.append(rel(request.request_path(self.s.run_root)))
            responses.append(rel(request.response_path(self.s.run_root)))
            raw = self.s.provider.decide(request)
            parsed, errors = validate_response(step, raw)
            if not errors:
                return parsed, attempt - 1, [], requests, responses
        return None, self.s.max_rerequests, errors, requests, responses

    # ---- nodes -------------------------------------------------------------------------
    def load_case(self, state: dict) -> dict:
        memory = self._memory_block(state)
        return {
            "route_history": ["load_case"],
            "memory_size": int((memory or {}).get("size") or 0),
            "nearest_distance": (memory or {}).get("nearest_distance"),
        }

    def ask_senior(self, state: dict) -> dict:
        payload = {"case": self._case_block(state), "manual": self.s.manual}
        questions, _, errors, requests, responses = self._ask(state, "ask", payload)
        asked = list((questions or {}).get("questions") or [])
        answers = answer_questions(asked, state["case"], self.s.max_questions)
        return {
            "route_history": ["ask_senior"],
            "senior_answers": answers,
            "senior_usage": {**usage(answers), "ask_validation_errors": len(errors)},
            "request_files": requests,
            "response_files": responses,
        }

    def decide(self, state: dict) -> dict:
        payload: dict = {"case": self._case_block(state), "manual": self.s.manual}
        memory = self._memory_block(state)
        if memory is not None:
            payload["memory"] = memory
        if state["condition"] in ASKING_CONDITIONS:
            payload["senior_answers"] = for_request(state.get("senior_answers") or [])
        answer, rerequests, errors, requests, responses = self._ask(state, "decide", payload)
        return {
            "route_history": ["decide"],
            "answer": answer,
            "answer_invalid": answer is None,
            "validation_errors": errors,
            "rerequests": rerequests,
            "request_files": requests,
            "response_files": responses,
        }

    def score(self, state: dict) -> dict:
        golden = self.s.goldens[state["case_id"]]
        scores = score_answer(state.get("answer"), golden, unparseable=bool(state.get("answer_invalid")))
        return {"route_history": ["score"], "scores": scores}

    def markup(self, state: dict) -> dict:
        if state["phase"] != "train":
            return {"route_history": ["markup"], "markup": None}
        golden = self.s.goldens[state["case_id"]]
        return {
            "route_history": ["markup"],
            "markup": build_markup(golden, state.get("answer"), state.get("scores") or {}),
        }

    def reflect(self, state: dict) -> dict:
        payload = {
            "case": self._case_block(state),
            "manual": self.s.manual,
            "memory": self.s.rulebook().memory_block(),
            "reflection_context": {
                "your_answer": state.get("answer"),
                "markup": state.get("markup"),
            },
        }
        answer, _, errors, requests, responses = self._ask(state, "reflect", payload)
        return {
            "route_history": ["reflect"],
            "rulebook_pending": (answer or {}).get("rulebook_markdown"),
            "validation_errors": errors,
            "request_files": requests,
            "response_files": responses,
        }

    def update_memory(self, state: dict) -> dict:
        """The only node that writes an arm's memory. In the held-out phase it writes nothing."""
        if state["phase"] != "train":
            return {"route_history": ["update_memory"], "rulebook_version": None}
        condition = state["condition"]
        version = None
        if condition == "notebook" and state.get("markup"):
            self.s.notebook().append(state["case_index"], state["case_id"], state["markup"], utc_now())
        elif condition == "precedent":
            self.s.precedent().append(state["case"], self.s.goldens[state["case_id"]])
        elif condition == "written_rules":
            pending = state.get("rulebook_pending")
            if pending:
                version = self.s.rulebook().write(pending)
        return {"route_history": ["update_memory"], "rulebook_version": version}

    def advance(self, state: dict) -> dict:
        scores = state.get("scores") or {}
        record = {
            "run_id": state["run_id"],
            "condition": state["condition"],
            "phase": state["phase"],
            "case_index": state["case_index"],
            "case_id": state["case_id"],
            "ladder_distance": scores.get("ladder_distance"),
            "decision_match": scores.get("decision_match"),
            "modifier_f1": (scores.get("modifier") or {}).get("f1"),
            "driver_recall": (scores.get("driver") or {}).get("recall"),
            "agent_decision": scores.get("agent_decision"),
            "agent_rating_class": scores.get("agent_rating_class"),
            "unparseable": bool(scores.get("unparseable")),
            "rerequests": int(state.get("rerequests") or 0),
            "questions_asked": int((state.get("senior_usage") or {}).get("questions_asked") or 0),
            "senior_usage": state.get("senior_usage") or {},
            "memory_size": int(state.get("memory_size") or 0),
            "nearest_distance": state.get("nearest_distance"),
            "rulebook_version": state.get("rulebook_version"),
            "request_files": list(state.get("request_files") or []),
            "response_files": list(state.get("response_files") or []),
            "mode": state.get("mode"),
            "operator": state.get("operator"),
            "model_identifier": state.get("model_identifier"),
            "recorded_at": utc_now(),
            **self.s.extra_log_fields,
        }
        self.s.log(state["condition"], record)
        return {"route_history": ["advance"], "status": "done"}
