"""Draft cartoon for figure 4, panel A.

Idealized exponential-growth model of NB volume across generations under
VCV=0 (fixed absolute threshold) vs VCV=1 (threshold scales with birth size).
Numbers are illustrative, not from a real sim. Saves SVG for easy editing.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

REPO_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = REPO_ROOT / "docs" / "tex_draft" / "figures"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 16,
    "svg.fonttype": "none",  # keep text as text in SVG so it's editable
})

# --- model parameters (illustrative only) ---
V_STAR = 1.0          # WT division volume in VCV=0 / WT steady-state in VCV=1
GROWTH_RATE = 1.1
WT_FRAC_DIV = 0.65    # WT asymmetric: NB keeps ~2/3 of parent volume
MUT_FRAC_DIV = 0.50   # mutant symmetric: NB keeps half
VCV1_FACTOR = 1.0 / WT_FRAC_DIV  # threshold = 1.54 x birth_size: makes WT stable, mutant shrink

WT_BIRTH = WT_FRAC_DIV * V_STAR
MUT_BIRTH = MUT_FRAC_DIV * V_STAR

# --- styling ---
WT_COLOR = "#1f1f1f"
MUT_COLOR = "#1f1f1f"
WT_KW = dict(color=WT_COLOR, linewidth=2.6, linestyle="-")
MUT_KW = dict(color=MUT_COLOR, linewidth=2.2, linestyle=(0, (5, 3)))  # dashed
THRESHOLD_KW = dict(color="#888888", linewidth=1.4, linestyle=":", alpha=0.95)


def grow_segment(v_start: float, v_end: float, t0: float = 0.0, n: int = 80) -> tuple[np.ndarray, np.ndarray]:
    t_total = np.log(v_end / v_start) / GROWTH_RATE
    t = np.linspace(0.0, t_total, n)
    v = v_start * np.exp(GROWTH_RATE * t)
    return t + t0, v


def cycles(birth: float, frac_div: float, n: int, *, fixed_threshold: float | None = None,
           factor_threshold: float | None = None):
    segments = []
    thresholds = []
    cycle_birth = birth
    t0 = 0.0
    for _ in range(n):
        v_div = fixed_threshold if fixed_threshold is not None else factor_threshold * cycle_birth
        if v_div <= cycle_birth:
            break
        t, v = grow_segment(cycle_birth, v_div, t0=t0)
        segments.append((t, v))
        thresholds.append((t[0], t[-1], v_div))
        t0 = t[-1]
        cycle_birth = v_div * frac_div
    return segments, thresholds


def draw_trajectory(ax, segments, label, **kw):
    for i, (t, v) in enumerate(segments):
        ax.plot(t, v, label=label if i == 0 else None, zorder=4, **kw)
        if i < len(segments) - 1:
            ax.plot([t[-1], t[-1]], [v[-1], v[-1] * (kw.get("frac_div", 0.5))],
                    color=kw["color"], linewidth=kw["linewidth"], linestyle=kw["linestyle"], zorder=4)


def draw_division_drop(ax, segments, frac_div, **kw):
    for i in range(len(segments) - 1):
        t_end = segments[i][0][-1]
        v_end = segments[i][1][-1]
        v_next_birth = segments[i + 1][1][0]
        ax.plot([t_end, t_end], [v_end, v_next_birth],
                color=kw["color"], linewidth=kw["linewidth"], linestyle=kw["linestyle"], zorder=4)
        ax.plot([t_end], [v_end], "o", color=kw["color"], markersize=6, zorder=5)


def draw_threshold_line(ax, segments, label_text=None, label_xy=None):
    """Draw dashed segments at v_div for each cycle (stair-stepped if v_div changes)."""
    for t, v in segments:
        ax.plot([t[0], t[-1]], [v[-1], v[-1]], **THRESHOLD_KW, zorder=2)


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8), sharey=True)

    # ============================================================
    # Left: VCV = 0
    # ============================================================
    ax = axes[0]
    wt0, _ = cycles(WT_BIRTH, WT_FRAC_DIV, n=3, fixed_threshold=V_STAR)
    # Mutant repeats symmetric divisions: drops to V*/2 each time, climbs back to V*
    mut0, _ = cycles(MUT_BIRTH, MUT_FRAC_DIV, n=3, fixed_threshold=V_STAR)

    ax.axhline(V_STAR, **THRESHOLD_KW, zorder=2)
    ax.text(0.04, V_STAR + 0.04, "shared threshold V*",
            fontsize=14, va="bottom", color="#555555")

    for i, (t, v) in enumerate(wt0):
        ax.plot(t, v, label="WT NB  (asymm.)" if i == 0 else None, zorder=4, **WT_KW)
    draw_division_drop(ax, wt0, WT_FRAC_DIV, **WT_KW)

    for i, (t, v) in enumerate(mut0):
        ax.plot(t, v, label="mutant NB  (symm.)" if i == 0 else None, zorder=4, **MUT_KW)
    draw_division_drop(ax, mut0, MUT_FRAC_DIV, **MUT_KW)

    ax.set_title("VCV = 0    fixed threshold", fontsize=18, pad=10)
    ax.set_xlabel("time", fontsize=16)
    ax.set_ylabel("NB volume", fontsize=16)
    ax.set_yticks([0, MUT_BIRTH, WT_BIRTH, V_STAR], ["0", "½ V*", "⅔ V*", "V*"])
    ax.set_xticks([])
    ax.set_ylim(0, 1.18)
    ax.set_xlim(left=-0.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    division_marker = Line2D([0], [0], marker="o", color="black",
                             markersize=6, linestyle="None", label="division event")
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles=handles + [division_marker], loc="lower left", fontsize=13, frameon=False)

    ax.text(mut0[-1][0][-1] + 0.05, V_STAR, "mutant threshold\nstays constant",
            fontsize=12, va="center", ha="left", color="#cc4444")

    # ============================================================
    # Right: VCV = 1
    # ============================================================
    ax = axes[1]

    # WT: factor_threshold = 1/WT_FRAC_DIV → stable at V*
    wt1, wt1_thr = cycles(WT_BIRTH, WT_FRAC_DIV, n=3, factor_threshold=VCV1_FACTOR)
    # Mutant: same factor_threshold but symmetric division → shrinks 25% per cycle
    mut1, mut1_thr = cycles(MUT_BIRTH, MUT_FRAC_DIV, n=4, factor_threshold=VCV1_FACTOR)

    # Mutant threshold line first (stair-step down)
    for t, v in mut1:
        ax.plot([t[0], t[-1]], [v[-1], v[-1]],
                color="#cc4444", linewidth=1.4, linestyle=":", alpha=0.95, zorder=2)
    # WT threshold line (single horizontal line at V*)
    wt1_xmax = wt1[-1][0][-1]
    ax.plot([0, wt1_xmax], [V_STAR, V_STAR], **THRESHOLD_KW, zorder=2)

    # Trajectories
    for i, (t, v) in enumerate(wt1):
        ax.plot(t, v, label="WT NB  (asymm.)" if i == 0 else None, zorder=4, **WT_KW)
    draw_division_drop(ax, wt1, WT_FRAC_DIV, **WT_KW)
    for i, (t, v) in enumerate(mut1):
        ax.plot(t, v, label="mutant NB  (symm.)" if i == 0 else None, zorder=4, **MUT_KW)
    draw_division_drop(ax, mut1, MUT_FRAC_DIV, **MUT_KW)

    # Threshold labels
    ax.text(wt1_xmax + 0.05, V_STAR, "WT threshold\n(stable)",
            fontsize=12, va="center", ha="left", color="#555555")
    last_mut = mut1[-1]
    ax.text(last_mut[0][-1] + 0.05, last_mut[1][-1], "mutant threshold falls\neach symmetric division",
            fontsize=12, va="center", ha="left", color="#cc4444")

    ax.set_title("VCV = 1    threshold scales with birth size", fontsize=18, pad=10)
    ax.set_xlabel("time", fontsize=16)
    ax.set_xticks([])
    ax.set_xlim(left=-0.05)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles=handles + [division_marker], loc="lower left", fontsize=13, frameon=False)

    fig.tight_layout()

    out_svg = FIG_DIR / "figure4_panel_a_draft.svg"
    out_png = FIG_DIR / "figure4_panel_a_draft.png"
    out_pdf = FIG_DIR / "figure4_panel_a_draft.pdf"
    fig.savefig(out_svg, bbox_inches="tight", facecolor="white")
    fig.savefig(out_png, bbox_inches="tight", facecolor="white")
    fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
    print(f"saved {out_svg}")
    print(f"saved {out_png}")
    print(f"saved {out_pdf}")


if __name__ == "__main__":
    main()
