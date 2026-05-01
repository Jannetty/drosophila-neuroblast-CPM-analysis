# Extract metrics implementation plan

## Goal

Implement voxel-only lineage metrics for experimental and simulation data,
following `docs/plans/design_plans/5_EXTRACTMETRICS.md`.

Outputs:

```text
data/exp/processed/metrics.csv
data/sim/processed/timepoint_metrics.csv
```

Do not write `*_area_um2` columns. Include `ds` so real-unit areas can be
derived downstream.

## Files

Add:

```text
src/npa/metrics.py
scripts/extract_metrics.py
tests/test_metrics.py
tests/test_extract_metrics_cli.py
```

Update:

```text
docs/PIPELINE.md
```

## Implementation steps

1. Add `src/npa/metrics.py`.
   - Keep it flat.
   - Define stable experimental and simulation column lists.
   - Add small helpers for mean/std where zero-count populations return `NaN`.

2. Experimental extraction.
   - Load `lineage_index.csv`.
   - Cache each `analysis/{genotype}.npz` once.
   - For each accepted lineage, compute total `dpn_area_vox`,
     `pros_area_vox`, and `lin_area_vox` from `geo`.
   - Load the matching mesh NPZ and reconstruct per-cell 2D territories from
     `lin_poly_2d_px`, `dpn_centroids_2d_px`, and `pros_centroids_2d_px`.
   - Compute per-cell Dpn/Pros means and standard deviations in pixels.

3. Simulation extraction.
   - Add `iter_sim_timepoint_metrics(...)` as the primary path.
   - Iterate condition dirs, sim dirs, and matched timepoints in sorted order.
   - For each CELLS/LOCATIONS pair, compute one metrics dict from raw voxel
     lists, yield it, and discard the JSON payloads.
   - Add `write_sim_timepoint_metrics_csv(rows, out_path)` that streams yielded
     rows directly to CSV.

4. CLI.
   - `--kind exp --processed-dir data/exp/processed`
   - `--kind sim --sweep-root data/sim/bioparams_rotation_sweep --out-dir data/sim/processed`
   - Support `--conditions`, `--sim-ids`, and `--ds` for simulation.
   - Default outputs to `metrics.csv` and `timepoint_metrics.csv`.

5. Documentation.
   - Update `docs/PIPELINE.md` with the new script, outputs, columns, and
     voxel-only unit policy.

## Tests

1. Experimental unit test.
   - Build tiny `lineage_index.csv`, `analysis/wt.npz`, and mesh NPZ.
   - Assert total voxel areas, means, stds, and absence of `*_area_um2`.

2. Simulation unit test.
   - Build one condition with one sim, one run, two timepoints.
   - Use current LOCATIONS format.
   - Assert one row per timepoint, population counts, total areas, means, stds,
     sorting, and absence of `*_area_um2`.

3. Streaming writer test.
   - Pass a generator to `write_sim_timepoint_metrics_csv`.
   - Assert rows are written without requiring a DataFrame.

4. CLI tests.
   - `--kind exp` writes `metrics.csv`.
   - `--kind sim` writes `timepoint_metrics.csv`.
   - Filters apply for `--conditions` and `--sim-ids`.

## Verification

Run:

```bash
uv run pytest tests/test_metrics.py tests/test_extract_metrics_cli.py
uv run pytest
```

Then smoke-test:

```bash
uv run python scripts/extract_metrics.py --kind exp --processed-dir data/exp/processed
uv run python scripts/extract_metrics.py --kind sim --sweep-root data/sim/bioparams_rotation_sweep --out-dir data/sim/processed
```
