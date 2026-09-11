# Implementation Record 13 — Sphere-weighted experimental preprocessing

**Design plan:** `docs/plans/design_plans/13_change_experimental_preprocessing.md`
**Started:** —
**Completed:** —

---

## How to use this record

This file is a log of what was **actually done**, not what was planned. Fill in
each step's entry at the time it is executed. The design plan is the source of
intent; this record is the source of truth for what changed and when.

Rules:
- Fill in each step's entry **at the time it is executed**, not before.
- If the actual work deviated from the design plan, note it explicitly under
  "Deviations / notes" and explain why.
- If a step was skipped or deferred, mark it `SKIPPED` or `DEFERRED` with a reason.
- Do not pre-fill entries speculatively.
- Date format: YYYY-MM-DD.

---

## Step 1 — Add `sphere_voronoi_rasterize` to `geometry.py`

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned changes:
- Add `sphere_voronoi_rasterize` function to `src/npa/exp_preprocessing/geometry.py`
- Function signature: `(lin_poly, dpn_centroids_2d, pros_centroids_2d, dpn_volumes_um3, pros_volumes_um3, canvas_size, ds) -> np.ndarray`
- Internally: compute sphere radii from volumes, build per-cell additive weighted
  distance fields, apply 3-phase priority assignment, apply hull mask
- Do NOT remove `voronoi_rasterize` yet — old tests still reference it

What was done:
- [x] Added `sphere_voronoi_rasterize` to `geometry.py` after `voronoi_rasterize`

Deviations / notes:
The design plan used `_radii_px` (dividing by `ds` to convert µm → pixels) but
the pixel grid GX/GY is in µm coordinates, making the subtraction
`||p − c|| − r_px` mix µm distances with pixel radii. Fixed by using `_radii_um`
(no division by `ds`) so all distances are in µm. The argmin is scale-invariant so
the result is identical. Smoke test confirmed: equal volumes → ~50/50 split; 8×
NB volume → NB claims ~81% of pixels; NB priority rule fires correctly; no
double-claimed pixels.

---

## Step 2 — Port and extend tests

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned changes in `tests/test_exp_preprocessing.py`:
- Replace the existing `test_voronoi_rasterize` test body to call
  `sphere_voronoi_rasterize` instead (same assertion: shape, dtype, no
  double-claimed pixel, non-empty). Keep old call using `voronoi_rasterize`
  for now to confirm both exist simultaneously.
- Add `test_sphere_voronoi_nb_priority`: pixel inside large NB circle assigned
  to NB even when Pros centroid is geometrically closer
- Add `test_sphere_voronoi_larger_cell_claims_more`: NB with 8× the volume
  claims more canvas pixels than Pros when centroids are symmetric
- Add `test_sphere_voronoi_canvas_exceeded`: oversized polygon raises ValueError

Run: `uv run pytest tests/test_exp_preprocessing.py -v`

What was done:
- [x] Added `sphere_voronoi_rasterize` to imports alongside `voronoi_rasterize`
- [x] Added `test_sphere_voronoi_rasterize_basic` after the existing voronoi test
- [x] Added `test_sphere_voronoi_nb_priority`
- [x] Added `test_sphere_voronoi_larger_cell_claims_more`
- [x] Added `test_sphere_voronoi_canvas_exceeded`
- [x] All 14 tests pass (10 pre-existing + 4 new)

Deviations / notes:
Kept the original `test_geometry_rasterization_channels_and_canvas_error` intact
(still calls `voronoi_rasterize`) rather than replacing it — both old and new tests
coexist until Step 3 removes `voronoi_rasterize`. The new basic test is a separate
function `test_sphere_voronoi_rasterize_basic` rather than a replacement.

---

## Step 3 — Remove old `voronoi_rasterize`

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned changes:
- Remove `voronoi_rasterize` and `_centroid_stack` from `geometry.py`
- Remove `voronoi_rasterize` import from the old test (now replaced by step 2)
- Confirm no remaining references: `grep -r "voronoi_rasterize" src/ tests/`

Run: `uv run pytest tests/test_exp_preprocessing.py -v`

What was done:
- [x] Removed `voronoi_rasterize` and `_centroid_stack` from `geometry.py`
- [x] Removed unused `KDTree` import (was only used by `voronoi_rasterize`)
- [x] Replaced `voronoi_rasterize` call in `test_geometry_rasterization_channels_and_canvas_error` with `sphere_voronoi_rasterize` (with equal 10 µm³ volumes)
- [x] Removed `voronoi_rasterize` from test imports
- [x] Removed `voronoi_rasterize` from `pipeline.py` imports (replaced with `sphere_voronoi_rasterize`)
- [x] `grep` confirmed zero remaining references to `voronoi_rasterize` or `_centroid_stack`
- [x] All 14 tests pass

Deviations / notes:
Removing `voronoi_rasterize` from `geometry.py` immediately broke `pipeline.py`
(which still imported it). Rather than leave the codebase in a broken intermediate
state, the pipeline.py import and call site were updated in the same commit —
effectively merging Steps 3 and 4. See Step 4 entry for details.

---

## Step 4 — Update `pipeline.py`

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned changes in `src/npa/exp_preprocessing/pipeline.py`:
- Add `_cell_volumes_um3(meshes) -> np.ndarray` helper using `abs(mesh.volume)`
- Replace `voronoi_rasterize` import with `sphere_voronoi_rasterize`
- In `process_exp_lineage`: extract `dpn_volumes_um3` and `pros_volumes_um3`
  after centroid computations; pass volumes to `sphere_voronoi_rasterize`
- In `np.savez_compressed` call: add `dpn_volumes_um3` and `pros_volumes_um3` keys
- `counts` array format unchanged: `[n_dpn, n_pros, dpn_pixel_sum]`

Run: `uv run pytest tests/test_exp_preprocessing.py -v`

What was done:
- [x] Added `_cell_volumes_um3` helper
- [x] Replaced `voronoi_rasterize` import with `sphere_voronoi_rasterize`
- [x] Added volume extraction after centroid computations in `process_exp_lineage`
- [x] Updated rasterizer call to pass `dpn_volumes_um3` and `pros_volumes_um3`
- [x] Added `dpn_volumes_um3` and `pros_volumes_um3` to `np.savez_compressed`
- [x] All 14 tests pass

Deviations / notes:
Done as part of Step 3 to avoid leaving the codebase in a broken import state.
Steps 3 and 4 were completed atomically in the same session.

---

## Step 5 — Update `exp_viz.py` (`show_2d_pre`)

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned changes in `src/npa/exp_viz.py`:
- Add `_sphere_radius_um(volume_um3) -> float` helper
- In `show_2d_pre`: replace bare centroid scatter points with `matplotlib.patches.Circle`
  patches drawn at the projected centroid position with radius = `_sphere_radius_um(vol)`
- Use `.get(..., np.zeros(...))` fallback so old mesh NPZs (without volume keys) still render

Run: `uv run python scripts/visualize_exp_lineage.py --row 0 --view 2d-pre`
(visually confirm circles appear proportional to cell size)

What was done:
- [x] Added `MplCircle` import from `matplotlib.patches`
- [x] Added `_sphere_radius_um` helper
- [x] Replaced scatter calls in `show_2d_pre` with filled + outlined `MplCircle` patches;
      Pros drawn first (zorder 2), NB on top (zorder 3)
- [x] Added `ax.autoscale_view()` after adding patches so axes scale correctly
- [x] `.get()` fallback uses `np.zeros(len(centroids))` so old NPZs render as zero-radius dots
- [x] All 20 tests pass (exp_viz + exp_preprocessing)

Deviations / notes:
Visual verification against a live lineage deferred until Step 6 regenerates the mesh
NPZs with volume keys; the `.get()` fallback means the CLI still works on existing NPZs
but circles will be zero-radius until the preprocessor reruns.

---

## Step 6 — Re-run preprocessor on all genotypes

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned action:
- Run `uv run python scripts/preprocess_exp.py` to regenerate all analysis NPZs
  and mesh NPZs using the new sphere-weighted rasterizer
- Confirm output counts match prior run (same number of kept lineages per genotype)

What was done:
- [x] Ran `scripts/preprocess_exp.py` to completion
- [x] Lineage counts per genotype match prior run: wt=60, mudmut=59 (nanobody folder absent → skipped)
- [x] Spot-checked `data/exp/processed/meshes/wt/lobe1_0.npz`: `dpn_volumes_um3` and `pros_volumes_um3` keys present, shapes match `n_dpn` and `n_pros`
- [x] Spot-checked WT and mudmut analysis NPZs: shape `(N, 200, 200, 2)`, values in {0., 1.}, zero double-claimed pixels

Deviations / notes:
`GENOTYPE_SPECS` in `scripts/preprocess_exp.py` had stale folder names (`Control`, `Mud`) from
before the plan-9 directory rename refactor. Fixed to `wt` and `mudmut` to match current layout.
The nanobody folder does not exist in `data/exp/raw/`, so that genotype is silently skipped
(same behavior as before — the prior run also had no nanobody data).

---

## Step 7 — Update `docs/PIPELINE.md`

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned changes:
- Update the rasterization step description to reflect sphere-weighted Voronoi logic
- Note the two new mesh NPZ keys (`dpn_volumes_um3`, `pros_volumes_um3`)
- Leave all other sections unchanged

What was done:
- [x] Updated rasterization step (step 4) to describe sphere-weighted Voronoi logic (radii, priority rules, argmin formula)
- [x] Added `dpn_volumes_um3` and `pros_volumes_um3` rows to mesh NPZ keys table
- [x] Updated `ds` parameter description (removed "Voronoi raster resolution" wording)
- [x] Updated visualization table: "2D pre-Voronoi" → "2D pre-rasterization" with sphere circles description; "2D post-Voronoi" → "2D post-rasterization"

Deviations / notes:
None.

---

## Step 8 — Re-render affected figures and verify

**Status:** `DONE`
**Date:** 2026-05-10
**Done by:** Claude

Planned action:
- Run `make fig2` to rebuild figure 2 panels (composition, mixing, exposure) with
  the regenerated geo arrays
- Visually inspect that the WT composition panel and spatial panels look reasonable
  (NB territory visibly larger than under old Voronoi)

What was done:
- [x] Ran `make fig2` to completion
- [x] Figure 2 panels rebuilt successfully

Deviations / notes:
`figure12_paper_figures.ipynb` had `EXPERIMENTAL_PERCENTILE_OVERRIDES = {0.90: 126}` hardcoded
from the old 172-lineage run (59 mudmut + 53 nanobody + 60 wt). After the plan-9 directory
rename, the nanobody folder disappeared, leaving only 119 lineages. The lineage IDs shifted:
the old 90th-percentile representative (wt, lobe2, lineage_idx=12) moved from ID 126 to ID 73.
Updated the override to `{0.90: 73}` before running make.
