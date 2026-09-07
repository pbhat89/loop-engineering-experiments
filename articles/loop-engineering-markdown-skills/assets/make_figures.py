"""Figures for the article, drawn only from the run_005 logs (experiment 3).

    uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py

Writes into this folder:
  hero.png                 typographic hero (author-made)
  loop_diagram.png         the loop as a plain diagram for a non-technical reader
  score_by_attempt.png     checker score after each attempt, one panel per task, three arms
  attempts_and_findings.png  attempts needed per task + problems found on the first try
  self_review_vs_checker.png what the self-reviewing agent declared vs what the checker found
Every number comes from logs/experiment_events.jsonl, logs/skill_events.jsonl and logs/graph_events.jsonl.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.utils import LOGS_DIR, read_jsonl  # noqa: E402

RUN_ID = "run_005"
TASKS = ["T2", "T4", "T3", "T7"]
TASK_LABEL = {
    "T2": "1 · Describe the book",
    "T4": "2 · Where denials happen",
    "T3": "3 · Providers & network",
    "T7": "4 · High-cost model",
}
TASK_SHORT = {"T2": "Describe\nthe book", "T4": "Where denials\nhappen", "T3": "Providers &\nnetwork", "T7": "High-cost\nmodel"}
ARMS = ["reflection_only", "skill_learning", "self_refine"]
ARM_LABEL = {"reflection_only": "Checker, no memory", "skill_learning": "Checker + skill notebook", "self_refine": "Self-review only"}
ARM_COLOR = {"reflection_only": "#0072B2", "skill_learning": "#009E73", "self_refine": "#D55E00"}
ARM_MARKER = {"reflection_only": "o", "skill_learning": "s", "self_refine": "^"}
PASS = 3.5
INK, INK2, LINE, PAPER = "#1b2a24", "#5b6b65", "#c9d1cc", "#fbfbf8"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12, "legend.fontsize": 11,
    "axes.edgecolor": LINE, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
})


# --------------------------------------------------------------------------- data
def load() -> dict:
    ev = [r for r in read_jsonl(LOGS_DIR / "experiment_events.jsonl") if r.get("run_id") == RUN_ID]
    sk = [r for r in read_jsonl(LOGS_DIR / "skill_events.jsonl") if r.get("run_id") == RUN_ID]
    gr = [r for r in read_jsonl(LOGS_DIR / "graph_events.jsonl") if r.get("run_id") == RUN_ID]
    attempts: dict[tuple[str, str], list[dict]] = defaultdict(list)
    done: dict[tuple[str, str], dict] = {}
    for r in ev:
        key = (r["condition"], r["task_id"])
        if r.get("status") == "attempt":
            attempts[key].append(r)
        elif r.get("status") == "done":
            done[key] = r
    for key in attempts:
        attempts[key].sort(key=lambda r: r["attempt"])
    verdicts: dict[tuple[str, int], dict] = {}
    for r in gr:
        if r.get("event_type") == "node_transition" and r.get("destination_node") == "self_evaluate" and r.get("verdict"):
            verdicts[(r["task_id"], int(r["attempt"]))] = r
    persisted = [r for r in sk if r.get("event") == "skill_persisted"]
    return {"attempts": attempts, "done": done, "verdicts": verdicts, "persisted": persisted}


# --------------------------------------------------------------------------- figure 1: score by attempt
def fig_score_by_attempt(d: dict) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 4.6), sharey=True)
    max_attempt = max(len(v) for v in d["attempts"].values())
    for ax, task in zip(axes, TASKS):
        ax.axhspan(PASS, 4.02, color="#009E73", alpha=0.07, lw=0)
        ax.axhline(PASS, color=INK2, lw=1, ls=(0, (4, 3)))
        for arm in ARMS:
            rows = d["attempts"].get((arm, task), [])
            xs = [r["attempt"] for r in rows]
            ys = [r["evaluator_score_total"] for r in rows]
            ax.plot(xs, ys, color=ARM_COLOR[arm], marker=ARM_MARKER[arm], ms=8, lw=2.2, label=ARM_LABEL[arm], zorder=3)
            for r in rows:  # star where the learned skill was actually applied in the plan
                if arm == "skill_learning" and r.get("skills_applied"):
                    ax.plot(r["attempt"], r["evaluator_score_total"], marker="*", ms=17, color="#f2c200", mec=INK, mew=0.8, zorder=4)
            if arm == "self_refine" and rows:
                last = rows[-1]
                ax.annotate("agent said\n\"done\"", (last["attempt"], last["evaluator_score_total"]), textcoords="offset points",
                            xytext=(14, -6), ha="left", va="center", fontsize=9.5, color=ARM_COLOR[arm])
        ax.set_title(TASK_LABEL[task], loc="left", fontweight="bold")
        ax.set_xticks(range(1, max_attempt + 1))
        ax.set_xlim(0.6, max_attempt + 0.4)
        ax.set_ylim(0, 4.15)
        ax.set_xlabel("attempt")
        ax.grid(axis="y", color=LINE, lw=0.6)
    axes[0].set_ylabel("checker score (0–4)")
    axes[0].text(0.62, PASS + 0.07, "pass mark 3.5", fontsize=9.5, color=INK2)
    handles, labels = axes[0].get_legend_handles_labels()
    handles.append(plt.Line2D([0], [0], marker="*", color="none", markerfacecolor="#f2c200", markeredgecolor=INK, ms=14, lw=0))
    labels.append("learned skill used in this plan")
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("The same four claims tasks, three ways of closing the loop (Haiku 4.5 as the analyst, frozen checker scoring every attempt)",
                 x=0.01, ha="left", fontsize=12.5, color=INK2)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(HERE / "score_by_attempt.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure 2: attempts + first-try problems
def fig_attempts_and_findings(d: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.8))
    width = 0.26
    x = list(range(len(TASKS)))
    for i, arm in enumerate(ARMS):
        offs = [xi + (i - 1) * width for xi in x]
        attempts = [len(d["attempts"].get((arm, t), [])) for t in TASKS]
        passed = [bool(d["done"][(arm, t)].get("passed")) for t in TASKS]
        bars = ax1.bar(offs, attempts, width, color=ARM_COLOR[arm], label=ARM_LABEL[arm],
                       hatch=["" if p else "//" for p in passed][0] if len(set(passed)) == 1 else None, edgecolor=PAPER, lw=0.8)
        for b, n, p in zip(bars, attempts, passed):
            if not p:
                b.set_hatch("//")
                b.set_alpha(0.75)
            ax1.text(b.get_x() + b.get_width() / 2, n + 0.06, f"{n}" + ("" if p else " ✗"), ha="center", va="bottom", fontsize=10.5, color=INK)
        firsts = [d["attempts"][(arm, t)][0].get("n_failed_checks", 0) for t in TASKS]
        bars2 = ax2.bar(offs, firsts, width, color=ARM_COLOR[arm], label=ARM_LABEL[arm], edgecolor=PAPER, lw=0.8)
        for b, n in zip(bars2, firsts):
            ax2.text(b.get_x() + b.get_width() / 2, n + 0.15, f"{n}", ha="center", va="bottom", fontsize=10.5, color=INK)
    for ax in (ax1, ax2):
        ax.set_xticks(x)
        ax.set_xticklabels([TASK_SHORT[t] for t in TASKS], fontsize=11)
        ax.grid(axis="y", color=LINE, lw=0.6)
        ax.set_axisbelow(True)
    ax1.set_title("Attempts until the checker passed the work", loc="left", fontweight="bold")
    ax1.set_ylabel("attempts (✗ = stopped without passing)")
    ax1.set_ylim(0, 3.7)
    ax1.set_yticks([0, 1, 2, 3])
    ax2.set_title("Problems the checker found on the first try", loc="left", fontweight="bold")
    ax2.set_ylabel("failed checks on attempt 1")
    # when the notebook had something in it (skill_learning arm only)
    ax2.text(0, 15.4, "notebook\nempty", ha="center", va="center", fontsize=9.5, color=INK2, style="italic")
    ax2.text(2.0, 15.4, "one learned skill in the notebook (task 1's denominator lesson)", ha="center", va="center", fontsize=9.5, color=INK2, style="italic")
    ax2.plot([0.75, 3.35], [14.6, 14.6], color=LINE, lw=1)
    ax2.set_ylim(0, 16.6)
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(HERE / "attempts_and_findings.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure 3: self review vs checker
def fig_self_review(d: dict) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axvspan(PASS, 4.05, color="#009E73", alpha=0.07, lw=0)
    ax.axvline(PASS, color=INK2, lw=1, ls=(0, (4, 3)))
    ax.text(PASS + 0.04, 3.55, "pass mark 3.5", fontsize=9.5, color=INK2)
    for i, task in enumerate(TASKS):
        rows = d["attempts"][("self_refine", task)]
        y = len(TASKS) - 1 - i
        scores = [r["evaluator_score_total"] for r in rows]
        ax.plot(scores, [y] * len(scores), color=LINE, lw=3, zorder=1)
        for r in rows:
            v = d["verdicts"].get((task, r["attempt"]))
            verdict = (v or {}).get("verdict")
            passed = bool(r.get("passed"))
            face = "#009E73" if passed else "#D55E00"
            ax.scatter(r["evaluator_score_total"], y, s=170, color=face, edgecolor=INK, lw=0.8, zorder=3)
            label = {"accept": "said: done", "revise": "said: revise"}.get(verdict, "")
            below = r["attempt"] % 2 == 1 and len(rows) > 1
            ax.annotate(f"try {r['attempt']} · {label}", (r["evaluator_score_total"], y), textcoords="offset points",
                        xytext=(0, -24 if below else 13), ha="center", fontsize=9.5)
        final = rows[-1]
        ax.text(4.1, y, "checker: pass" if final.get("passed") else "checker: FAIL", va="center", fontsize=11,
                color="#009E73" if final.get("passed") else "#D55E00", fontweight="bold")
    ax.set_yticks(range(len(TASKS)))
    ax.set_yticklabels([TASK_LABEL[t] for t in reversed(TASKS)])
    ax.set_xlim(0, 4.9)
    ax.set_ylim(-0.6, len(TASKS) - 0.3)
    ax.set_xlabel("checker score of the attempt the agent was judging (the agent never saw this number)")
    fig.text(0.01, 0.965, "Marking its own homework", fontsize=13.5, fontweight="bold", va="top")
    fig.text(0.01, 0.905, "What the self-reviewing agent declared after each try, against the frozen checker's score of that same try", fontsize=11, color=INK2, va="top")
    ax.grid(axis="x", color=LINE, lw=0.6)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    fig.savefig(HERE / "self_review_vs_checker.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure 4: the loop diagram
def _box(ax, xy, w, h, text, fc, ec=INK, fs=12.5, bold=False, tc=INK, style="round,pad=0.02,rounding_size=0.08"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.35)


def _arrow(ax, a, b, text=None, color=INK, rad=0.0, tpos=(0, 0), fs=10.5, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=16, lw=1.6, color=color, connectionstyle=f"arc3,rad={rad}", linestyle=ls))
    if text:
        mx, my = (a[0] + b[0]) / 2 + tpos[0], (a[1] + b[1]) / 2 + tpos[1]
        ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=color, bbox=dict(fc=PAPER, ec="none", pad=1.5))


def fig_loop_diagram() -> None:
    fig, ax = plt.subplots(figsize=(13, 8.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8.8)
    ax.axis("off")
    agent, code, checker, memory = "#dfeee8", "#eef1ee", "#fbe9d9", "#fff4cc"
    # header: title + the three arms
    ax.text(0.3, 8.6, "One loop, three ways of closing it", fontsize=15, fontweight="bold", va="top")
    ax.text(0.3, 8.05, "Checker, no memory:   PLAN → RUN → CHECK → REFLECT & REVISE; nothing is kept between tasks", fontsize=11, va="top", color=INK2)
    ax.text(0.3, 7.65, "Checker + skill notebook:   the same, plus the notebook is read before planning and written after a pass", fontsize=11, va="top", color=INK2)
    ax.text(0.3, 7.25, "Self-review only:   CHECK still scores every attempt for the record, but the agent sees only its own review and decides when it is done",
            fontsize=11, va="top", color=INK2)
    # main row
    top, h = 5.3, 1.25
    _box(ax, (0.3, top), 1.9, h, "Brief\n(what the\nbusiness asked)", PAPER, fs=11.5)
    _box(ax, (2.6, top), 2.3, h, "PLAN\nthe agent picks the\nmethod & settings", agent, fs=11.5)
    _box(ax, (5.3, top), 2.3, h, "RUN\nfixed code executes\nthe plan", code, fs=11.5)
    _box(ax, (8.0, top), 2.6, h, "CHECK\nfrozen checker scores\nagainst the answer key", checker, fs=11.5)
    _box(ax, (11.0, top), 1.8, h, "Next task", PAPER, fs=12)
    mid = top + h / 2
    _arrow(ax, (2.2, mid), (2.6, mid))
    _arrow(ax, (4.9, mid), (5.3, mid))
    _arrow(ax, (7.6, mid), (8.0, mid))
    _arrow(ax, (10.6, mid), (11.0, mid), color="#0a7a4f")
    ax.text(11.9, top - 0.12, "pass: score ≥ 3.5\nand no critical miss", ha="center", va="top", fontsize=10, color="#0a7a4f")
    # retry loop
    _box(ax, (5.1, 2.75), 3.3, 1.25, "REFLECT & REVISE\nthe agent gets the 3 biggest\nproblems and fixes the plan", agent, fs=11.5)
    _arrow(ax, (8.7, top), (8.1, 4.0), color="#b3400a")
    ax.text(7.9, 4.75, "fail\n(up to 5 tries)", ha="right", va="center", fontsize=10, color="#b3400a")
    _arrow(ax, (5.1, 3.5), (3.9, top), color="#b3400a", rad=0.25)
    ax.text(3.95, 3.95, "new plan", fontsize=10, color="#b3400a", ha="center")
    # memory
    _box(ax, (8.9, 0.95), 3.9, 1.3, "SKILL NOTEBOOK\nMarkdown lessons the agent wrote\nitself, one per file, never edited", memory, ec="#b58a00", fs=11.5)
    _arrow(ax, (9.9, top), (10.8, 2.25), color="#8a6a00")
    ax.text(10.75, 3.95, "after a pass:\nwrite the reusable\nlesson", ha="left", va="center", fontsize=10, color="#8a6a00")
    # read path: notebook -> left along y=1.6 -> up into PLAN
    ax.plot([8.9, 3.3], [1.6, 1.6], color="#8a6a00", lw=1.6)
    _arrow(ax, (3.3, 1.6), (3.3, top), color="#8a6a00")
    ax.text(6.1, 1.28, "before planning: read the lessons whose trigger matches the task", ha="center", va="top", fontsize=10, color="#8a6a00")
    # legend / caption
    ax.text(0.3, 0.55, "Green = the agent (Claude Haiku 4.5, a fresh, memoryless subagent at every step).   Grey = deterministic pandas / scikit-learn.\n"
                       "Orange = 76 rubric checks over the four tasks, frozen before the run.   Yellow = the only thing that carries over between tasks.",
            fontsize=10, color=INK2, va="top", linespacing=1.5)
    fig.savefig(HERE / "loop_diagram.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- hero
def fig_hero() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    fig.patch.set_facecolor("#0f1f1a")
    ax.set_facecolor("#0f1f1a")
    import numpy as np
    t = np.linspace(0.15 * np.pi, 1.85 * np.pi, 300)
    cx, cy, r = 3.0, 2.7, 1.75
    ax.plot(cx + r * np.cos(t), cy + r * np.sin(t), color="#3fbf95", lw=9, solid_capstyle="round", alpha=0.95)
    ax.add_patch(FancyArrowPatch((cx + r * np.cos(0.22 * np.pi), cy + r * np.sin(0.22 * np.pi)), (cx + r * np.cos(0.145 * np.pi), cy + r * np.sin(0.145 * np.pi)),
                                 arrowstyle="-|>", mutation_scale=44, lw=0, color="#3fbf95"))
    for ang, word in ((90, "plan"), (0, "run"), (270, "check"), (180, "learn")):
        a = np.deg2rad(ang)
        ax.text(cx + (r + 0.62) * np.cos(a), cy + (r + 0.62) * np.sin(a), word, ha="center", va="center", fontsize=17, color="#e6ece8", fontweight="bold")
    ax.text(6.1, 3.55, "Teaching a claims analyst agent\nthe house rules", fontsize=27, color="#f4f6f3", fontweight="bold", va="center", linespacing=1.2)
    ax.text(6.1, 2.05, "Four claims questions · one frozen answer key · three ways of closing the loop\nSynthetic data, real pipeline, every number from the logs",
            fontsize=13.5, color="#9baaa3", va="center", linespacing=1.55)
    fig.savefig(HERE / "hero.png", dpi=170, bbox_inches="tight", facecolor="#0f1f1a")
    plt.close(fig)


def main() -> int:
    d = load()
    fig_score_by_attempt(d)
    fig_attempts_and_findings(d)
    fig_self_review(d)
    fig_loop_diagram()
    fig_hero()
    for name in ("hero", "loop_diagram", "score_by_attempt", "attempts_and_findings", "self_review_vs_checker"):
        print("wrote", HERE / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
