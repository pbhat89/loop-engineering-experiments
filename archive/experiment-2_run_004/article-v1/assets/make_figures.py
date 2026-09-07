"""Article figures for experiment 2, computed only from logs/ (run_004). Image by Author.

    uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from src.utils import read_jsonl  # noqa: E402

RUN = "run_004"
OUT = Path(__file__).resolve().parent
COND = {
    "baseline": ("#0072B2", "no memory"),
    "reflection_only": ("#E69F00", "reflection within a task"),
    "skill_learning": ("#009E73", "persistent Markdown skills"),
}
TASKS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
DIMS = ["correctness", "completeness", "reproducibility", "statistical_discipline", "communication"]
INK, INK2, GRID = "#1f2328", "#57606a", "#e4e6ea"
plt.rcParams.update(
    {"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2}
)

events = [r for r in read_jsonl(REPO / "logs" / "experiment_events.jsonl") if r["run_id"] == RUN]
first: dict = defaultdict(dict)
done: dict = defaultdict(dict)
for r in events:
    if r["status"] == "attempt" and r["attempt"] == 1:
        first[r["condition"]][r["task_id"]] = r
    if r["status"] == "done":
        done[r["condition"]][r["task_id"]] = r
skill_events = [r for r in read_jsonl(REPO / "logs" / "skill_events.jsonl") if r["run_id"] == RUN]


def style(ax, title: str, subtitle: str) -> None:
    ax.set_title(title, loc="left", fontsize=13, fontweight="semibold", color=INK, pad=22)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color=INK2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


# 1. first-attempt rubric score by task ---------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150)
for i, (cond, (color, label)) in enumerate(COND.items()):
    ys = [first[cond][t]["evaluator_score_total"] for t in TASKS]
    xs = [k + (i - 1) * 0.06 for k in range(len(TASKS))]
    ax.plot(xs, ys, marker="o", ms=6, lw=2, color=color, label=f"{cond} - {label}", zorder=3)
ax.axhline(3.5, ls="--", color=INK2, lw=1)
ax.text(len(TASKS) - 0.6, 3.55, "pass threshold 3.5", ha="right", fontsize=9, color=INK2)
ax.set_xticks(range(len(TASKS)), TASKS)
ax.set_ylim(0, 4.2)
ax.set_ylabel("first-attempt rubric score (0-4)")
ax.set_xlabel("task, fixed suite order")
style(ax, "First-attempt quality by task", f"source: logs/experiment_events.jsonl - run {RUN} - status=attempt, attempt=1 - baseline and reflection_only coincide")
ax.legend(frameon=False, loc="lower right", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "first_attempt_by_task.png")

# 2. per-dimension first-attempt means, T2-T8 ------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
width = 0.36
for i, cond in enumerate(("baseline", "skill_learning")):
    means = [sum(first[cond][t]["evaluator_score_by_dimension"][d] for t in TASKS[1:]) / 7 for d in DIMS]
    xs = [k + (i - 0.5) * width for k in range(len(DIMS))]
    bars = ax.bar(xs, means, width=width - 0.04, color=COND[cond][0], label=cond, zorder=3)
    for b, m in zip(bars, means):
        ax.text(b.get_x() + b.get_width() / 2, m + 0.06, f"{m:.2f}", ha="center", fontsize=8.5, color=INK)
ax.set_xticks(range(len(DIMS)), [d.replace("_", "\n") for d in DIMS])
ax.set_ylim(0, 4.2)
ax.set_ylabel("mean first-attempt score, T2-T8 (0-4)")
style(ax, "Where the conventions land: gains by rubric dimension", f"source: logs/experiment_events.jsonl - run {RUN} - reflection_only equals baseline on first attempts")
ax.legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "dimension_gains.png")

# 3. skill reuse matrix ------------------------------------------------------------------------
created = {r["skill_id"]: r["task_id"] for r in skill_events if r["event"] == "skill_persisted"}
skills = sorted(created)
fig, ax = plt.subplots(figsize=(9, 3.6), dpi=150)
green = COND["skill_learning"][0]
for row, sid in enumerate(skills):
    for col, t in enumerate(TASKS):
        applied = sid in (done["skill_learning"][t].get("skills_reused") or [])
        if t == created[sid]:
            ax.add_patch(FancyBboxPatch((col - 0.4, row - 0.4), 0.8, 0.8, boxstyle="round,pad=0.02", fc="white", ec=green, lw=1.6))
            ax.text(col, row, "created", ha="center", va="center", fontsize=7.5, color=INK2)
        elif applied:
            ax.add_patch(FancyBboxPatch((col - 0.4, row - 0.4), 0.8, 0.8, boxstyle="round,pad=0.02", fc=green, ec="white", lw=1.2))
            ax.text(col, row, "applied", ha="center", va="center", fontsize=7.5, color="white")
ax.set_xlim(-0.6, len(TASKS) - 0.4)
ax.set_ylim(len(skills) - 0.4, -0.6)
ax.set_xticks(range(len(TASKS)), TASKS)
ax.set_yticks(range(len(skills)), [f"{s.split('_')[-1]} - after {created[s]}" for s in skills])
ax.set_ylabel("evolved skill")
ax.grid(False)
style(ax, "Which learned skill fired on which later task", f"source: logs/skill_events.jsonl (skill_persisted, skill_reused) - run {RUN} - skill_learning condition")
for side in ("left", "bottom"):
    ax.spines[side].set_visible(False)
ax.tick_params(length=0)
fig.tight_layout()
fig.savefig(OUT / "skill_reuse_matrix.png")

# 4. the loop, as built ------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 3.8), dpi=150)
ax.set_xlim(0, 12)
ax.set_ylim(0, 3.8)
ax.axis("off")
W, H, Y = 1.72, 0.9, 2.0
boxes = [
    (1.0, "retrieve\nskills", "#009E73"),
    (3.0, "plan\ncatalogue choices", INK2),
    (5.0, "execute\ndeterministic code", INK2),
    (7.0, "evaluate\nfrozen goldens + rubric", "#0072B2"),
    (9.0, "reflect\non feedback", "#E69F00"),
    (11.0, "propose, validate,\npersist a skill", "#009E73"),
]
for x, label, color in boxes:
    ax.add_patch(FancyBboxPatch((x - W / 2, Y - H / 2), W, H, boxstyle="round,pad=0.04", fc="white", ec=color, lw=1.8))
    ax.text(x, Y, label, ha="center", va="center", fontsize=8.4, color=INK)
for (x1, *_), (x2, *_) in zip(boxes, boxes[1:]):
    ax.add_patch(FancyArrowPatch((x1 + W / 2 + 0.02, Y), (x2 - W / 2 - 0.02, Y), arrowstyle="-|>", mutation_scale=12, color=INK2, lw=1.4))
# retry: evaluate -> plan (revise), below the row
ax.add_patch(FancyArrowPatch((7.0, Y - H / 2), (3.0, Y - H / 2), arrowstyle="-|>", mutation_scale=12, color="#E69F00", lw=1.5, connectionstyle="arc3,rad=0.32"))
ax.text(5.0, 0.42, "retry: revise the plan (at most 2 per task)", ha="center", fontsize=8.6, color="#E69F00")
# memory: persist -> retrieve on the next task, above the row
ax.add_patch(FancyArrowPatch((11.0, Y + H / 2), (1.0, Y + H / 2), arrowstyle="-|>", mutation_scale=12, color="#009E73", lw=1.7, connectionstyle="arc3,rad=-0.24"))
ax.text(6.0, 3.55, "next task: the versioned Markdown skill is retrieved by tag", ha="center", fontsize=8.8, color="#009E73")
ax.text(0.15, 0.05, "One LangGraph StateGraph. The Python runtime makes no model calls; in experiment 2 the planner is a deterministic rule learner.", fontsize=8, color=INK2)
fig.savefig(OUT / "loop_diagram.png", bbox_inches="tight")

# 5. hero: abstract loop ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 4.2), dpi=150)
fig.patch.set_facecolor("#f7f7f5")
ax.set_facecolor("#f7f7f5")
ax.axis("off")
theta = np.linspace(0, 2 * np.pi, 400)
for k, (color, r) in enumerate([("#0072B2", 1.25), ("#E69F00", 1.55), ("#009E73", 1.85)]):
    ax.plot(2.9 * r * np.cos(theta), r * np.sin(theta), color=color, lw=2.2 + k, alpha=0.9)
for t in TASKS:
    ang = 2 * np.pi * (TASKS.index(t) + 0.5) / len(TASKS)
    ax.text(2.9 * 1.85 * np.cos(ang) * 1.1, 1.85 * np.sin(ang) * 1.16, t, ha="center", va="center", fontsize=10, color=INK2)
ax.text(0, 0.16, "plan → execute → evaluate → reflect → skill", ha="center", fontsize=13, color=INK, fontweight="bold")
ax.text(0, -0.26, "external procedural memory in Markdown,\ngraded against a frozen golden pack", ha="center", va="top", fontsize=9.5, color=INK2, linespacing=1.4)
ax.set_xlim(-6.0, 6.0)
ax.set_ylim(-2.5, 2.5)
fig.savefig(OUT / "hero_loop.png", bbox_inches="tight", facecolor=fig.get_facecolor())
print("figures written:", sorted(p.name for p in OUT.glob("*.png")))
