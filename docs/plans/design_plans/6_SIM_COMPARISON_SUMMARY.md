# Simulation Comparison Summary Plan

**Date:** 2026-04-23
**Goal:** Add one compact analysis step that turns the existing long-form
simulation metrics into comparison-ready tables for the last timepoint or a
user-selected timepoint, and add a matching summary table for the experimental
dataset.

This plan is intentionally narrow. It does not add plotting yet. It creates the
smallest stable tabular layer needed so later visualizations can stay simple.

---

## Why this step exists

The current metrics pipeline already produces:

- `data/sim/processed/timepoint_metrics.csv`
- `data/exp/processed/metrics.csv`

That is enough raw information, but not yet the right shape for the two main
comparison modes:

1. compare different simulation conditions within one `divMean...` folder
2. compare the same simulation condition across different `divMean...` folders

The missing layer is a summary step that:

- selects one timepoint per simulation run
- keeps a run-level table for downstream boxplots
- writes an aggregated per-condition/per-sim summary table
- writes a matching experimental summary table

This keeps plotting code thin and avoids re-deriving the same grouping logic in
notebooks or ad hoc scripts.

---

## Existing inputs

### Simulation input

Use:

`data/sim/processed/timepoint_metrics.csv`

Each row already represents one:

`(condition, sim_id, run_id, time_id)`

with metrics including:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

and several other columns.

The simulation metrics CSV is large, so this step should not read the full file
schema by default. It should load only the columns needed for timepoint
selection, grouping, and the five comparison metrics:

- `condition`
- `sim_id`
- `run_id`
- `time_id`
- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

Implementation preference:

- use `pandas.read_csv(..., usecols=[...])`
- provide explicit dtypes where practical
- do not load large unused string columns such as `cells_path` and `locs_path`

This should be the default approach for the current dataset. A true streaming
summary pass is not required unless future sweep sizes make the narrow-column
read too large in practice.

### Experimental input

Use:

`data/exp/processed/metrics.csv`

Each row represents one accepted experimental lineage and already includes the
same core comparison metrics:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

---

## Core comparison metrics

The new comparison step should focus on these five metrics only:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

These are the canonical fields for the first comparison pass. Additional
metrics can be added later only if they are clearly useful for interpretation.

---

## Timepoint policy

The comparison step must support:

- `timepoint=last`
- `timepoint=<integer>`

### `last`

For simulations, `last` means:

for each unique `(condition, sim_id, run_id)`, select the row with the maximum
`time_id`

This allows the caller to ask for final-state comparisons without needing to
know the actual final tick for each run.

### explicit integer

If a specific integer timepoint is requested, keep only rows whose `time_id`
matches that value.

If some runs do not contain that timepoint, they are simply absent from the
selected-timepoint output for that request.

Experimental data is already final-state only, so no additional timepoint
selection is needed for the current experimental summary.

---

## Output files

Write CSVs only. CSV keeps this step inspectable and easy to use from scripts,
notebooks, and plotting code.

### 1. Selected simulation rows

Path example:

`data/sim/processed/sim_metrics_last.csv`

One row per selected simulation run after timepoint selection.

This table is the direct input for boxplots and other per-run visualizations.

### 2. Simulation summary

Path example:

`data/sim/processed/sim_summary_last.csv`

One row per:

`(condition, sim_id)`

aggregated across simulation runs after timepoint selection.

### 3. Experimental summary

Path:

`data/exp/processed/exp_summary.csv`

One row per experimental genotype.

This provides the experimental mean and standard deviation values that the
simulation summaries will be compared against.

---

## Selected simulation rows spec

The selected simulation table should retain the original identifying columns
needed for plotting and grouping:

- `condition`
- `sim_id`
- `run_id`
- `time_id`

It should also carry the five comparison metrics:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

And it should add parsed metadata columns so plotting code does not need to
reverse-engineer names from strings later:

- `div_mean`
- `div_stdev`
- `rot_mean`
- `rot_stdev`
- `genotype`
- `critical_volume_mode`
- `regulatory_dynamic`

These columns should be derived from the existing condition names and sim IDs
using the simulation ledger in `data/sim/bioparams_rotation_sweep/METADATA.md`.

This is the key organizational decision in the plan: parse once here, reuse
everywhere later.

To keep memory use modest, this table should be built from the narrow-column
simulation CSV read described above rather than from the full
`timepoint_metrics.csv` schema.

---

## Simulation summary spec

Group the selected simulation rows by:

`(condition, sim_id)`

For each metric:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

compute:

- mean across runs
- standard deviation across runs

The summary table should also include:

- `n_runs`
- `condition`
- `sim_id`
- `div_mean`
- `div_stdev`
- `rot_mean`
- `rot_stdev`
- `genotype`
- `critical_volume_mode`
- `regulatory_dynamic`

Recommended naming pattern:

- `{metric}_mean`
- `{metric}_std`

This table is meant for summary views and overlays with experimental reference
values.

---

## Experimental summary spec

Group `data/exp/processed/metrics.csv` by:

`genotype`

For the same five metrics:

- `n_dpn`
- `avg_dpn_area_vox`
- `lin_area_vox`
- `n_pros`
- `dpn_area_vox`

compute:

- mean across accepted experimental lineages
- standard deviation across accepted experimental lineages

Also include:

- `n_samples`
- `genotype`

Recommended naming pattern matches the simulation summary:

- `{metric}_mean`
- `{metric}_std`

This symmetry matters. Later plotting code should be able to read both summary
tables without special-case column names.

---

## Grouping logic for the two target comparisons

The planned tables should make both requested comparison directions trivial.

### Compare within one `divMean...` folder

Filter selected simulation rows or summary rows by one `condition`, then compare
across `sim_id` or `regulatory_dynamic`.

### Compare one simulation condition across folders

Filter by one `sim_id`, then compare across `condition` or the parsed condition
parameters:

- `div_mean`
- `div_stdev`
- `rot_mean`
- `rot_stdev`

No additional reshaping step should be required for either case.

---

## Module and script layout

Keep this minimal.

Add one new CLI:

`scripts/summarize_metrics.py`

Put the helper functions in:

`src/npa/metrics.py`

Do not create a new package or a notebook-first workflow for this step.

Recommended responsibilities:

### `src/npa/metrics.py`

- select simulation rows for `last` or an explicit timepoint
- parse condition metadata from `condition`
- parse simulation metadata from `sim_id`
- build selected simulation DataFrame
- build simulation summary DataFrame
- build experimental summary DataFrame
- write summary CSVs

### `scripts/summarize_metrics.py`

Thin CLI only.

It should:

1. read the experimental metrics CSV normally
2. read the simulation metrics CSV with `usecols` limited to the required columns
3. choose `last` or a specific timepoint
4. write the selected simulation rows CSV
5. write the simulation summary CSV
6. write the experimental summary CSV

---

## CLI shape

Recommended interface:

```bash
uv run python scripts/summarize_metrics.py \
  --sim-metrics data/sim/processed/timepoint_metrics.csv \
  --exp-metrics data/exp/processed/metrics.csv \
  --timepoint last
```

Optional flags:

- `--timepoint last|INT`
- `--sim-out PATH`
- `--sim-summary-out PATH`
- `--exp-summary-out PATH`
- `--conditions ...`
- `--sim-ids ...`

Condition and sim filters are optional but useful for quick focused work.

---

## Notebook policy

This step should not require a notebook.

If notebooks are used later, they should:

- read the generated CSVs
- make figures
- avoid recomputing grouping and summary logic

That keeps notebooks disposable and keeps the reusable logic in the main code
path.

---

## Validation checklist

- [ ] `sim_metrics_last.csv` contains exactly one row per `(condition, sim_id, run_id)` when `--timepoint last` is used
- [ ] `sim_summary_last.csv` contains exactly one row per `(condition, sim_id)`
- [ ] `exp_summary.csv` contains exactly one row per genotype present in `metrics.csv`
- [ ] all five comparison metrics appear in both summary outputs with matching `{metric}_mean` and `{metric}_std` naming
- [ ] parsed simulation metadata matches the ledger in `data/sim/bioparams_rotation_sweep/METADATA.md`
- [ ] filtering by one condition makes within-folder comparison immediate
- [ ] filtering by one sim ID makes across-folder comparison immediate
- [ ] no plotting logic is required to recreate summary statistics

---

## Out of scope for this plan

- plotting code
- notebook authoring
- significance testing
- effect-size calculations
- normalization across sim and experimental datasets
- adding new biological metrics beyond the five listed above

Those can be added later, once the summary tables are in place and reviewed.
