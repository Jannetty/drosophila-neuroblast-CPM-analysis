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

METRICS = [
    ("n_dpn",        "# neuroblasts",           "fold-change from WT"),
    ("dpn_area",     "total NB area/vol",        "fold-change from WT"),
    ("avg_dpn_area", "avg NB area/vol per cell", "fold-change from WT"),
    ("lin_area",     "lineage area/vol",         "fold-change from WT"),
    ("n_pros",       "# non-neuroblasts",        "fold-change from WT"),
]
