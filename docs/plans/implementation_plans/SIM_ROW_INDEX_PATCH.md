# Simulation row index patch

## Goal

Make every row in each simulation condition NPZ discoverable without opening the
NPZ manually.

## Current behavior

- `sim_index.csv` records one row per condition NPZ.
- Each condition NPZ stores row-aligned arrays: `geo`, `counts`, `sim_id`,
  `run_id`, and `time_id`.
- `scripts/visualize_sim.py --mode npz` requires `--row`, but there is no
  human-readable row-level ledger beside the processed outputs.

## Proposed behavior

Create `sim_row_index.csv` in the same processed output directory as
`sim_index.csv`. It will contain one row per NPZ row with:

```text
condition,npz_path,npz_row,sim_id,run_id,time_id,n_nb,n_progeny,cells_path,locs_path
```

Rows are written during preprocessing, using the same sorted `(sim_id, run_id)`
order that writes the NPZ arrays. Corrupt skipped runs are omitted.

## CLI adaptation

Extend `scripts/visualize_sim.py --mode npz` so users can:

- list rows in an NPZ: `--list`
- select a row by metadata: `--sim-id <id> --run-id <id>`
- keep using explicit `--row`

If both `--row` and `--sim-id/--run-id` are provided, `--row` remains the direct
selection. Metadata lookup reads `sim_row_index.csv` from the NPZ parent
directory.

## Tests

- Unit test that `process_condition` returns row records for saved rows.
- Unit test that `write_sim_row_index` writes the expected CSV columns.
- CLI test that preprocessing writes both `sim_index.csv` and
  `sim_row_index.csv`.
- Visualization CLI tests for `--list` and `--sim-id/--run-id` lookup.

## Documentation

Update `docs/PIPELINE.md` Step 3 and Step 4 to describe the new row ledger and
the new visualization selection options.
