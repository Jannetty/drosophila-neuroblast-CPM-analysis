"""Plot 5 endpoint metrics for each calibration-sweep condition vs experimental mud.

One PDF page per condition. Within each page: 1 row × 5 metric panels,
log y-axis, sim boxplot (no fliers), experimental mud IQR band + median.
Pages sorted by the order in conditions.csv.

Input:
  data/sim/processed_calibrate/sim_metrics_last.csv
  data/sim/calibrate_sweep/conditions.csv
  data/exp/processed/metrics.csv

Output:
  docs/tex_draft/figures/calibrate_sweep_plots.pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch

matplotlib.use("Agg")

REPO_ROOT       = Path(__file__).resolve().parents[1]
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_calibrate" / "sim_metrics_last.csv"
CONDITIONS_CSV  = REPO_ROOT / "data" / "sim" / "calibrate_sweep" / "conditions.csv"
EXP_METRICS_CSV = REPO_ROOT / "data" / "exp" / "processed" / "metrics.csv"
OUT_PDF         = REPO_ROOT / "docs" / "tex_draft" / "figures" / "calibrate_sweep_plots.pdf"

DS_UM_PER_VOX  = 0.3
AREA_SCALE     = DS_UM_PER_VOX ** 2
EXP_BAND_COLOR = "#c0392b"
EXP_BAND_ALPHA = 0.13
SIM_BOX_COLOR  = "#5f5f5f"

METRIC_SPECS = [
    ("lin_area_vox",     "Lineage area",  "µm²",      True),
    ("dpn_area_vox",     "Total NB area", "µm²",      True),
    ("avg_dpn_area_vox", "Mean NB area",  "µm²/cell", True),
    ("n_pros",           "Pros count",    "cells",    False),
    ("n_dpn",            "NB count",      "cells",    False),
]


def _scale(values: np.ndarray, is_area: bool) -> np.ndarray:
    return values * AREA_SCALE if is_area else values


def _param_label(row: pd.Series) -> str:
    if row["regulation"] == "volume":
        return f"sensitivity={row['GROWTH_RATE_VOLUME_SENSITIVITY']}"
    parts = [f"half_max={row['NB_CONTACT_HALF_MAX']}"]
    hn = str(row["NB_CONTACT_HILL_N"])
    if hn not in ("N/A", "3.0"):
        parts.append(f"hill_n={hn}")
    return "  ".join(parts)


def main() -> None:
    sim       = pd.read_csv(SIM_METRICS_CSV)
    cond_meta = pd.read_csv(CONDITIONS_CSV)
    exp       = pd.read_csv(EXP_METRICS_CSV)
    exp_mud   = exp.loc[exp["genotype"] == "mudmut"]

    # Pre-compute exp mud reference values once
    exp_refs: dict[str, tuple[float, float, float]] = {}
    for key, _, _, is_area in METRIC_SPECS:
        vals = _scale(exp_mud[key].astype(float).to_numpy(), is_area)
        exp_refs[key] = (
            float(np.median(vals)),
            float(np.percentile(vals, 25)),
            float(np.percentile(vals, 75)),
        )

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    n_written = 0

    with PdfPages(OUT_PDF) as pdf:
        for _, cond_row in cond_meta.iterrows():
            folder    = cond_row["folder"]
            cond_runs = sim.loc[sim["condition"] == folder]
            if cond_runs.empty:
                print(f"WARNING: no runs for {folder} — skipping page")
                continue

            fig, axes = plt.subplots(1, len(METRIC_SPECS), figsize=(16, 4))

            for ax, (key, title, unit, is_area) in zip(axes, METRIC_SPECS):
                sim_vals = _scale(cond_runs[key].astype(float).to_numpy(), is_area)
                med, q25, q75 = exp_refs[key]

                ax.boxplot(
                    [sim_vals],
                    positions=[1],
                    widths=0.55,
                    patch_artist=True,
                    showfliers=False,
                    medianprops={"color": "black", "linewidth": 1.4},
                    boxprops={"facecolor": SIM_BOX_COLOR, "edgecolor": "black", "linewidth": 1.0},
                    whiskerprops={"color": "black", "linewidth": 0.9},
                    capprops={"color": "black", "linewidth": 0.9},
                    manage_ticks=False,
                )
                ax.axhspan(q25, q75, color=EXP_BAND_COLOR, alpha=EXP_BAND_ALPHA, zorder=1)
                ax.axhline(med, color=EXP_BAND_COLOR, linewidth=1.4, linestyle="--", zorder=2)
                ax.set_yscale("log")
                ax.set_title(title, fontsize=10)
                ax.set_ylabel(unit, fontsize=9)
                ax.set_xticks([])

            vcv       = "VCV1" if folder.startswith("vcv1") else "VCV0"
            param_str = _param_label(cond_row)
            fig.suptitle(
                f"{folder}   [{vcv}  {cond_row['regulation']}  "
                f"{cond_row['mechanism']}  {param_str}]",
                fontsize=10, y=1.02,
            )

            legend_handles = [
                Patch(facecolor=SIM_BOX_COLOR, edgecolor="black", label=f"simulation (n={len(cond_runs)})"),
                Patch(facecolor=EXP_BAND_COLOR, alpha=EXP_BAND_ALPHA + 0.2, label="exp mud IQR"),
            ]
            fig.legend(
                handles=legend_handles, loc="upper right",
                fontsize=8, frameon=False, bbox_to_anchor=(1.0, 1.10),
            )
            fig.tight_layout()
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            n_written += 1

    print(f"Wrote {n_written} pages to {OUT_PDF}")


if __name__ == "__main__":
    main()
