"""The LangGraph ``StateGraph`` for the claims skill loop.

One graph serves all three experimental conditions; the routing functions read
``state["condition"]`` and the ``next_route`` decisions recorded by
``evaluate_output`` / ``validate_skill``:

    START -> load_context -> [skill_learning: retrieve_skills] -> plan_task -> execute_task -> evaluate_output
      completed -> finalize_task -> END
      retry     -> [baseline: revise_plan | others: reflect_on_feedback -> revise_plan] -> execute_task
      learn     -> reflect_on_feedback -> propose_skill -> validate_skill
                     accepted       -> persist_skill -> finalize_task -> END
                     rejected       -> finalize_task -> END
                     retry_revision -> revise_skill_proposal -> validate_skill

``designed_topology()`` describes the same graph as plain nodes/edges for the
topology diagram (design, not observation).
"""
from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from src.graph_nodes import ClaimsNodes, Services
from src.graph_state import ClaimsGraphState

NODES: tuple[str, ...] = (
    "load_context",
    "retrieve_skills",
    "plan_task",
    "execute_task",
    "evaluate_output",
    "reflect_on_feedback",
    "revise_plan",
    "propose_skill",
    "validate_skill",
    "revise_skill_proposal",
    "persist_skill",
    "finalize_task",
)


# --------------------------------------------------------------------------- routing


def route_after_load(state: dict) -> Literal["retrieve_skills", "plan_task"]:
    return "retrieve_skills" if state.get("condition") == "skill_learning" else "plan_task"


def route_after_evaluation(state: dict) -> Literal["finalize_task", "revise_plan", "reflect_on_feedback"]:
    decision = state.get("next_route")
    if decision == "retry":
        return "revise_plan" if state.get("condition") == "baseline" else "reflect_on_feedback"
    if decision == "learn":
        return "reflect_on_feedback"
    return "finalize_task"


def route_after_reflection(state: dict) -> Literal["revise_plan", "propose_skill"]:
    return "revise_plan" if state.get("next_route") == "retry" else "propose_skill"


def route_after_validation(state: dict) -> Literal["persist_skill", "revise_skill_proposal", "finalize_task"]:
    decision = state.get("next_route")
    if decision == "accepted":
        return "persist_skill"
    if decision == "retry_revision":
        return "revise_skill_proposal"
    return "finalize_task"


# --------------------------------------------------------------------------- builder


def build_claims_skill_graph(services: Services, checkpointer: Any = None):
    """Compile the graph. Pass a checkpointer (e.g. ``SqliteSaver``) to enable interrupts/resume."""
    nodes = ClaimsNodes(services)
    builder = StateGraph(ClaimsGraphState)
    for name in NODES:
        builder.add_node(name, getattr(nodes, name))

    builder.add_edge(START, "load_context")
    builder.add_conditional_edges("load_context", route_after_load, ["retrieve_skills", "plan_task"])
    builder.add_edge("retrieve_skills", "plan_task")
    builder.add_edge("plan_task", "execute_task")
    builder.add_edge("execute_task", "evaluate_output")
    builder.add_conditional_edges(
        "evaluate_output", route_after_evaluation, ["finalize_task", "revise_plan", "reflect_on_feedback"]
    )
    builder.add_conditional_edges("reflect_on_feedback", route_after_reflection, ["revise_plan", "propose_skill"])
    builder.add_edge("revise_plan", "execute_task")
    builder.add_edge("propose_skill", "validate_skill")
    builder.add_conditional_edges(
        "validate_skill", route_after_validation, ["persist_skill", "revise_skill_proposal", "finalize_task"]
    )
    builder.add_edge("revise_skill_proposal", "validate_skill")
    builder.add_edge("persist_skill", "finalize_task")
    builder.add_edge("finalize_task", END)
    return builder.compile(checkpointer=checkpointer)


def designed_topology() -> dict:
    """Nodes and labelled edges of the designed workflow, for the topology diagram and config/graph.yaml tests."""
    edges = [
        ("START", "load_context", ""),
        ("load_context", "retrieve_skills", "skill_learning"),
        ("load_context", "plan_task", "baseline | reflection_only"),
        ("retrieve_skills", "plan_task", ""),
        ("plan_task", "execute_task", ""),
        ("execute_task", "evaluate_output", ""),
        ("evaluate_output", "finalize_task", "completed"),
        ("evaluate_output", "revise_plan", "retry (baseline)"),
        ("evaluate_output", "reflect_on_feedback", "retry (reflection_only, skill_learning) | learn (skill_learning)"),
        ("reflect_on_feedback", "revise_plan", "retry"),
        ("reflect_on_feedback", "propose_skill", "learn"),
        ("revise_plan", "execute_task", ""),
        ("propose_skill", "validate_skill", ""),
        ("validate_skill", "persist_skill", "accepted"),
        ("validate_skill", "revise_skill_proposal", "retry_revision"),
        ("validate_skill", "finalize_task", "rejected"),
        ("revise_skill_proposal", "validate_skill", ""),
        ("persist_skill", "finalize_task", ""),
        ("finalize_task", "END", ""),
    ]
    per_condition = {
        "baseline": ["load_context", "plan_task", "execute_task", "evaluate_output", "revise_plan", "finalize_task"],
        "reflection_only": [
            "load_context", "plan_task", "execute_task", "evaluate_output", "reflect_on_feedback", "revise_plan", "finalize_task",
        ],
        "skill_learning": list(NODES),
    }
    return {"nodes": list(NODES), "edges": [{"source": s, "target": t, "label": l} for s, t, l in edges], "per_condition": per_condition}


def compiled_edges(graph: Any) -> set[tuple[str, str]]:
    """Edges of a compiled graph as (source, target) pairs, with LangGraph's START/END names normalised."""
    g = graph.get_graph()
    norm = lambda n: "START" if n == "__start__" else "END" if n == "__end__" else n  # noqa: E731
    return {(norm(e.source), norm(e.target)) for e in g.edges}
