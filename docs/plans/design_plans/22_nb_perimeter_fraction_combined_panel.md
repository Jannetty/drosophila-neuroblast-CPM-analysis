# Combined NB Perimeter-Fraction Panel with Experimental Reference Band

Date: 2026-07-20

## Goal

Produce a single NB perimeter-fraction (`exposed_frac`) boxplot panel that shows
all four experimentally varied component groups side by side, with the
experimental WT data drawn as a light-red reference band spanning all groups.

The four groups already exist as `FIG2_GROUPS`:

- Apical axis reorientation
- Division orientation range
- Offset shift
- Differentiation rule

The experimental data is the nonconvex-preprocessed exp WT (`make preprocess-exp-nonconvex`),
already computed in the notebook as `EXP_WT_SPATIAL["exposed_frac"]`.

## Location

`docs/tex_draft/figure12_paper_figures.ipynb` — the notebook that `make fig2`
runs. All required pieces already exist there:

- `make_grouped_metric_panel(metric_key="exposed_frac", ...)` plots the four groups.
- `EXP_WT_SPATIAL["exposed_frac"]` holds the experimental values.
- A commented-out experimental-band block already lives inside
  `make_grouped_metric_panel` (mean ± SD version).

## Design

### 1. Add an `exp_band` flag to `make_grouped_metric_panel`

Add a parameter `exp_band: bool = False`. When `True` and `metric_key` is in
`EXP_WT_SPATIAL`, draw on each subplot (behind the boxes):

- A shaded `axhspan` from the experimental **25th percentile** to **75th
  percentile** (IQR), filled with `EXP_FILL_COLOR` (`#f5b8b8`, light red) at low
  alpha, `zorder=0`.
- A dashed horizontal line at the experimental **median**, colored
  `EXP_MEDIAN_COLOR` (`#c0392b`, dark red).

Percentiles/median computed over the finite values of
`EXP_WT_SPATIAL["exposed_frac"]`.

This replaces the existing commented block. It is gated by the flag so the
existing split exposure panels (which call the function without the flag) are
unchanged.

Rationale for IQR + median: the boxplots themselves show medians and IQR boxes,
so an IQR band + median line is the directly comparable reference. (The original
commented code used mean ± SD; superseded per design discussion.)

### 2. Add one new save block

Next to the existing exposure-panel loop, add a single call:

```python
_exp_all_fig, _ = make_grouped_metric_panel(
    metric_key="exposed_frac",
    ylabel="NB perimeter fraction\nexposed to extracellular space",
    is_area=False,
    groups=FIG2_GROUPS,      # all four, unsplit
    exp_band=True,
)
```

Saving to:

- `figure2_wt_exposure_panel_all.png`
- `figure2_wt_exposure_panel_all.pdf`

The two existing `_orientation` / `_perturbation` exposure panels are left
exactly as-is.

## Out of Scope

- No change to the split panels.
- No change to `colors.py` or `_style.py` (light/dark red already defined).
- No compositor wiring — this is a standalone panel output for now.

## Regeneration

`make fig2` (nonconvex exp data via `figures-nonconvex` env, matching how the exp
metrics were built). Confirm the new panel renders with the four groups and the
light-red band before completing.
