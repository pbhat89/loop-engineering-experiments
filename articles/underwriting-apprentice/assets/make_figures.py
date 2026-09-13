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

Writes into --out, which defaults to ``<root>/<run-id>/figures/`` -- a run's own
artifacts directory, never the article's committed assets folder. Refreshing the figures
the article actually publishes is therefore always an explicit

    --out articles/underwriting-apprentice/assets

so following the reproduction guide with your own run id can never overwrite them. The
output directory is printed on every run.

Files written:
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

Every figure is stamped with a visible "STUB DATA -- no model was called" watermark
whenever the run is a stub: that is, when ``mode`` in ``<root>/<run-id>/run.json`` is
``stub`` (the reliable signal, whatever the run is called), or as a belt-and-braces
fallback when the run id starts with "uw_stub".
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as patheffects  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_uw_run import NOVEL_RULES, default_window, load_run, summarize  # noqa: E402
from src.underwriting.data import goldens_by_case_id  # noqa: E402

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


def is_stub_run(run_id: str, mode: str | None) -> bool:
    """True when the run was produced by the stub operator rather than a real model.

    ``mode`` comes from the run's own ``run.json`` and is the signal that actually
    tracks reality: the docs tell people to smoke-test with ids like ``uw_demo``, so the
    run-id prefix alone silently let stub charts out unlabelled. The prefix is kept as a
    second trigger for runs whose ``run.json`` is missing or unreadable.
    """
    return str(mode or "").strip().lower() == "stub" or run_id.startswith("uw_stub")


def _stub_watermark(fig, run_id: str, mode: str | None = None) -> None:
    if not is_stub_run(run_id, mode):
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
def fig_learning_curve(run_id: str, root: Path, out_dir: Path, mode: str | None = None) -> None:
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
    ax.set_ylabel("average deviation from the actual rating")
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

    fig.text(0.012, 0.99, "Deviation falls as the files add up, for the designs that keep something",
              fontsize=15.5, fontweight="bold", va="top")
    fig.text(0.012, 0.945,
             "Average deviation from the actual rating, running across all 38 files, one design per line",
             fontsize=10.3, color=INK2, va="top")
    fig.text(0.012, 0.052,
             "Each line is the average deviation from the actual rating over every file done so far. "
             "Lower is better; zero means the rating matched exactly.",
             fontsize=9.8, color=INK2, va="bottom", style="italic")
    fig.text(0.012, 0.014,
             "Thirty training files with a marked-up correction after each, then eight held-out files with "
             "memory frozen and no feedback. Each design did this once.",
             fontsize=8.3, color=INK2, va="bottom")

    _stub_watermark(fig, run_id, mode)
    fig.tight_layout(rect=(0, 0.09, 1, 0.905))
    fig.savefig(out_dir / "learning_curve.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure B: holdout
def fig_holdout(summary: dict, run_id: str, out_dir: Path, run_root: Path | None = None, mode: str | None = None) -> None:
    """How many of the eight held-out files each design rated exactly right.

    Counted upward on purpose. The earlier version of this figure plotted average error,
    where the longest bar was the worst design and readers reliably drew the opposite
    conclusion. Two of the eight files turn on a house rule that appears in no training
    file, so six is the most any design could get; that appears as a ceiling line rather
    than as a second bar, because a bar that is identical for every design carries no
    comparison and invites being read as a score.
    """
    data_by_arm = load_run(run_id, run_root if run_root is not None else ROOT / "artifacts" / "uw")["arms"]
    goldens = goldens_by_case_id()
    unlearnable = {
        cid for cid, g in goldens.items()
        if g.get("phase") == "holdout" and set(g.get("fired_rule_ids", [])) & set(NOVEL_RULES)
    }

    exact, total = {}, 0
    for arm in ARM_ORDER:
        held = [r for r in data_by_arm.get(arm, []) if r["phase"] == "holdout"]
        if not held:
            continue
        total = len(held)
        exact[arm] = sum(1 for r in held if r["ladder_distance"] == 0)

    present = [a for a in ARM_ORDER if a in exact]
    ceiling = total - len(unlearnable)

    fig, ax = plt.subplots(figsize=(11, 5.4))
    y_pos = list(range(len(present)))
    for y, arm in zip(y_pos, present):
        ax.barh(y, exact[arm], height=0.5, color=ARM_COLOR[arm], zorder=3)
        ax.text(exact[arm] + 0.12, y, f"{exact[arm]} of {total}", va="center", ha="left",
                fontsize=11.5, fontweight="bold", color=ARM_COLOR[arm], zorder=4)

    ax.axvline(ceiling, color=INK, lw=1.2, ls=(0, (5, 3)), zorder=5)
    ax.text(ceiling - 0.12, -0.72, f"{ceiling} is the most anyone could get",
            ha="right", va="center", fontsize=9.4, style="italic", color=INK, zorder=6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([DISPLAY[a] for a in present], fontsize=11.5, fontweight="bold", color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, total + 0.6)
    ax.set_ylim(len(present) - 0.4, -1.0)
    ax.set_xticks(list(range(total + 1)))
    ax.set_xlabel("held-out files rated exactly right (longer is better)")
    ax.grid(axis="x", color=LINE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)

    fig.text(0.012, 0.99, "On unseen files, the designs that kept something got nearly everything right",
             fontsize=15, fontweight="bold", va="top")
    subtitle = textwrap.fill(
        f"Eight fresh files, memory frozen, one attempt each and no feedback. {len(unlearnable)} of the {total} turn on a "
        f"house rule that appears in no training file, so nothing written down could cover them and every design missed "
        f"both. That puts the ceiling at {ceiling}, and the two note-taking designs reached it.",
        width=106)
    fig.text(0.012, 0.945, subtitle, fontsize=9.8, color=INK2, va="top", linespacing=1.45)

    _stub_watermark(fig, run_id, mode)
    fig.tight_layout(rect=(0, 0.01, 1, 0.85))
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


def fig_what_each_gets(run_id: str, out_dir: Path, mode: str | None = None) -> None:
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

    _stub_watermark(fig, run_id, mode)
    fig.savefig(out_dir / "what_each_gets.png", dpi=100)
    plt.close(fig)


# --------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--root", default=None, help="defaults to artifacts/uw")
    ap.add_argument("--out", default=None,
                    help="output directory (default: <root>/<run-id>/figures). Pass "
                         "--out articles/underwriting-apprentice/assets to refresh the article's own figures.")
    ap.add_argument("--window", type=int, default=None,
                    help="trailing-mean window; defaults to trailing_window in config/underwriting.yaml")
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else ROOT / "artifacts" / "uw"
    # Default to the run's own artifacts directory. The article's committed assets folder
    # is only ever written when it is asked for by name.
    out_dir = Path(args.out) if args.out else root / args.run_id / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = load_summary(args.run_id, root, args.window if args.window is not None else default_window())
    mode = summary.get("mode")

    fig_learning_curve(args.run_id, root, out_dir, mode)
    fig_holdout(summary, args.run_id, out_dir, root, mode)
    fig_what_each_gets(args.run_id, out_dir, mode)

    print(f"output directory: {out_dir}")
    if is_stub_run(args.run_id, mode):
        print("stub run (mode=stub): every figure is watermarked STUB DATA")
    for name in ("learning_curve", "holdout", "what_each_gets"):
        print("wrote", out_dir / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
