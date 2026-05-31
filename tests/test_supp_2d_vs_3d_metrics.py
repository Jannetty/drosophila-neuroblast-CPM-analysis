import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

PROC_DIR = Path("data/exp/processed")


def test_load_2d_metrics_unit_conversion():
    from make_supp_2d_vs_3d_metrics import load_2d_metrics

    df = load_2d_metrics(PROC_DIR)
    raw = pd.read_csv(PROC_DIR / "metrics.csv")
    raw = raw[raw["genotype"].isin(["wt", "mudmut"])].reset_index(drop=True)
    df = df.reset_index(drop=True)

    expected = raw["dpn_area_vox"] * raw["ds"] ** 2
    np.testing.assert_allclose(df["dpn_area"].values, expected.values, rtol=1e-5)


def test_load_2d_metrics_only_wt_mudmut():
    from make_supp_2d_vs_3d_metrics import load_2d_metrics

    df = load_2d_metrics(PROC_DIR)
    assert set(df["genotype"].unique()) <= {"wt", "mudmut"}
