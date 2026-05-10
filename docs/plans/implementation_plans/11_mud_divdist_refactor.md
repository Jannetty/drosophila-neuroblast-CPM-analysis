# Implementation Record 11 — Mudmut div-distribution refactor: Stdev26 → Stdev50

**Design plan:** `docs/plans/design_plans/11_mud_divdist_refactor.md`
**Started:** 2026-05-04
**Completed:** —

---

## How to use this record

This file is a log of what was **actually done**, not what was planned.  It is filled
out incrementally as each step is executed.  The design plan is the source of intent;
this record is the source of truth for what changed and when.

Rules:
- Fill in each step's entry **at the time it is executed**, not before.
- If the actual work deviated from the design plan, note the deviation explicitly
  under "Deviations / notes" and explain why.
- If a step was skipped or deferred, mark it `SKIPPED` or `DEFERRED` with a reason.
- Do not pre-fill entries speculatively.
- Date format: YYYY-MM-DD.

---

## Step 1a — ARCADE/sweep/ setup files

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

What was done:
- [x] Renamed `mudmut_divMean0Stdev26_rotMean0Stdev30` → `mudmut_divMean0Stdev50_rotMean0Stdev30`
- [x] Renamed `mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion` → `mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion`
- [x] Edited all 12 XMLs: `SIGMA=26` → `SIGMA=50` in `DIV_ROTATION_DISTRIBUTION`

Method: `mv` for directory renames; `sed -i ''` in-place substitution on all `.xml`
files found under both renamed directories.

Verified: `grep -r "SIGMA=50"` returned 12 hits; `grep -r "SIGMA=26"` returned 0 hits
across both mudmut sweep dirs.  `wt_divMean0Stdev26/` XMLs were confirmed untouched.

Deviations / notes: None. Design plan noted that sweep XML series names do not encode
`sg26`, so no series-name edits were needed — confirmed correct by inspection before
starting.

---

## Step 1b — ARCADE/decoupling_adhesion/ setup files

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

What was done:
- [x] Removed (or archived) all 36 existing condition directories
- [x] Created 12 new `Stdev50` condition directories, each with `vcv1_vol_abm/` and `vcv1_vol_pde/` subdirs
- [x] In each new XML: `SIGMA=26` → `SIGMA=50` in `DIV_ROTATION_DISTRIBUTION`
- [x] In each new XML: `sg26` → `sg50` in `<series name=...>`
- [x] Updated `CONDITION_DIRS` in `run_decoupling_adhesion.sh` to the 12 new names

Method: Python script created each of the 12 new condition directories by copying the
corresponding `Stdev26` source XML for each of the two sim_ids (`vcv1_vol_abm`,
`vcv1_vol_pde`), then applying both substitutions (`SIGMA=26`→`SIGMA=50` and
`sg26`→`sg50`) via string replacement.  The old 36 directories (Stdev26, Stdev45,
Stdev90) were then removed with `shutil.rmtree`.  The `CONDITION_DIRS` array in
`run_decoupling_adhesion.sh` was replaced with the 12 new names using Edit.

Verified:
- `decoupling_adhesion/` now contains exactly 12 dirs, all `Stdev50`
- `grep -r "SIGMA=26"` and `grep -r "sg26"` across new dirs: 0 hits each
- `grep -r "SIGMA=50"` and `grep -r "sg50"` across new dirs: 24 hits each
- `run_decoupling_adhesion.sh` contains 0 references to Stdev26/45/90

Deviations / notes: The design plan listed "Remove (or archive)" for the old dirs.
They were deleted outright rather than archived here — archiving the ARCADE setup
files is unnecessary since the XML content is fully recoverable from git history and
the data files (the actual simulation outputs) are what need archiving in Step 2.

---

## Step 2 — Archive old raw simulation data

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

What was done:
- [x] Moved `data/sim/sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/` to archive
- [x] Moved `data/sim/sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/` to archive
- [x] Moved all 36 `data/sim/decoupling_adhesion/mudmut_adh*_divMean0Stdev{26,45,90}*/` dirs to archive

Archive destinations used:
- Sweep dirs → `data/archive/sim/sweep_unused_conditions/` (directory pre-existed)
- Decoupling-adhesion dirs → `data/archive/sim/decoupling_adhesion_stdev_sweep/` (created new)

Method: `mv` for sweep dirs; Python `shutil.move` loop for the 36 adhesion dirs.

Verified:
- `data/sim/sweep/` now contains only `wt_divMean0Stdev26/`
- `data/sim/decoupling_adhesion/` is empty
- `data/archive/sim/decoupling_adhesion_stdev_sweep/` contains exactly 36 dirs

Deviations / notes: None.

---

## Step 3 — Re-run simulations

**Status:** `DONE`
**Date started:** 2026-05-04
**Date completed:** 2026-05-04
**Done by:** jannetty (script written by Claude)

Script written: `~/bagherilab/ARCADE/run_mudmut_stdev50_all.sh`
Invocation: `cd ~/bagherilab/ARCADE && ./run_mudmut_stdev50_all.sh`

What was done:
- [x] Re-ran sweep mudmut simulations with new Stdev50 XMLs; raw output landed in `data/sim/sweep/mudmut_divMean0Stdev50_rotMean0Stdev30/`
- [x] Re-ran sweep mudmut_noadhesion simulations; raw output landed in `data/sim/sweep/mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion/`
- [x] Re-ran all 12 decoupling_adhesion conditions; raw output landed in `data/sim/decoupling_adhesion/mudmut_adh*_divMean0Stdev50*/`

Verified at completion (2026-05-04):
- sweep/mudmut_divMean0Stdev50_rotMean0Stdev30/: all 10 sim_ids × 201 JSON files ✓
- sweep/mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion/: both sim_ids × 201 JSON files ✓
- decoupling_adhesion/: all 12 conditions present; all 24 (condition × sim_id) entries × 201 JSON files ✓
- No ARCADE processes still running

Deviations / notes: Script runs 36 XMLs total (10 sweep main + 2 noadhesion + 24
adhesion). WT conditions are absent from the condition lists; confirmed no WT processes
started.

---

## Step 4a — Preprocess sweep outputs

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

Command(s) run:
```
rm data/sim/processed_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30.npz
rm data/sim/processed_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion.npz
uv run python scripts/preprocess_sim.py --sweep-root data/sim/sweep --out-dir data/sim/processed_sweep
```

What was done:
- [x] Deleted stale `mudmut_divMean0Stdev26_rotMean0Stdev30*.npz` from `processed_sweep/`
- [x] Ran `preprocess_sim.py` on `data/sim/sweep/`
- [x] Confirmed new NPZ files present: `mudmut_divMean0Stdev50_rotMean0Stdev30.npz` (500 runs), `mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion.npz` (100 runs)
- [x] Confirmed `sim_index.csv` condition names reflect `Stdev50` for mudmut rows

Deviations / notes: `sim_index.csv` does not carry a `div_stdev` column (it has only
`condition`, `n_runs`, `npz_path`); the stdev is encoded in the condition name string
itself (`mudmut_divMean0Stdev50_rotMean0Stdev30`), which is correct.

---

## Step 4b — Preprocess decoupling_adhesion outputs

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

Command(s) run:
```
make adh-clean
make preprocess-adh
```

What was done:
- [x] Ran `make adh-clean` (removed all 36 stale Stdev26/45/90 NPZs and CSVs)
- [x] Ran `make preprocess-adh` (preprocess_sim.py → extract_metrics.py → extract_adhesion_metrics.py)
- [x] Confirmed 12 new NPZ files present in `processed_decoupling_adhesion/`
- [x] Confirmed metric CSVs regenerated with `div_stdev=50` in all rows

Verified:
- 12 NPZ files (one per condition)
- 4 metric CSVs: 1200 rows each
- `div_stdev` levels in CSVs: `[50]` only
- Adhesion levels: `[20, 40, 50]`
- Sim IDs: `['vcv1_vol_abm', 'vcv1_vol_pde']`
- Relrot mean levels: `[0.0, 45.0, 90.0]`

Deviations / notes: None.

---

## Step 5a — Update `adhesion_decoupling_analysis.ipynb`

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

What was done:
- [x] Cell `title` (intro markdown): updated description to reflect 2-factor sweep, sigma=50 fixed
- [x] Cell `s0-constants`: removed `SIGMA_ORDER = [26, 45, 90]`; updated `_cond_order` to sort by adhesion × relrot (not div_stdev)
- [x] Cell `dc41865c` (`_cond_name`): removed `sigma` parameter, hardcoded Stdev50 in condition name
- [x] Cells `s3-hdr`, `s3-chart`, `f7ce6a3d`, `2edd00c8`: removed (entire Section 3 sigma-sweep)
- [x] Cell `s2-chart` (baseline): removed `div_stdev == 26` filter
- [x] Cell `s4-chart` (relrot slice): removed `div_stdev == 26` filter
- [x] Cell `s5-heatmap`: redesigned as adhesion × relrot matrix (rows=ADH_ORDER, cols=RELROT_ORDER)
- [x] Cell `40fc851b` (heatmap example grid): redesigned as 3×4 adh × relrot grid (removed sigma loop)
- [x] Cells `5c067852`, `ac3ef133`: removed `_SIGMA` variable; updated `_cond_name` call from 3-arg to 2-arg
- [x] Cell `s6-render`: `_SIGMA = 26` → `_SIGMA = 50`
- [x] All section headers and suptitles updated to remove sigma=26 and "36 conditions" references
- [x] Re-ran all cells end-to-end; no errors

Method: Python script `/tmp/apply_step5a.py` manipulated the notebook JSON directly,
replacing cell sources and removing unwanted cells.

Verified:
- 26 cells remain (30 original − 4 sigma-sweep cells)
- No remaining `SIGMA_ORDER`, `div_stdev == 26`, `Stdev26`, `_cond_name(adh, _SIGMA`, `sigma=26`, or `sg26` in any cell

Deviations / notes: The design plan described cell changes by index (Cell 0, 6, 7, …).
Used actual cell IDs from the notebook instead, which are more stable than indices.
Also updated sections 1/2/3/4 headers and several additional `_SIGMA` references that
the design plan listed only for cells 5c and 14 (ac3ef133) — cleaned up all occurrences
throughout the notebook. Section 3 (sigma sweep) was removed and subsequent sections
renumbered accordingly in the markdown headers.

---

## Step 5b — Update `mudmut_systematic_analysis.ipynb`

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

What was done:
- [x] Audited all cells for `Stdev26` / `mudmut_divMean0Stdev26` references

Cells changed: **none**

Deviations / notes: `mudmut_systematic_analysis.ipynb` does not reference the
`mudmut_divMean0Stdev26_rotMean0Stdev30` condition at all. The `rotMean0Stdev30`
hits found in cell `s0-conditions` are for a different sweep
(`divMean0Stdev0_rotMean0Stdev30`, etc.) that is not being changed. No edits needed.

---

## Step 5c — Update figure generation files (`docs/tex_draft/`)

**Status:** `DONE`
**Date:** 2026-05-04
**Done by:** Claude

What was done:
- [x] Grepped `docs/tex_draft/` for `Stdev26` and `sg26` in mudmut contexts
- [x] Updated all mudmut condition strings in `_figure4_build_notebook.py`
- [x] Updated all mudmut condition strings in `_figure5_build_notebook.py`
- [x] Left all WT condition strings (`wt_divMean0Stdev26`) unchanged
- [x] Fixed pre-existing `SIM_MAP` bug in `_figure4_build_notebook.py`: `sim41`–`sim55` / `sim61` IDs never existed in CSVs; replaced with `vcv*` IDs to match actual data
- [x] Fixed pre-existing `SIM_MAP` bug in `_figure5_build_notebook.py`: `sim43`, `sim45` → `vcv1_vol_abm`, `vcv1_vol_pde`
- [x] Fixed pre-existing CSV path bug in `_figure5_build_notebook.py`: `HET_METRICS_CSV` and `EXP_METRICS_CSV` pointed to stale `processed_adhesion/`; updated to `processed_sweep/`
- [x] Regenerated stale sweep metric CSVs in `processed_sweep/` (`sim_timepoint_metrics.csv`, `sim_metrics_last.csv`, `het_contact_metrics.csv`, `nb_exposure_metrics.csv`, `nb_cohesion_metrics.csv`, `nb_connectivity_metrics.csv`)
- [x] Rebuilt both notebooks from updated `.py` scripts
- [x] Executed both notebooks end-to-end; no errors

Files changed and specific lines updated:

`_figure4_build_notebook.py`:
- Line 23: description comment `mudmut_divMean0Stdev26_rotMean0Stdev30` → `mudmut_divMean0Stdev50_rotMean0Stdev30`; also updated sim ID description from `sim41–55/sim61` style → `vcv1_*/vcv0_*` style
- Line 78: `MUD_CONDITION = "mudmut_divMean0Stdev26_rotMean0Stdev30"` → `…Stdev50…`
- Lines 84–95: `SIM_MAP` entries replaced with `vcv*` IDs (`vcv1_noreg`, `vcv1_nb_abm`, `vcv1_vol_abm`, `vcv1_nb_pde`, `vcv1_vol_pde`, `vcv0_noreg`, `vcv0_nb_abm`, `vcv0_vol_abm`, `vcv0_nb_pde`, `vcv0_vol_pde`)
- Line 97: `WT_SIM_ID = "sim61"` → `WT_SIM_ID = "vcv1_vol_abm"`
- Line 117: `WT_CONDITION = "wt_divMean0Stdev26"` — unchanged (WT)

`_figure5_build_notebook.py`:
- Line 24: description comment `mudmut_divMean0Stdev26_rotMean0Stdev30` → `mudmut_divMean0Stdev50_rotMean0Stdev30`; `sim43 = VOL-ABM, sim45 = VOL-PDE` → `vcv1_vol_abm = VOL-ABM, vcv1_vol_pde = VOL-PDE`
- Line 80: `MUD_BASE = "mudmut_divMean0Stdev26_rotMean0Stdev30"` → `…Stdev50…`
- Line 81: `MUD_NOADH = "mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion"` → `…Stdev50…`
- Lines 84–87: `SIM_MAP` entries `("sim43", ...)` → `("vcv1_vol_abm", ...)` and `("sim45", ...)` → `("vcv1_vol_pde", ...)`
- Lines 95–96: `HET_METRICS_CSV` and `EXP_METRICS_CSV` paths changed from `processed_adhesion/` → `processed_sweep/`

Commands run to regenerate sweep metric CSVs (before figures could execute):
```
uv run python scripts/extract_metrics.py --kind sim --sweep-root data/sim/sweep --out-dir data/sim/processed_sweep
uv run python scripts/summarize_metrics.py --sim-metrics data/sim/processed_sweep/sim_timepoint_metrics.csv --exp-metrics data/exp/processed/metrics.csv
uv run python scripts/extract_adhesion_metrics.py --proc-dir data/sim/processed_sweep
```

Deviations / notes:
- Pre-existing bug discovered: `SIM_MAP` in both figure build scripts used `sim41`–`sim55` / `sim61`-style IDs that were never present in any data CSV.  All CSVs use `vcv*` directory names (e.g., `vcv1_vol_abm`).  The scripts silently produced empty subsets, causing `IndexError: single positional indexer is out-of-bounds` in figure4 at `panel_c()`. Fixed in both scripts.
- Pre-existing bug discovered: `_figure5_build_notebook.py` read `het_contact_metrics.csv` and `nb_exposure_metrics.csv` from `data/sim/processed_adhesion/`, a now-stale directory.  Fresh data was already in `processed_sweep/` after Step 4a; updated paths accordingly.
- `sim_metrics_last.csv` in `processed_sweep/` was not regenerated by any Makefile target (the Makefile's `SIM_SWEEP_ROOT` points at the WT decoupling directory, not the main sweep).  Regenerated manually by running `extract_metrics.py` + `summarize_metrics.py` directly.
- `het_contact_metrics.csv` etc. in `processed_sweep/` did not previously exist; created by `extract_adhesion_metrics.py --proc-dir data/sim/processed_sweep`.
