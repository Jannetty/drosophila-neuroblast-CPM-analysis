# Comparison Figures Plan

**Date:** 2026-04-23
**Goal:** Add a reusable, scripted comparison-figure workflow for simulation vs
experimental metrics, using the new summary inputs without falling into
notebook-only or one-off plotting code.

This plan is for exploratory analysis figures first. Publication polishing is a
later step.

---

## Primary decisions

The first comparison workflow should use these choices:

- **scripted figures first**, not notebook-first
- **one metric per figure**
- **WT as the normalization baseline**
- **WT and mudmut only** for the first experimental reference workflow
- **experimental references shown as horizontal mean lines plus shaded `±1 SD`
  bands**
- **Phase 1 = plotting**, **Phase 2 = optional similarity scoring**

These decisions keep the first version minimal, reproducible, and easy to
iterate on.

---

## Why this step exists

The repo now has the right tabular inputs for comparisons:

- `data/sim/processed/sim_metrics_last.csv`
- `data/sim/processed/sim_summary_last.csv`
- `data/exp/processed/metrics.csv`
- `data/exp/processed/exp_summary.csv`

That solves the data-shaping problem, but not the figure-making problem. The
next missing layer is a plotting workflow that makes the two practical
comparison modes easy:

1. compare simulation categories within one `divMean...` folder
2. compare the same simulation category across different `divMean...` folders

The plotting layer should sit on top of the CSV outputs and avoid recomputing
metrics or aggregation logic.

---

## Input policy

### Primary simulation plotting input

Use:

`data/sim/processed/sim_metrics_last.csv`

This is the main plotting input because boxplots and whisker plots should use
the actual per-run distributions, not already-aggregated summaries.

### Secondary inputs

Use:

- `data/exp/processed/metrics.csv` for experimental raw distributions when
  needed for normalization/reference calculations
- `data/exp/processed/exp_summary.csv` for experimental mean and standard
  deviation overlays
- `data/sim/processed/sim_summary_last.csv` only for tables, spot checks, or
  future summary-only views

The first comparison figures should not use `sim_summary_last.csv` as the main
boxplot source.

---

## Metrics in scope

The first plotting workflow should use the same five metrics already chosen for
the comparison tables:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

Each metric should be visualized independently in its own figure.

No multi-metric composite figure is required for v1.

---

## Figure types

For each metric, the workflow should support two figure variants:

### 1. Raw-value view

Plot the raw metric values directly from the selected simulation runs.

This preserves the real scale and keeps the interpretation biologically
grounded.

### 2. WT fold-change view

Transform both simulation and experimental comparison quantities into fold
change relative to the **experimental WT mean** for that same metric:

`fold_change = value / experimental_wt_mean`

This gives a shared normalized view across metrics and matches the user’s
existing analysis style.

The first workflow should treat WT as the single normalization anchor.

---

## Experimental references

Each figure should show experimental WT and mudmut as reference overlays:

- one horizontal line for the experimental mean
- one shaded band spanning mean `±1 SD`

This should be done for:

- WT
- mudmut

Nanobody should be excluded from the first comparison workflow.

The first version should not add experimental boxplots to the same figure.
Horizontal reference bands are less crowded and better match the current
comparison style.

---

## Comparison modes

The plotting workflow should support two explicit modes.

### Intra-condition mode

Fix one `condition` such as:

`divMean36Stdev30_rotMean0Stdev30`

Then compare simulation categories across the x-axis using one row group per
`sim_id`.

Recommended x-axis labeling for this mode:

use the parsed simulation shorthand / category identity, not raw folder names
or only `sim43`-style labels

At minimum the label should distinguish:

- genotype
- critical-volume mode
- regulatory dynamic

Example style:

`MM-VCV1-VOL-ABM`

### Inter-condition mode

Fix one `sim_id` such as:

`sim43`

Then compare parameter folders across the x-axis using one row group per
`condition`.

Recommended x-axis labeling for this mode:

use compact parameter tags derived from the condition name

Example style:

`D36S30_R0S30`

This is easier to scan than the full `divMean...` directory string.

---

## Plot form

The simulation values should be shown as box-and-whisker plots derived from the
per-run distribution in `sim_metrics_last.csv`.

The first version should keep the visual design simple:

- boxplot + whiskers per x-axis group
- experimental WT and mudmut reference lines
- shaded WT and mudmut standard-deviation bands
- one metric per figure

The first version does not need:

- swarm overlays
- significance annotations
- faceted all-metric dashboards
- interactive plotting

Static figures are sufficient.

---

## Output behavior

The plotting workflow should write figures to disk rather than only display
them interactively.

Outputs should be organized so they are easy to regenerate and browse. A
reasonable structure is:

```text
data/sim/processed/figures/comparisons/
    intra/
    inter/
```

Within those directories, filenames should encode:

- comparison mode
- metric
- raw vs fold-change
- the fixed grouping value

Examples:

- `intra_divMean36Stdev30_rotMean0Stdev30_n_dpn_raw.png`
- `inter_sim43_n_dpn_foldchange_wt.png`

Exact filenames can be finalized at implementation time, but they should be
deterministic and descriptive.

---

## Notebook policy

The first comparison workflow should not depend on notebooks.

If a notebook is added later, it should call into the same reusable plotting
helpers and use the generated CSVs as inputs. The notebook should not become
the only place where comparison logic exists.

---

## Phase 2 — Similarity scoring

Similarity scoring should be planned as a second phase, not part of the first
implementation target.

The scoring phase should not force a single choice between “compare to WT” and
“compare to mudmut.” Instead, it should treat those as two separate reference
questions:

- how WT-like is this simulation?
- how mudmut-like is this simulation?

That is more informative than a single WT-only scalar because a simulation can
be close to WT, close to mudmut, somewhere in between, or close to neither.

The first plotting workflow should be completed and reviewed before choosing a
specific scoring metric.

---

## Validation checklist

- [ ] each metric can be plotted in both raw-value and WT-fold-change forms
- [ ] intra-condition mode fixes one `condition` and compares across simulation
      categories
- [ ] inter-condition mode fixes one `sim_id` and compares across parameter
      folders
- [ ] simulation distributions come from `sim_metrics_last.csv`, not from the
      aggregated summary CSV
- [ ] WT and mudmut reference overlays appear as mean lines with shaded
      standard-deviation bands
- [ ] the first workflow excludes nanobody
- [ ] labels are compact and human-readable in both modes
- [ ] figure generation is scriptable and repeatable without notebook-only code

---

## Out of scope for this plan

- publication-ready styling
- multi-metric combined dashboards
- nanobody comparison support
- scalar similarity scoring implementation
- statistical testing and p-value annotation

Those can follow once the first comparison figure workflow is working cleanly.
