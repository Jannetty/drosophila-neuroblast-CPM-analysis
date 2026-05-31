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


METRICS = [
    ("n_dpn",        "# neuroblasts",           "fold-change from WT"),
    ("dpn_area",     "total NB area/vol",        "fold-change from WT"),
    ("avg_dpn_area", "avg NB area/vol per cell", "fold-change from WT"),
    ("lin_area",     "lineage area/vol",         "fold-change from WT"),
    ("n_pros",       "# non-neuroblasts",        "fold-change from WT"),
]
