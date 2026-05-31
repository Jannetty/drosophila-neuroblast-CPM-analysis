from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import trimesh
from scipy.stats import mannwhitneyu

matplotlib.use("Agg")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docs" / "tex_draft"))
from _style import RCPARAMS, FONT_SIZE_TITLE, FONT_SIZE_LABEL

plt.rcParams.update(RCPARAMS)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROC_DIR = REPO_ROOT / "data" / "exp" / "processed"
FIG_DIR = REPO_ROOT / "docs" / "tex_draft" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

GENOTYPES = ["wt", "mudmut"]

DIM2D_COLOR = "#4C72B0"
DIM3D_COLOR = "#DD8452"

def load_3d_metrics(proc_dir: Path) -> pd.DataFrame:
    index = pd.read_csv(proc_dir / "lineage_index.csv")
    index = index[index["genotype"].isin(GENOTYPES)].copy()

    rows = []
    for _, row in index.iterrows():
        npz_path = proc_dir / "meshes" / row["genotype"] / f"{row['lobe']}_{row['lineage_idx']}.npz"
        npz = np.load(npz_path)
        dpn_vols = npz["dpn_volumes_um3"]
        pros_vols = npz["pros_volumes_um3"]
        mesh = trimesh.Trimesh(vertices=npz["lin_vertices"], faces=npz["lin_faces"], process=False)
        lin_vol = abs(float(mesh.volume))
        rows.append({
            "lineage_id": int(row["lineage_id"]),
            "genotype": row["genotype"],
            "n_dpn": len(dpn_vols),
            "dpn_area": float(dpn_vols.sum()),
            "avg_dpn_area": float(dpn_vols.mean()),
            "lin_area": lin_vol,
            "n_pros": len(pros_vols),
        })
    return pd.DataFrame(rows)


def load_2d_metrics(proc_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(proc_dir / "metrics.csv")
    df = df[df["genotype"].isin(GENOTYPES)].copy()
    ds = df["ds"].values
    df["dpn_area"] = df["dpn_area_vox"] * ds * ds
    df["avg_dpn_area"] = df["avg_dpn_area_vox"] * ds * ds
    df["lin_area"] = df["lin_area_vox"] * ds * ds
    return df[["lineage_id", "genotype", "n_dpn", "dpn_area", "avg_dpn_area", "lin_area", "n_pros"]].copy()


def _fmt_p(p: float) -> str:
    if p < 0.001:
        return "<0.001"
    if p < 0.01:
        return f"{p:.3f}"
    return f"{p:.2f}"


def build_table(df_2d: pd.DataFrame, df_3d: pd.DataFrame) -> pd.DataFrame:
    metric_labels = {
        "n_dpn":        "# neuroblasts (dpn)",
        "dpn_area":     "Total NB area/volume",
        "avg_dpn_area": "Avg NB area/volume",
        "lin_area":     "Lineage area/volume",
        "n_pros":       "# non-neuroblasts (pros)",
    }
    rows = []
    for col, label in metric_labels.items():
        for dim, df in [("2D", df_2d), ("3D", df_3d)]:
            wt_vals  = df.loc[df["genotype"] == "wt",     col].values.astype(float)
            mud_vals = df.loc[df["genotype"] == "mudmut", col].values.astype(float)
            wt_mean  = wt_vals.mean()
            mud_mean = mud_vals.mean()
            fc       = mud_mean / wt_mean
            _, p     = mannwhitneyu(wt_vals, mud_vals, alternative="two-sided")
            rows.append({
                "feature":     col,
                "metric":      label,
                "dim":         dim,
                "wt_mean":     wt_mean,
                "mudmut_mean": mud_mean,
                "fold_change": fc,
                "p_mwu":       p,
                "p_mwu_fmt":   _fmt_p(p),
            })
    return pd.DataFrame(rows)


def make_genotype_histogram_panel(
    df_2d: pd.DataFrame,
    df_3d: pd.DataFrame,
    genotype: str,
) -> plt.Figure:
    metric_cols = ["n_dpn", "dpn_area", "avg_dpn_area", "lin_area", "n_pros"]
    metric_titles = [
        "# neuroblasts\n(dpn)",
        "total NB\narea / volume",
        "avg NB area /\nvolume per cell",
        "lineage\narea / volume",
        "# non-neuroblasts\n(pros)",
    ]
    label = "WT" if genotype == "wt" else "mudmut"

    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    fig.suptitle(f"{label} lineages: 2D vs 3D representations", fontsize=FONT_SIZE_TITLE)

    for ax, col, title in zip(axes, metric_cols, metric_titles):
        wt_mean_2d = df_2d.loc[df_2d["genotype"] == "wt", col].mean()
        wt_mean_3d = df_3d.loc[df_3d["genotype"] == "wt", col].mean()

        vals_2d = (df_2d.loc[df_2d["genotype"] == genotype, col] / wt_mean_2d).values
        vals_3d = (df_3d.loc[df_3d["genotype"] == genotype, col] / wt_mean_3d).values

        all_vals = np.concatenate([vals_2d, vals_3d])
        lo, hi   = np.nanpercentile(all_vals, 2), np.nanpercentile(all_vals, 98)
        if hi <= lo:
            lo, hi = lo - 0.5, hi + 0.5
        bins     = np.linspace(lo, hi, 20)

        ax.hist(vals_2d, bins=bins, alpha=0.5, color=DIM2D_COLOR, edgecolor=DIM2D_COLOR,
                linewidth=1.2, label="2D", density=True)
        ax.hist(vals_3d, bins=bins, alpha=0.0, color=DIM3D_COLOR, edgecolor=DIM3D_COLOR,
                linewidth=1.5, hatch="///", label="3D", density=True)

        ax.axvline(1.0, color="gray", linestyle="--", linewidth=1.0)
        ax.set_xlabel("fold-change from WT mean", fontsize=FONT_SIZE_LABEL - 2)
        ax.set_title(title, fontsize=FONT_SIZE_LABEL)
        ax.set_ylabel("density" if ax is axes[0] else "", fontsize=FONT_SIZE_LABEL - 2)

    handles = [
        plt.Rectangle((0, 0), 1, 1, fc=DIM2D_COLOR, alpha=0.5, label="2D (area, µm²)"),
        plt.Rectangle((0, 0), 1, 1, fc="none", ec=DIM3D_COLOR, hatch="///",
                       linewidth=1.5, label="3D (volume, µm³)"),
    ]
    axes[-1].legend(handles=handles, loc="upper right", fontsize=FONT_SIZE_LABEL - 3, frameon=False)

    fig.tight_layout()
    return fig


METRICS = [
    ("n_dpn",        "# neuroblasts",           "fold-change from WT"),
    ("dpn_area",     "total NB area/vol",        "fold-change from WT"),
    ("avg_dpn_area", "avg NB area/vol per cell", "fold-change from WT"),
    ("lin_area",     "lineage area/vol",         "fold-change from WT"),
    ("n_pros",       "# non-neuroblasts",        "fold-change from WT"),
]
