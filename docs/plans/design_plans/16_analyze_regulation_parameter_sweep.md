# Plan 16 — Analyze regulation parameter calibration sweep

**Date:** 2026-05-12
**Goal:** Run the existing preprocessing/metrics pipeline on the 48-condition
calibration sweep in `data/sim/calibrate_sweep/`, then produce (a) a
browsable per-condition PDF showing all 5 endpoint metrics against the
experimental *mud* IQR, and (b) an alignment-summary CSV that quantifies
how well each condition matches experiment across each metric.

---

## Context

Figure 4 shows how 5 regulatory-dynamics variants compare to experimental
*mud* lineages on 5 endpoint metrics (lineage area, total NB area, mean NB
area, Pros count, NB count), using the experimental IQR as the reference
band.

The calibration sweep varies hyperparameters of those same regulatory
mechanisms to find which parameter combinations best recapitulate the
experimental *mud* phenotype. There are 48 conditions across two VCV modes
(vcv0, vcv1), two regulation types (volume, NB_contact), two mechanisms
(ABM, PDE), and swept parameter values documented in
`data/sim/calibrate_sweep/conditions.csv`.

**Important:** The condition folders currently contain only XML config files.
Simulations must be run before preprocessing can proceed. The scripts and
Makefile targets described below can be implemented immediately; they can be
executed once simulation output lands in the condition subdirectories.

---

## Expected simulation output structure

When ARCADE runs each XML, it creates a subdirectory under the condition
folder named after the series (e.g.
`vcv1_nb_abm_hm3p0_mudmut_vcv1_nb_abm/`). After running:

```
data/sim/calibrate_sweep/
  conditions.csv
  vcv1_nb_abm_hm3p0/
    vcv1_nb_abm_hm3p0.xml
    vcv1_nb_abm_hm3p0_mudmut_vcv1_nb_abm/   ← ARCADE writes here
      2026-05-12-calibrate_...._0001_000000.CELLS.json
      2026-05-12-calibrate_...._0001_000000.LOCATIONS.json
      ...  (50 runs × 2 timepoints each)
  vcv1_nb_abm_hm4p0/
    ...
```

This fits the existing `preprocess_sim.py` / `extract_metrics.py` pattern
unchanged:
- sweep root → `data/sim/calibrate_sweep/`
- condition = top-level folder name (e.g. `vcv1_nb_abm_hm3p0`)
- sim_id   = series output subfolder name

---

## Files to create or modify

| File | Action | Purpose |
|---|---|---|
| `Makefile` | Modify | Add calibrate-sweep pipeline targets |
| `scripts/plot_calibration_sweep.py` | Create | Per-condition 5-metric PDF |
| `scripts/analyze_calibration_alignment.py` | Create | Alignment-summary CSV |
| `docs/PIPELINE.md` | Modify | Document new pipeline stage |

No changes to `src/npa/`. All new logic lives in the two scripts, which
follow the same flat style as existing scripts in `scripts/`.

---

## Makefile additions

Add these variables and targets. Insert them after the adhesion-sweep block
and before the figures block.

### Variables (add near top with other dir vars)

```makefile
SIM_CALIB_DIR        := data/sim/calibrate_sweep
SIM_CALIB_PROC_DIR   := data/sim/processed_calibrate
```

### Targets

```makefile
# ── Calibration-sweep pipeline ───────────────────────────────────────────────
preprocess-calibrate-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(SIM_CALIB_DIR) \
		--out-dir $(SIM_CALIB_PROC_DIR)

extract-metrics-calibrate: preprocess-calibrate-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(SIM_CALIB_DIR) \
		--out-dir $(SIM_CALIB_PROC_DIR)

summarize-calibrate: extract-metrics-exp extract-metrics-calibrate
	$(UV) scripts/summarize_metrics.py \
		--sim-metrics $(SIM_CALIB_PROC_DIR)/sim_timepoint_metrics.csv \
		--exp-metrics $(EXP_PROC_DIR)/metrics.csv \
		--sim-out          $(SIM_CALIB_PROC_DIR)/sim_metrics_last.csv \
		--sim-summary-out  $(SIM_CALIB_PROC_DIR)/sim_summary_last.csv \
		--exp-summary-out  $(SIM_CALIB_PROC_DIR)/exp_summary.csv

analyze-calibrate: summarize-calibrate
	$(UV) scripts/analyze_calibration_alignment.py

plot-calibrate: summarize-calibrate
	$(UV) scripts/plot_calibration_sweep.py
```

Also add `preprocess-calibrate-raw extract-metrics-calibrate summarize-calibrate
analyze-calibrate plot-calibrate calibrate-clean` to the `.PHONY` list, and
add a `calibrate-clean` target:

```makefile
calibrate-clean:
	rm -rf $(SIM_CALIB_PROC_DIR)
```

`summarize-calibrate` does **not** need to be wired into `preprocess-data`
(calibration analysis is separate from the main figures pipeline).

---

## `scripts/analyze_calibration_alignment.py`

Reads the processed sim metrics and experimental mud metrics. For every
calibration condition × metric it records: sim median, sim IQR, exp IQR,
whether the sim median falls inside the exp IQR, and the IQR overlap
fraction (Jaccard of the two IQR intervals). Writes one CSV.

```python
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_METRICS_CSV  = REPO_ROOT / "data" / "sim" / "processed_calibrate" / "sim_metrics_last.csv"
CONDITIONS_CSV   = REPO_ROOT / "data" / "sim" / "calibrate_sweep" / "conditions.csv"
EXP_METRICS_CSV  = REPO_ROOT / "data" / "exp" / "processed" / "metrics.csv"
OUT_CSV          = REPO_ROOT / "data" / "sim" / "processed_calibrate" / "alignment_summary.csv"

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
    sim = pd.read_csv(SIM_METRICS_CSV)
    cond_meta = pd.read_csv(CONDITIONS_CSV)
    exp = pd.read_csv(EXP_METRICS_CSV)
    exp_mud = exp.loc[exp["genotype"] == "mudmut"]

    rows: list[dict] = []
    for _, cond_row in cond_meta.iterrows():
        folder = cond_row["folder"]
        cond_runs = sim.loc[sim["condition"] == folder]
        if cond_runs.empty:
            print(f"WARNING: no runs found for {folder} — skipping")
            continue

        rec: dict = dict(cond_row)
        n_aligned = 0

        for key, is_area in METRIC_SPECS:
            sim_vals = _scale(cond_runs[key].astype(float).to_numpy(), is_area)
            exp_vals = _scale(exp_mud[key].astype(float).to_numpy(), is_area)

            sim_med = float(np.median(sim_vals))
            sim_q25, sim_q75 = float(np.percentile(sim_vals, 25)), float(np.percentile(sim_vals, 75))
            exp_q25, exp_q75 = float(np.percentile(exp_vals, 25)), float(np.percentile(exp_vals, 75))

            in_iqr = exp_q25 <= sim_med <= exp_q75

            overlap = max(0.0, min(sim_q75, exp_q75) - max(sim_q25, exp_q25))
            union   = max(sim_q75, exp_q75) - min(sim_q25, exp_q25)
            overlap_frac = round(overlap / union, 3) if union > 0 else 0.0

            rec[f"{key}_sim_median"] = round(sim_med, 3)
            rec[f"{key}_sim_q25"]    = round(sim_q25, 3)
            rec[f"{key}_sim_q75"]    = round(sim_q75, 3)
            rec[f"{key}_exp_q25"]    = round(exp_q25, 3)
            rec[f"{key}_exp_q75"]    = round(exp_q75, 3)
            rec[f"{key}_in_iqr"]     = in_iqr
            rec[f"{key}_overlap_frac"] = overlap_frac
            if in_iqr:
                n_aligned += 1

        rec["n_metrics_aligned"] = n_aligned
        rows.append(rec)

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(out)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
```

**Verify:** after running, open `alignment_summary.csv` and confirm all 48
conditions are present, `n_metrics_aligned` ranges 0–5, and no metric
columns are all-NaN.

---

## `scripts/plot_calibration_sweep.py`

Produces a single multi-page PDF at
`docs/tex_draft/figures/calibrate_sweep_plots.pdf`. Pages are sorted by VCV
mode → regulation type → mechanism → parameter value, matching the order
in `conditions.csv`. Each page is one condition: 1 row × 5 columns, one
panel per metric. Each panel shows:
- boxplot of the 50 simulation runs (no fliers)
- shaded red IQR band from experimental mud
- dashed red median line from experimental mud
- log y-axis (same convention as figure 4 panel B)

The page title names the condition and its key parameters.

```python
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_calibrate" / "sim_metrics_last.csv"
CONDITIONS_CSV  = REPO_ROOT / "data" / "sim" / "calibrate_sweep" / "conditions.csv"
EXP_METRICS_CSV = REPO_ROOT / "data" / "exp" / "processed" / "metrics.csv"
OUT_PDF         = REPO_ROOT / "docs" / "tex_draft" / "figures" / "calibrate_sweep_plots.pdf"

DS_UM_PER_VOX = 0.3
AREA_SCALE    = DS_UM_PER_VOX ** 2
EXP_BAND_COLOR = "#c0392b"
EXP_BAND_ALPHA = 0.13

METRIC_SPECS = [
    ("lin_area_vox",     "Lineage area",    "µm²",       True),
    ("dpn_area_vox",     "Total NB area",   "µm²",       True),
    ("avg_dpn_area_vox", "Mean NB area",    "µm²/cell",  True),
    ("n_pros",           "Pros count",      "cells",     False),
    ("n_dpn",            "NB count",        "cells",     False),
]


def _scale(values: np.ndarray, is_area: bool) -> np.ndarray:
    return values * AREA_SCALE if is_area else values


def _param_label(row: pd.Series) -> str:
    if row["regulation"] == "volume":
        return f"sensitivity={row['GROWTH_RATE_VOLUME_SENSITIVITY']}"
    parts = [f"half_max={row['NB_CONTACT_HALF_MAX']}"]
    if str(row["NB_CONTACT_HILL_N"]) not in ("N/A", "3.0"):
        parts.append(f"hill_n={row['NB_CONTACT_HILL_N']}")
    return "  ".join(parts)


def main() -> None:
    sim = pd.read_csv(SIM_METRICS_CSV)
    cond_meta = pd.read_csv(CONDITIONS_CSV)
    exp = pd.read_csv(EXP_METRICS_CSV)
    exp_mud = exp.loc[exp["genotype"] == "mudmut"]

    # Pre-compute exp mud reference values once
    exp_refs: dict[str, tuple[float, float, float]] = {}
    for key, _, _, is_area in METRIC_SPECS:
        vals = _scale(exp_mud[key].astype(float).to_numpy(), is_area)
        exp_refs[key] = (float(np.median(vals)),
                         float(np.percentile(vals, 25)),
                         float(np.percentile(vals, 75)))

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    n_written = 0
    with PdfPages(OUT_PDF) as pdf:
        for _, cond_row in cond_meta.iterrows():
            folder = cond_row["folder"]
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
                    boxprops={"facecolor": "#5f5f5f", "edgecolor": "black", "linewidth": 1.0},
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

            vcv = "VCV1" if folder.startswith("vcv1") else "VCV0"
            param_str = _param_label(cond_row)
            title_str = (f"{folder}   [{vcv}  {cond_row['regulation']}  "
                         f"{cond_row['mechanism']}  {param_str}]")
            fig.suptitle(title_str, fontsize=10, y=1.01)

            legend_handles = [
                Patch(facecolor="#5f5f5f", edgecolor="black", label="simulation (n=50)"),
                Patch(facecolor=EXP_BAND_COLOR, alpha=EXP_BAND_ALPHA, label="exp mud IQR"),
            ]
            fig.legend(handles=legend_handles, loc="upper right",
                       fontsize=8, frameon=False, bbox_to_anchor=(1.0, 1.08))
            fig.tight_layout()
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            n_written += 1

    print(f"Wrote {n_written} pages to {OUT_PDF}")


if __name__ == "__main__":
    main()
```

**Verify:** open the PDF; confirm it has one page per condition, each page
has 5 subplots, the red IQR band is visible, and log scaling is applied.

---

## PIPELINE.md additions

Add a new section "Calibration-sweep pipeline" documenting:
- sweep root: `data/sim/calibrate_sweep/` — 48 conditions (vcv0/vcv1 × vol/NB_contact × ABM/PDE × parameter values)
- processed output: `data/sim/processed_calibrate/`
- key outputs: `sim_metrics_last.csv`, `alignment_summary.csv`, `calibrate_sweep_plots.pdf`
- dependency note: simulations must run before any preprocessing step

---

## Steps

1. Implement the Makefile additions (variables + 5 targets + `.PHONY` entries)
2. Write `scripts/analyze_calibration_alignment.py` (code above)
3. Write `scripts/plot_calibration_sweep.py` (code above)
4. Update `docs/PIPELINE.md`
5. Run simulations (user action — execute each XML in `data/sim/calibrate_sweep/`)
6. Run `make summarize-calibrate` to preprocess, extract metrics, and summarize
7. Run `make analyze-calibrate` → inspect `data/sim/processed_calibrate/alignment_summary.csv`
8. Run `make plot-calibrate` → open `docs/tex_draft/figures/calibrate_sweep_plots.pdf`
