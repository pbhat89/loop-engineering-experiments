"""Figures for the underwriting-apprentice article (experiment 7), drawn from one run's
per-case logs.

    .venv/Scripts/python.exe articles/underwriting-apprentice/assets/make_figures.py \
        --run-id RUN_ID [--root ROOT_DIR] [--out OUT_DIR] [--window N]

Reads ``<root>/<run-id>/<arm>/cases.jsonl`` for the five arms (new_joiner, notebook,
written_rules, precedent, ask_senior) and joins the tier and fired rule ids in from
``data/underwriting/goldens.json`` at analysis time, exactly as
``scripts/summarize_uw_run.py`` does (its ``load_run``/``summarize`` are imported and
reused directly here, so the two never drift apart).

Writes into --out (default: this folder):
  learning_curve.png   the article's closing chart -- trailing 5-case mean of rating
                        error (ladder steps) for all five arms across the 30 training
                        cases, with the raw per-case points behind each line
  holdout.png           horizontal bars: mean rating error on the 8 held-out cases per
                        arm, plus a thin bar for the 2 "novel rule" held-out cases
                        (golden fires only HR-13 or HR-14) and ask-a-senior's mean
                        questions asked per held-out case
  what_each_gets.png     the shared five-step spine every case goes through, plus the
                        five-row table of what each design is handed and keeps
                        (wording from docs/underwriting-apprentice-design.md)

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
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_uw_run import NOVEL_RULES, load_run, summarize  # noqa: E402
from src.underwriting.state import ASKING_CONDITIONS, CONDITIONS  # noqa: E402

# --------------------------------------------------------------------------- shared look
# Same palette / type treatment as articles/loop-engineering-markdown-skills/assets/make_figures.py
INK, INK2, LINE, PAPER = "#1b2a24", "#5b6b65", "#c9d1cc", "#fbfbf8"
FAIL = "#b3400a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12, "legend.fontsize": 11,
    "axes.edgecolor": LINE, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
})

ARM_ORDER = list(CONDITIONS)  # ("new_joiner", "notebook", "written_rules", "precedent", "ask_senior") -- new joiner first
DISPLAY = {
    "new_joiner": "New joiner",
    "notebook": "Running notebook",
    "written_rules": "Written rules",
    "precedent": "Precedent file",
    "ask_senior": "Ask a senior",
}
# Fixed per-arm colour, never cycled -- same colour-blind-safe (Okabe-Ito) palette as the
# loop-engineering article, reused here so an arm's colour never means two different things
# across the two articles.
ARM_COLOR = {
    "new_joiner": "#0072B2",
    "notebook": "#56B4E9",
    "written_rules": "#009E73",
    "precedent": "#D55E00",
    "ask_senior": "#8C564B",
}


def _stub_watermark(fig, run_id: str) -> None:
    if not run_id.startswith("uw_stub"):
        return
    fig.text(0.5, 0.5, "STUB DATA — no model was called", fontsize=34, fontweight="bold",
              color="#b3400a", alpha=0.28, ha="center", va="center", rotation=28, zorder=50)


def _spread_labels(values: dict[str, float], min_gap: float) -> dict[str, float]:
    """Nudge label y-positions apart just enough to keep them from overlapping,
    preserving their relative order."""
    order = sorted(values, key=lambda k: values[k])
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
def fig_learning_curve(summary: dict, run_id: str, out_dir: Path) -> None:
    arms = summary["arms"]
    n_cases = max((len(arms[a]["per_case_distance"]) for a in ARM_ORDER if a in arms), default=30)

    fig, ax = plt.subplots(figsize=(12, 7.2))

    # tiny fixed horizontal jitter per arm so overlapping raw dots stay distinguishable --
    # deterministic (not random) so the figure is reproducible byte-for-byte.
    jitter = {arm: (i - (len(ARM_ORDER) - 1) / 2) * 0.11 for i, arm in enumerate(ARM_ORDER)}

    max_y = 0.5
    last_values: dict[str, float] = {}
    for arm in ARM_ORDER:
        if arm not in arms:
            continue
        s = arms[arm]
        raw = s["per_case_distance"]
        trail = s["trailing_mean"]
        xs = list(range(1, len(raw) + 1))
        ax.scatter([x + jitter[arm] for x in xs], raw, s=13, color=ARM_COLOR[arm], alpha=0.25,
                   linewidths=0, zorder=2)
        ax.plot(xs, trail, color=ARM_COLOR[arm], lw=2.0, zorder=3, solid_capstyle="round")
        if raw:
            max_y = max(max_y, max(raw))
        if trail:
            last_values[arm] = trail[-1]

    ax.set_xlim(0.3, 35.5)
    ax.set_ylim(0, max_y * 1.15)
    ax.set_xticks([1, 5, 10, 15, 20, 25, 30])
    ax.set_xlabel("case number")
    ax.set_ylabel("rating error, ladder steps")
    ax.grid(axis="y", color=LINE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.axvline(n_cases + 0.5, color=LINE, lw=0.8, zorder=1)

    # direct labels at the right end of each line, nudged apart so none overlap
    adjusted = _spread_labels(last_values, min_gap=max_y * 1.15 * 0.055)
    label_x = n_cases + 0.7
    for arm, y_label in adjusted.items():
        y_actual = last_values[arm]
        if abs(y_label - y_actual) > 1e-6:
            ax.plot([n_cases + 0.15, label_x - 0.15], [y_actual, y_label], color=ARM_COLOR[arm], lw=0.8, alpha=0.55, zorder=2)
        ax.text(label_x, y_label, DISPLAY[arm], color=ARM_COLOR[arm], fontsize=11.3, fontweight="bold",
                va="center", ha="left", zorder=4)

    fig.text(0.012, 0.99, "How fast each design catches up", fontsize=15.5, fontweight="bold", va="top")
    fig.text(0.012, 0.945,
             "Trailing five-case mean of rating error on the 30 training cases, one design per line",
             fontsize=10.3, color=INK2, va="top")
    fig.text(0.012, 0.028,
             "Each point is one case, rated once. Lines are the trailing five-case mean. "
             "Lower is better; zero is a perfect match with the reviewer.",
             fontsize=9.8, color=INK2, va="bottom", style="italic")

    _stub_watermark(fig, run_id)
    fig.tight_layout(rect=(0, 0.05, 1, 0.905))
    fig.savefig(out_dir / "learning_curve.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure B: holdout
def fig_holdout(summary: dict, run_id: str, root: Path, out_dir: Path) -> None:
    arms = summary["arms"]
    data_by_arm = load_run(summary["run_id"], root)["arms"]

    main_vals, novel_vals = {}, {}
    quest_per_case: dict[str, float] = {}
    for arm in ARM_ORDER:
        if arm not in arms:
            continue
        s = arms[arm]
        main_vals[arm] = s["mean_distance_holdout"] or 0.0
        novel_vals[arm] = s["mean_distance_holdout_novel"] or 0.0
        held = [r for r in data_by_arm.get(arm, []) if r["phase"] == "holdout"]
        if arm in ASKING_CONDITIONS and held:
            quest_per_case[arm] = sum(int(r.get("questions_asked") or 0) for r in held) / len(held)

    present = [a for a in ARM_ORDER if a in main_vals]
    n = len(present)
    max_val = max(list(main_vals.values()) + list(novel_vals.values()) + [0.1])

    fig, ax = plt.subplots(figsize=(11, 6.4))
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

        if arm in quest_per_case:
            ax.text(max_val * 1.32, y, f"~{quest_per_case[arm]:.1f} questions / held-out case",
                    va="center", ha="left", fontsize=9, color=INK2, zorder=4)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([DISPLAY[a] for a in present], fontsize=11.5, fontweight="bold", color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, max_val * 1.7)
    ax.set_ylim(n - 0.35, -0.75)
    ax.set_xlabel("rating error, ladder steps")
    ax.grid(axis="x", color=LINE, lw=0.6, zorder=0)
    ax.set_axisbelow(True)

    fig.text(0.012, 0.99, "Held-out cases: everyone slips on the rule nobody trained on", fontsize=15, fontweight="bold", va="top")
    fig.text(0.012, 0.935,
             "Solid bar = mean rating error over the 8 held-out cases. Thin bar = the 2 of those 8 whose golden "
             "fires only rule HR-13 or HR-14, a rule never seen in training.",
             fontsize=9.8, color=INK2, va="top")

    _stub_watermark(fig, run_id)
    fig.tight_layout(rect=(0, 0.01, 1, 0.865))
    fig.savefig(out_dir / "holdout.png", dpi=170)
    plt.close(fig)


# --------------------------------------------------------------------------- figure C: what each design gets
# Wording taken verbatim from the table in docs/underwriting-apprentice-design.md, section
# "The shared spine, every case, every design".
SPINE_STEPS = [
    "A fresh agent\nopens the case",
    "Reads the manual +\nwhat its design hands it",
    "Decides: decision,\nrating, modifiers, drivers",
    "Reviewer scores it against\nthe hidden house rules",
    "The design's memory\nis updated, or not",
]
TABLE_ROWS = [
    ("New joiner", "The starter manual, nothing else", "Nothing. Permanently on day one"),
    ("Running notebook", "Every past markup, verbatim, newest first", "Appends the markup as written"),
    ("Written rules", "Its own house-rule book, the entries whose trigger matches",
     "Writes or rewrites a rule in its own words"),
    ("Precedent file", "The three nearest past cases with their correct answers",
     "Files this case with its correct answer"),
    ("Ask a senior",
     "Nothing extra, but may ask up to four questions, answered narrowly and literally from the hidden rules. "
     "It chooses how many; usage is recorded",
     "Nothing. Pays the cost again every case"),
]


def _box(ax, xy, w, h, text, fc=PAPER, ec=INK, fs=11.5, tc=INK):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, linespacing=1.3)


def fig_what_each_gets(run_id: str, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis("off")

    # heading sits in its own band above the boxes so its text never collides with them
    ax.text(0.3, 10.85, "The shared spine — identical for every arm, every case", fontsize=13.5,
            fontweight="bold", color=INK, va="top")

    # --- top: the shared five-step spine, one plain box per step, plain arrows between
    n = len(SPINE_STEPS)
    top, h, gap = 9.45, 1.0, 0.28
    w = (16 - 0.6 - gap * (n - 1)) / n
    xs = [0.3 + i * (w + gap) for i in range(n)]
    for x, text in zip(xs, SPINE_STEPS):
        _box(ax, (x, top), w, h, text, fc="#eef1ee", fs=11.8)
    mid = top + h / 2
    for i in range(n - 1):
        a = (xs[i] + w, mid)
        b = (xs[i + 1], mid)
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=15, lw=1.4, color=INK2))

    # --- below: the five-row table, design | handed before deciding | kept afterwards
    col_x = [0.3, 3.2, 10.15]
    col_w = [2.7, 6.75, 5.55]
    header_y = 8.55
    ax.text(0.3, header_y, "Design", fontsize=12.5, fontweight="bold", color=INK)
    ax.text(3.2, header_y, "Handed to it before deciding", fontsize=12.5, fontweight="bold", color=INK)
    ax.text(10.15, header_y, "Kept afterwards", fontsize=12.5, fontweight="bold", color=INK)
    ax.plot([0.3, 15.7], [header_y - 0.32, header_y - 0.32], color=INK, lw=1.3)

    row_top = header_y - 0.62
    row_h = 1.5
    for i, (design, handed, kept) in enumerate(TABLE_ROWS):
        y = row_top - i * row_h
        arm_key = ARM_ORDER[i]
        ax.text(col_x[0], y, design, fontsize=12.5, fontweight="bold", color=ARM_COLOR[arm_key], va="top")
        wrapped_handed = textwrap.fill(handed, width=46)
        wrapped_kept = textwrap.fill(kept, width=34)
        ax.text(col_x[1], y, wrapped_handed, fontsize=11.3, color=INK, va="top", linespacing=1.45)
        ax.text(col_x[2], y, wrapped_kept, fontsize=11.3, color=INK, va="top", linespacing=1.45)
        if i < len(TABLE_ROWS) - 1:
            ax.plot([0.3, 15.7], [y - row_h + 0.35, y - row_h + 0.35], color=LINE, lw=0.9)

    ax.text(0.3, row_top - len(TABLE_ROWS) * row_h + 0.05,
            "Wording from docs/underwriting-apprentice-design.md · \"The shared spine, every case, every design\"",
            fontsize=9.3, color=INK2, style="italic")

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

    fig_learning_curve(summary, args.run_id, out_dir)
    fig_holdout(summary, args.run_id, root, out_dir)
    fig_what_each_gets(args.run_id, out_dir)

    for name in ("learning_curve", "holdout", "what_each_gets"):
        print("wrote", out_dir / f"{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
