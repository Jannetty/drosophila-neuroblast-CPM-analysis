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


def test_load_3d_metrics_n_dpn_matches_index():
    from make_supp_2d_vs_3d_metrics import load_3d_metrics

    df3d = load_3d_metrics(PROC_DIR)
    index = pd.read_csv(PROC_DIR / "lineage_index.csv")
    index = index[index["genotype"].isin(["wt", "mudmut"])]
    merged = df3d.merge(index[["lineage_id", "n_dpn"]], on="lineage_id", suffixes=("_3d", "_idx"))
    assert (merged["n_dpn_3d"] == merged["n_dpn_idx"]).all()


def test_load_3d_metrics_lin_area_positive():
    from make_supp_2d_vs_3d_metrics import load_3d_metrics

    df3d = load_3d_metrics(PROC_DIR)
    assert (df3d["lin_area"] > 0).all()


def test_build_table_fold_change():
    from make_supp_2d_vs_3d_metrics import load_2d_metrics, load_3d_metrics, build_table

    tbl = build_table(load_2d_metrics(PROC_DIR), load_3d_metrics(PROC_DIR))
    row = tbl[(tbl["feature"] == "n_dpn") & (tbl["dim"] == "2D")].iloc[0]
    assert abs(row["fold_change"] - row["mudmut_mean"] / row["wt_mean"]) < 1e-10
