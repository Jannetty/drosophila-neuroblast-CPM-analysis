"""Compute per-condition alignment of calibration-sweep runs against experimental mud.

For each condition × metric: records sim median, sim IQR, exp mud IQR,
whether the sim median falls inside the exp IQR, and the IQR overlap
fraction (Jaccard of the two IQR intervals).

Input:
  data/sim/processed_calibrate/sim_metrics_last.csv
  data/sim/calibrate_sweep/conditions.csv
  data/exp/processed/metrics.csv

Output:
  data/sim/processed_calibrate/alignment_summary.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT       = Path(__file__).resolve().parents[1]
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_calibrate" / "sim_metrics_last.csv"
CONDITIONS_CSV  = REPO_ROOT / "data" / "sim" / "calibrate_sweep" / "conditions.csv"
EXP_METRICS_CSV = REPO_ROOT / "data" / "exp" / "processed" / "metrics.csv"
OUT_CSV         = REPO_ROOT / "data" / "sim" / "processed_calibrate" / "alignment_summary.csv"

DS_UM_PER_VOX = 0.3
AREA_SCALE    = DS_UM_PER_VOX ** 2

METRIC_SPECS = [
    ("lin_area_vox",     True),
    ("dpn_area_vox",     True),
    ("avg_dpn_area_vox", True),
    ("n_pros",           False),
    ("n_dpn",            False),
]


def _scale(values: np.ndarray, is_area: bool) -> np.ndarray:
    return values * AREA_SCALE if is_area else values


def main() -> None:
    sim      = pd.read_csv(SIM_METRICS_CSV)
    cond_meta = pd.read_csv(CONDITIONS_CSV)
    exp      = pd.read_csv(EXP_METRICS_CSV)
    exp_mud  = exp.loc[exp["genotype"] == "mudmut"]

    rows: list[dict] = []
    for _, cond_row in cond_meta.iterrows():
        folder     = cond_row["folder"]
        cond_runs  = sim.loc[sim["condition"] == folder]
        if cond_runs.empty:
            print(f"WARNING: no runs for {folder} — skipping")
            continue

        rec: dict = dict(cond_row)
        n_aligned = 0

        for key, is_area in METRIC_SPECS:
            sim_vals = _scale(cond_runs[key].astype(float).to_numpy(), is_area)
            exp_vals = _scale(exp_mud[key].astype(float).to_numpy(),   is_area)

            sim_med        = float(np.median(sim_vals))
            sim_q25, sim_q75 = float(np.percentile(sim_vals, 25)), float(np.percentile(sim_vals, 75))
            exp_q25, exp_q75 = float(np.percentile(exp_vals, 25)), float(np.percentile(exp_vals, 75))

            in_iqr  = exp_q25 <= sim_med <= exp_q75

            overlap      = max(0.0, min(sim_q75, exp_q75) - max(sim_q25, exp_q25))
            union        = max(sim_q75, exp_q75) - min(sim_q25, exp_q25)
            overlap_frac = round(overlap / union, 3) if union > 0 else 0.0

            rec[f"{key}_sim_median"]    = round(sim_med, 3)
            rec[f"{key}_sim_q25"]       = round(sim_q25, 3)
            rec[f"{key}_sim_q75"]       = round(sim_q75, 3)
            rec[f"{key}_exp_q25"]       = round(exp_q25, 3)
            rec[f"{key}_exp_q75"]       = round(exp_q75, 3)
            rec[f"{key}_in_iqr"]        = in_iqr
            rec[f"{key}_overlap_frac"]  = overlap_frac
            if in_iqr:
                n_aligned += 1

        rec["n_metrics_aligned"] = n_aligned
        rows.append(rec)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(out)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
