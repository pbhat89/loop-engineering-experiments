"""Learning visuals computed strictly from the JSONL logs (A5), plus the designed-topology diagram.

Figures (``artifacts/figures/`` unless ``out_dir`` says otherwise), all matplotlib Agg::

    learning_curve.png         final rubric score by task, one line per condition
    reliability_curve.png      execution errors and retries by task and condition (two panels, never a dual axis)
    skill_accumulation.png     foundational and evolved skills available over task order (skill + graph events)
    skill_utility.png          per evolved skill: reuse count and mean final score where reused vs not (illustrative)
    skill_lifecycle_graph.png  observed graph task -> feedback -> skill created -> later retrieval / reuse (also copied to artifacts/graphs/)
    rubric_heatmap.png         task x condition mean of dimension scores, plus one small panel per dimension
    figures_manifest.json      every figure with its source log files, run ids, and "no observations" notes

``render_topology()`` draws ``claims_graph.designed_topology()`` into ``artifacts/graphs/langgraph_topology.png``
and is labelled as design, not observation.

Rules: condition colours are fixed and identical everywhere; condition names are spelled exactly as in the logs;
text is set in ink colours; every figure carries a subtitle naming its source files and the run ids included;
a series without observations draws nothing and gets a "no observations" note. No value is ever invented.
matplotlib and networkx are imported lazily so importing this module stays cheap for the dashboard/tracker.
"""
from __future__ import annotations

import argparse
import math
import os
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.experiment_logger import (
    EXPERIMENT_EVENTS_FILE,
    FEEDBACK_EVENTS_FILE,
    GRAPH_EVENTS_FILE,
    SKILL_EVENTS_FILE,
    STATUS_FILE,
    read_log,
    read_status,
    summarize_runs,
    task_sort_key,
)
from src.utils import ARTIFACTS_DIR, CONFIG_DIR, LOGS_DIR, atomic_write_json, ensure_dir, read_yaml, rel, utc_now

# --------------------------------------------------------------------------- constants (one visual system)

# Fixed condition order and colours (Okabe-Ito, colour-blind safe), identical in every figure and in the dashboard.
CONDITION_ORDER: tuple[str, ...] = (
    "baseline", "reflection_only", "skill_learning", "foundational_only", "self_refine", "feedback_memory", "self_refine_memory",
)
CONDITION_COLORS: dict[str, str] = {
    "baseline": "#0072B2", "reflection_only": "#E69F00", "skill_learning": "#009E73", "foundational_only": "#CC79A7",
    "self_refine": "#D55E00", "feedback_memory": "#56B4E9", "self_refine_memory": "#8C564B",
}
# Fills for node-membership groups in the topology diagram, assigned from the largest group (all conditions) down.
MEMBERSHIP_FILLS: tuple[str, ...] = ("#ffffff", "#fbe7c6", "#e6dcf2", "#c9ebdc", "#dbe7f3", "#f6d6d1")
OTHER_COLOR = "#8b949e"
INK = "#1f2328"
INK2 = "#57606a"
MUTED = "#8b949e"
GRID = "#e4e6ea"
MISSING = "#eceef1"
PAPER = "#ffffff"
FOUNDATIONAL_COLOR = "#7a5aa6"
FEEDBACK_COLOR = "#f3d9a4"
SKILL_COLOR = "#bfe3d3"
TASK_COLOR = "#ffffff"
RUN_LINESTYLES: tuple[str, ...] = ("-", "--", ":", "-.")
DIMENSIONS: tuple[str, ...] = ("correctness", "completeness", "reproducibility", "statistical_discipline", "communication")
SCORE_MAX = 4.0

FIGURES_DIR = ARTIFACTS_DIR / "figures"
GRAPHS_DIR = ARTIFACTS_DIR / "graphs"
MANIFEST_FILE = "figures_manifest.json"
TOPOLOGY_FILE = "langgraph_topology.png"
LIFECYCLE_FILE = "skill_lifecycle_graph.png"

# name -> (file, title, one-line description). The dashboard embeds these in this order.
FIGURE_CATALOGUE: dict[str, tuple[str, str, str]] = {
    "learning_curve": ("learning_curve.png", "Learning curve", "Final rubric score (0-4) by task and condition."),
    "reliability_curve": ("reliability_curve.png", "Reliability curve", "Execution errors and retries by task and condition."),
    "skill_accumulation": ("skill_accumulation.png", "Skill accumulation", "Foundational and evolved skills available over task order."),
    "skill_utility": ("skill_utility.png", "Skill utility (illustrative)", "Reuse count per evolved skill and mean final score where reused vs not."),
    "skill_lifecycle_graph": (LIFECYCLE_FILE, "Observed skill lifecycle", "task -> feedback -> skill created -> later retrieval / reuse, from logs."),
    "rubric_heatmap": ("rubric_heatmap.png", "Rubric heatmap", "Mean dimension score per task and condition, plus one panel per dimension."),
}

_RC = {
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "font.size": 9.5,
    "text.color": INK,
    "axes.labelcolor": INK2,
    "axes.edgecolor": GRID,
    "axes.titlecolor": INK,
    "axes.titlesize": 10.5,
    "axes.titleweight": "semibold",
    "axes.titlelocation": "left",
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "legend.labelcolor": INK,
    "axes.unicode_minus": False,
}


# --------------------------------------------------------------------------- lazy imports


def _mpl():
    import matplotlib

    matplotlib.use("Agg", force=False)
    import matplotlib.pyplot as plt

    return matplotlib, plt


def _nx():
    import networkx as nx

    return nx


# --------------------------------------------------------------------------- data


@dataclass
class Series:
    run_id: str
    condition: str
    label: str
    color: str
    linestyle: str
    tasks: dict = field(default_factory=dict)  # task_id -> {"final": dict | None, "attempts": [dict]}

    def final(self, task_id: str) -> dict | None:
        return (self.tasks.get(task_id) or {}).get("final")

    def has_observations(self) -> bool:
        return any(t.get("final") for t in self.tasks.values())


@dataclass
class ChartData:
    logs_dir: Path
    run_ids: list[str]
    summary: dict
    series: list[Series]
    task_ids: list[str]
    skill_events: list[dict]
    feedback_events: list[dict]
    graph_events: list[dict]
    pass_threshold: float | None = None

    def source(self, *names: str) -> str:
        files = ", ".join(rel(self.logs_dir / n) for n in names)
        runs = ", ".join(self.run_ids) if self.run_ids else "none"
        return f"Source: {files}  |  runs: {runs}"

    def sources_list(self, *names: str) -> list[str]:
        return [rel(self.logs_dir / n) for n in names]


def configured_task_order() -> list[str]:
    """Task ids from config (axis labels only, never outcomes); empty when no config exists yet."""
    try:
        exp = CONFIG_DIR / "experiment.yaml"
        if exp.exists():
            order = (read_yaml(exp) or {}).get("task_order")
            if isinstance(order, list) and order:
                return [str(t) for t in order]
        tasks = CONFIG_DIR / "tasks.yaml"
        if tasks.exists():
            suite = (read_yaml(tasks) or {}).get("tasks") or []
            return [str(t.get("task_id")) for t in suite if isinstance(t, dict) and t.get("task_id")]
    except Exception:  # noqa: BLE001 - config is optional for charts
        pass
    return []


def configured_pass_threshold() -> float | None:
    for path, key in ((CONFIG_DIR / "rubric.yaml", "pass_threshold"), (CONFIG_DIR / "experiment.yaml", "pass_threshold")):
        try:
            if path.exists():
                value = (read_yaml(path) or {}).get(key)
                if isinstance(value, (int, float)):
                    return float(value)
        except Exception:  # noqa: BLE001
            continue
    return None


def condition_color(condition: str) -> str:
    return CONDITION_COLORS.get(condition, OTHER_COLOR)


def load_chart_data(logs_dir: Path | str = LOGS_DIR, run_ids: list[str] | None = None) -> ChartData:
    logs_dir = Path(logs_dir)
    summary = summarize_runs(logs_dir)
    status = read_status(logs_dir)
    known = set(summary["run_ids"]) | set((status.get("runs") or {}).keys())
    selected = sorted(run_ids) if run_ids else sorted(known)
    multi = len(selected) > 1
    observed_conditions = set(summary["conditions"])
    for run in (status.get("runs") or {}).values():
        observed_conditions.update((run.get("conditions") or {}).keys())
    conditions = list(CONDITION_ORDER) + sorted(c for c in observed_conditions if c not in CONDITION_ORDER)
    series: list[Series] = []
    for i, run_id in enumerate(selected):
        run = summary["runs"].get(run_id, {"conditions": {}})
        for cond in conditions:
            tasks = ((run["conditions"].get(cond) or {}).get("tasks")) or {}
            series.append(
                Series(
                    run_id=run_id,
                    condition=cond,
                    label=f"{cond} · {run_id}" if multi else cond,
                    color=condition_color(cond),
                    linestyle=RUN_LINESTYLES[i % len(RUN_LINESTYLES)],
                    tasks=tasks,
                )
            )
    task_ids: set[str] = set(configured_task_order())
    for s in series:
        task_ids.update(s.tasks.keys())
    for run_id in selected:
        for cond in ((status.get("runs") or {}).get(run_id, {}).get("conditions") or {}).values():
            task_ids.update((cond.get("scores") or {}).keys())
    in_run = lambda r: r.get("run_id") in selected  # noqa: E731
    return ChartData(
        logs_dir=logs_dir,
        run_ids=selected,
        summary=summary,
        series=series,
        task_ids=sorted(task_ids, key=task_sort_key),
        skill_events=[r for r in read_log(logs_dir / SKILL_EVENTS_FILE) if in_run(r)],
        feedback_events=[r for r in read_log(logs_dir / FEEDBACK_EVENTS_FILE) if in_run(r)],
        graph_events=[r for r in read_log(logs_dir / GRAPH_EVENTS_FILE) if in_run(r)],
        pass_threshold=configured_pass_threshold(),
    )


# --------------------------------------------------------------------------- figure plumbing


def _atomic_savefig(fig: Any, out_path: Path, dpi: int = 150) -> Path:
    out_path = Path(out_path)
    ensure_dir(out_path.parent)
    tmp = out_path.with_name(f".{out_path.name}.{os.getpid()}.tmp.png")
    fig.savefig(tmp, dpi=dpi, format="png", bbox_inches="tight", pad_inches=0.25)
    os.replace(tmp, out_path)
    return out_path


def _finish(fig: Any, title: str, subtitle: str, notes: list[str], out_path: Path) -> Path:
    _, plt = _mpl()
    fig_h = float(fig.get_size_inches()[1])
    title_h = 12.5 * 1.5 / 72 / fig_h  # one title line in figure fraction, so the subtitle never overlaps on short figures
    fig.suptitle(title, x=0.01, y=0.995, ha="left", va="top", fontsize=12.5, fontweight="semibold", color=INK)
    fig.text(0.01, 0.995 - title_h, subtitle, ha="left", va="top", fontsize=8.5, color=INK2, transform=fig.transFigure, wrap=True)
    if notes:
        fig.text(0.01, 0.005, "  |  ".join(notes), ha="left", va="bottom", fontsize=8, color=INK2, transform=fig.transFigure, wrap=True)
    try:
        return _atomic_savefig(fig, out_path)
    finally:
        plt.close(fig)


def _bottom_legend(fig: Any, handles: list[Any], ncol: int, axis_height_in: float = 0.55) -> None:
    """Legend in a reserved strip under the axes and above the notes line, sized by its row count so neither overlaps."""
    fig_h = float(fig.get_size_inches()[1])
    rows = max(1, math.ceil(len(handles) / max(ncol, 1)))
    note_strip = 0.28 / fig_h
    legend_h = (rows * 0.19 + 0.12) / fig_h
    fig.subplots_adjust(bottom=min(0.6, note_strip + legend_h + axis_height_in / fig_h))
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.01, note_strip), ncol=ncol)


def _empty_axes(ax: Any, text: str = "no observations yet") -> None:
    ax.text(0.5, 0.5, text, ha="center", va="center", color=MUTED, fontsize=10, transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


def _task_axis(ax: Any, task_ids: list[str]) -> None:
    ax.set_xticks(range(len(task_ids)))
    ax.set_xticklabels(task_ids)
    ax.set_xlim(-0.5, max(len(task_ids) - 0.5, 0.5))
    ax.set_xlabel("task (fixed suite order)")


def _condition_handles(series: list[Series], only_observed: bool = True) -> list[Any]:
    from matplotlib.lines import Line2D

    handles = []
    for s in series:
        if only_observed and not s.has_observations():
            continue
        handles.append(Line2D([0], [0], color=s.color, linestyle=s.linestyle, marker="o", markersize=4, label=s.label))
    return handles


def _no_obs_notes(series: list[Series], what: str = "no observations") -> list[str]:
    missing = [s.label for s in series if not s.has_observations()]
    return [f"{what}: {', '.join(missing)}"] if missing else []


def _score_of(final: dict | None) -> float | None:
    if not final:
        return None
    v = final.get("evaluator_score_total")
    return float(v) if isinstance(v, (int, float)) else None


def _dimension_mean(final: dict | None) -> float | None:
    if not final:
        return None
    dims = final.get("evaluator_score_by_dimension") or {}
    values = [float(v) for v in dims.values() if isinstance(v, (int, float))]
    if values:
        return sum(values) / len(values)
    return _score_of(final)


# --------------------------------------------------------------------------- 1. learning curve


def render_learning_curve(data: ChartData, out_path: Path) -> tuple[Path, dict]:
    _, plt = _mpl()
    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        fig.subplots_adjust(top=0.82, bottom=0.2)
        notes: list[str] = []
        any_obs = any(s.has_observations() for s in data.series)
        if not any_obs or not data.task_ids:
            _empty_axes(ax)
            notes.append("no observations: no final task records in " + rel(data.logs_dir / EXPERIMENT_EVENTS_FILE))
        else:
            x_index = {t: i for i, t in enumerate(data.task_ids)}
            observed = [s for s in data.series if s.has_observations()]
            for k, s in enumerate(observed):
                dodge = (k - (len(observed) - 1) / 2) * 0.05  # small categorical offset so identical scores stay visible
                xs, ys = [], []
                for t in data.task_ids:
                    score = _score_of(s.final(t))
                    xs.append(x_index[t] + dodge)
                    ys.append(score if score is not None else math.nan)
                ax.plot(xs, ys, color=s.color, linestyle=s.linestyle, linewidth=1.8, zorder=2)
                first = [(x, y, bool(s.final(t).get("first_attempt_passed"))) for x, y, t in zip(xs, ys, data.task_ids) if not math.isnan(y)]
                ax.scatter([x for x, _, f in first if f], [y for _, y, f in first if f], s=34, color=s.color, zorder=3)
                ax.scatter(
                    [x for x, _, f in first if not f], [y for _, y, f in first if not f],
                    s=34, facecolors=PAPER, edgecolors=s.color, linewidths=1.6, zorder=3,
                )
            if data.pass_threshold is not None:
                ax.axhline(data.pass_threshold, color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
                ax.text(len(data.task_ids) - 0.45, data.pass_threshold + 0.05, f"pass threshold {data.pass_threshold:g} (config)", ha="right", va="bottom", fontsize=8, color=INK2)
            _task_axis(ax, data.task_ids)
            ax.set_ylim(0, SCORE_MAX + 0.25)
            ax.set_ylabel("final rubric score (0-4, higher is better)")
            handles = _condition_handles(data.series)
            from matplotlib.lines import Line2D

            handles += [
                Line2D([0], [0], marker="o", color=INK2, linestyle="none", markersize=5, label="filled: passed on first attempt"),
                Line2D([0], [0], marker="o", markerfacecolor=PAPER, markeredgecolor=INK2, linestyle="none", markersize=5, label="hollow: needed a retry"),
            ]
            _bottom_legend(fig, handles, 3)
            if len(observed) > 1:
                notes.append("series are offset slightly along the task axis so overlapping scores stay visible")
            notes += _no_obs_notes(data.series)
        path = _finish(fig, "Learning curve: final rubric score by task", data.source(EXPERIMENT_EVENTS_FILE), notes, out_path)
    return path, {"observations": any_obs, "notes": notes, "sources": data.sources_list(EXPERIMENT_EVENTS_FILE)}


# --------------------------------------------------------------------------- 2. reliability curve


def render_reliability_curve(data: ChartData, out_path: Path) -> tuple[Path, dict]:
    _, plt = _mpl()
    from matplotlib.ticker import MaxNLocator

    with plt.rc_context(_RC):
        fig, (ax_err, ax_retry) = plt.subplots(2, 1, figsize=(8.5, 5.8), sharex=True)
        fig.subplots_adjust(top=0.85, bottom=0.17, hspace=0.35)
        notes: list[str] = []
        observed = [s for s in data.series if s.has_observations()]
        if not observed or not data.task_ids:
            _empty_axes(ax_err)
            _empty_axes(ax_retry)
            notes.append("no observations: no final task records in " + rel(data.logs_dir / EXPERIMENT_EVENTS_FILE))
        else:
            n = len(observed)
            width = 0.8 / n
            max_err = max_retry = 0
            for k, s in enumerate(observed):
                offs = (k - (n - 1) / 2) * width
                xs = [i + offs for i in range(len(data.task_ids))]
                errors = [(s.final(t) or {}).get("execution_errors") if s.final(t) else None for t in data.task_ids]
                retries = []
                for t in data.task_ids:
                    f = s.final(t)
                    if not f:
                        retries.append(None)
                    elif f.get("retry_count") is not None:
                        retries.append(int(f["retry_count"]))
                    else:
                        retries.append(max(int(f.get("execution_attempts") or 1) - 1, 0))
                max_err = max([max_err, *[int(v) for v in errors if v is not None]])
                max_retry = max([max_retry, *[int(v) for v in retries if v is not None]])
                hatch = None if s.linestyle == "-" else "//"
                ax_err.bar([x for x, v in zip(xs, errors) if v is not None], [v for v in errors if v is not None], width=width, color=s.color, hatch=hatch, edgecolor=PAPER, linewidth=0.5, label=s.label)
                ax_retry.bar([x for x, v in zip(xs, retries) if v is not None], [v for v in retries if v is not None], width=width, color=s.color, hatch=hatch, edgecolor=PAPER, linewidth=0.5, label=s.label)
            for ax, label, ttl, peak in (
                (ax_err, "execution errors (count)", "Execution errors per task", max_err),
                (ax_retry, "retries (count)", "Retries per task (attempts beyond the first)", max_retry),
            ):
                ax.set_ylabel(label)
                ax.set_title(ttl)
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                ax.set_ylim(0, max(1, peak) * 1.15)
                if peak == 0:
                    ax.text(0.5, 0.5, "every observed count is 0", ha="center", va="center", fontsize=9, color=MUTED, transform=ax.transAxes)
            _task_axis(ax_retry, data.task_ids)
            _bottom_legend(fig, _condition_handles(data.series), 4)
            notes += _no_obs_notes(data.series)
        path = _finish(fig, "Reliability curve: errors and retries by task", data.source(EXPERIMENT_EVENTS_FILE), notes, out_path)
    return path, {"observations": bool(observed), "notes": notes, "sources": data.sources_list(EXPERIMENT_EVENTS_FILE)}


# --------------------------------------------------------------------------- 3. skill accumulation


def _skill_kind(event: dict) -> str | None:
    kind = event.get("kind")
    if kind:
        return str(kind)
    sid = str(event.get("skill_id") or "")
    if sid.startswith("foundational"):
        return "foundational"
    if sid.startswith("evolved"):
        return "evolved"
    return None


def skill_accumulation_series(data: ChartData) -> dict[tuple[str, str], dict[str, list[int | None]]]:
    """Per (run, condition) with skill events: counts by task order.

    ``evolved_persisted``: evolved skills persisted by the end of each task (cumulative ``skill_persisted``).
    ``foundational_seen``: distinct foundational skill ids retrieved so far (cumulative ``skill_retrieved``, a lower bound on availability).
    ``available_at_start``: ``available_skill_count`` recorded by ``load_context`` (graph events) when present, else None.
    """
    out: dict[tuple[str, str], dict[str, list[int | None]]] = {}
    keys = sorted({(str(e.get("run_id")), str(e.get("condition"))) for e in data.skill_events})
    idx = {t: i for i, t in enumerate(data.task_ids)}
    for key in keys:
        run_id, cond = key
        persisted_at: dict[str, set[str]] = {}
        retrieved_at: dict[str, set[str]] = {}
        for e in data.skill_events:
            if (str(e.get("run_id")), str(e.get("condition"))) != key or e.get("task_id") not in idx:
                continue
            t = str(e["task_id"])
            if e.get("event") == "skill_persisted" and e.get("skill_id"):
                persisted_at.setdefault(t, set()).add(str(e["skill_id"]))
            if e.get("event") == "skill_retrieved" and e.get("skill_id") and _skill_kind(e) == "foundational":
                retrieved_at.setdefault(t, set()).add(str(e["skill_id"]))
        available_at: dict[str, int] = {}
        for g in data.graph_events:
            if (str(g.get("run_id")), str(g.get("condition"))) == key and g.get("destination_node") == "load_context" and isinstance(g.get("available_skill_count"), int):
                available_at[str(g.get("task_id"))] = int(g["available_skill_count"])
        evolved, foundational, available = [], [], []
        seen_e: set[str] = set()
        seen_f: set[str] = set()
        task_records = {t for s in data.series if (s.run_id, s.condition) == key for t, entry in s.tasks.items() if entry.get("final") or entry.get("attempts")}
        touched = set(persisted_at) | set(retrieved_at) | set(available_at) | task_records
        last_observed = max((idx[t] for t in touched if t in idx), default=-1)
        for i, t in enumerate(data.task_ids):
            seen_e |= persisted_at.get(t, set())
            seen_f |= retrieved_at.get(t, set())
            # cumulative counts are carried forward only up to the last task this condition has actually reached
            has_data = i <= last_observed and (t in touched or bool(seen_e) or bool(seen_f))
            evolved.append(len(seen_e) if has_data else None)
            foundational.append(len(seen_f) if has_data else None)
            available.append(available_at.get(t))
        out[key] = {"evolved_persisted": evolved, "foundational_seen": foundational, "available_at_start": available}
    return out


def render_skill_accumulation(data: ChartData, out_path: Path) -> tuple[Path, dict]:
    _, plt = _mpl()
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MaxNLocator

    per_key = skill_accumulation_series(data)
    multi = len(data.run_ids) > 1
    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        fig.subplots_adjust(top=0.82, bottom=0.26)
        notes: list[str] = []
        if not per_key or not data.task_ids:
            _empty_axes(ax)
            notes.append("no observations: no skill events in " + rel(data.logs_dir / SKILL_EVENTS_FILE))
        else:
            xs = list(range(len(data.task_ids)))
            handles = []
            for i, ((run_id, cond), counts) in enumerate(sorted(per_key.items())):
                color = condition_color(cond)
                label = f"{cond} · {run_id}" if multi else cond
                for name, style, marker in (("evolved_persisted", "-", "o"), ("foundational_seen", ":", "s"), ("available_at_start", "--", "^")):
                    ys = [v if v is not None else math.nan for v in counts[name]]
                    if all(math.isnan(y) for y in ys):
                        continue
                    ax.plot(xs, ys, color=color, linestyle=style, marker=marker, markersize=4.5, linewidth=1.6)
                handles.append(Line2D([0], [0], color=color, linewidth=3, label=label))
            handles += [
                Line2D([0], [0], color=INK2, linestyle="-", marker="o", markersize=4, label="evolved skills persisted so far"),
                Line2D([0], [0], color=INK2, linestyle=":", marker="s", markersize=4, label="distinct foundational skills retrieved so far"),
                Line2D([0], [0], color=INK2, linestyle="--", marker="^", markersize=4, label="skills listed at task start (load_context)"),
            ]
            _task_axis(ax, data.task_ids)
            ax.set_ylabel("skills (count)")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            ax.set_ylim(bottom=0)
            _bottom_legend(fig, handles, 2)
            silent = [c for c in CONDITION_ORDER if not any(k[1] == c for k in per_key)]
            if silent:
                notes.append("no skill events: " + ", ".join(silent) + " (only skill_learning and foundational_only retrieve skills; only skill_learning creates them)")
        path = _finish(fig, "Skill accumulation over the task order", data.source(SKILL_EVENTS_FILE, GRAPH_EVENTS_FILE), notes, out_path)
    return path, {"observations": bool(per_key), "notes": notes, "sources": data.sources_list(SKILL_EVENTS_FILE, GRAPH_EVENTS_FILE)}


# --------------------------------------------------------------------------- 4. skill utility


def skill_utility_table(data: ChartData) -> list[dict]:
    """One row per evolved skill: reuse count and mean final score of tasks where it was / was not reused (same run + condition, later tasks only)."""
    rows: list[dict] = []
    persisted = [e for e in data.skill_events if e.get("event") == "skill_persisted" and e.get("skill_id")]
    created_from_finals = []
    for s in data.series:
        for t, entry in s.tasks.items():
            for sid in ((entry.get("final") or {}).get("skills_created") or []):
                created_from_finals.append({"run_id": s.run_id, "condition": s.condition, "task_id": t, "skill_id": sid, "skill_name": None})
    seen: set[tuple[str, str, str]] = set()
    for e in persisted + created_from_finals:
        key = (str(e.get("run_id")), str(e.get("condition")), str(e.get("skill_id")))
        if key in seen:
            continue
        seen.add(key)
        run_id, cond, sid = key
        created_task = str(e.get("task_id"))
        reuse_events = sum(1 for r in data.skill_events if r.get("event") == "skill_reused" and str(r.get("skill_id")) == sid and str(r.get("run_id")) == run_id)
        series = next((s for s in data.series if s.run_id == run_id and s.condition == cond), None)
        reused_scores, other_scores = [], []
        if series:
            for t, entry in series.tasks.items():
                final = entry.get("final")
                if not final or task_sort_key(t) <= task_sort_key(created_task):
                    continue
                score = _score_of(final)
                if score is None:
                    continue
                (reused_scores if sid in (final.get("skills_reused") or []) else other_scores).append(score)
        rows.append(
            {
                "run_id": run_id,
                "condition": cond,
                "skill_id": sid,
                "skill_name": e.get("skill_name"),
                "created_after_task": created_task,
                "reuse_count": reuse_events,
                "tasks_reused": len(reused_scores),
                "tasks_not_reused": len(other_scores),
                "mean_score_reused": round(statistics.mean(reused_scores), 3) if reused_scores else None,
                "mean_score_not_reused": round(statistics.mean(other_scores), 3) if other_scores else None,
            }
        )
    rows.sort(key=lambda r: (r["run_id"], r["condition"], task_sort_key(r["created_after_task"]), r["skill_id"]))
    return rows


def render_skill_utility(data: ChartData, out_path: Path) -> tuple[Path, dict]:
    _, plt = _mpl()
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MaxNLocator

    rows = skill_utility_table(data)
    multi = len(data.run_ids) > 1
    with plt.rc_context(_RC):
        height = max(3.8, 1.6 + 0.55 * len(rows))
        fig, (ax_reuse, ax_score) = plt.subplots(1, 2, figsize=(9.5, height), gridspec_kw={"width_ratios": [1, 1.3]})
        fig.subplots_adjust(top=0.8, bottom=0.24, wspace=0.55)
        notes: list[str] = ["illustrative: descriptive comparison within one condition, later tasks only; not a causal estimate"]
        if not rows:
            _empty_axes(ax_reuse)
            _empty_axes(ax_score)
            notes.append("no observations: no evolved skills persisted yet (" + rel(data.logs_dir / SKILL_EVENTS_FILE) + ")")
        else:
            labels = [f"{r['skill_id']}" + (f" · {r['run_id']}" if multi else "") for r in rows]
            ys = list(range(len(rows)))
            colors = [condition_color(r["condition"]) for r in rows]
            ax_reuse.barh(ys, [r["reuse_count"] for r in rows], color=colors, height=0.55)
            ax_reuse.set_yticks(ys)
            ax_reuse.set_yticklabels(labels)
            ax_reuse.invert_yaxis()
            ax_reuse.set_xlabel("reuse count (skill_reused events)")
            ax_reuse.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax_reuse.set_title("Reuse count per evolved skill")
            ax_reuse.grid(axis="x")
            ax_reuse.grid(False, axis="y")
            for i, r in enumerate(rows):
                c = condition_color(r["condition"])
                if r["mean_score_reused"] is not None:
                    ax_score.scatter([r["mean_score_reused"]], [i], s=46, color=c, zorder=3)
                if r["mean_score_not_reused"] is not None:
                    ax_score.scatter([r["mean_score_not_reused"]], [i], s=46, facecolors=PAPER, edgecolors=c, linewidths=1.6, zorder=3)
                if r["mean_score_reused"] is not None and r["mean_score_not_reused"] is not None:
                    ax_score.plot([r["mean_score_not_reused"], r["mean_score_reused"]], [i, i], color=c, linewidth=1.2, zorder=2)
                if r["mean_score_reused"] is None and r["mean_score_not_reused"] is None:
                    ax_score.text(0.05, i, "no later tasks scored yet", va="center", fontsize=8, color=MUTED)
                elif r["mean_score_not_reused"] is None:
                    ax_score.text(SCORE_MAX + 0.22, i, "no later task without reuse", va="center", fontsize=7.5, color=MUTED)
                elif r["mean_score_reused"] is None:
                    ax_score.text(SCORE_MAX + 0.22, i, "never reused", va="center", fontsize=7.5, color=MUTED)
            ax_score.set_yticks(ys)
            ax_score.set_yticklabels([""] * len(rows))
            ax_score.invert_yaxis()
            ax_score.set_xlim(0, SCORE_MAX + 0.1)
            ax_score.set_xlabel("mean final rubric score of later tasks (0-4)")
            ax_score.set_title("Where reused vs not reused")
            ax_score.grid(axis="x")
            ax_score.grid(False, axis="y")
            handles = [
                Line2D([0], [0], marker="o", color=INK2, linestyle="none", markersize=6, label="filled: tasks where the skill was reused"),
                Line2D([0], [0], marker="o", markerfacecolor=PAPER, markeredgecolor=INK2, linestyle="none", markersize=6, label="hollow: later tasks where it was not reused"),
            ]
            handles += [Line2D([0], [0], color=condition_color(c), linewidth=3, label=c) for c in sorted({r["condition"] for r in rows}, key=lambda c: CONDITION_ORDER.index(c) if c in CONDITION_ORDER else 99)]
            _bottom_legend(fig, handles, 2)
        path = _finish(fig, "Skill utility (illustrative)", data.source(SKILL_EVENTS_FILE, EXPERIMENT_EVENTS_FILE), notes, out_path)
    return path, {"observations": bool(rows), "notes": notes, "sources": data.sources_list(SKILL_EVENTS_FILE, EXPERIMENT_EVENTS_FILE), "rows": rows}


# --------------------------------------------------------------------------- 5. observed skill lifecycle graph


_LIFECYCLE_LAYERS: dict[str, int] = {"task": 0, "feedback": 1, "skill": 2, "task_use": 3}


def build_lifecycle_graph(data: ChartData):
    """networkx DiGraph of the observed lifecycle: creating task -> source feedback -> evolved skill -> later task (retrieved / reused).

    Only feedback items that became the source of a persisted skill are drawn (a real run issues dozens of items per
    task); the number left out is stored in ``G.graph["feedback_omitted"]`` and printed on the figure. A task appears
    once as a creator (``kind="task"``, left) and once as a user (``kind="task_use"``, right) so the flow always reads
    left to right. Before any skill is persisted, every feedback item of the skill conditions is drawn instead, so the
    task -> feedback half of the lifecycle is still visible early in a run.
    """
    nx = _nx()
    G = nx.DiGraph()
    persisted = [e for e in data.skill_events if e.get("event") == "skill_persisted" and e.get("skill_id")]
    skill_conditions = {(str(e.get("run_id")), str(e.get("condition"))) for e in data.skill_events}
    multi = len(data.run_ids) > 1

    def task_label(task_id: str, run_id: str) -> str:
        return f"{task_id}\n{run_id}" if multi else task_id

    def creator(run_id: str, cond: str, task_id: str) -> str:
        node = f"task:{run_id}:{cond}:{task_id}"
        if node not in G:
            G.add_node(node, kind="task", label=task_label(task_id, run_id), task_id=task_id, run_id=run_id, condition=cond)
        return node

    def user(run_id: str, cond: str, task_id: str) -> str:
        node = f"use:{run_id}:{cond}:{task_id}"
        if node not in G:
            G.add_node(node, kind="task_use", label=task_label(task_id, run_id), task_id=task_id, run_id=run_id, condition=cond)
        return node

    issued: dict[tuple[str, str, str], dict] = {}
    for fb in data.feedback_events:
        key = (str(fb.get("run_id")), str(fb.get("condition")), str(fb.get("feedback_id")))
        if fb.get("event") == "feedback_issued" and fb.get("feedback_id") and key[:2] in skill_conditions:
            issued.setdefault(key, fb)

    def feedback(run_id: str, cond: str, fid: str, fallback_task: str) -> str:
        fnode = f"feedback:{run_id}:{cond}:{fid}"
        if fnode not in G:
            task_id = str((issued.get((run_id, cond, fid)) or {}).get("task_id") or fallback_task)
            G.add_node(fnode, kind="feedback", label=fid, task_id=task_id, run_id=run_id, condition=cond)
            G.add_edge(creator(run_id, cond, task_id), fnode, kind="issued")
        return fnode

    drawn: set[tuple[str, str, str]] = set()
    evolved_ids = {str(e["skill_id"]) for e in persisted}
    for e in persisted:
        run_id, cond, sid = str(e.get("run_id")), str(e.get("condition")), str(e["skill_id"])
        created_task = str(e.get("task_id"))
        snode = f"skill:{run_id}:{sid}"
        G.add_node(snode, kind="skill", label=sid, run_id=run_id, condition=cond, created_task=created_task, task_id=created_task)
        prov = e.get("provenance") or {}
        for fid in prov.get("source_feedback_ids") or e.get("source_feedback_ids") or []:
            G.add_edge(feedback(run_id, cond, str(fid), created_task), snode, kind="source")
            drawn.add((run_id, cond, str(fid)))
        G.add_edge(creator(run_id, cond, created_task), snode, kind="created")
    if not persisted:
        for (run_id, cond, fid), fb in issued.items():
            feedback(run_id, cond, fid, str(fb.get("task_id")))
            drawn.add((run_id, cond, fid))
    foundational_retrievals = 0
    for e in data.skill_events:
        if e.get("event") not in ("skill_retrieved", "skill_reused") or not e.get("skill_id"):
            continue
        sid = str(e["skill_id"])
        if sid not in evolved_ids and _skill_kind(e) != "evolved":
            foundational_retrievals += 1
            continue
        run_id, cond = str(e.get("run_id")), str(e.get("condition"))
        snode = f"skill:{run_id}:{sid}"
        if snode not in G:
            G.add_node(snode, kind="skill", label=sid, run_id=run_id, condition=cond, created_task=None, task_id=None)
        unode = user(run_id, cond, str(e.get("task_id")))
        kind = "reused" if e.get("event") == "skill_reused" else "retrieved"
        if G.has_edge(snode, unode) and G.edges[snode, unode].get("kind") == "reused":
            continue
        G.add_edge(snode, unode, kind=kind)
    G.graph["foundational_retrievals_omitted"] = foundational_retrievals
    G.graph["feedback_total"] = len(issued)
    G.graph["feedback_omitted"] = sum(1 for key in issued if key not in drawn)
    return G


def _lifecycle_layout(G: Any) -> dict[str, tuple[float, float]]:
    """Layered left-to-right layout: creating tasks | source feedback | skills | later tasks that retrieved / reused."""
    pos: dict[str, tuple[float, float]] = {}
    for layer in range(4):
        members = [n for n, a in G.nodes(data=True) if _LIFECYCLE_LAYERS.get(a.get("kind"), 0) == layer]
        members.sort(key=lambda n: (task_sort_key(G.nodes[n].get("task_id") or ""), G.nodes[n].get("label", "")))
        count = len(members)
        for i, n in enumerate(members):
            pos[n] = (float(layer) * 2.2, (count - 1) / 2 - i)
    return pos


def render_skill_lifecycle_graph(data: ChartData, out_path: Path, copy_to: Path | None = None) -> tuple[Path, dict]:
    _, plt = _mpl()
    nx = _nx()
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    G = build_lifecycle_graph(data)
    has_skill = any(a.get("kind") == "skill" for _, a in G.nodes(data=True))
    with plt.rc_context(_RC):
        n_nodes = G.number_of_nodes()
        tallest = max((sum(1 for _, a in G.nodes(data=True) if _LIFECYCLE_LAYERS.get(a.get("kind"), 0) == layer) for layer in range(4)), default=0)
        height = max(4.2, min(16.0, 2.6 + 0.62 * tallest))  # sized by the tallest layer so nodes never stack on each other
        fig, ax = plt.subplots(figsize=(10.5, height))
        fig.subplots_adjust(top=0.86, bottom=0.14, left=0.03, right=0.97)
        notes: list[str] = ["observed from logs; foundational skill retrievals omitted"]
        ax.grid(False)
        ax.set_axis_off()
        if n_nodes == 0:
            _empty_axes(ax, "no observations yet: no feedback or skill events for a skill_learning condition")
            notes.append("no observations: " + rel(data.logs_dir / SKILL_EVENTS_FILE) + ", " + rel(data.logs_dir / FEEDBACK_EVENTS_FILE))
        else:
            pos = _lifecycle_layout(G)
            kinds = {
                "task": (TASK_COLOR, INK, "s", 1300),
                "task_use": (TASK_COLOR, INK, "s", 1300),
                "feedback": (FEEDBACK_COLOR, INK2, "o", 1500),
                "skill": (SKILL_COLOR, INK2, "D", 1500),
            }
            for kind, (fill, edge, shape, size) in kinds.items():
                nodes = [n for n, a in G.nodes(data=True) if a.get("kind") == kind]
                if nodes:
                    nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_color=fill, edgecolors=edge, linewidths=1.2, node_shape=shape, node_size=size, ax=ax)
            styles = {"issued": (INK2, "-", 1.2), "source": ("#b26a00", "-", 1.6), "created": (MUTED, ":", 1.0), "retrieved": (MUTED, "--", 1.2), "reused": ("#2f7d4f", "-", 1.8)}
            for kind, (color, style, width) in styles.items():
                edges = [(u, v) for u, v, a in G.edges(data=True) if a.get("kind") == kind]
                if edges:
                    nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color, style=style, width=width, arrows=True, arrowsize=12, arrowstyle="-|>", node_size=1500, connectionstyle="arc3,rad=0.12", ax=ax)
            labels = {n: _wrap(a.get("label", n), 18) for n, a in G.nodes(data=True)}
            nx.draw_networkx_labels(G, pos, labels=labels, font_size=7.5, font_color=INK, ax=ax)
            xs = [p[0] for p in pos.values()]
            ys = [p[1] for p in pos.values()]
            ax.set_xlim(min(xs) - 1.0, max(xs) + 1.0)
            ax.set_ylim(min(ys) - 0.9, max(ys) + 0.9)
            for x, text in ((0.0, "task where feedback was issued"), (2.2, "evaluator feedback"), (4.4, "evolved skill persisted"), (6.6, "later task: retrieved / reused")):
                ax.text(x, max(ys) + 0.75, text, ha="center", va="bottom", fontsize=8, color=INK2)
            handles = [
                Patch(facecolor=TASK_COLOR, edgecolor=INK, label="task"),
                Patch(facecolor=FEEDBACK_COLOR, edgecolor=INK2, label="feedback item"),
                Patch(facecolor=SKILL_COLOR, edgecolor=INK2, label="evolved skill"),
                Line2D([0], [0], color=INK2, label="feedback issued"),
                Line2D([0], [0], color="#b26a00", label="source feedback of the skill"),
                Line2D([0], [0], color=MUTED, linestyle="--", label="skill retrieved"),
                Line2D([0], [0], color="#2f7d4f", linewidth=2, label="skill reused in plan"),
            ]
            _bottom_legend(fig, handles, 4, axis_height_in=0.1)
            if not has_skill:
                notes.append("no evolved skill persisted yet: only the task -> feedback part of the lifecycle is observed")
            omitted = G.graph.get("foundational_retrievals_omitted", 0)
            if omitted:
                notes[0] = f"observed from logs; {omitted} foundational skill retrieval events omitted for legibility"
            omitted_fb = G.graph.get("feedback_omitted", 0)
            if omitted_fb:
                notes.append(f"{omitted_fb} of {G.graph.get('feedback_total', 0)} feedback items never became a skill source and are not drawn")
        path = _finish(fig, "Observed skill lifecycle (from logs, not the designed topology)", data.source(SKILL_EVENTS_FILE, FEEDBACK_EVENTS_FILE), notes, out_path)
    if copy_to is not None:
        copy_to = Path(copy_to)
        ensure_dir(copy_to.parent)
        tmp = copy_to.with_name(f".{copy_to.name}.{os.getpid()}.tmp.png")
        tmp.write_bytes(Path(path).read_bytes())
        os.replace(tmp, copy_to)
    return path, {
        "observations": G.number_of_nodes() > 0,
        "notes": notes,
        "sources": data.sources_list(SKILL_EVENTS_FILE, FEEDBACK_EVENTS_FILE),
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "copy": rel(copy_to) if copy_to else None,
    }


def _wrap(text: str, width: int) -> str:
    out, line = [], ""
    for part in str(text).replace("\n", " \n ").split(" "):
        if part == "\n":
            out.append(line)
            line = ""
            continue
        if line and len(line) + 1 + len(part) > width:
            out.append(line)
            line = part
        else:
            line = f"{line} {part}".strip()
    out.append(line)
    return "\n".join(x for x in out if x)


# --------------------------------------------------------------------------- 6. rubric heatmap


def _score_cmap():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("rubric", ["#f5f7fa", "#c9dcef", "#7fa8d6"])


def _heat_panel(ax: Any, matrix: list[list[float | None]], rows: list[str], cols: list[str], title: str, annotate: bool = True, decimals: int = 2) -> None:
    import numpy as np

    arr = np.array([[math.nan if v is None else v for v in r] for r in matrix], dtype=float) if matrix else np.zeros((0, 0))
    cmap = _score_cmap().with_extremes(bad=MISSING)
    ax.imshow(np.ma.masked_invalid(arr), cmap=cmap, vmin=0, vmax=SCORE_MAX, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.grid(False)
    ax.set_title(title)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if annotate:
        for i in range(len(rows)):
            for j in range(len(cols)):
                v = matrix[i][j]
                ax.text(j, i, "—" if v is None else f"{v:.{decimals}f}", ha="center", va="center", fontsize=8 if len(cols) <= 8 else 7, color=INK if v is not None else MUTED)


def render_rubric_heatmap(data: ChartData, out_path: Path) -> tuple[Path, dict]:
    _, plt = _mpl()
    observed = [s for s in data.series if s.has_observations()]
    with plt.rc_context(_RC):
        rows = observed or [s for s in data.series if s.condition in CONDITION_ORDER][: len(CONDITION_ORDER)]
        n_rows = max(len(rows), 1)
        fig = plt.figure(figsize=(10.5, 2.4 + 0.42 * n_rows + 2.0 + 0.32 * n_rows))
        gs = fig.add_gridspec(2, len(DIMENSIONS), height_ratios=[1.35, 1], hspace=0.7, wspace=0.35)
        fig.subplots_adjust(top=0.86, bottom=0.08, left=0.16, right=0.98)
        ax_top = fig.add_subplot(gs[0, :])
        notes: list[str] = []
        if not observed or not data.task_ids:
            _empty_axes(ax_top)
            for j, dim in enumerate(DIMENSIONS):
                axd = fig.add_subplot(gs[1, j])
                _empty_axes(axd, "")
                axd.set_title(dim.replace("_", " "))
            notes.append("no observations: no final task records in " + rel(data.logs_dir / EXPERIMENT_EVENTS_FILE))
        else:
            labels = [s.label for s in observed]
            top = [[_dimension_mean(s.final(t)) for t in data.task_ids] for s in observed]
            _heat_panel(ax_top, top, labels, data.task_ids, "Mean of the five dimension scores (0-4); grey with — = no final record")
            for j, dim in enumerate(DIMENSIONS):
                axd = fig.add_subplot(gs[1, j])
                mat = []
                for s in observed:
                    row = []
                    for t in data.task_ids:
                        dims = (s.final(t) or {}).get("evaluator_score_by_dimension") or {}
                        v = dims.get(dim)
                        row.append(float(v) if isinstance(v, (int, float)) else None)
                    mat.append(row)
                _heat_panel(axd, mat, labels if j == 0 else [""] * len(labels), data.task_ids, dim.replace("_", " "), annotate=len(data.task_ids) <= 6, decimals=1)
                axd.tick_params(axis="x", labelsize=6.5)
            notes += _no_obs_notes(data.series)
        path = _finish(fig, "Rubric heatmap by task and condition", data.source(EXPERIMENT_EVENTS_FILE), notes, out_path)
    return path, {"observations": bool(observed), "notes": notes, "sources": data.sources_list(EXPERIMENT_EVENTS_FILE)}


# --------------------------------------------------------------------------- 7. designed topology (architecture, not observation)

_TOPOLOGY_POS: dict[str, tuple[float, float]] = {
    "START": (0.0, 0.0),
    "load_context": (1.0, 0.0),
    "retrieve_skills": (2.0, 1.25),
    "plan_task": (3.0, 0.0),
    "execute_task": (4.2, 0.0),
    "evaluate_output": (5.4, 0.0),
    "revise_plan": (4.2, -1.35),
    "reflect_on_feedback": (5.4, -1.35),
    "propose_skill": (6.6, 1.25),
    "validate_skill": (7.8, 1.25),
    "revise_skill_proposal": (7.8, 2.5),
    "persist_skill": (9.0, 1.25),
    "finalize_task": (9.0, 0.0),
    "END": (10.0, 0.0),
}


def render_topology(topology: dict | None = None, out_path: Path | str = GRAPHS_DIR / TOPOLOGY_FILE) -> Path:
    """Draw the designed LangGraph workflow (nodes, labelled edges, per-condition membership). Design, not observation."""
    _, plt = _mpl()
    nx = _nx()
    from matplotlib.patches import Patch

    if topology is None:
        from src.claims_graph import designed_topology

        topology = designed_topology()
    nodes = list(topology.get("nodes") or [])
    edges = list(topology.get("edges") or [])
    per_condition: dict[str, list[str]] = topology.get("per_condition") or {}
    membership: dict[str, tuple[str, ...]] = {}
    for n in nodes:
        membership[n] = tuple(c for c in CONDITION_ORDER if n in (per_condition.get(c) or [])) or tuple(c for c in per_condition if n in per_condition[c])
    # One fill per distinct membership set, largest group first, so any number of conditions renders with a truthful legend.
    order_index = lambda c: CONDITION_ORDER.index(c) if c in CONDITION_ORDER else len(CONDITION_ORDER)  # noqa: E731
    groups = sorted({membership[n] for n in nodes if membership.get(n)}, key=lambda k: (-len(k), [order_index(c) for c in k]))
    fills: dict[tuple[str, ...], tuple[str, str]] = {}
    for i, key in enumerate(groups):
        label = "all conditions" if set(key) == set(per_condition) else (" + ".join(key) if len(key) > 1 else f"{key[0]} only")
        fills[key] = (MEMBERSHIP_FILLS[i % len(MEMBERSHIP_FILLS)], label)
    G = nx.DiGraph()
    for n in ["START", *nodes, "END"]:
        G.add_node(n)
    for e in edges:
        G.add_edge(e["source"], e["target"], label=e.get("label") or "")
    pos = {n: _TOPOLOGY_POS.get(n, (float(i), -2.5)) for i, n in enumerate(G.nodes)}
    with plt.rc_context(_RC):
        fig, ax = plt.subplots(figsize=(13, 6.2))
        fig.subplots_adjust(top=0.86, bottom=0.12, left=0.02, right=0.98)
        ax.set_axis_off()
        ax.grid(False)
        node_size = 2600
        for key, (fill, _label) in fills.items():
            members = [n for n in nodes if membership.get(n) == key]
            if members:
                nx.draw_networkx_nodes(G, pos, nodelist=members, node_color=fill, edgecolors=INK, linewidths=1.1, node_shape="s", node_size=node_size, ax=ax)
        leftover = [n for n in nodes if membership.get(n) not in fills]
        if leftover:
            nx.draw_networkx_nodes(G, pos, nodelist=leftover, node_color=MISSING, edgecolors=INK, linewidths=1.1, node_shape="s", node_size=node_size, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=["START", "END"], node_color=MISSING, edgecolors=INK2, linewidths=1.0, node_shape="o", node_size=1100, ax=ax)
        straight = [(u, v) for u, v in G.edges if not (G.has_edge(v, u))]
        curved = [(u, v) for u, v in G.edges if G.has_edge(v, u)]
        loops_back = [(u, v) for u, v in straight if pos[u][0] > pos[v][0]]
        straight = [e for e in straight if e not in loops_back]
        nx.draw_networkx_edges(G, pos, edgelist=straight, edge_color=INK2, arrows=True, arrowsize=13, arrowstyle="-|>", node_size=node_size, width=1.2, ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=loops_back, edge_color=INK2, arrows=True, arrowsize=13, arrowstyle="-|>", node_size=node_size, width=1.2, connectionstyle="arc3,rad=0.35", ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=curved, edge_color=INK2, arrows=True, arrowsize=13, arrowstyle="-|>", node_size=node_size, width=1.2, connectionstyle="arc3,rad=0.25", ax=ax)
        nx.draw_networkx_labels(G, pos, labels={n: _wrap(n.replace("_", " "), 12) for n in G.nodes}, font_size=7.8, font_color=INK, ax=ax)
        labels = {(u, v): _wrap(d["label"], 22) for u, v, d in G.edges(data=True) if d.get("label")}
        for edge_list, rad in ((straight, 0.0), (loops_back, 0.35), (curved, 0.25)):
            sub = {e: labels[e] for e in edge_list if e in labels}
            if sub:
                nx.draw_networkx_edge_labels(
                    G, pos, edge_labels=sub, font_size=6.8, font_color=INK2, bbox={"boxstyle": "round,pad=0.15", "fc": PAPER, "ec": "none", "alpha": 0.9},
                    label_pos=0.5, rotate=False, connectionstyle=f"arc3,rad={rad}", node_size=node_size, ax=ax,
                )
        ax.set_xlim(-0.6, 10.6)
        ax.set_ylim(-2.1, 3.2)
        handles = [Patch(facecolor=fill, edgecolor=INK, label=label) for fill, label in fills.values()]
        handles.append(Patch(facecolor=MISSING, edgecolor=INK2, label="START / END"))
        fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.02, 0.02), ncol=4, title="node membership by condition", title_fontsize=8.5)
        subtitle = "Source: src/claims_graph.designed_topology() - the architecture as designed; edge labels are routing decisions. This is not measured behaviour."
        path = _finish(fig, "Designed LangGraph workflow (not observed performance)", subtitle, [], Path(out_path))
    return path


# --------------------------------------------------------------------------- render_all + manifest


def render_all(
    logs_dir: Path | str = LOGS_DIR,
    out_dir: Path | str = FIGURES_DIR,
    run_ids: list[str] | None = None,
    graphs_dir: Path | str | None = None,
) -> list[Path]:
    """Render the six log-derived figures into ``out_dir`` and write ``figures_manifest.json``. Returns the PNG paths."""
    out_dir = Path(out_dir)
    graphs_dir = Path(graphs_dir) if graphs_dir is not None else (GRAPHS_DIR if out_dir == FIGURES_DIR else out_dir.parent / "graphs")
    ensure_dir(out_dir)
    data = load_chart_data(logs_dir, run_ids)
    renderers = {
        "learning_curve": lambda p: render_learning_curve(data, p),
        "reliability_curve": lambda p: render_reliability_curve(data, p),
        "skill_accumulation": lambda p: render_skill_accumulation(data, p),
        "skill_utility": lambda p: render_skill_utility(data, p),
        "skill_lifecycle_graph": lambda p: render_skill_lifecycle_graph(data, p, copy_to=graphs_dir / LIFECYCLE_FILE),
        "rubric_heatmap": lambda p: render_rubric_heatmap(data, p),
    }
    paths: list[Path] = []
    entries: list[dict] = []
    for name, (file_name, title, description) in FIGURE_CATALOGUE.items():
        path, meta = renderers[name](out_dir / file_name)
        paths.append(path)
        entries.append({"name": name, "file": file_name, "path": rel(path), "title": title, "description": description, "run_ids": list(data.run_ids), **{k: v for k, v in meta.items() if k != "rows"}})
    manifest = {
        "generated_at": utc_now(),
        "logs_dir": rel(data.logs_dir),
        "run_ids": list(data.run_ids),
        "task_ids": list(data.task_ids),
        "condition_colors": dict(CONDITION_COLORS),
        "figures": entries,
        "skill_utility_rows": skill_utility_table(data),
        "status_file": rel(data.logs_dir / STATUS_FILE),
        "note": "Every figure is computed from the named log files; missing observations are drawn as missing and listed in 'notes'.",
    }
    atomic_write_json(out_dir / MANIFEST_FILE, manifest)
    return paths


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    p = argparse.ArgumentParser(prog="charts", description="Render the learning visuals from the JSONL logs (matplotlib Agg) and the designed topology.")
    p.add_argument("--run-id", action="append", dest="run_ids", default=None, help="restrict to this run id (repeatable); default: every run in the logs")
    p.add_argument("--logs-dir", default=str(LOGS_DIR))
    p.add_argument("--out-dir", default=str(FIGURES_DIR))
    p.add_argument("--graphs-dir", default=None)
    p.add_argument("--no-topology", action="store_true", help="skip the designed-topology diagram")
    args = p.parse_args(argv)
    paths = render_all(args.logs_dir, args.out_dir, args.run_ids, args.graphs_dir)
    for path in paths:
        print(f"figure written: {rel(path)}")
    print(f"manifest written: {rel(Path(args.out_dir) / MANIFEST_FILE)}")
    if not args.no_topology:
        graphs_dir = Path(args.graphs_dir) if args.graphs_dir else (GRAPHS_DIR if Path(args.out_dir) == FIGURES_DIR else Path(args.out_dir).parent / "graphs")
        print(f"topology written: {rel(render_topology(out_path=graphs_dir / TOPOLOGY_FILE))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
