# Implementation Record 15 — Add differentiation-rule conditions to figure 2

**Design plan:** `docs/plans/15_add_diff_rulesets.md`
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

## Step 1 — Re-run decoupling preprocessing

**Status:** —
**Date:** —
**Done by:** —

Planned: `make summarize-decouple`

Verify: `cut -d',' -f1 data/sim/processed_decoupling/sim_metrics_last.csv | grep "apicalgmc\|randomnb"`
Expected: both condition names appear.

What was done:

Deviations / notes:

---

## Step 2 — Add constants to notebook cell

**Status:** —
**Date:** —
**Done by:** —

Planned: In cell `7bc2792c` of `figure12_paper_figures.ipynb`, add:
- `FIG2_DIFF_CONDITIONS` list
- 4th entry in `FIG2_GROUPS`
- Two new entries in `FIG2_SHORT_LABELS`
- Two new entries in `FIG2_BOX_FILLS`
- New entry in `FIG2_LINEAGE_LABEL_OVERRIDES`
- 4th row in `FIG2_LINEAGE_ROWS`

What was done:

Deviations / notes:

---

## Step 3 — Update `make_figure2_lineages_panel`

**Status:** —
**Date:** —
**Done by:** —

Planned:
- Increase `figsize` height: `(13.8, 14.0)` → `(13.8, 18.7)`
- Extend label-override block to handle `wt_divMean0Stdev26_yoffset50` in the
  "Differentiation rule" row
- Add pre-compute block for the new row (downsample-2x, crop, uniform pad)
- Add per-column render block for the new row

What was done:

Deviations / notes:

---

## Step 4 — Update `make_grouped_metric_panel`

**Status:** —
**Date:** —
**Done by:** —

Planned:
- Fix figsize formula: `len(FIG2_GROUPS)` → `3` (hardcoded baseline)
- Add `"Differentiation rule": "Differentiation\nrule"` to `title_map`

What was done:

Deviations / notes:

---

## Step 5 — Execute notebook and inspect PNGs

**Status:** —
**Date:** —
**Done by:** —

Planned:
```
uv run jupyter nbconvert --to notebook --execute --inplace docs/tex_draft/figure12_paper_figures.ipynb
```
Check:
- `figure2_wt_geometry_examples_panel.png` shows 4 rows
- `figure2_wt_mixing_panel.png` shows 4 groups, wider
- `figure2_wt_exposure_panel.png` shows 4 groups, wider

What was done:

Deviations / notes:

---

## Step 6 — Run `make fig2` to update SVG

**Status:** —
**Date:** —
**Done by:** —

Planned: `make fig2`

What was done:

Deviations / notes:

---

## Step 7 — Inkscape canvas extension (manual)

**Status:** —
**Date:** —
**Done by:** —

Planned: Open `docs/tex_draft/figures/fig2/fig2.svg` in Inkscape. Extend the
canvas downward to accommodate the new 4th geometry-examples row and realign the
`image1-4` element (geometry examples panel).

What was done:

Deviations / notes:

---

## Step 8 — Update PIPELINE.md

**Status:** —
**Date:** —
**Done by:** —

Planned: Add the two new conditions to the decoupling-sweep conditions table.

What was done:

Deviations / notes:

---

## Step 9 — Commit

**Status:** —
**Date:** —
**Done by:** —

Planned:
```bash
git add docs/tex_draft/figure12_paper_figures.ipynb \
        docs/tex_draft/figures/figure2_wt_geometry_examples_panel.png \
        docs/tex_draft/figures/figure2_wt_geometry_examples_panel.pdf \
        docs/tex_draft/figures/figure2_wt_mixing_panel.png \
        docs/tex_draft/figures/figure2_wt_mixing_panel.pdf \
        docs/tex_draft/figures/figure2_wt_exposure_panel.png \
        docs/tex_draft/figures/figure2_wt_exposure_panel.pdf \
        docs/tex_draft/figures/fig2/fig2.svg \
        docs/plans/15_add_diff_rulesets.md \
        docs/plans/implementation_plans/15_add_diff_rulesets.md \
        docs/PIPELINE.md
git commit -m "feat: add differentiation-rule row and group to figure 2"
```

What was done:

Deviations / notes:
