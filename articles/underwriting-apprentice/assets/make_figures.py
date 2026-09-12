"""Figures for the underwriting-apprentice article (experiment 7), drawn from one run's
per-case logs.

    .venv/Scripts/python.exe articles/underwriting-apprentice/assets/make_figures.py \
        --run-id RUN_ID [--root ROOT_DIR] [--out OUT_DIR] [--window N]

Reads ``<root>/<run-id>/<arm>/cases.jsonl`` for the four arms this article covers
(new_joiner, notebook, written_rules, precedent -- see ``ARM_ORDER`` below; the
ask_senior arm's logs stay on disk untouched but are never plotted here) and joins the
tier and fired rule ids in from ``data/underwriting/goldens.json`` at analysis time,
exactly as ``scripts/summarize_uw_run.py`` does (its ``load_run``/``summarize`` are
imported and reused directly here, so the two never drift apart).

Writes into --out (default: this folder):
  learning_curve.png   the article's closing chart -- cumulative (running) mean of
                        rating error (ladder steps) over all 38 files per arm: the 30
                        training cases in file order, then the 8 held-out cases, on one
                        shared axis with the held-out phase shaded
  holdout.png           horizontal bars: mean rating error on the 8 held-out cases per
                        arm, plus a thin bar for the 2 "novel rule" held-out cases
                        (golden fires only HR-13 or HR-14)
  what_each_gets.png     the shared five-step spine every case goes through, plus the
                        four-row table of what each design is handed and keeps, in
                        plain language for a non-technical reader

When --run-id starts with "uw_stub", every figure is stamped with a visible
"STUB DATA -- no model was called" watermark.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.patheffects as patheffects  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_uw_run import NOVEL_RULES, load_run, summarize  # noqa: E402

# --------------------------------------------------------------------------- shared look
# Same palette / type treatment as articles/loop-engineering-markdown-skills/assets/make_figures.py
INK, INK2, LINE, PAPER = "#1b2a24", "#5b6b65", "#c9d1cc", "#fbfbf8"
FAIL = "#b3400a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12, "legend.fontsize": 11,
    "axes.edgecolor": LINE, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
})

# The only four designs this article's figures ever show -- new joiner first. ask_senior's
# logs still exist on disk (see module docstring) but no code below iterates over it: every
# figure loops over this constant, so it is never plotted.
ARM_ORDER: tuple[str, ...] = ("new_joiner", "notebook", "written_rules", "precedent")
DISPLAY = {
    "new_joiner": "New joiner",
    "notebook": "Running notebook",
    "written_rules": "Written rules",
    "precedent": "Precedent file",
}
# Fixed per-arm colour, never cycled -- same colour-blind-safe (Okabe-Ito) palette as the
# loop-engineering article, reused here so an arm's colour never means two different things
# across the two articles.
ARM_COLOR = {
    "new_joiner": "#0072B2",
    "notebook": "#56B4E9",
    "written_rules": "#009E73",
    "precedent": "#D55E00",
}


def _stub_watermark(fig, run_id: str) -> None:
    if not run_id.startswith("uw_stub"):
        return
    fig.text(0.5, 0.5, "STUB DATA. No model was called", fontsize=34, fontweight="bold",
              color="#b3400a", alpha=0.28, ha="center", va="center", rotation=28, zorder=50)


def _spread_labels(values: dict[str, float], min_gap: float, anchor_first: tuple[str, ...] = ()) -> dict[str, float]:
    """Nudge label y-positions apart just enough to keep them from overlapping,
    preserving their relative order. When two or more series end in an exact tie,
    ``anchor_first`` says which of them keeps its label at the true value -- it is
    processed first within its tie group, so it is never the one pushed off zero (or
    off any other shared value); the rest of the tie absorbs the nudging instead."""
    order = sorted(values, key=lambda k: (values[k], 0 if k in anchor_first else 1))
    adjusted: dict[str, float] = {}
    prev = None
    for key in order:
        y = values[key]
        if prev is not None and y < prev + min_gap:
            y = prev + min_gap
        adjusted[key] = y
        prev = y
    return adjusted


# --------------------------------------------------------------------------- data
def load_summary(run_id: str, root: Path, window: int) -> dict:
    return summarize(run_id, root, window)


# --------------------------------------------------------------------------- figure A: learning curve
def fig_learning_curve(run_id: str, root: Path, out_dir: Path) -> None:
    """Cumulative (running) mean of ``ladder_distance`` over all 38 files per arm -- the
    30 training cases in file order, then the 8 held-out cases in their own case-index
    order, numbered 1..38 on one shared axis. No smoothing beyond the running mean
    itself: cum[n] is exactly the average of cases 1..n."""
    data_by_arm = load_run(run_id, root)["arms"]

    cum_by_arm: dict[str, list[float]] = {}
    last_values: dict[str, float] = {}
    max_y = 0.1
    n_train = n_holdout = 0
    for arm in ARM_ORDER:
        records = data_by_arm.get(arm)
        if not records:
            continue
        train = sorted((r for r in records if r["phase"] == "train"), key=lambda r: r["case_index"])
        held = sorted((r for r in records if r["phase"] == "holdout"), key=lambda r: r["case_index"])
        n_train, n_holdout = len(train), len(held)
        series = [float(r["ladder_distance"]) for r in train] + [float(r["ladder_distance"]) for r in held]
        cum: list[float] = []
        running_total = 0.0
        for i, value in enumerate(series, start=1):
            running_total += value
            cum.append(running_total / i)
        cum_by_arm[arm] = cum
        if cum:
            max_y = max(max_y, max(cum))
            last_values[arm] = cum[-1]

    n_cases = n_train + n_holdout  # 38
    split = n_train + 0.5  # 30.5 -- last training case to first held-out case

    fig, ax = plt.subplots(figsize=(12, 7.2))

    y_top = max_y * 1.15
    ax.set_ylim(-0.04, y_top)

    # held-out phase: memory is frozen and there is no feedback, shaded so the change in
    # regime is visible without needing the caption to explain it.
    ax.axvspan(split, n_cases + 0.5, color=INK2, alpha=0.10, lw=0, zorder=0)
    ax.axvline(split, color=INK, lw=1.1, alpha=0.6, zorder=1)
    ax.text((split + n_cases + 0.5) / 2, 0.965, "held-out test: memory frozen, no feedback",
            transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=9.2,
            style="italic", color=INK2, zorder=5)

    for arm in ARM_ORDER:
        if arm not in cum_by_arm:
            continue
        cum = cum_by_arm[arm]
        xs = list(range(1, len(cum) + 1))
        ax.plot(xs, cum, color=ARM_COLOR[arm], lw=2.5, zorder=3, solid_capstyle="round",
                 path_effects=[patheffects.Stroke(linewidth=4.5, foreground=PAPER), patheffects.Normal()])

    ax.set_xlim(0.3, n_cases + 7.5)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30, 34, 38])
    ax.set_xlabel("file number")
    ax.set_ylabel("rating classes off the correct answer")
    ax.grid(axis="y", color=LINE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)

    # direct labels at the right end of each line, nudged apart so none overlap
    adjusted = _spread_labels(last_values, min_gap=(y_top + 0.08) * 0.055)
    label_x = n_cases + 0.7
    for arm, y_label in adjusted.items():
        y_actual = last_values[arm]
        if abs(y_label - y_actual) > 1e-6:
            ax.plot([n_cases + 0.15, label_x - 0.15], [y_actual, y_label], color=ARM_COLOR[arm], lw=0.8, alpha=0.55, zorder=2)
        ax.text(label_x, y_label, DISPLAY[arm], color=ARM_COLOR[arm], fontsize=11.3, fontweight="bold",
                va="center", ha="left", zorder=4)

    fig.text(0.012, 0.99, "Error falls as the files add up, for the designs that keep something",
              fontsize=15.5, fontweight="bold", va="top")
    fig.text(0.012, 0.945,
             "Running average of how far off the rating was, across all 38 files, one design per line",
             fontsize=10.3, color=INK2, va="top")
    fig.text(0.012, 0.052,
             "Each line is the average rating error over every file done so far. Lower is better; zero "
             "is a perfect match with the senior's markup.",
             fontsize=9.8, color=INK2, va="bottom", style="italic")
    fig.text(0.012, 0.014,
             "Operators were Claude Fable 5.1 throughout, except the written-rules design, whose last "
             "two training files and all eight held-out files ran on Claude Opus 5 after the Fable "
             "quota ran out (D-28).",
             fontsize=8.3, color=INK2, va="bottom")

    _stub_watermark(fig, run_id)
    fig.tight_layout(rect=(0, 0.09, 1, 0.905))
    fig.savefig(out_dir / "learning_curve.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure B: holdout
def fig_holdout(summary: dict, run_id: str, out_dir: Path) -> None:
    arms = summary["arms"]

    main_vals, novel_vals = {}, {}
    for arm in ARM_ORDER:
        if arm not in arms:
            continue
        s = arms[arm]
        main_vals[arm] = s["mean_distance_holdout"] or 0.0
        novel_vals[arm] = s["mean_distance_holdout_novel"] or 0.0

    present = [a for a in ARM_ORDER if a in main_vals]
    n = len(present)
    max_val = max(list(main_vals.values()) + list(novel_vals.values()) + [0.1])

    fig, ax = plt.subplots(figsize=(11, 5.6))
    y_pos = list(range(n))
    for i, arm in enumerate(present):
        y = y_pos[i]
        ax.barh(y, main_vals[arm], height=0.42, color=ARM_COLOR[arm], zorder=3)
        ax.text(main_vals[arm] + max_val * 0.02, y, f"{main_vals[arm]:.2f}", va="center", ha="left",
                fontsize=11, fontweight="bold", color=ARM_COLOR[arm], zorder=4)

        y_thin = y + 0.34
        ax.barh(y_thin, novel_vals[arm], height=0.16, color=ARM_COLOR[arm], alpha=0.55,
                edgecolor=INK, lw=0.6, zorder=3)
        ax.text(novel_vals[arm] + max_val * 0.02, y_thin, f"novel {novel_vals[arm]:.2f}", va="center", ha="left",
                fontsize=8.6, color=INK2, style="italic", zorder=4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([DISPLAY[a] for a in present], fontsize=11.5, fontweight="bold", color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, max_val * 1.4)
    ax.set_ylim(n - 0.35, -0.75)
    ax.set_xlabel("rating classes off the correct answer")
    ax.grid(axis="x", color=LINE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)

    fig.text(0.012, 0.99, "Held-out cases: everyone slips on the rule nobody trained on", fontsize=15, fontweight="bold", va="top")
    fig.text(0.012, 0.935,
             "Solid bar = average rating error over the 8 held-out files. Thin bar = the 2 of those 8 that turn "
             "on a house rule which never appeared in training.",
             fontsize=9.8, color=INK2, va="top")
    footnote = textwrap.fill(
        "New joiner, running notebook and precedent file took this test on Claude Fable 5.1; written rules "
        "took it on Claude Opus 5 after the Fable quota ran out, so its number is not strictly "
        "like-for-like.", width=118)
    fig.text(0.012, 0.895, footnote, fontsize=8.3, color=INK2, va="top", linespacing=1.5)

    _stub_watermark(fig, run_id)
    fig.tight_layout(rect=(0, 0.01, 1, 0.79))
    fig.savefig(out_dir / "holdout.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure C: what each design gets
# Plain-language spine and table -- a non-technical reader should follow this without any
# of the ML jargon ("arm", "case", "reviewer scores it") the earlier version used.
SPINE_STEPS = [
    "A fresh underwriter\nopens the file",
    "Reads the manual,\nplus whatever their\ndesign gives them",
    "Decides the\nrating",
    "The senior\nmarks it up",
    "Their memory is\nupdated, or not",
]
TABLE_ROWS = [
    ("New joiner", "The manual, and nothing else",
     "Nothing. Every file is day one again"),
    ("Running notebook", "The manual, plus every comment the senior has ever written, word for word",
     "Pastes the senior's comment into the notebook exactly as written"),
    ("Written rules", "The manual, plus a rule book they have written themselves from past corrections",
     "Turns the new correction into a rule in their own words and rewrites the book"),
    ("Precedent file", "The manual, plus the three most similar past files and how each was finally rated",
     "Files this case away with its correct answer"),
]


def _box(ax, xy, w, h, text, fc=PAPER, ec=INK, fs=11.5, tc=INK):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, linespacing=1.3)


def fig_what_each_gets(run_id: str, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(17, 9.6))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 9.6)
    ax.axis("off")

    # heading sits in its own band above the boxes so its text never collides with them
    ax.text(0.3, 9.45, "The shared spine: every design follows the same five steps", fontsize=13.5,
            fontweight="bold", color=INK, va="top")

    # --- top: the shared five-step spine, one plain box per step, plain arrows between
    n = len(SPINE_STEPS)
    top, h, gap = 8.05, 1.05, 0.28
    w = (17 - 0.6 - gap * (n - 1)) / n
    xs = [0.3 + i * (w + gap) for i in range(n)]
    for x, text in zip(xs, SPINE_STEPS):
        _box(ax, (x, top), w, h, text, fc="#eef1ee", fs=11.8)
    mid = top + h / 2
    for i in range(n - 1):
        a = (xs[i] + w, mid)
        b = (xs[i + 1], mid)
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=15, lw=1.4, color=INK2))

    # --- below: the four-row table, design | what they have | what they keep
    col_x = [0.3, 3.2, 10.4]
    header_y = 6.75
    ax.text(col_x[0], header_y, "Design", fontsize=12.5, fontweight="bold", color=INK)
    ax.text(col_x[1], header_y, "What they have when they open the file", fontsize=12.5,
            fontweight="bold", color=INK)
    ax.text(col_x[2], header_y, "What they keep when the file is done", fontsize=12.5,
            fontweight="bold", color=INK)
    ax.plot([0.3, 16.7], [header_y - 0.32, header_y - 0.32], color=INK, lw=1.3)

    row_top = header_y - 0.62
    row_h = 1.55
    for i, (design, have, keep) in enumerate(TABLE_ROWS):
        y = row_top - i * row_h
        arm_key = ARM_ORDER[i]
        ax.text(col_x[0], y, design, fontsize=12.5, fontweight="bold", color=ARM_COLOR[arm_key], va="top")
        wrapped_have = textwrap.fill(have, width=40)
        wrapped_keep = textwrap.fill(keep, width=36)
        ax.text(col_x[1], y, wrapped_have, fontsize=11.3, color=INK, va="top", linespacing=1.45)
        ax.text(col_x[2], y, wrapped_keep, fontsize=11.3, color=INK, va="top", linespacing=1.45)
        if i < len(TABLE_ROWS) - 1:
            ax.plot([0.3, 16.7], [y - row_h + 0.5, y - row_h + 0.5], color=LINE, lw=0.9)

    _stub_watermark(fig, run_id)
    fig.savefig(out_dir / "what_each_gets.png", dpi=100)
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--root", default=None, help="defaults to artifacts/uw")
    ap.add_argument("--out", default=None, help="override for the output directory (default: this assets folder)")
    ap.add_argument("--window", type=int, default=5)
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else ROOT / "artifacts" / "uw"
    out_dir = Path(args.out) if args.out else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = load_summary(args.run_id, root, args.window)

    fig_learning_curve(args.run_id, root, out_dir)
    fig_holdout(summary, args.run_id, out_dir)
    fig_what_each_gets(args.run_id, out_dir)

    for name in ("learning_curve", "holdout", "what_each_gets"):
        print("wrote", out_dir / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
