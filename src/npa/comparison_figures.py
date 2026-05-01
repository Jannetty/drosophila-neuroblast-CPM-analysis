from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from npa.metrics import COMPARISON_METRIC_COLUMNS, EXP_SUMMARY_COLUMNS

WT_REF_COLOR = "#4a4a4a"
MUDMUT_REF_COLOR = "#c25b5b"

COMPARISON_MODES = (
    "intra",
    "inter-div-priority",
    "inter-rot-priority",
)

SCALES = ("raw", "foldchange")

SIM_PLOTTING_DTYPES: dict[str, str] = {
    "condition": "string",
    "sim_id": "string",
    "run_id": "string",
    "genotype": "string",
    "regulatory_dynamic": "string",
    "critical_volume_mode": "Int64",
    "div_mean": "Int64",
    "div_stdev": "Int64",
    "rot_mean": "Int64",
    "rot_stdev": "Int64",
}

SIM_CATEGORY_LABELS = {
    "wt": "WT",
    "mudmut": "MM",
}

GENOTYPE_SORT_ORDER = {
    "wt": 0,
    "mudmut": 1,
}

METRIC_TITLES = {
    "n_dpn": "n_dpn",
    "avg_dpn_area_vox": "avg_dpn_area_vox",
    "lin_area_vox": "lin_area_vox",
    "n_pros": "n_pros",
    "dpn_area_vox": "dpn_area_vox",
}

METRIC_RAW_UNITS = {
    "n_dpn": "cells",
    "avg_dpn_area_vox": "vox/cell",
    "lin_area_vox": "vox",
    "n_pros": "cells",
    "dpn_area_vox": "vox",
}


def load_sim_plotting_input(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=SIM_PLOTTING_DTYPES)
    missing = [column for column in ("condition", "sim_id", "run_id", *COMPARISON_METRIC_COLUMNS) if column not in df.columns]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing simulation plotting columns: {joined}")
    return df


def load_exp_summary(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [column for column in EXP_SUMMARY_COLUMNS if column not in df.columns]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing experimental summary columns: {joined}")
    return df.loc[df["genotype"].isin(["wt", "mudmut"])].reset_index(drop=True)


def _require_metric(metric: str) -> None:
    if metric not in COMPARISON_METRIC_COLUMNS:
        joined = ", ".join(COMPARISON_METRIC_COLUMNS)
        raise ValueError(f"Unsupported metric '{metric}'. Expected one of: {joined}")


def _sim_category_label(row: pd.Series) -> str:
    genotype = SIM_CATEGORY_LABELS.get(str(row["genotype"]), str(row["genotype"]).upper())
    vcv = f"VCV{int(row['critical_volume_mode'])}"
    dynamic = str(row["regulatory_dynamic"])
    return f"{genotype}-{vcv}\n{dynamic}"


def _condition_tag(row: pd.Series) -> str:
    return f"D{int(row['div_mean'])}S{int(row['div_stdev'])}\nR{int(row['rot_mean'])}S{int(row['rot_stdev'])}"


def _inter_sort_columns(mode: str) -> list[str]:
    if mode == "inter-div-priority":
        return ["rot_mean", "rot_stdev", "div_mean", "div_stdev"]
    if mode == "inter-rot-priority":
        return ["div_mean", "div_stdev", "rot_mean", "rot_stdev"]
    raise ValueError(f"Unsupported inter mode: {mode}")


def _reference_stats(exp_summary: pd.DataFrame, metric: str) -> dict[str, dict[str, float]]:
    _require_metric(metric)
    refs: dict[str, dict[str, float]] = {}
    for genotype in ("wt", "mudmut"):
        rows = exp_summary.loc[exp_summary["genotype"] == genotype]
        if rows.empty:
            raise ValueError(f"Experimental summary is missing genotype '{genotype}'")
        row = rows.iloc[0]
        refs[genotype] = {
            "mean": float(row[f"{metric}_mean"]),
            "std": float(row[f"{metric}_std"]),
        }
    return refs


def _scale_values(values: list[float], wt_mean: float, scale: str) -> list[float]:
    if scale == "raw":
        return values
    if wt_mean == 0:
        raise ValueError("Cannot compute fold-change because the experimental WT mean is zero")
    return [value / wt_mean for value in values]


def _scale_reference_stats(
    refs: dict[str, dict[str, float]],
    scale: str,
) -> dict[str, dict[str, float]]:
    if scale == "raw":
        return refs
    wt_mean = refs["wt"]["mean"]
    if wt_mean == 0:
        raise ValueError("Cannot compute fold-change because the experimental WT mean is zero")
    scaled: dict[str, dict[str, float]] = {}
    for genotype, stats in refs.items():
        scaled[genotype] = {
            "mean": stats["mean"] / wt_mean,
            "std": stats["std"] / wt_mean,
        }
    return scaled


def prepare_intra_condition_data(
    sim_df: pd.DataFrame,
    condition: str,
    metric: str,
    scale: str,
    exp_summary: pd.DataFrame,
) -> pd.DataFrame:
    _require_metric(metric)
    subset = sim_df.loc[sim_df["condition"] == condition].copy()
    if subset.empty:
        raise ValueError(f"No simulation rows found for condition '{condition}'")
    subset["plot_label"] = subset.apply(_sim_category_label, axis=1)
    subset["genotype_sort"] = subset["genotype"].map(
        lambda value: GENOTYPE_SORT_ORDER.get(str(value), 99)
    )
    subset = subset.sort_values(
        ["genotype_sort", "critical_volume_mode", "regulatory_dynamic", "sim_id", "run_id"],
        kind="stable",
    ).reset_index(drop=True)
    refs = _reference_stats(exp_summary, metric)
    wt_mean = refs["wt"]["mean"]
    subset["plot_value"] = _scale_values(subset[metric].astype(float).tolist(), wt_mean, scale)
    return subset.drop(columns=["genotype_sort"])


def prepare_inter_condition_data(
    sim_df: pd.DataFrame,
    sim_id: str,
    metric: str,
    scale: str,
    exp_summary: pd.DataFrame,
    mode: str,
) -> pd.DataFrame:
    _require_metric(metric)
    subset = sim_df.loc[sim_df["sim_id"] == sim_id].copy()
    if subset.empty:
        raise ValueError(f"No simulation rows found for sim_id '{sim_id}'")
    sort_cols = _inter_sort_columns(mode)
    subset["plot_label"] = subset.apply(_condition_tag, axis=1)
    subset = subset.sort_values(sort_cols + ["condition", "run_id"], kind="stable").reset_index(drop=True)
    refs = _reference_stats(exp_summary, metric)
    wt_mean = refs["wt"]["mean"]
    subset["plot_value"] = _scale_values(subset[metric].astype(float).tolist(), wt_mean, scale)
    return subset


def prepare_plot_data(
    *,
    sim_df: pd.DataFrame,
    exp_summary: pd.DataFrame,
    mode: str,
    metric: str,
    scale: str,
    condition: str | None = None,
    sim_id: str | None = None,
) -> tuple[pd.DataFrame, dict[str, dict[str, float]], str]:
    if scale not in SCALES:
        raise ValueError(f"Unsupported scale '{scale}'")
    refs = _scale_reference_stats(_reference_stats(exp_summary, metric), scale)
    if mode == "intra":
        if condition is None:
            raise ValueError("mode 'intra' requires a condition")
        return (
            prepare_intra_condition_data(sim_df, condition, metric, scale, exp_summary),
            refs,
            condition,
        )
    if mode in {"inter-div-priority", "inter-rot-priority"}:
        if sim_id is None:
            raise ValueError(f"mode '{mode}' requires a sim_id")
        return (
            prepare_inter_condition_data(sim_df, sim_id, metric, scale, exp_summary, mode),
            refs,
            sim_id,
        )
    raise ValueError(f"Unsupported mode '{mode}'")


def _y_label(metric: str, scale: str) -> str:
    if scale == "foldchange":
        return f"{metric} (fold change from WT mean, log scale)"
    return f"{metric} ({METRIC_RAW_UNITS[metric]}, log scale)"


def _title(mode: str, metric: str, anchor: str, scale: str) -> str:
    mode_title = {
        "intra": "Intra-condition",
        "inter-div-priority": "Inter-condition (div-priority)",
        "inter-rot-priority": "Inter-condition (rot-priority)",
    }[mode]
    scale_title = "WT fold-change" if scale == "foldchange" else "raw"
    return f"{mode_title} | {anchor} | {METRIC_TITLES[metric]} | {scale_title}"


def draw_comparison_figure(
    *,
    plot_df: pd.DataFrame,
    refs: dict[str, dict[str, float]],
    mode: str,
    metric: str,
    scale: str,
    anchor: str,
) -> plt.Figure:
    grouped = list(plot_df.groupby("plot_label", sort=False))
    if not grouped:
        raise ValueError("No plotting groups were prepared")

    labels = [label for label, _ in grouped]
    values = [group["plot_value"].astype(float).tolist() for _, group in grouped]

    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.3), 6))
    ax.boxplot(values, tick_labels=labels, patch_artist=False)

    for genotype, color in (("wt", WT_REF_COLOR), ("mudmut", MUDMUT_REF_COLOR)):
        mean = refs[genotype]["mean"]
        std = refs[genotype]["std"]
        ax.axhspan(mean - std, mean + std, color=color, alpha=0.12)
        ax.axhline(mean, color=color, linewidth=1.8, label=genotype)

    ax.set_yscale("log")
    ax.set_title(_title(mode, metric, anchor, scale))
    ax.set_ylabel(_y_label(metric, scale))
    ax.set_xlabel("")
    ax.tick_params(axis="x", labelrotation=0)
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


def default_output_path(
    *,
    sim_metrics_path: Path,
    mode: str,
    metric: str,
    scale: str,
    condition: str | None = None,
    sim_id: str | None = None,
) -> Path:
    figures_root = sim_metrics_path.parent / "figures" / "comparisons"
    if mode == "intra":
        assert condition is not None
        return figures_root / "intra" / f"intra_{condition}_{metric}_{scale}.png"
    if mode == "inter-div-priority":
        assert sim_id is not None
        return figures_root / "inter_div_priority" / f"inter_div_priority_{sim_id}_{metric}_{scale}.png"
    if mode == "inter-rot-priority":
        assert sim_id is not None
        return figures_root / "inter_rot_priority" / f"inter_rot_priority_{sim_id}_{metric}_{scale}.png"
    raise ValueError(f"Unsupported mode '{mode}'")


def create_and_save_comparison_figure(
    *,
    sim_metrics_path: Path,
    exp_summary_path: Path,
    mode: str,
    metric: str,
    scale: str,
    condition: str | None = None,
    sim_id: str | None = None,
    out_path: Path | None = None,
) -> Path:
    sim_df = load_sim_plotting_input(sim_metrics_path)
    exp_summary = load_exp_summary(exp_summary_path)
    plot_df, refs, anchor = prepare_plot_data(
        sim_df=sim_df,
        exp_summary=exp_summary,
        mode=mode,
        metric=metric,
        scale=scale,
        condition=condition,
        sim_id=sim_id,
    )
    fig = draw_comparison_figure(
        plot_df=plot_df,
        refs=refs,
        mode=mode,
        metric=metric,
        scale=scale,
        anchor=anchor,
    )
    destination = (
        out_path
        if out_path is not None
        else default_output_path(
            sim_metrics_path=sim_metrics_path,
            mode=mode,
            metric=metric,
            scale=scale,
            condition=condition,
            sim_id=sim_id,
        )
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return destination
