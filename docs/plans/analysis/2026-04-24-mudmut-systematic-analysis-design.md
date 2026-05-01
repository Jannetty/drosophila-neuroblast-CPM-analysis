# Mudmut Systematic Analysis — Design Spec

**Date:** 2026-04-24
**Notebook:** `notebooks/mudmut_systematic_analysis.ipynb`

---

## Scientific motivation

Experimental *mud* mutant lineages are smaller and less populous than WT across
most metrics. Without growth regulation in simulation, this phenotype does not
emerge — simulated mudmut tracks or exceeds simulated WT. The goal of this
analysis is to systematically identify which combinations of:

- critical-volume determination rule (VCV=0 vs VCV=1)
- growth regulatory dynamic (NONE, NB-ABM, VOL-ABM, NB-PDE, VOL-PDE)
- division-plane rotation distribution (DIV_ROTATION_DISTRIBUTION)
- apical-axis rotation distribution (APICAL_AXIS_ROTATION_DISTRIBUTION)

bring simulated mudmut lineages toward the experimental mudmut phenotype.

The analysis proceeds through two comparison thresholds in sequence:

1. **WT threshold (coarse):** can a simulated mudmut condition fall below the
   experimental WT mean? This is the easier target.
2. **Mudmut target (fine):** does the simulated mudmut distribution align with
   the experimental mudmut mean ± 1 SD? This is the real goal.

---

## Reference data

Loaded from `data/exp/processed/exp_summary.csv`:

| Reference | Symbol | Role |
|---|---|---|
| Experimental WT mean | `wt_mean[m]` | Y-axis anchor (fold change = 0 in log scale) |
| Experimental WT SD | `wt_std[m]` | WT calibration band in Section 1 |
| Experimental mudmut mean | `mm_mean[m]` | Target reference line |
| Experimental mudmut SD | `mm_std[m]` | Target band (±1 SD) |

All reference values are in voxel units (area: vox, count: cells). Metrics with
`_vox` suffix require `area_um2 = area_vox * ds²` if real units are needed, but
all fold-change comparisons within this notebook are done in voxel units
consistently, so no conversion is needed.

### Direction of effect by metric

Experimental mudmut is below experimental WT for four of the five metrics.
`n_dpn` is the exception.

| Metric | Mudmut vs WT (exp) | Target direction for simulated mudmut |
|---|---|---|
| `lin_area_vox` | mudmut < WT | go below WT line (log FC < 0) |
| `n_pros` | mudmut < WT | go below WT line (log FC < 0) |
| `n_dpn` | mudmut > WT | go above WT line (log FC > 0) |
| `dpn_area_vox` | mudmut < WT | go below WT line (log FC < 0) |
| `avg_dpn_area_vox` | mudmut < WT | go below WT line (log FC < 0) |

Charts for `n_dpn` carry an explicit note that the direction is reversed.
Priority order for interpretation: `lin_area_vox` > `n_pros` > `n_dpn` >
`dpn_area_vox` > `avg_dpn_area_vox`.

---

## Simulation data

Loaded from `data/sim/processed/sim_metrics_last.csv`.
Relevant columns: `condition, sim_id, run_id, div_mean, div_stdev, rot_mean,
rot_stdev, genotype, critical_volume_mode, regulatory_dynamic, n_dpn,
avg_dpn_area_vox, lin_area_vox, n_pros, dpn_area_vox`.

### Simulation subsets

| Subset | sim_ids | genotype | VCV | Used in |
|---|---|---|---|---|
| WT | sim61–65 | wt | 1 | Section 1 only |
| Mudmut VCV=1 | sim41–45 | mudmut | 1 | Sections 2+3, 4, 5 |
| Mudmut VCV=0 | sim51–55 | mudmut | 0 | Sections 2+3, 4, 5 |

### Angle conditions

Nine conditions in the sweep, organized by which angle parameter varies:

| Tag | DIV distribution | APICAL distribution | DIV-only? | APICAL-only? |
|---|---|---|---|---|
| D0S0_R0S30 | NORMAL(0,0) | NORMAL(0,30) | — | yes |
| D0S0_R0S43 | NORMAL(0,0) | NORMAL(0,43) | — | yes |
| D0S0_R36S43 | NORMAL(0,0) | NORMAL(36,43) | — | yes |
| D0S30_R0S0 | NORMAL(0,30) | NORMAL(0,0) | yes | — |
| D0S30_R0S30 | NORMAL(0,30) | NORMAL(0,30) | — | — |
| D0S43_R0S0 | NORMAL(0,43) | NORMAL(0,0) | yes | — |
| D36S43_R0S0 | NORMAL(36,43) | NORMAL(0,0) | yes | — |
| D36S30_R0S0 | NORMAL(36,30) | NORMAL(0,0) | yes | — |
| D36S30_R0S30 | NORMAL(36,30) | NORMAL(0,30) | — | — |

Five unique DIV distributions: NORMAL(0,0), NORMAL(0,30), NORMAL(0,43),
NORMAL(36,43), NORMAL(36,30). Because APICAL_AXIS_ROTATION_DISTRIBUTION only
applies following symmetric divisions, it has no effect on WT simulations
(which have no symmetric divisions). Section 1 therefore groups conditions by
DIV distribution only.


---

## Chart convention

All quantitative figures in Sections 1–5 follow this convention unless noted.

**Y-axis:** `log10(metric_value / wt_mean[metric])` — log fold change from
experimental WT mean. WT mean anchors at 0 on every chart.

**Reference lines — Sections 2+3, 4, 5 (mudmut analysis):**
- Dotted horizontal line at **y = 0**: experimental WT mean
- Solid horizontal line at **y = log10(mm_mean[m] / wt_mean[m])**: experimental
  mudmut mean
- Shaded band centered on the solid mudmut line:
  `[log10((mm_mean[m] − mm_std[m]) / wt_mean[m]),
   log10((mm_mean[m] + mm_std[m]) / wt_mean[m])]`

**Reference lines — Section 1 (WT filter):**
- Dotted horizontal line at **y = 0**: experimental WT mean
- Shaded band centered on the dotted WT line (acceptance region):
  `[log10((wt_mean[m] − wt_std[m]) / wt_mean[m]),
   log10((wt_mean[m] + wt_std[m]) / wt_mean[m])]`
- No mudmut reference line in Section 1; it is not relevant there.

In Sections 4a–4c the y-axis shifts to fold change from mudmut mean
(`log10(value / mm_mean[m])`), with the mudmut mean anchoring at 0 (solid line,
no shaded band needed since 0 is now exact) and the WT mean shown as a dotted
line above 0. This is explicitly noted at the start of Section 4.

**Bars:** each bar represents the mean log fold change across all runs for a
given (condition, sim_id) pair. Error bars show ±1 SD across runs. Each bar is
annotated with its numeric log fold change value (2 decimal places).

**Figure layout for Sections 2+3:** one figure per metric (5 figures). Each
figure is a 2-row × 5-column sub-panel grid:
- Rows: VCV mode (top = VCV=0, bottom = VCV=1)
- Columns: regulatory dynamic (NONE | NB-ABM | VOL-ABM | NB-PDE | VOL-PDE)
- X-axis within each panel: accepted angle conditions (determined by Sections
  1 and 1b filters)
- Colors: one consistent color per angle condition, shared across all figures

**Figure saving:** all figures saved to
`data/sim/processed/figures/analysis/`, with filenames encoding the section
and metric.

---

## Shared utilities (Section 0)

```
fold_change_log(values, ref_mean)
    → log10(values / ref_mean); element-wise

draw_example_lineage(condition, sim_id, run_id=None, title=None)
    → imports sim_viz directly; calls render_geo on the geo tensor for that
      (condition, sim_id, run_id) row. NPZ row is looked up via
      sim_run_index.csv (condition + sim_id + run_id → npz_path + npz_row).
      If run_id is None, selects the run whose lin_area_vox is closest to the
      mean for that (condition, sim_id) pair (the "median" run) using
      sim_metrics_last.csv. Returns a matplotlib figure.

nb_circularity(geo_tensor)
    → for a single (200, 200, 2) geo tensor, extract connected components from
      channel 0 (NB mask), compute circularity = 4π·area/perimeter² for each
      component, return the minimum circularity across all NB components in
      that tensor. Components smaller than 50 voxels are ignored (likely
      artifacts).
```

---

## Section 0 — Setup

- Load `sim_metrics_last.csv` and `exp_summary.csv`
- Extract `wt_ref` and `mm_ref` dicts from experimental summary
- Print reference table: for each metric, show wt_mean, mm_mean,
  log10(mm_mean/wt_mean), direction of effect
- Define shared utilities above
- Print angle condition table with DIV group assignments

---

## Section 1 — DIV distribution filter (WT simulations)

**Question:** Which DIV_ROTATION distributions keep WT simulations within
±1 SD of experimental WT for the top 3 metrics?

**Data:** WT sims (sim61–65), all angle conditions.

**Preliminary sanity check (before main filter charts):** for each of the 5 unique
DIV distributions that appear in more than one condition (i.e. those paired with
different APICAL values), show the WT results for all conditions sharing that DIV
distribution side by side across metrics. Because APICAL has no effect on WT
outcomes, these bars should be effectively identical. This confirms the
expectation before pooling; if they differ meaningfully, investigate before
proceeding.

**Main filter charts** group conditions by DIV distribution (5 groups) after the
sanity check has passed.

**Charts:** one figure per metric (5 figures, prioritize top 3 first). Each
figure:
- X-axis groups: 5 DIV distributions
- Bars within each group: one per regulatory dynamic (5 bars)
- Y-axis: log fold change from experimental WT mean
- WT ±1 SD band shown as the acceptance region

**Filter criterion:** a DIV distribution is eliminated if any of its bars falls
outside the WT ±1 SD band on any of the top 3 metrics
(`lin_area_vox`, `n_pros`, `n_dpn`). The `dpn_area_vox` and `avg_dpn_area_vox`
charts are shown for completeness but do not drive the filter decision.

**Output cell:** a Python list `accepted_div_distributions` and the
corresponding `accepted_conditions` list (the subset of the 9 angle conditions
whose DIV distribution passed the filter). These variables are used by all
subsequent sections.

**Visual gut-check:** `draw_example_lineage` for one WT sim at the largest-sigma
accepted DIV distribution vs the D36S30_R0S0 baseline (or the lowest-sigma
accepted distribution if D36S30 was eliminated), to confirm lineages look
reasonable before proceeding.

---

## Section 1b — NB roundness filter

**Question:** Do any accepted angle conditions produce systematically flat or
elongated neuroblasts?

**Motivation:** if many divisions occur along the same axis, NBs can become
very flat. A flatness threshold is calibrated visually in this section and
applied to eliminate conditions that produce degenerate NB morphology.

**Data:** mudmut VCV=1 sims (sim41–45) across `accepted_conditions`, all runs,
last timepoint. WT and VCV=0 are not used here (roundness is a morphological
check on the mudmut conditions we intend to analyze).

**Computation:** for each (condition, sim_id, run_id) row, load the geo tensor
from the condition NPZ and compute `nb_circularity(geo_tensor)`. Collect
results into a DataFrame with columns `[condition, sim_id, run_id, min_circularity]`.

**Charts:**
1. Box plots of `min_circularity` grouped by accepted angle condition — shows
   the distribution across runs. X-axis = angle condition, Y-axis = minimum NB
   circularity.
2. Example lineage grid: call `draw_example_lineage` for runs at several
   circularity quantiles (e.g., 10th, 50th, 90th percentile) across all
   accepted conditions combined, to calibrate what each circularity value looks
   like visually.

**Threshold calibration:** an interactive markdown cell prompts the analyst to
record the chosen threshold after reviewing the example lineages. A code cell
below applies the threshold: any `accepted_condition` whose median
`min_circularity` falls below the threshold is appended to a
`roundness_excluded_conditions` list.

**Output cell:** updated `accepted_conditions` with roundness exclusions
applied. If `roundness_excluded_conditions` is empty, a note confirms all
conditions passed.

**Visual gut-check:** `draw_example_lineage` for the lowest-circularity
accepted condition vs the highest-circularity condition, as a final confirmation
the threshold is appropriate.

---

## Section 2+3 — Regulatory dynamics and VCV (mudmut)

**Question:** Across all accepted angle conditions, which (regulatory dynamic,
VCV mode) combinations push simulated mudmut below the experimental WT mean?
Which reach the experimental mudmut target?

**Data:** mudmut VCV=0 (sim51–55) and VCV=1 (sim41–45), across
`accepted_conditions`.

**Charts:** one figure per metric (5 figures, shown in priority order). Each
figure:
- 2-row × 5-column sub-panel grid
- Row 1 (top): VCV=0
- Row 2 (bottom): VCV=1
- Columns: NONE | NB-ABM | VOL-ABM | NB-PDE | VOL-PDE
- X-axis within each panel: accepted angle conditions
- Y-axis: log fold change from experimental WT mean
- Both reference lines (WT at 0, mudmut target) in every panel
- Bars annotated with numeric log fold change values

**Reading the grid:**
- Compare across columns (same row, same angle condition) to see regulatory
  dynamic effects
- Compare across rows (same column, same angle condition) to see VCV effect
- Read within a panel to see whether a regulatory dynamic's effect varies by
  angle condition

**Interpretation cells:** markdown cells after each figure note which panels
cross below the WT line (y < 0 for metrics where mudmut < WT, y > 0 for
`n_dpn`), and which approach the mudmut band. Expected finding: VCV=0 panels
rarely cross the WT threshold; VCV=1 panels show crossing in some regulatory
dynamics for some metrics. These cells are pre-written as placeholders and
updated by the analyst after running.

---

## Section 4 — Angle distribution effects

**Question:** Among accepted angle conditions, do DIV or APICAL distributions
systematically affect alignment with the experimental mudmut target?

**Y-axis shift:** this section uses fold change from **experimental mudmut mean**
(`log10(value / mm_mean[m])`), so the mudmut mean anchors at 0 and the WT mean
appears as a secondary reference line above 0 (for metrics where mudmut < WT).
This is explicitly stated at the section header.

**Data:** same as Section 2+3 — mudmut VCV=0 and VCV=1 across accepted
conditions. The figure layout (2-row × 5-column) is preserved so patterns from
Section 2+3 remain comparable.

**Sub-sections:**

**4a — DIV_ROTATION alone:** figures restricted to accepted conditions where
APICAL = NORMAL(0,0). X-axis shows the accepted DIV distributions in order of
increasing sigma (then mean). Comparison isolates DIV effect.

**4b — APICAL_ROTATION alone:** figures restricted to accepted conditions where
DIV = NORMAL(0,0) (tags D0S0_R0S30, D0S0_R0S43, D0S0_R36S43). If DIV(0,0)
was excluded by the Section 1 filter, this sub-section is skipped with a note.
X-axis shows the accepted APICAL distributions in order of increasing sigma
(then mean). Comparison isolates APICAL effect.

**4c — Both parameters varying:** the two conditions that vary both
(D0S30_R0S30 and D36S30_R0S30, if accepted). Shown alongside their DIV-only
and APICAL-only counterparts as a combined reference so the interaction is
visible.

**Visual gut-checks:** `draw_example_lineage` for the extreme accepted
conditions in each sub-section — largest sigma vs smallest sigma, and biased
mean vs zero mean.

---

## Section 5 — Synthesis

**Ranked proximity table:** for each of the top 3 metrics
(`lin_area_vox`, `n_pros`, `n_dpn`), a table of all (VCV, regulatory dynamic,
accepted angle condition) combinations ranked by the fraction of simulated runs
falling within the experimental mudmut ±1 SD band. Columns:
`rank, vcv, regulatory_dynamic, condition, metric, frac_within_mm_band,
mean_log_fc_from_mm`.

A combined-rank table (sum of per-metric ranks across the 3 metrics) identifies
the overall best-performing combinations.

**Interpretation cell:** free-text markdown cell for the analyst to record
conclusions, noting which regulatory mechanisms show the most promise, whether
VCV=1 is necessary, and whether any angle condition consistently improves or
worsens alignment. This cell becomes the foundation for the discussion section.

---

## Open questions and known limitations

- **Roundness threshold:** must be calibrated visually in Section 1b. Cannot be
  pre-specified.
- **Section 4b availability:** depends on whether DIV=NORMAL(0,0) conditions
  survive the Section 1 filter. If all three APICAL-only conditions are
  eliminated, Section 4b has no data.
- **n_dpn direction:** the reversed interpretation for `n_dpn` must be noted
  consistently by the analyst when reading figures; the chart convention does
  not visually invert the axis.
- **Run count per condition:** assumed to be consistent across conditions.
  A setup cell checks this and warns if any (condition, sim_id) pair has
  substantially fewer runs than the others.
