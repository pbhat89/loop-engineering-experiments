"""Figures for the article, drawn from one run's logs (default run_006, experiment 4)
plus an optional second run (default run_007, experiment 5) that continues three of
the five arms onto three held-out tasks (run_008, memory frozen).

    uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py \
        [--run-id RUN_ID] [--logs LOGS_DIR] \
        [--transfer-run TRANSFER_RUN_ID] [--transfer-logs TRANSFER_LOGS_DIR] \
        [--out OUT_DIR]

Writes into --out (default: this folder):
  hero.png            typographic hero (author-made, unchanged)
  loop_diagram.png     the loop as a plain diagram for a non-technical reader, all five arms
  results_grid.png     attempts-to-pass and final score, one cell per (task, arm) -- the
                        main results figure; grows a "held-out" block of rows underneath
                        when --transfer-run has records
  oneshot_test.png     first attempt only (no feedback yet) on the three held-out tasks --
                        three employees given the same tasks, one attempt each, nothing
                        learned during the test -- only drawn when --transfer-run has
                        records; skipped without error otherwise
Every number comes from <logs>/experiment_events.jsonl, <logs>/skill_events.jsonl and
<logs>/graph_events.jsonl for --run-id, and the same files under --transfer-logs (default:
the same directory as --logs) for --transfer-run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.utils import LOGS_DIR as DEFAULT_LOGS_DIR, read_jsonl  # noqa: E402

TASKS = ["T1", "T2", "T4", "T3", "T7", "T8"]
TASK_LABEL = {
    "T1": "1 · Data check",
    "T2": "2 · Describe the book",
    "T4": "3 · Where denials happen",
    "T3": "4 · Providers & network",
    "T7": "5 · High-cost model",
    "T8": "6 · Executive brief",
}
TASK_SHORT = {
    "T1": "1 · Data\ncheck",
    "T2": "2 · Describe\nthe book",
    "T4": "3 · Where denials\nhappen",
    "T3": "4 · Providers &\nnetwork",
    "T7": "5 · High-cost\nmodel",
    "T8": "6 · Executive\nbrief",
}
ARMS = ["reflection_only", "feedback_memory", "skill_learning", "self_refine", "self_refine_memory"]
ARM_LABEL = {
    "reflection_only": "Checker only",
    "feedback_memory": "Checker + raw log",
    "skill_learning": "Checker + skills",
    "self_refine": "Self-review only",
    "self_refine_memory": "Self-review + raw log",
}
ARM_COLOR = {
    "reflection_only": "#0072B2",
    "feedback_memory": "#56B4E9",
    "skill_learning": "#009E73",
    "self_refine": "#D55E00",
    "self_refine_memory": "#8C564B",
}
MEMORY_ARMS = {"feedback_memory", "self_refine_memory"}
SKILL_ARM = "skill_learning"

# Experiment 5: run_007 continues three of the five arms onto three held-out tasks (run_008, memory frozen) that
# reuse the same conventions but ask different questions. Article numbering continues
# 7-10 from the six run_006 tasks above.
TRANSFER_TASKS = ["T11", "T12", "T13"]
TRANSFER_TASK_LABEL = {
    "T11": "7 · Portfolio deep-dive",
    "T12": "8 · High-cost model (top 10 %)",
    "T13": "9 · Brief for the CFO",
}
TRANSFER_TASK_SHORT = {
    "T11": "7 · Portfolio\ndeep-dive",
    "T12": "8 · High-cost\nmodel (top 10 %)",
    "T13": "9 · Brief for\nthe CFO",
}
TRANSFER_ARMS = ["reflection_only", "feedback_memory", "skill_learning"]
INK, INK2, LINE, PAPER = "#1b2a24", "#5b6b65", "#c9d1cc", "#fbfbf8"
FAIL = "#b3400a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12, "legend.fontsize": 11,
    "axes.edgecolor": LINE, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
})


# --------------------------------------------------------------------------- data
def load(run_id: str, logs_dir: Path, tasks: list[str] = TASKS, arms: list[str] = ARMS) -> dict:
    ev = [r for r in read_jsonl(logs_dir / "experiment_events.jsonl") if r.get("run_id") == run_id]
    sk = [r for r in read_jsonl(logs_dir / "skill_events.jsonl") if r.get("run_id") == run_id]
    attempts: dict[tuple[str, str], list[dict]] = {}
    done: dict[tuple[str, str], dict] = {}
    for r in ev:
        key = (r["condition"], r["task_id"])
        if r.get("status") == "attempt":
            attempts.setdefault(key, []).append(r)
        elif r.get("status") == "done":
            done[key] = r
    for key in attempts:
        attempts[key].sort(key=lambda r: r["attempt"])
    persisted = [r for r in sk if r.get("event") == "skill_persisted"]

    # Self-review arms are exactly those whose done record carries a self-declared
    # verdict (see docs/OPERATOR_PROTOCOL.md); check that against the fixed ARM_LABEL
    # names so a future arm rename or reorder can't silently drift out of sync.
    for arm in arms:
        rows = [done[(arm, t)] for t in tasks if (arm, t) in done]
        is_self_review = any(r.get("self_declared_pass") is not None for r in rows)
        expected = "self-review" in ARM_LABEL[arm].lower()
        if rows:
            assert is_self_review == expected, f"arm classification mismatch for {arm}"
    return {"attempts": attempts, "done": done, "persisted": persisted}


# --------------------------------------------------------------------------- figure: results grid
def fig_results_grid(d: dict, out_dir: Path, d_transfer: dict | None = None) -> None:
    attempts, done = d["attempts"], d["done"]
    n_arms, n_tasks = len(ARMS), len(TASKS)
    all_attempt_lists = list(attempts.values())
    if d_transfer:
        all_attempt_lists += list(d_transfer["attempts"].values())
    max_attempts = max([len(v) for v in all_attempt_lists] + [1])

    label_w, cell_w = 2.55, 1.9
    header_h, row_h, total_h = 1.05, 0.95, 1.05
    grid_w = label_w + n_arms * cell_w
    grid_h = header_h + n_tasks * row_h + total_h

    n_transfer_tasks = len(TRANSFER_TASKS)
    divider_gap, group_label_h = 0.18, 0.4
    if d_transfer:
        grid_h += divider_gap + group_label_h + n_transfer_tasks * row_h + total_h

    fig, ax = plt.subplots(figsize=(12, 9.5) if d_transfer else (12, 6.5))
    ax.set_xlim(0, grid_w)
    ax.set_ylim(0, grid_h)
    ax.axis("off")
    ax.set_facecolor(PAPER)

    def col_x(i: int) -> float:
        return label_w + i * cell_w

    def row_y(j: int) -> float:  # j=0 is the first task row, counting down from the header
        return grid_h - header_h - (j + 1) * row_h

    # column headers (wrap at " + " so the two longest labels stay inside their cell)
    for i, arm in enumerate(ARMS):
        x = col_x(i)
        header_label = ARM_LABEL[arm].replace(" + ", "\n+ ")
        ax.add_patch(Rectangle((x, grid_h - header_h), cell_w, header_h, fc=mcolors.to_rgba(ARM_COLOR[arm], 0.12),
                                ec=LINE, lw=1.0))
        ax.text(x + cell_w / 2, grid_h - header_h / 2, header_label, ha="center", va="center",
                fontsize=10.8, fontweight="bold", color=ARM_COLOR[arm], linespacing=1.25)

    # cells
    light_rgb = mcolors.to_rgb("#e7f0fa")
    dark_rgb = mcolors.to_rgb("#08306b")
    for j, task in enumerate(TASKS):
        y = row_y(j)
        ax.text(label_w - 0.2, y + row_h / 2, TASK_SHORT[task], ha="right", va="center", fontsize=10.5,
                fontweight="bold", color=INK, linespacing=1.2)
        for i, arm in enumerate(ARMS):
            x = col_x(i)
            rows = attempts.get((arm, task), [])
            rec = done.get((arm, task), {})
            n = len(rows)
            frac = 0.0 if max_attempts <= 1 else (n - 1) / (max_attempts - 1)
            face = tuple(l + (dd - l) * frac for l, dd in zip(light_rgb, dark_rgb))
            passed = bool(rec.get("passed"))
            ax.add_patch(Rectangle((x, y), cell_w, row_h, fc=face, ec=LINE, lw=1.0))
            if not passed:
                ax.add_patch(Rectangle((x, y), cell_w, row_h, fc="none", ec=FAIL, lw=1.2, hatch="////"))
            text_color = "#f2f6fb" if frac > 0.55 else INK
            label = f"{n}" + ("" if passed else " ✗")
            ax.text(x + cell_w / 2, y + row_h / 2 + 0.135, label, ha="center", va="center",
                    fontsize=21, fontweight="bold", color=text_color if passed else FAIL)
            score = rec.get("evaluator_score_total")
            if score is not None:
                ax.text(x + cell_w / 2, y + row_h / 2 - 0.25, f"{score:.2f}", ha="center", va="center",
                        fontsize=9.5, color=text_color)
            if arm == SKILL_ARM and any(a.get("skills_applied") for a in rows):
                ax.plot(x + cell_w - 0.24, y + row_h - 0.2, marker="*", ms=13, color="#f2c200",
                        mec=INK, mew=0.6, zorder=5, clip_on=False)
            if arm in MEMORY_ARMS and rec.get("past_feedback_count", 0) > 0:
                ax.plot(x + cell_w - 0.24, y + row_h - 0.2, marker="D", ms=7, color="#8C564B",
                        mec=INK, mew=0.5, zorder=5, clip_on=False)

    # total row
    ty = row_y(n_tasks - 1) - total_h
    ax.add_patch(Rectangle((0, ty), label_w, total_h, fc=PAPER, ec="none"))
    ax.text(label_w - 0.2, ty + total_h / 2, "Total attempts ·\ntasks passed", ha="right", va="center",
            fontsize=9.5, fontweight="bold", color=INK2, linespacing=1.2)
    for i, arm in enumerate(ARMS):
        x = col_x(i)
        total_attempts = sum(len(attempts.get((arm, t), [])) for t in TASKS)
        n_passed = sum(1 for t in TASKS if done.get((arm, t), {}).get("passed"))
        ax.add_patch(Rectangle((x, ty), cell_w, total_h, fc="#eef1ee", ec=LINE, lw=1.2))
        ax.text(x + cell_w / 2, ty + total_h / 2, f"{total_attempts} · {n_passed}/{n_tasks}", ha="center", va="center",
                fontsize=13, fontweight="bold", color=INK)

    # held-out block (experiment 5: run_007 continues three arms onto four new tasks)
    if d_transfer:
        attempts_t, done_t = d_transfer["attempts"], d_transfer["done"]
        divider_y = ty - divider_gap / 2
        ax.plot([0, grid_w], [divider_y, divider_y], color=LINE, lw=1.4)
        group_top = ty - divider_gap
        ax.text(0.02, group_top - group_label_h / 2, "HELD-OUT TEST  ·  run_008  ·  memory frozen", ha="left", va="center",
                fontsize=9.5, fontweight="bold", color=INK2, style="italic")

        def row_y2(k: int) -> float:
            return group_top - group_label_h - (k + 1) * row_h

        for k, task in enumerate(TRANSFER_TASKS):
            y = row_y2(k)
            ax.text(label_w - 0.2, y + row_h / 2, TRANSFER_TASK_SHORT[task], ha="right", va="center",
                    fontsize=10.5, fontweight="bold", color=INK, linespacing=1.2)
            for i, arm in enumerate(ARMS):
                x = col_x(i)
                if arm not in TRANSFER_ARMS:
                    ax.add_patch(Rectangle((x, y), cell_w, row_h, fc=PAPER, ec=LINE, lw=1.0))
                    ax.text(x + cell_w / 2, y + row_h / 2, "—", ha="center", va="center",
                            fontsize=17, color=INK2, alpha=0.55)
                    continue
                rows = attempts_t.get((arm, task), [])
                rec = done_t.get((arm, task), {})
                n = len(rows)
                frac = 0.0 if max_attempts <= 1 else (n - 1) / (max_attempts - 1)
                face = tuple(l + (dd - l) * frac for l, dd in zip(light_rgb, dark_rgb))
                passed = bool(rec.get("passed"))
                ax.add_patch(Rectangle((x, y), cell_w, row_h, fc=face, ec=LINE, lw=1.0))
                if not passed:
                    ax.add_patch(Rectangle((x, y), cell_w, row_h, fc="none", ec=FAIL, lw=1.2, hatch="////"))
                text_color = "#f2f6fb" if frac > 0.55 else INK
                label = f"{n}" + ("" if passed else " ✗")
                ax.text(x + cell_w / 2, y + row_h / 2 + 0.135, label, ha="center", va="center",
                        fontsize=21, fontweight="bold", color=text_color if passed else FAIL)
                score = rec.get("evaluator_score_total")
                if score is not None:
                    ax.text(x + cell_w / 2, y + row_h / 2 - 0.25, f"{score:.2f}", ha="center", va="center",
                            fontsize=9.5, color=text_color)
                if arm == SKILL_ARM and any(a.get("skills_applied") for a in rows):
                    ax.plot(x + cell_w - 0.24, y + row_h - 0.2, marker="*", ms=13, color="#f2c200",
                            mec=INK, mew=0.6, zorder=5, clip_on=False)
                if arm in MEMORY_ARMS and rec.get("past_feedback_count", 0) > 0:
                    ax.plot(x + cell_w - 0.24, y + row_h - 0.2, marker="D", ms=7, color="#8C564B",
                            mec=INK, mew=0.5, zorder=5, clip_on=False)

        # held-out totals row
        ty2 = row_y2(n_transfer_tasks - 1) - total_h
        ax.add_patch(Rectangle((0, ty2), label_w, total_h, fc=PAPER, ec="none"))
        ax.text(label_w - 0.2, ty2 + total_h / 2, "Held-out: attempts ·\npassed", ha="right", va="center",
                fontsize=9.5, fontweight="bold", color=INK2, linespacing=1.2)
        for i, arm in enumerate(ARMS):
            x = col_x(i)
            if arm not in TRANSFER_ARMS:
                ax.add_patch(Rectangle((x, ty2), cell_w, total_h, fc=PAPER, ec=LINE, lw=1.0))
                ax.text(x + cell_w / 2, ty2 + total_h / 2, "—", ha="center", va="center",
                        fontsize=17, color=INK2, alpha=0.55)
                continue
            total_attempts = sum(len(attempts_t.get((arm, t), [])) for t in TRANSFER_TASKS)
            n_passed = sum(1 for t in TRANSFER_TASKS if done_t.get((arm, t), {}).get("passed"))
            ax.add_patch(Rectangle((x, ty2), cell_w, total_h, fc="#eef1ee", ec=LINE, lw=1.2))
            ax.text(x + cell_w / 2, ty2 + total_h / 2, f"{total_attempts} · {n_passed}/{n_transfer_tasks}",
                    ha="center", va="center", fontsize=13, fontweight="bold", color=INK)

    # title / subtitle (figure-fraction text sitting in the margin tight_layout reserves above the grid)
    fig.text(0.012, 0.99, "How many tries each loop design needed on each task", fontsize=15.5, fontweight="bold", va="top")
    fig.text(0.012, 0.935,
             "number = attempts until the frozen checker passed (✗ = stopped without passing) · small text = final checker score out of 4",
             fontsize=10.3, color=INK2, va="top")
    fig.text(0.012, 0.9,
             "★ = a learned skill was used on that attempt   ·   ◆ = past comments were available for that task",
             fontsize=10.3, color=INK2, va="top")

    fig.tight_layout(rect=(0, 0.005, 1, 0.865))
    fig.savefig(out_dir / "results_grid.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure: one-shot test
ONESHOT_ARMS = [
    ("reflection_only", "New joiner — checker only, nothing carried"),
    ("feedback_memory", "Colleague A — carries a raw log of past comments"),
    ("skill_learning", "Colleague B — carries two self-written skills"),
]
ONESHOT_SHORT = {"reflection_only": "New joiner", "feedback_memory": "Colleague A", "skill_learning": "Colleague B"}


def fig_oneshot(d_transfer: dict, out_dir: Path) -> None:
    """Three employees given the same three held-out tasks, one attempt each, no feedback,
    nothing learned during the test: first attempt only (status == attempt, attempt == 1)
    from the transfer run, per (task, employee)."""
    attempts = d_transfer["attempts"]
    first: dict[tuple[str, str], tuple[int, bool, float]] = {}
    for arm, _ in ONESHOT_ARMS:
        for task in TRANSFER_TASKS:
            rows = [r for r in attempts.get((arm, task), []) if r.get("attempt") == 1]
            if rows:
                r = rows[0]
                first[(arm, task)] = (r["n_failed_checks"], bool(r["passed"]), r["evaluator_score_total"])

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.8), gridspec_kw={"width_ratios": [2.2, 1.3]})

    # ---- left: problems the checker found in the single attempt, per task x employee
    x = list(range(len(TRANSFER_TASKS)))
    w = 0.26
    for i, (arm, label) in enumerate(ONESHOT_ARMS):
        offs = [xi + (i - 1) * w for xi in x]
        vals = [first[(arm, t)][0] for t in TRANSFER_TASKS]
        bars = ax.bar(offs, vals, w, color=ARM_COLOR[arm], label=label, edgecolor=PAPER, lw=0.8, zorder=3)
        for b, t in zip(bars, TRANSFER_TASKS):
            n, passed, _ = first[(arm, t)]
            mark_color = "#0a7a4f" if passed else FAIL
            ax.text(b.get_x() + b.get_width() / 2, n + 0.18, f"{n} {'✓' if passed else '✗'}",
                    ha="center", va="bottom", fontsize=10, color=mark_color,
                    fontweight="bold" if passed else "normal", zorder=4)

    max_problems = max(v[0] for v in first.values())
    ax.set_xticks(x)
    ax.set_xticklabels([TRANSFER_TASK_LABEL[t] for t in TRANSFER_TASKS], fontsize=10.5)
    ax.set_ylim(0, max_problems + 1.7)
    ax.set_ylabel("problems the checker found in the single attempt")
    ax.grid(axis="y", color=LINE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("One attempt, no feedback, nothing learned during the test", loc="left", fontweight="bold", fontsize=13)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=10.5)
    ax.text(0.5, -0.66, "number = problems found  ·  ✓ accepted  ·  ✗ sent back", transform=ax.transAxes,
            ha="center", va="top", fontsize=9, color=INK2)

    # ---- right: average score of the single attempt per employee
    means, accepted, problems = [], [], []
    for arm, _ in ONESHOT_ARMS:
        vals = [first[(arm, t)] for t in TRANSFER_TASKS]
        means.append(sum(v[2] for v in vals) / len(vals))
        accepted.append(sum(1 for v in vals if v[1]))
        problems.append(sum(v[0] for v in vals))

    bar_colors = [ARM_COLOR[arm] for arm, _ in ONESHOT_ARMS]
    bars = ax2.bar(range(3), means, 0.6, color=bar_colors, edgecolor=PAPER, zorder=3)
    for i, (b, m) in enumerate(zip(bars, means)):
        ax2.text(b.get_x() + b.get_width() / 2, m + 0.1, f"{m:.2f}", ha="center", va="bottom",
                  fontsize=12, fontweight="bold", color=bar_colors[i], zorder=4)

    ax2.axhline(3.5, color=INK2, lw=1.2, ls="--", zorder=2)
    ax2.text(2.35, 3.5, "pass mark", ha="left", va="center", fontsize=9.5, color=INK2, zorder=5,
             bbox=dict(fc=PAPER, ec="none", pad=1.5))

    ax2.set_xlim(-0.55, 3.05)
    ax2.set_ylim(0, 4.2)
    ax2.set_yticks([0, 1, 2, 3, 4])
    ax2.set_xticks(range(3))
    ax2.set_xticklabels([])
    ax2.tick_params(axis="x", length=0)
    for i, (arm, _) in enumerate(ONESHOT_ARMS):
        ax2.text(i, -0.06, ONESHOT_SHORT[arm], transform=ax2.get_xaxis_transform(),
                  ha="center", va="top", fontsize=9.5, fontweight="bold", color=INK)
        ax2.text(i, -0.16, f"accepted {accepted[i]} of {len(TRANSFER_TASKS)}", transform=ax2.get_xaxis_transform(),
                  ha="center", va="top", fontsize=8.3, color=INK2)
        ax2.text(i, -0.245, f"{problems[i]} problem" + ("s" if problems[i] != 1 else ""),
                  transform=ax2.get_xaxis_transform(), ha="center", va="top", fontsize=8.3, color=INK2)
    ax2.set_ylabel("average score of the single attempt (0–4)")
    ax2.grid(axis="y", color=LINE, lw=0.6, zorder=0)
    ax2.set_axisbelow(True)
    ax2.set_title("Average score of the single attempt", loc="left", fontweight="bold", fontsize=12)

    fig.text(0.1, 0.975,
             "Same frozen checker, same tasks, same model. The colleagues carry what they learned on six earlier\n"
             "tasks; nothing is added during the test.",
             fontsize=10.3, color=INK2, va="top", linespacing=1.4)

    fig.subplots_adjust(left=0.065, right=0.965, top=0.74, bottom=0.34, wspace=0.32)
    fig.savefig(out_dir / "oneshot_test.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- the loop diagram
def _box(ax, xy, w, h, text, fc, ec=INK, fs=12.5, bold=False, tc=INK, style="round,pad=0.02,rounding_size=0.08"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=tc, linespacing=1.35)


def _arrow(ax, a, b, text=None, color=INK, rad=0.0, tpos=(0, 0), fs=10.5, ls="-"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=16, lw=1.6, color=color, connectionstyle=f"arc3,rad={rad}", linestyle=ls))
    if text:
        mx, my = (a[0] + b[0]) / 2 + tpos[0], (a[1] + b[1]) / 2 + tpos[1]
        ax.text(mx, my, text, ha="center", va="center", fontsize=fs, color=color, bbox=dict(fc=PAPER, ec="none", pad=1.5))


def fig_loop_diagram(out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 9.6))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10.3)
    ax.axis("off")
    agent, code, checker, memory = "#dfeee8", "#eef1ee", "#fbe9d9", "#fff4cc"
    # header: title + the five arms, one short line each
    ax.text(0.3, 10.1, "One loop, five ways of closing it", fontsize=15, fontweight="bold", va="top")
    ax.text(0.3, 9.55, "Checker only:   PLAN → RUN → CHECK → REFLECT & REVISE; nothing is kept between tasks",
            fontsize=11, va="top", color=INK2)
    ax.text(0.3, 9.15, "Checker + raw log:   the same as Checker only, plus every past checker comment is shown before planning",
            fontsize=11, va="top", color=INK2)
    ax.text(0.3, 8.75, "Checker + skills:   the same as Checker only, plus the notebook is read before planning and written after a pass",
            fontsize=11, va="top", color=INK2)
    ax.text(0.3, 8.35, "Self-review only:   CHECK still scores every attempt for the record, but the agent sees only its own review and decides when it is done",
            fontsize=11, va="top", color=INK2)
    ax.text(0.3, 7.95, "Self-review + raw log:   the same as Self-review only, plus its own past review notes are shown before planning",
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
    # memory: raw notes (the two raw-log arms) or self-written skills (the skill arm)
    _box(ax, (8.15, 0.75), 4.65, 1.8,
         "MEMORY — either raw notes of past findings\n(the two raw-log arms) or self-written skills\n(the skills arm)",
         memory, ec="#b58a00", fs=11)
    _arrow(ax, (9.9, top), (10.5, 2.55), color="#8a6a00")
    ax.text(10.85, 3.95, "after each task: raw-log arms append;\nskills arm persists only after a pass",
            ha="left", va="center", fontsize=9.5, color="#8a6a00")
    # read path: memory -> left along y=1.6 -> up into PLAN
    ax.plot([8.15, 3.3], [1.6, 1.6], color="#8a6a00", lw=1.6)
    _arrow(ax, (3.3, 1.6), (3.3, top), color="#8a6a00")
    ax.text(0.3, 1.35, "before planning: raw-log arms see every\npast comment; the skills arm sees only matching skills",
            ha="left", va="top", fontsize=10, color="#8a6a00", linespacing=1.4)
    # legend / caption
    ax.text(0.3, 0.55, "Green = the agent (Claude Haiku 4.5, a fresh, memoryless subagent at every step).   Grey = deterministic pandas / scikit-learn.\n"
                       "Orange = the rubric checks for the six tasks, frozen before the run.   Yellow = the only thing that carries over between tasks.",
            fontsize=10, color=INK2, va="top", linespacing=1.5)
    fig.savefig(out_dir / "loop_diagram.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- hero
def fig_hero(out_dir: Path) -> None:
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
    fig.savefig(out_dir / "hero.png", dpi=170, bbox_inches="tight", facecolor="#0f1f1a")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="run_006")
    parser.add_argument("--logs", default=None, help="override for the logs directory (default: the repo logs/ dir)")
    parser.add_argument("--transfer-run", default="run_008", help="experiment-5 held-out test run (three tasks, memory frozen)")
    parser.add_argument("--transfer-logs", default=None, help="logs dir for --transfer-run (default: same as --logs)")
    parser.add_argument("--out", default=None, help="override for the output directory (default: this assets folder)")
    args = parser.parse_args()

    logs_dir = Path(args.logs) if args.logs else DEFAULT_LOGS_DIR
    transfer_logs_dir = Path(args.transfer_logs) if args.transfer_logs else logs_dir
    out_dir = Path(args.out) if args.out else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    d = load(args.run_id, logs_dir)
    d_transfer = load(args.transfer_run, transfer_logs_dir, TRANSFER_TASKS, TRANSFER_ARMS)
    has_transfer = bool(d_transfer["attempts"]) or bool(d_transfer["done"])

    fig_results_grid(d, out_dir, d_transfer if has_transfer else None)
    fig_loop_diagram(out_dir)
    fig_hero(out_dir)
    names = ["hero", "loop_diagram", "results_grid"]
    if has_transfer:
        fig_oneshot(d_transfer, out_dir)
        names.append("oneshot_test")
    for name in names:
        print("wrote", out_dir / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
