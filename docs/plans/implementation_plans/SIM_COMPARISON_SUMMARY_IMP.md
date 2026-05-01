# Simulation Comparison Summary Implementation Plan

## Goal

Implement the comparison-summary step described in
`docs/plans/design_plans/6_SIM_COMPARISON_SUMMARY.md`.

This step should:

- read the existing simulation and experimental metrics CSVs
- select simulation rows for `last` or a requested integer timepoint
- write a run-level simulation CSV for downstream plots
- write a per-`(condition, sim_id)` simulation summary CSV
- write a per-genotype experimental summary CSV

Keep this minimal. No plotting in this step.

## Files

Add:

```text
scripts/summarize_metrics.py
tests/test_summarize_metrics_cli.py
```

Update:

```text
src/npa/metrics.py
tests/test_metrics.py
docs/PIPELINE.md
```

## Implementation steps

1. Add small summary helpers to `src/npa/metrics.py`.
   - Keep the module flat.
   - Define the five comparison metrics in one stable list.
   - Add helpers to:
     - select simulation rows for `last` or a specific `time_id`
     - parse condition metadata from `condition`
     - parse simulation metadata from `sim_id`
     - build the simulation run-level table
     - build the simulation summary table
     - build the experimental summary table

2. Keep simulation CSV loading narrow.
   - Read only the required columns from `timepoint_metrics.csv`:
     `condition, sim_id, run_id, time_id, n_dpn, avg_dpn_area_vox, lin_area_vox, n_pros, dpn_area_vox`
   - Use `usecols` and explicit dtypes where practical.
   - Do not load `cells_path` or `locs_path`.

3. Add a thin CLI in `scripts/summarize_metrics.py`.
   - Inputs:
     - `--sim-metrics`
     - `--exp-metrics`
     - `--timepoint`
   - Optional outputs:
     - `--sim-out`
     - `--sim-summary-out`
     - `--exp-summary-out`
   - Optional filters:
     - `--conditions`
     - `--sim-ids`

4. Update `docs/PIPELINE.md`.
   - Document the new summary step.
   - Document the three output CSVs.
   - Note that the simulation summary step reads only a narrow subset of columns
     from the large simulation metrics CSV.

## Tests

1. Summary helper test in `tests/test_metrics.py`.
   - Build a tiny simulation DataFrame with multiple runs and timepoints.
   - Assert `timepoint=last` selects one row per run.
   - Assert explicit integer timepoint filtering works.
   - Assert summary means/stds are correct.
   - Assert parsed metadata columns are present and correct.

2. Experimental summary test in `tests/test_metrics.py`.
   - Build a tiny experimental metrics DataFrame.
   - Assert grouping by genotype and summary columns are correct.

3. CLI test in `tests/test_summarize_metrics_cli.py`.
   - Create small input CSVs.
   - Run the CLI with `--timepoint last`.
   - Assert the three output CSVs are written.
   - Assert sim filters work.

## Verification

Run:

```bash
uv run pytest tests/test_metrics.py tests/test_summarize_metrics_cli.py
uv run pytest
```

Then smoke-test:

```bash
uv run python scripts/summarize_metrics.py \
  --sim-metrics data/sim/processed/timepoint_metrics.csv \
  --exp-metrics data/exp/processed/metrics.csv \
  --timepoint last
```
