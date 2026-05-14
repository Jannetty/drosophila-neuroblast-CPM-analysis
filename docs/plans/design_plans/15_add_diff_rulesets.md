# Plan 15 — Add differentiation-rule conditions to figure 2

**Date:** 2026-05-12
**Goal:** Add the two new offset-50% differentiation-rule conditions
(`wt_divMean0Stdev26_yoffset50_randomnb` and
`wt_divMean0Stdev26_yoffset50_apicalgmc`) to figure 2: a new fourth row in the
geometry-examples panel (labeled "Differentiation rule") and a new fourth group
in both the mixing and NB-exposure box-and-whisker panels.

---

## Context

The decoupling sweep already has three sweep axes visualised in figure 2:

| Row / group | Variable swept | Conditions |
|---|---|---|
| Apical axis reorientation | `div_mean` (relrot) | 4 conditions |
| Spindle orientation range | `div_stdev` | 6 conditions |
| Offset shift | `y_offset` | 4 conditions |

The two new conditions fix `y_offset = 50%` and vary the **differentiation
rule** (how the neuroblast decides which daughter becomes the GMC):

- `wt_divMean0Stdev26_yoffset50` — basal GMC (default, WT rule)
- `wt_divMean0Stdev26_yoffset50_randomnb` — random NB identity
- `wt_divMean0Stdev26_yoffset50_apicalgmc` — apical GMC

This adds a fourth axis: **Differentiation rule** (3 conditions).

---

## Prerequisites

`make all` re-runs all `.PHONY` steps. The two new condition directories were
added after the preprocessing step ran, so the NPZ files for the new conditions
are currently empty (0 runs). Before any figure work, the decoupling pipeline
must be re-run:

```bash
make summarize-decouple
```

This regenerates all NPZ files, `sim_run_index.csv`, `sim_metrics_last.csv`,
and the spatial metrics used by the notebook.

---

## Files changed

| File | Change |
|---|---|
| `docs/tex_draft/figure12_paper_figures.ipynb` | All figure-2 logic lives in one cell; additions to constants and to two `make_*` functions |
| `docs/PIPELINE.md` | Add the two new conditions to the decoupling-sweep table |

No new source files. No changes outside these two.

---

## Notebook changes — detailed

All changes are inside the single cell that defines the figure-2 constants and
functions (cell id `7bc2792c`).

### A. New condition list

Add after `FIG2_OFFSET_CONDITIONS`:

```python
FIG2_DIFF_CONDITIONS = [
    "wt_divMean0Stdev26_yoffset50",
    "wt_divMean0Stdev26_yoffset50_randomnb",
    "wt_divMean0Stdev26_yoffset50_apicalgmc",
]
```

### B. Add 4th group to `FIG2_GROUPS`

Append to the list:

```python
FIG2_GROUPS = [
    ("Apical axis reorientation", FIG2_RELROT_CONDITIONS),
    ("Spindle orientation range", FIG2_STDEV_CONDITIONS),
    ("Offset shift", FIG2_OFFSET_CONDITIONS),
    ("Differentiation rule", FIG2_DIFF_CONDITIONS),   # NEW
]
```

Because `FIG2_ALL_CONDITIONS` is derived from `FIG2_GROUPS`, and
`decoupling_run_index_vcv1` / `decoupling_vcv1` both filter on
`FIG2_ALL_CONDITIONS`, no further index changes are needed.

### C. Short labels

Add to `FIG2_SHORT_LABELS`:

```python
"wt_divMean0Stdev26_yoffset50_randomnb": "Random NB",
"wt_divMean0Stdev26_yoffset50_apicalgmc": "Apical GMC",
```

### D. Box fills

Add to `FIG2_BOX_FILLS`:

```python
"wt_divMean0Stdev26_yoffset50_randomnb": "#7d7d7d",
"wt_divMean0Stdev26_yoffset50_apicalgmc": "#3c3c3c",
```

### E. Lineage label overrides

Add to `FIG2_LINEAGE_LABEL_OVERRIDES`:

```python
"wt_divMean0Stdev26_yoffset50__diff_row": "Basal GMC",
```

### F. 4th row in `FIG2_LINEAGE_ROWS`

Append:

```python
FIG2_LINEAGE_ROWS = [
    ("Apical axis reorientation", "spindle orientation range stdev = 26\noffset = 86%", FIG2_RELROT_CONDITIONS),
    ("Spindle orientation range", "apical axis reorientation mean = 0\noffset = 86%", ["wt_divMean0Stdev26", "wt_divMean0Stdev26_yoffset35", "wt_divMean0Stdev26_yoffset60", "wt_divMean0Stdev26_yoffset90"]),
    ("Offset shift", "apical axis reorientation mean = 0\nspindle orientation range stdev = 26", FIG2_OFFSET_CONDITIONS),
    ("Differentiation rule", "apical axis reorientation mean = 0\nspindle orientation range stdev = 26\noffset = 50%", FIG2_DIFF_CONDITIONS),  # NEW
]
```

### G. `make_figure2_lineages_panel` — figsize and new row rendering

1. **Increase figure height** for 4 rows:
   Change `figsize=(13.8, 14.0)` → `figsize=(13.8, 18.7)`.

2. **Label logic** — extend the condition-override block to handle the
   reference condition in the diff row:

   Change the block that starts `if condition == "wt_divMean0Stdev26":` to:

   ```python
   if condition == "wt_divMean0Stdev26":
       if row_title == "Offset shift":
           display_label = FIG2_LINEAGE_LABEL_OVERRIDES["wt_divMean0Stdev26__offset_row"]
       elif row_title == "Apical axis reorientation":
           display_label = FIG2_LINEAGE_LABEL_OVERRIDES["wt_divMean0Stdev26__relrot_row"]
       elif row_title == "Spindle orientation range":
           display_label = FIG2_LINEAGE_LABEL_OVERRIDES["wt_divMean0Stdev26__stdev_row"]
   elif condition == "wt_divMean0Stdev26_yoffset50" and row_title == "Differentiation rule":
       display_label = FIG2_LINEAGE_LABEL_OVERRIDES.get("wt_divMean0Stdev26_yoffset50__diff_row", display_label)
   else:
       display_label = FIG2_LINEAGE_LABEL_OVERRIDES.get(condition, display_label)
       if row_title == "Apical axis reorientation":
           display_label = f"mean = {display_label}"
       elif row_title == "Spindle orientation range":
           display_label = f"stdev = {display_label}"
   ```

3. **Pre-compute and render the new row** — add a new branch parallel to
   `if row_title == "Offset shift":` (in both the pre-compute block and the
   per-column render block).

   **Pre-compute block** (before the column loop):

   ```python
   elif row_title == "Differentiation rule":
       reps = pick_condition_representative_rows_joint(
           decoupling_vcv1, conditions,
           metrics=["norm_het_frac", "exposed_frac"],
           target_mode="mean",
       )
       n_cols = len(conditions)
       _diff_crops_geo: list[np.ndarray] = []
       _diff_crops_lab: list[np.ndarray] = []
       _diff_ppum: list[float] = []
       for _, _drow in reps.iterrows():
           _cond = _drow["condition"]
           _geo_r, _lm_r, _ = load_decoupling_snapshot(_cond, int(_drow["run_id"]))
           _ds = FIG2_OFFSET_PERTURBED_DOWNSAMPLE_STEP
           _gd = _geo_r[::_ds, ::_ds, :]
           _ld = _lm_r[::_ds, ::_ds]
           _gc = crop_to_content(_gd, pad=FIG2_OFFSET_CROP_PAD)
           _lc = crop_to_content(_ld, pad=FIG2_OFFSET_CROP_PAD)
           _ppum = (1.0 / DS_UM_PER_VOX) / _ds
           _diff_crops_geo.append(_gc)
           _diff_crops_lab.append(_lc)
           _diff_ppum.append(_ppum)
       _max_h = max(c.shape[0] for c in _diff_crops_geo)
       _max_w = max(c.shape[1] for c in _diff_crops_geo)
   ```

   **Per-column render block** (inside the column loop):

   ```python
   elif row_title == "Differentiation rule":
       geo_crop = _diff_crops_geo[col_idx]
       label_crop = _diff_crops_lab[col_idx]
       pixels_per_um = _diff_ppum[col_idx]
       h, w = geo_crop.shape[:2]
       pt = (_max_h - h) // 2; pb = _max_h - h - pt
       pl = (_max_w - w) // 2; pr = _max_w - w - pl
       geo_crop = np.pad(geo_crop, ((pt, pb), (pl, pr), (0, 0)), constant_values=0)
       label_crop = np.pad(label_crop, ((pt, pb), (pl, pr)), constant_values=0)
       render_raw(geo_crop, ax=ax, label_map=label_crop, title="")
       add_vertical_scale_bar(ax, pixels_per_um=pixels_per_um)
   ```

### H. `make_grouped_metric_panel` — figsize and title map

1. **Fix the figsize baseline** (was `len(FIG2_GROUPS)` = 3, now FIG2_GROUPS has 4
   entries, which would break the scaling). Change:

   ```python
   figsize=(11.0 + 2.5 * (len(groups) - len(FIG2_GROUPS)), 3.9),
   ```
   to:
   ```python
   figsize=(11.0 + 2.5 * max(0, len(groups) - 3), 3.9),
   ```

   Result: 3 groups → 11.0 in, 4 groups → 13.5 in.

2. **Add "Differentiation rule" to `title_map`**:

   ```python
   title_map = {
       "Apical axis reorientation": "Apical axis\nreorientation",
       "Spindle orientation range": "Spindle orientation\nrange",
       "Offset shift": "Offset shift",
       "Differentiation rule": "Differentiation\nrule",   # NEW
   }
   ```

---

## PIPELINE.md change

In the decoupling-sweep conditions table, add two new rows for the new
conditions noting `y_offset=50%`, differentiation rule = random NB / apical GMC.

---

## Steps

1. Re-run preprocessing: `make summarize-decouple`
2. Verify new conditions in CSVs: `cut -d',' -f1 data/sim/processed_decoupling/sim_metrics_last.csv | grep "apicalgmc\|randomnb"`
3. Apply notebook changes A–H above (all in cell `7bc2792c`)
4. Run the notebook: `uv run jupyter nbconvert --to notebook --execute --inplace docs/tex_draft/figure12_paper_figures.ipynb`
5. Inspect output PNGs in `docs/tex_draft/figures/` for the 4-row examples panel and the 4-group box plots
6. Run `make fig2` to update `fig2.svg` via the compositor
7. Open `docs/tex_draft/figures/fig2/fig2.svg` in Inkscape and extend the canvas downward to accommodate the new 4th examples row, then realign the geometry-examples image element
8. Update `docs/PIPELINE.md`
9. Commit
