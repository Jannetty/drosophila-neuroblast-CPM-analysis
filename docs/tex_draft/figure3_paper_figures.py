from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from npa.sim_viz import load_raw_snapshot_full, render_raw

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = REPO_ROOT / "docs" / "tex_draft" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DS_UM_PER_VOX = 0.3
AREA_SCALE = DS_UM_PER_VOX ** 2

WT_CONDITION = "wt_divMean0Stdev26"
WT_SIM_ID = "vcv1_noreg"
WT_VCV = 1

MUD_CONDITION = "mudmut_divMean0Stdev50_rotMean0Stdev30"
MUD_SIM_ID = "vcv0_noreg"
MUD_VCV = 0

REPRESENTATIVE_PERCENTILES = (0.10, 0.50, 0.90)

SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_run_index.csv"
EXP_SUMMARY_CSV = REPO_ROOT / "data" / "exp" / "processed" / "exp_summary.csv"
EXP_INDEX_CSV = REPO_ROOT / "data" / "exp" / "processed" / "lineage_index.csv"
EXP_ANALYSIS_DIR = REPO_ROOT / "data" / "exp" / "processed" / "analysis"

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import RCPARAMS as _RCPARAMS, FONT_SIZE_TITLE, FONT_SIZE_LABEL, EXP_FILL_COLOR, EXP_MEDIAN_COLOR
plt.rcParams.update(_RCPARAMS)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sim_df = pd.read_csv(SIM_METRICS_CSV)
    run_index_df = pd.read_csv(SIM_RUN_INDEX_CSV)
    exp_summary_df = pd.read_csv(EXP_SUMMARY_CSV)
    exp_index_df = pd.read_csv(EXP_INDEX_CSV)

    wt_runs = sim_df.loc[
        (sim_df["condition"] == WT_CONDITION)
        & (sim_df["sim_id"] == WT_SIM_ID)
        & (sim_df["critical_volume_mode"] == WT_VCV)
    ].copy().sort_values("run_id")
    mud_runs = sim_df.loc[
        (sim_df["condition"] == MUD_CONDITION)
        & (sim_df["sim_id"] == MUD_SIM_ID)
        & (sim_df["critical_volume_mode"] == MUD_VCV)
    ].copy().sort_values("run_id")

    return sim_df, run_index_df, exp_summary_df, exp_index_df, pd.concat(
        [
            wt_runs.assign(group="WT Sim"),
            mud_runs.assign(group="mudmut Sim"),
        ],
        ignore_index=True,
    )


def attach_exp_analysis(exp_index_df: pd.DataFrame, genotype: str) -> pd.DataFrame:
    analysis_path = EXP_ANALYSIS_DIR / f"{genotype}.npz"
    selected = exp_index_df.loc[exp_index_df["genotype"] == genotype].copy().sort_values("analysis_row").reset_index(drop=True)
    with np.load(analysis_path) as data:
        selected["lin_area_vox"] = data["geo"].sum(axis=(1, 2, 3))
        selected["dpn_area_vox"] = data["counts"][:, 2]
    selected["avg_dpn_area_vox"] = selected["dpn_area_vox"] / selected["n_dpn"].clip(lower=1)
    return selected


def pick_percentile_runs(df: pd.DataFrame, metric: str, percentiles: tuple[float, ...]) -> pd.DataFrame:
    chosen_rows = []
    used_ids: set[int] = set()
    for pct in percentiles:
        target = df[metric].quantile(pct)
        candidates = df.assign(abs_delta=(df[metric] - target).abs()).sort_values(
            ["abs_delta", metric, "run_id"], kind="stable"
        )
        for _, row in candidates.iterrows():
            run_id = int(row["run_id"])
            if run_id in used_ids:
                continue
            used_ids.add(run_id)
            payload = row.drop(labels=["abs_delta"]).to_dict()
            payload["percentile"] = pct
            payload["target_value"] = float(target)
            chosen_rows.append(payload)
            break
    return pd.DataFrame(chosen_rows).sort_values("percentile").reset_index(drop=True)


def load_run_snapshot(run_index_df: pd.DataFrame, condition: str, sim_id: str, run_id: int) -> tuple[np.ndarray, np.ndarray]:
    row = run_index_df.loc[
        (run_index_df["condition"] == condition)
        & (run_index_df["sim_id"] == sim_id)
        & (run_index_df["run_id"].astype(int) == int(run_id))
    ].iloc[0]
    cells_path = REPO_ROOT / row["cells_path"]
    locs_path = REPO_ROOT / row["locs_path"]
    return load_raw_snapshot_full(cells_path, locs_path)


def content_bbox(arr: np.ndarray, pad: int = 6) -> tuple[int, int, int, int]:
    occ = arr.any(axis=-1) if arr.ndim == 3 else arr > 0
    ys, xs = np.where(occ)
    if len(xs) == 0:
        h, w = arr.shape[:2]
        return 0, 0, h, w
    y0 = max(int(ys.min()) - pad, 0)
    y1 = min(int(ys.max()) + pad + 1, arr.shape[0])
    x0 = max(int(xs.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad + 1, arr.shape[1])
    return y0, x0, y1, x1


def uniform_crop_size(geo_arrays: list[np.ndarray], pad: int = 6) -> int:
    max_dim = 0
    for arr in geo_arrays:
        y0, x0, y1, x1 = content_bbox(arr, pad=pad)
        max_dim = max(max_dim, y1 - y0, x1 - x0)
    return max_dim


def crop_centered(arr: np.ndarray, target_size: int) -> np.ndarray:
    occ = arr.any(axis=-1) if arr.ndim == 3 else arr > 0
    ys, xs = np.where(occ)
    if len(xs) == 0:
        cy, cx = arr.shape[0] // 2, arr.shape[1] // 2
    else:
        cy = (int(ys.min()) + int(ys.max())) // 2
        cx = (int(xs.min()) + int(xs.max())) // 2
    half = target_size // 2
    y0 = max(0, min(cy - half, arr.shape[0] - target_size))
    x0 = max(0, min(cx - half, arr.shape[1] - target_size))
    if arr.ndim == 3:
        return arr[y0:y0 + target_size, x0:x0 + target_size, :]
    return arr[y0:y0 + target_size, x0:x0 + target_size]


def style_publication_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#d0d0d0", linewidth=0.6, alpha=0.5)
    ax.tick_params(axis="x", length=0)


def make_boxplot_panel(
    ax: plt.Axes,
    groups: list[tuple[str, np.ndarray]],
    title: str,
    ylabel: str | None,
    fill_map: dict[str, str],
) -> None:
    positions = np.arange(1, len(groups) + 1, dtype=float)
    bp = ax.boxplot(
        [values for _, values in groups],
        positions=positions,
        widths=0.62,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "black", "linewidth": 1.4},
        boxprops={"facecolor": "white", "edgecolor": "black", "linewidth": 1.0},
        whiskerprops={"color": "black", "linewidth": 0.9},
        capprops={"color": "black", "linewidth": 0.9},
        manage_ticks=False,
        zorder=3,
    )
    for patch, (label, _) in zip(bp["boxes"], groups):
        patch.set_facecolor(fill_map[label])
    for median, (label, _) in zip(bp["medians"], groups):
        if fill_map.get(label) == EXP_FILL_COLOR:
            median.set(color=EXP_MEDIAN_COLOR, linewidth=1.8, linestyle="--")
    ax.set_xticks(positions, [label for label, _ in groups])
    ax.set_title(title, pad=10)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    style_publication_axis(ax)


def representative_lineages_panel(wt_runs: pd.DataFrame, mud_runs: pd.DataFrame, run_index_df: pd.DataFrame) -> plt.Figure:
    wt_rep = pick_percentile_runs(wt_runs, "lin_area_vox", REPRESENTATIVE_PERCENTILES)
    mud_rep = pick_percentile_runs(mud_runs, "lin_area_vox", REPRESENTATIVE_PERCENTILES)

    fig, axes = plt.subplots(2, 3, figsize=(11.5, 7.6))
    rows = [
        ("WT", WT_CONDITION, WT_SIM_ID, wt_rep),
        ("mudmut\nunregulated", MUD_CONDITION, MUD_SIM_ID, mud_rep),
    ]

    for col, pct in enumerate(REPRESENTATIVE_PERCENTILES):
        axes[0, col].set_title(f"{int(round(pct * 100))}th percentile", pad=20, fontsize=FONT_SIZE_TITLE)
        axes[0, col].text(0.5, 1.0, "lineage area", transform=axes[0, col].transAxes,
                          ha="center", va="bottom", fontsize=FONT_SIZE_LABEL)

    snapshots = []
    for row_idx, (row_label, condition, sim_id, rep_df) in enumerate(rows):
        for col_idx, (_, row) in enumerate(rep_df.iterrows()):
            geo_raw, label_map = load_run_snapshot(run_index_df, condition, sim_id, int(row["run_id"]))
            snapshots.append((row_idx, col_idx, geo_raw, label_map, row))

    target_size = uniform_crop_size([s[2] for s in snapshots], pad=6)

    for row_idx, col_idx, geo_raw, label_map, row in snapshots:
        ax = axes[row_idx, col_idx]
        geo_crop = crop_centered(geo_raw, target_size)
        label_crop = crop_centered(label_map, target_size)
        render_raw(geo_crop, ax=ax, label_map=label_crop, title="")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xlabel(
            f"run {int(row['run_id']):04d}\narea = {row['lin_area_vox'] * AREA_SCALE:.0f} µm²",
            fontsize=FONT_SIZE_LABEL,
            labelpad=2,
        )
        ax.xaxis.set_label_coords(0.5, -0.03)

    for row_idx, (row_label, *_) in enumerate(rows):
        bbox = axes[row_idx, 0].get_position()
        fig.text(
            bbox.x0 - 0.005,
            (bbox.y0 + bbox.y1) / 2,
            row_label,
            ha="right",
            va="center",
            fontsize=FONT_SIZE_TITLE,
            fontweight="bold",
        )

    fig.subplots_adjust(left=0.10, right=0.995, top=0.93, bottom=0.05, wspace=0.04, hspace=0.30)
    return fig


def endpoint_metrics_panel(
    exp_wt: pd.DataFrame,
    exp_mud: pd.DataFrame,
    wt_runs: pd.DataFrame,
    mud_runs: pd.DataFrame,
) -> plt.Figure:
    metric_specs = [
        ("lin_area_vox", "Lineage area", "µm²", True),
        ("dpn_area_vox", "Total NB area", "µm²", True),
        ("avg_dpn_area_vox", "Mean NB area", "µm²/cell", True),
        ("n_pros", "Pros count", "cells", False),
        ("n_dpn", "NB count", "cells", False),
    ]
    fill_map = {
        "WT Exp": EXP_FILL_COLOR,
        "WT Sim": "#ffffff",
        "mud Exp": EXP_FILL_COLOR,
        "mud Sim": "#5f5f5f",
    }

    fig, axes = plt.subplots(1, len(metric_specs), figsize=(18.2, 5.2))
    for col_idx, (ax, (metric_key, title, unit, is_area)) in enumerate(zip(axes, metric_specs)):
        def vals(df: pd.DataFrame) -> np.ndarray:
            values = df[metric_key].astype(float).to_numpy()
            return values * AREA_SCALE if is_area else values

        groups = [
            ("WT Exp", vals(exp_wt)),
            ("WT Sim", vals(wt_runs)),
            ("mud Exp", vals(exp_mud)),
            ("mud Sim", vals(mud_runs)),
        ]
        make_boxplot_panel(ax, groups, title, unit, fill_map)
        ax.tick_params(axis="x", labelsize=FONT_SIZE_LABEL, pad=2)
        ax.tick_params(axis="y", labelsize=FONT_SIZE_LABEL)
        for label in ax.get_xticklabels():
            label.set_rotation(35)
            label.set_ha("right")
    fig.subplots_adjust(left=0.06, right=0.995, top=0.92, bottom=0.28, wspace=0.45)
    return fig


def regulatory_hypothesis_panel(
    exp_wt: pd.DataFrame,
    exp_mud: pd.DataFrame,
) -> plt.Figure:
    fill_map = {
        "WT Exp": EXP_FILL_COLOR,
        "mud Exp": EXP_FILL_COLOR,
    }
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 5.2))
    specs = [
        ("n_dpn", "NB count", "cells", False),
        ("avg_dpn_area_vox", "Mean NB area", "µm²/cell", True),
    ]
    for ax, (metric_key, title, ylabel, is_area) in zip(axes, specs):
        def vals(df: pd.DataFrame) -> np.ndarray:
            values = df[metric_key].astype(float).to_numpy()
            return values * AREA_SCALE if is_area else values

        groups = [
            ("WT Exp", vals(exp_wt)),
            ("mud Exp", vals(exp_mud)),
        ]
        make_boxplot_panel(ax, groups, title, ylabel, fill_map)
        ax.tick_params(axis="x", labelsize=FONT_SIZE_LABEL, pad=2)
        ax.tick_params(axis="y", labelsize=FONT_SIZE_LABEL)
        for label in ax.get_xticklabels():
            label.set_rotation(35)
            label.set_ha("right")
    fig.subplots_adjust(left=0.13, right=0.99, top=0.92, bottom=0.22, wspace=0.40)
    return fig


def confirm_sim51_configuration() -> dict[str, object]:
    config_path = REPO_ROOT / "data" / "sim" / "sweep" / MUD_CONDITION / MUD_SIM_ID / "2026-04-26-biovcv0_noreg_mudmut_volume_none_detdiff.json"
    config = json.loads(config_path.read_text())
    pop = config["populations"]["fly-stem-mudmut"]
    potts = config["potts"]
    return {
        "div_rotation_mu": pop["proliferation/DIV_ROTATION_DISTRIBUTION_MU"],
        "div_rotation_sigma": pop["proliferation/DIV_ROTATION_DISTRIBUTION_SIGMA"],
        "apical_axis_rotation_mu": pop["proliferation/APICAL_AXIS_ROTATION_DISTRIBUTION_MU"],
        "apical_axis_rotation_sigma": pop["proliferation/APICAL_AXIS_ROTATION_DISTRIBUTION_SIGMA"],
        "critical_volume_mode": pop["proliferation/VOLUME_BASED_CRITICAL_VOLUME"],
        "dynamic_growth_rate_volume": pop["proliferation/DYNAMIC_GROWTH_RATE_VOLUME"],
        "dynamic_growth_rate_nb_self_repression": pop["proliferation/DYNAMIC_GROWTH_RATE_NB_SELF_REPRESSION"],
        "nb_nb_adhesion": potts["adhesion/ADHESION:fly-stem-mudmut:fly-stem-mudmut"],
        "default_cell_cell_adhesion": potts["adhesion/ADHESION:fly-stem-mudmut:fly-gmc"],
    }


def generate_all() -> dict[str, Path]:
    _, run_index_df, _, exp_index_df, sim_focus = load_data()
    wt_runs = sim_focus.loc[sim_focus["group"] == "WT Sim"].drop(columns=["group"]).copy()
    mud_runs = sim_focus.loc[sim_focus["group"] == "mudmut Sim"].drop(columns=["group"]).copy()
    exp_wt = attach_exp_analysis(exp_index_df, "wt")
    exp_mud = attach_exp_analysis(exp_index_df, "mudmut")

    fig_b = representative_lineages_panel(wt_runs, mud_runs, run_index_df)
    path_b_png = FIG_DIR / "figure3_mutant_examples_panel.png"
    path_b_pdf = FIG_DIR / "figure3_mutant_examples_panel.pdf"
    fig_b.savefig(path_b_png, bbox_inches="tight", facecolor="white")
    fig_b.savefig(path_b_pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig_b)

    fig_c = endpoint_metrics_panel(exp_wt, exp_mud, wt_runs, mud_runs)
    path_c_png = FIG_DIR / "figure3_endpoint_metrics_panel.png"
    path_c_pdf = FIG_DIR / "figure3_endpoint_metrics_panel.pdf"
    fig_c.savefig(path_c_png, bbox_inches="tight", facecolor="white")
    fig_c.savefig(path_c_pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig_c)

    fig_d = regulatory_hypothesis_panel(exp_wt, exp_mud)
    path_d_png = FIG_DIR / "figure3_mutant_hypothesis_panel.png"
    path_d_pdf = FIG_DIR / "figure3_mutant_hypothesis_panel.pdf"
    fig_d.savefig(path_d_png, bbox_inches="tight", facecolor="white")
    fig_d.savefig(path_d_pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig_d)

    return {
        "figure3_mutant_examples_panel.png": path_b_png,
        "figure3_mutant_examples_panel.pdf": path_b_pdf,
        "figure3_endpoint_metrics_panel.png": path_c_png,
        "figure3_endpoint_metrics_panel.pdf": path_c_pdf,
        "figure3_mutant_hypothesis_panel.png": path_d_png,
        "figure3_mutant_hypothesis_panel.pdf": path_d_pdf,
    }


if __name__ == "__main__":
    print(confirm_sim51_configuration())
    for name, path in generate_all().items():
        print(f"saved {name}: {path}")
