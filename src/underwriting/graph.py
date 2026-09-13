"""The LangGraph ``StateGraph`` for the underwriting apprentice.

One graph serves all five arms; the routers read ``state["condition"]`` and
``state["phase"]``::

    START -> load_case -> [ask_senior] -> decide -> score -> markup -> [reflect] -> update_memory -> advance -> END

``ask_senior`` runs only for the ``ask_senior`` arm. ``reflect`` runs only for
``written_rules``, and only in the training phase. In the held-out phase ``markup``
produces nothing and ``update_memory`` writes nothing - the memories are frozen, so the
held-out phase is strictly read-only.

``interrupt()`` fires inside ``ask_senior``, ``decide`` and ``reflect`` (manual mode).
Checkpoints live under ``artifacts/uw/<run_id>/checkpoints/``.
"""
from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from src.underwriting.nodes import Services, UwNodes
from src.underwriting.state import ASKING_CONDITIONS, CONDITIONS, REFLECTING_CONDITIONS, UwGraphState

NODES: tuple[str, ...] = (
    "load_case",
    "ask_senior",
    "decide",
    "score",
    "markup",
    "reflect",
    "update_memory",
    "advance",
)
INTERRUPTING_NODES: tuple[str, ...] = ("ask_senior", "decide", "reflect")


# --------------------------------------------------------------------------- routing


def route_after_load(state: dict) -> Literal["ask_senior", "decide"]:
    return "ask_senior" if state.get("condition") in ASKING_CONDITIONS else "decide"


def route_after_markup(state: dict) -> Literal["reflect", "update_memory"]:
    reflecting = state.get("condition") in REFLECTING_CONDITIONS and state.get("phase") == "train"
    return "reflect" if reflecting else "update_memory"


# --------------------------------------------------------------------------- builder


def build_underwriting_graph(services: Services, checkpointer: Any = None):
    """Compile the graph. Pass a checkpointer (``SqliteSaver``) to enable interrupts and resume."""
    nodes = UwNodes(services)
    builder = StateGraph(UwGraphState)
    for name in NODES:
        builder.add_node(name, getattr(nodes, name))
    builder.add_edge(START, "load_case")
    builder.add_conditional_edges("load_case", route_after_load, ["ask_senior", "decide"])
    builder.add_edge("ask_senior", "decide")
    builder.add_edge("decide", "score")
    builder.add_edge("score", "markup")
    builder.add_conditional_edges("markup", route_after_markup, ["reflect", "update_memory"])
    builder.add_edge("reflect", "update_memory")
    builder.add_edge("update_memory", "advance")
    builder.add_edge("advance", END)
    return builder.compile(checkpointer=checkpointer)


def designed_topology() -> dict:
    """Nodes, labelled edges and the path each arm takes - design, not observation."""
    edges = [
        ("START", "load_case", ""),
        ("load_case", "ask_senior", "ask_senior"),
        ("load_case", "decide", "new_joiner | notebook | written_rules | precedent"),
        ("ask_senior", "decide", ""),
        ("decide", "score", ""),
        ("score", "markup", ""),
        ("markup", "reflect", "written_rules, train phase"),
        ("markup", "update_memory", "every other arm, and every arm in the held-out phase"),
        ("reflect", "update_memory", ""),
        ("update_memory", "advance", ""),
        ("advance", "END", ""),
    ]
    base = ["load_case", "decide", "score", "markup", "update_memory", "advance"]
    per_condition = {c: list(base) for c in CONDITIONS}
    per_condition["ask_senior"] = ["load_case", "ask_senior"] + base[1:]
    per_condition["written_rules"] = base[:4] + ["reflect"] + base[4:]
    return {
        "nodes": list(NODES),
        "edges": [{"source": s, "target": t, "label": label} for s, t, label in edges],
        "per_condition": per_condition,
        "interrupting_nodes": list(INTERRUPTING_NODES),
    }


def compiled_edges(graph: Any) -> set[tuple[str, str]]:
    """Edges of a compiled graph as (source, target) pairs, with START/END normalised."""
    g = graph.get_graph()
    norm = lambda n: "START" if n == "__start__" else "END" if n == "__end__" else n  # noqa: E731
    return {(norm(e.source), norm(e.target)) for e in g.edges}
