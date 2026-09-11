# Implementation Record 17 — Non-convex lineage polygon

**Design plan:** `docs/plans/design_plans/17_non_convex_lineage_polygon.md`
**Started:** 2026-05-13
**Completed:** 2026-05-13

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

## Step 1 — Add `mesh_polygon` to `geometry.py`

**Status:** `DONE`
**Date:** 2026-05-13
**Done by:** Claude

Planned changes:
- Add `mesh_polygon(pts_2d, faces, buffer_px)` to `src/npa/exp_preprocessing/geometry.py`
- Takes projected 2D vertices and face indices; builds `unary_union` of valid triangles;
  applies buffer; falls back to convex hull if result is not a single Polygon
- Do NOT modify or remove `hull_polygon`

What was done:
- [x] Added `mesh_polygon` to `geometry.py`
- [x] `from shapely.ops import unary_union` added at module level

Deviations / notes:
None.

---

## Step 2 — Add tests for `mesh_polygon`

**Status:** `DONE`
**Date:** 2026-05-13
**Done by:** Claude

Planned changes in `tests/test_exp_preprocessing.py`:
- Add `test_mesh_polygon_basic`: L-shaped face set; area ≤ convex hull area
- Add `test_mesh_polygon_buffer`: square split into two triangles with buffer; valid Polygon
- Add `test_mesh_polygon_degenerate_faces_ignored`: mix of valid and collinear faces; no crash
- Add `test_mesh_polygon_bad_inputs`: all-zero pts → raises `ValueError("no valid projected triangles")`

Run: `uv run pytest tests/test_exp_preprocessing.py -v`
Expected: 4 new tests pass; all pre-existing tests still pass

What was done:
- [x] Added the four tests
- [x] All 18 tests pass (14 pre-existing + 4 new)

Deviations / notes:
Added `MultiPoint` and `ShapelyPolygon` imports to test file rather than using inline
`__import__` calls — cleaner and consistent with the existing `box` import pattern.

---

## Step 3 — Update `pipeline.py` to accept `use_convex_hull`

**Status:** `DONE`
**Date:** 2026-05-13
**Done by:** Claude

Planned changes in `src/npa/exp_preprocessing/pipeline.py`:
- Add `mesh_polygon` to the geometry imports
- Add `use_convex_hull: bool = True` keyword parameter to `process_exp_lineage`
- Replace fixed `hull_polygon(lin_pts_2d, ...)` call with branch on flag
- Add `use_convex_hull: bool = True` keyword parameter to `process_exp_lobe`
- Pass `use_convex_hull=use_convex_hull` to both `process_exp_lineage` calls inside
  `process_exp_lobe` (kept and rejected lineage loops)

Run: `uv run pytest tests/test_exp_preprocessing.py -v`
Expected: all tests still pass (default `use_convex_hull=True` preserves existing behavior)

What was done:
- [x] Added `mesh_polygon` to imports in `pipeline.py`
- [x] Added `use_convex_hull` to `process_exp_lineage`
- [x] Added `use_convex_hull` to `process_exp_lobe`
- [x] Both `process_exp_lineage` call sites in `process_exp_lobe` pass the flag
- [x] All 18 tests pass

Deviations / notes:
None.

---

## Step 4 — Add `--no-convex-hull` flag to `preprocess_exp.py`

**Status:** `DONE`
**Date:** 2026-05-13
**Done by:** Claude

Planned changes in `scripts/preprocess_exp.py`:
- In `parse_args`, add `--no-convex-hull` store_true argument
- In `main()`, pass `use_convex_hull=not args.no_convex_hull` to `process_exp_lobe`

What was done:
- [x] Added `--no-convex-hull` argument
- [x] `use_convex_hull=not args.no_convex_hull` passed to `process_exp_lobe`
- [x] `--help` shows the new flag with description

Deviations / notes:
None.

---

## Step 5 — Run preprocessor with `--no-convex-hull` and validate

**Status:** `DONE`
**Date:** 2026-05-13
**Done by:** Claude

Planned action:
```bash
uv run python scripts/preprocess_exp.py --no-convex-hull --out-dir data/exp/processed_non_convex
```

What was done:
- [x] Ran preprocessor with `--no-convex-hull` to completion (output to `data/exp/processed_non_convex`)
- [x] Lineage counts match: 59 mudmut + 60 wt = 119 total (identical to convex-hull run)
- [x] Spot-checked `wt/lobe1_0.npz`: convex hull has 125 polygon vertices; non-convex has 476
- [x] Verified WT geo arrays: non-convex has fewer filled pixels for all 60 lineages
  (avg 5027 vs 5569 = ~10% tighter); no lineage gained pixels relative to convex hull

Deviations / notes:
None.

---

## Step 6 — Update `docs/PIPELINE.md`

**Status:** `DONE`
**Date:** 2026-05-13
**Done by:** Claude

Planned changes:
- Update the polygon construction description in the Experimental Preprocessing section
  to document both modes (convex hull default and `--no-convex-hull` mesh-union mode)
- Update the `lin_poly_2d` and `lin_poly_2d_px` rows in the mesh NPZ table

What was done:
- [x] Updated step 3 in geometry section to document both modes
- [x] Updated `lin_poly_2d` table row to note variable vertex count
- [x] Updated `lin_poly_2d_px` row to remove "Hull" label

Deviations / notes:
None.
