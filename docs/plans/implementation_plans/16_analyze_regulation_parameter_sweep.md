# Implementation Record 16 — Analyze regulation parameter calibration sweep

**Design plan:** `docs/plans/design_plans/16_analyze_regulation_parameter_sweep.md`
**Started:** 2026-05-12
**Completed:** 2026-05-12

---

## How to use this record

Fill in each step's entry at the time it is executed. The design plan is the
source of intent; this record is the source of truth for what changed and when.

Rules:
- Fill in each step's entry **at the time it is executed**, not before.
- Note deviations from the design plan explicitly.
- Mark skipped or deferred steps `SKIPPED` or `DEFERRED` with a reason.
- Do not pre-fill entries speculatively.
- Date format: YYYY-MM-DD.

---

## Step 1 — Makefile additions

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

Added `SIM_CALIB_DIR` and `SIM_CALIB_PROC_DIR` variables. Added
`preprocess-calibrate`, `analyze-calibrate`, `plot-calibrate`, and
`calibrate-clean` targets. Added all four to `.PHONY`.

Deviations / notes: `plot-calibrate` and `analyze-calibrate` both depend only
on `preprocess-calibrate` (not on each other), matching the design plan.

---

## Step 2 — Write `scripts/preprocess_calibrate.py`

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

Wrote dedicated preprocessing script for the flat calibrate_sweep file
structure. Uses `CELLS_RE = re.compile(r".*_([0-9]{4})_([0-9]{6})\.CELLS\.json$")`
to parse run_id and time_id from filenames. Selects last timepoint per run.
Computes 5 metrics inline (NB = pop 1, progeny = pop 2+3). Outputs
`sim_metrics_last.csv` (2400 rows) and `sim_run_index.csv`.

Deviations / notes: Design plan assumed a sim_id subfolder layer (matching
the existing sweep pipeline). Actual output is flat — all CELLS/LOCATIONS
files directly inside each condition folder. The generic `preprocess_sim.py`
+ `extract_metrics.py` chain cannot be used. This script replaces both.
Metric logic implemented inline rather than imported from `npa.metrics`
(private functions there are not intended to be imported from scripts).

---

## Step 3 — Write `scripts/analyze_calibration_alignment.py`

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

For each condition (from `conditions.csv`), computes per-metric alignment
against experimental mudmut IQR. Outputs `alignment_summary.csv` with 48
rows (one per condition) plus `n_metrics_aligned` (count of metrics where sim
median falls within exp IQR, range 0–5).

Deviations / notes: None.

---

## Step 4 — Write `scripts/plot_calibration_sweep.py`

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

Multi-page PDF at `docs/tex_draft/figures/calibrate_sweep_plots.pdf`. One
page per condition in `conditions.csv` row order. Each page: 1×5 subplot
grid, log y-axis, dark gray boxplot (no fliers), red IQR axhspan + dashed
median line for exp mudmut reference. Page title includes folder, VCV,
regulation, mechanism, and parameter values.

Deviations / notes: None.

---

## Step 5 — Run `make preprocess-calibrate`

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

`wc -l data/sim/processed_calibrate/sim_metrics_last.csv` → 2401 lines
(1 header + 2400 data rows = 48 conditions × 50 runs each, all complete).

Deviations / notes: Expected 49 lines in design plan (which assumed fewer
runs or a different count). Actual output is 2401 lines — all 48 conditions
had exactly 50 successful runs.

---

## Step 6 — Run `make analyze-calibrate`

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

`wc -l data/sim/processed_calibrate/alignment_summary.csv` → 49 lines
(1 header + 48 condition rows). `n_metrics_aligned` column present and ranges
0–5 as expected.

Deviations / notes: Initial run failed with `FileNotFoundError` because
`data/sim/calibrate_sweep/conditions.csv` had not yet been placed in the
directory. User added the file and the step succeeded on the next run.

---

## Step 7 — Run `make plot-calibrate`

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

`ls -lh docs/tex_draft/figures/calibrate_sweep_plots.pdf` — non-empty PDF
produced. Script reported "Wrote 48 pages". Each page has 5 subplots, log
y-axis, gray boxplot, and red IQR band.

Deviations / notes: None.

---

## Step 8 — Update PIPELINE.md

**Status:** COMPLETED
**Date:** 2026-05-12
**Done by:** Claude

Added "Regulation parameter calibration sweep" section to `docs/PIPELINE.md`
describing the three-step pipeline (preprocess-calibrate, analyze-calibrate,
plot-calibrate), all inputs and outputs with column descriptions, and the
area-unit scaling note (raw voxels × 0.09 = µm²).

Deviations / notes: None.
