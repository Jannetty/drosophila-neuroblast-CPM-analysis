# Comparison Figures Phase 1 Implementation Plan

## Goal

Implement Phase 1 of the comparison-figure workflow described in
`docs/plans/design_plans/7_COMPARISON_FIGURES.md`.

Phase 1 should:

- generate exploratory comparison figures from the existing comparison CSVs
- support `intra-condition`, `inter-div-priority`, and `inter-rot-priority`
  comparison modes
- produce one metric per figure
- produce both raw-value and WT-fold-change variants
- overlay experimental WT and mudmut mean lines with shaded `±1 SD` bands

This phase is plotting only. Do not implement scalar similarity scoring yet.

## Files

Add:

```text
src/npa/comparison_figures.py
scripts/plot_comparisons.py
tests/test_comparison_figures.py
tests/test_plot_comparisons_cli.py
```

Update:

```text
docs/PIPELINE.md
```

## Architecture note

For Phase 1, keep this area flat:

- one plotting/helper module
- one thin CLI

Do not create a larger plotting package yet. The comparison/analysis figure
space may grow later, but Phase 1 should stay simple. If a second or third
distinct comparison-figure family appears later, that will be the right time to
split the plotting code into a more structured sub-area.

## Inputs

Primary plotting input:

```text
data/sim/processed/sim_metrics_last.csv
```

Reference inputs:

```text
data/exp/processed/exp_summary.csv
```

The main boxplots must be built from `sim_metrics_last.csv`, not from the
aggregated simulation summary CSV.

## Implementation steps

1. Add a small plotting module in `src/npa/comparison_figures.py`.
   - Define the five supported metrics in one stable list:
     - `n_dpn`
     - `avg_dpn_area_vox`
     - `lin_area_vox`
     - `n_pros`
     - `dpn_area_vox`
   - Add helpers to:
     - load the plotting CSVs
     - compute WT-fold-change values from the experimental WT mean
     - build compact labels for simulation categories and condition tags
     - prepare `intra-condition` plotting data
     - prepare `inter-div-priority` plotting data
     - prepare `inter-rot-priority` plotting data
     - draw a boxplot figure with experimental WT/mudmut overlays

2. Keep normalization rules explicit and fixed.
   - Raw plots use the metric values directly.
   - Fold-change plots divide by the experimental WT mean for the same metric.
   - Apply the same WT normalization to:
     - simulation run values
     - experimental WT mean and SD
     - experimental mudmut mean and SD
   - If the WT mean for a metric is zero, raise a clear error rather than
     silently plotting invalid fold-change values.

3. Define the plotting modes clearly.
   - `intra-condition`
     - fixed input: one `condition`
     - x-axis groups: simulation categories derived from `sim_id`
   - `inter-div-priority`
     - fixed input: one `sim_id`
     - x-axis groups: compact parameter tags derived from `condition`
     - sort first by rotation setting, then within each rotation block compare
       division changes so same-rotation comparisons stay visually local
   - `inter-rot-priority`
     - fixed input: one `sim_id`
     - x-axis groups: compact parameter tags derived from `condition`
     - sort first by division setting, then within each division block compare
       rotation changes so same-division comparisons stay visually local

4. Keep the first figure style simple and deterministic.
   - Use one metric per figure.
   - Use box-and-whisker plots for the simulation run distributions.
   - Add two horizontal reference lines:
     - WT mean
     - mudmut mean
   - Add two shaded `±1 SD` bands:
     - WT
     - mudmut
   - Exclude nanobody in Phase 1.
   - Save static image files; no interactive plotting is needed.

5. Add a thin CLI in `scripts/plot_comparisons.py`.
   - Required inputs:
     - `--mode intra|inter-div-priority|inter-rot-priority`
     - `--metric`
   - Required fixed-group selector:
     - `--condition` for `intra`
     - `--sim-id` for both inter modes
   - View selector:
     - `--scale raw|foldchange`
   - Optional overrides:
     - `--sim-metrics`
     - `--exp-summary`
     - `--out`
   - Default outputs should go under:
     - `data/sim/processed/figures/comparisons/intra/`
     - `data/sim/processed/figures/comparisons/inter_div_priority/`
     - `data/sim/processed/figures/comparisons/inter_rot_priority/`

6. Update `docs/PIPELINE.md`.
   - Document the new plotting step.
   - Document the three comparison modes.
   - Document raw vs WT-fold-change output variants.
   - Document that WT and mudmut are shown as line-plus-band references.

## Labels and grouping

Keep labels compact in Phase 1.

- Intra-condition mode:
  - label simulation groups using a compact parsed category label
  - include genotype, critical-volume mode, and regulatory dynamic
  - avoid showing only raw `sim43`-style labels

- Inter-condition modes:
  - label condition groups using a compact condition tag such as
    `D36S30_R0S30`
  - ensure the label clearly exposes both `D<mean>S<stdev>` and
    `R<mean>S<stdev>`
  - avoid full `divMean...` directory strings on the x-axis

The exact text format can stay short and utilitarian in Phase 1; it does not
need publication-style polish yet.

## Tests

1. Plot-data preparation test in `tests/test_comparison_figures.py`.
   - Build a tiny `sim_metrics_last.csv` fixture with at least:
     - two conditions
     - two sim IDs
     - multiple runs
   - Build a matching experimental summary fixture.
   - Assert:
     - `intra-condition` filtering is correct
     - `inter-div-priority` filtering and ordering are correct
     - `inter-rot-priority` filtering and ordering are correct
     - WT-fold-change values are computed correctly
     - labels are non-empty and deterministic

2. Plot rendering test in `tests/test_comparison_figures.py`.
   - Render a figure for one metric in raw mode.
   - Render a figure for one metric in fold-change mode.
   - Assert the function returns a figure object and can save successfully.

3. CLI test in `tests/test_plot_comparisons_cli.py`.
   - Run one `intra` example and one example for each inter mode.
   - Assert the output files are created in the expected locations.
   - Assert invalid argument combinations fail clearly, such as:
     - `--mode intra` without `--condition`
     - either inter mode without `--sim-id`

## Verification

Run:

```bash
uv run pytest tests/test_comparison_figures.py tests/test_plot_comparisons_cli.py
uv run pytest
```

Then smoke-test at least one figure in each mode:

```bash
uv run python scripts/plot_comparisons.py \
  --mode intra \
  --condition divMean36Stdev30_rotMean0Stdev30 \
  --metric n_dpn \
  --scale raw

uv run python scripts/plot_comparisons.py \
  --mode inter-div-priority \
  --sim-id sim43 \
  --metric n_dpn \
  --scale foldchange

uv run python scripts/plot_comparisons.py \
  --mode inter-rot-priority \
  --sim-id sim43 \
  --metric n_dpn \
  --scale foldchange
```
