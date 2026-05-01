# Extract Metrics Plan

**Date:** 2026-04-23
**Goal:** Extract compact, row-wise lineage metrics from the processed
experimental data and from all available simulation timepoints. Keep the output
human-readable and easy to join against existing ledgers.

This plan covers area and cell-count metrics only. A future plan can add a
division-event ledger for simulated neuroblast divisions.

---

## Output files

Write CSVs under the existing processed directories:

```
data/exp/processed/metrics.csv
data/sim/processed/timepoint_metrics.csv
```

CSV is preferred over NPZ for this step because the result is tabular,
inspectable, and meant to serve downstream plotting/statistics.

## Unit policy

Voxel/pixel measurements are the only stored area values in this metrics step.
Real-unit areas can be derived downstream from the canonical voxel columns and
`ds` when plotting or reporting.

Rules:

- Always compute `*_area_vox` first.
- Always include `ds` in each output row.
- Do not write `*_area_um2` columns to the metrics CSV.
- Convert selected voxel columns to µm² only in downstream analysis helpers or
  notebooks, using `area_um2 = area_vox * ds * ds`.
- If `ds` changes later, the voxel columns remain valid and real-unit values can
  be regenerated downstream.

---

## Experimental metrics

Input sources:

- `data/exp/processed/lineage_index.csv`
- `data/exp/processed/analysis/{genotype}.npz`
- `data/exp/processed/meshes/{genotype}/{lobe}_{lineage_idx}.npz`

Each row in `metrics.csv` represents one accepted experimental lineage.

### Columns

| Column | Meaning |
|---|---|
| `lineage_id` | Existing lineage ID from `lineage_index.csv` |
| `genotype` | Existing genotype |
| `lobe` | Existing lobe |
| `lineage_idx` | Original lineage index within the lobe |
| `analysis_row` | Row into `analysis/{genotype}.npz` |
| `ds` | Microns per pixel from the NPZ; retained for optional downstream unit conversion |
| `n_dpn` | Number of Dpn cells |
| `dpn_area_vox` | Total Dpn territory pixels |
| `avg_dpn_area_vox` | Mean Dpn per-cell territory area |
| `std_dpn_area_vox` | Standard deviation of Dpn per-cell territory areas |
| `n_pros` | Number of Pros cells |
| `pros_area_vox` | Total Pros territory pixels |
| `avg_pros_area_vox` | Mean Pros per-cell territory area |
| `std_pros_area_vox` | Standard deviation of Pros per-cell territory areas |
| `lin_area_vox` | Number of occupied lineage pixels |

### Computation

For each row in `lineage_index.csv`:

1. Load `analysis/{genotype}.npz`.
2. Select `geo[analysis_row]`, shape `(H, W, 2)`.
3. Read `ds` from the NPZ.
4. Use `n_dpn` and `n_pros` from `lineage_index.csv`.
5. Compute total binary-mask areas:
   - `dpn_area_vox = count(geo[..., 0] > 0)`
   - `pros_area_vox = count(geo[..., 1] > 0)`
   - `lin_area_vox = count((geo[..., 0] > 0) | (geo[..., 1] > 0))`
6. Load the matching mesh NPZ referenced by `mesh_path`.
7. Reconstruct per-cell 2D territories from existing mesh NPZ fields:
   - `lin_poly_2d_px`
   - `dpn_centroids_2d_px`
   - `pros_centroids_2d_px`
8. Assign each lineage pixel to the nearest Dpn or Pros centroid, matching the
   preprocessing Voronoi logic, and count pixels per cell.
9. Compute means and standard deviations from those per-cell pixel counts:
   - `avg_dpn_area_vox`, `std_dpn_area_vox`
   - `avg_pros_area_vox`, `std_pros_area_vox`

Accepted experimental lineages already require `n_dpn > 0`, so no special
zero-division behavior is needed for Dpn averages/stds. Pros counts should be
nonzero for accepted lineages in the current pipeline; if a future accepted row
has zero Pros cells, leave Pros average/std blank.

The analysis NPZ only stores population masks, not per-cell labels. That is why
standard deviations must use the mesh NPZ centroid and polygon fields. Do not
add per-cell labels to the analysis NPZ for this task.

---

## Simulation metrics

Input sources:

- `data/sim/bioparams_rotation_sweep/{condition}/{sim_id}/*.CELLS.json`
- `data/sim/bioparams_rotation_sweep/{condition}/{sim_id}/*.LOCATIONS.json`

Each row in `timepoint_metrics.csv` represents one simulation snapshot:
one `(condition, sim_id, run_id, time_id)` pair.

Unlike the current simulation NPZ preprocessing, this metrics step uses every
matched timepoint, not only the final timepoint.

### Columns

| Column | Meaning |
|---|---|
| `condition` | Condition directory name |
| `sim_id` | Simulation directory name |
| `run_id` | 4-digit run ID from filename |
| `time_id` | 6-digit time ID from filename |
| `cells_path` | Raw CELLS JSON used |
| `locs_path` | Raw LOCATIONS JSON used |
| `ds` | Microns per voxel; default `0.3`; retained for optional downstream unit conversion |
| `n_dpn` | Number of pop1 cells |
| `dpn_area_vox` | Total pop1 voxels |
| `avg_dpn_area_vox` | `dpn_area_vox / n_dpn` |
| `std_dpn_area_vox` | Standard deviation of pop1 per-cell voxel counts |
| `n_pros` | Number of non-NB cells: `n_gmc + n_neuron` |
| `pros_area_vox` | `gmc_area_vox + neuron_area_vox` |
| `avg_pros_area_vox` | `pros_area_vox / n_pros` |
| `std_pros_area_vox` | Standard deviation across all pop2+pop3 per-cell voxel counts |
| `n_gmc` | Number of pop2 cells |
| `gmc_area_vox` | Total pop2 voxels |
| `avg_gmc_area_vox` | `gmc_area_vox / n_gmc` |
| `std_gmc_area_vox` | Standard deviation of pop2 per-cell voxel counts |
| `n_neuron` | Number of pop3 cells |
| `neuron_area_vox` | Total pop3 voxels |
| `avg_neuron_area_vox` | `neuron_area_vox / n_neuron` |
| `std_neuron_area_vox` | Standard deviation of pop3 per-cell voxel counts |
| `lin_area_vox` | Total occupied pop1+pop2+pop3 voxels |

### Computation

For each matched CELLS/LOCATIONS pair:

1. Build `{cell_id: pop}` from CELLS.
2. Parse LOCATIONS using the existing current format:
   `{"id": 1, "center": [x, y, z], "location": [{"region": "...", "voxels": [[x, y, z], ...]}]}`.
3. Count cells by population using cells that appear in CELLS:
   - pop1 -> `n_dpn`
   - pop2 -> `n_gmc`
   - pop3 -> `n_neuron`
   - `n_pros = n_gmc + n_neuron`
4. Count canonical voxel area by summing each located cell's voxel list by
   population:
   - pop1 -> `dpn_area_vox`
   - pop2 -> `gmc_area_vox`
   - pop3 -> `neuron_area_vox`
   - `pros_area_vox = gmc_area_vox + neuron_area_vox`
   - `lin_area_vox = dpn_area_vox + gmc_area_vox + neuron_area_vox`
5. Keep per-cell voxel counts by population while parsing, then compute:
   - `avg_dpn_area_vox`, `std_dpn_area_vox`
   - `avg_gmc_area_vox`, `std_gmc_area_vox`
   - `avg_neuron_area_vox`, `std_neuron_area_vox`
   - `avg_pros_area_vox`, `std_pros_area_vox` over combined pop2+pop3 cells

If a population count is zero, write an empty value (`NaN` in pandas, blank in
CSV) for that population's average and standard deviation. Total area remains
numeric, usually `0`.

The simulation metrics should use raw voxel lists directly rather than the
centered 200x200 canvas. That keeps metrics independent of visualization
clipping and avoids silently losing area outside the display canvas.

### Streaming pass

Simulation extraction should stream through the raw JSON tree and write rows
incrementally. The raw simulation directory is many gigabytes, so the extractor
must not build one huge in-memory list of all snapshots.

Implementation shape:

1. Open `timepoint_metrics.csv` once and write the header.
2. Iterate condition directories in sorted order.
3. Iterate sim directories in sorted order.
4. Use `index_sim_files` to get matched `(run_id, time_id, cells_path,
   locs_path)` entries in sorted order.
5. For each matched pair:
   - load CELLS JSON and LOCATIONS JSON
   - compute one metrics dict
   - write one CSV row
   - discard the JSON payloads and per-cell lists before continuing

For tests and small programmatic use, expose a generator that yields row dicts:

```python
def iter_sim_timepoint_metrics(...) -> Iterator[dict]:
    """Yield one metrics row per matched simulation timepoint."""
```

The CLI should consume this generator directly into a CSV writer. A convenience
DataFrame wrapper is acceptable for tests and notebooks, but the production
simulation path should be streaming.

---

## Module and script layout

Keep this as one flat module plus one CLI:

```
src/npa/metrics.py
scripts/extract_metrics.py
```

### `src/npa/metrics.py`

Functions:

```python
def extract_exp_metrics(processed_dir: Path) -> pd.DataFrame:
    """Return one metrics row per accepted experimental lineage."""

def iter_sim_timepoint_metrics(
    sweep_root: Path,
    ds: float = 0.3,
    conditions: list[str] | None = None,
    sim_ids: list[str] | None = None,
) -> Iterator[dict]:
    """Yield one metrics row per matched simulation timepoint."""

def extract_sim_timepoint_metrics(...) -> pd.DataFrame:
    """Small-wrapper convenience for tests/notebooks; not used by the CLI for large runs."""

def write_exp_metrics_csv(df: pd.DataFrame, out_path: Path) -> None:
    """Write experimental metrics with stable column order."""

def write_sim_timepoint_metrics_csv(rows: Iterable[dict], out_path: Path) -> None:
    """Stream simulation row dicts to CSV with stable column order."""
```

Reuse small helpers from `sim_preprocessing.py` where they already exist:
`index_sim_files`, `_load_json`, and `_parse_voxels`-equivalent parsing logic if
it remains simple. Do not introduce a class hierarchy.

### `scripts/extract_metrics.py`

Interface:

```
python scripts/extract_metrics.py --kind exp --processed-dir data/exp/processed

python scripts/extract_metrics.py \
    --kind sim \
    --sweep-root data/sim/bioparams_rotation_sweep \
    --out-dir data/sim/processed \
    [--conditions ...] \
    [--sim-ids ...] \
    [--ds 0.3]
```

Defaults:

- Experimental output: `{processed_dir}/metrics.csv`
- Simulation output: `{out_dir}/timepoint_metrics.csv`
- Simulation `ds`: `0.3`

---

## Tests

Add focused tests without large fixtures.

### Experimental tests

- Build a tiny `lineage_index.csv`, `analysis/wt.npz`, and matching mesh NPZ.
- Use a small `(H, W, 2)` `geo` with known Dpn and Pros pixels.
- Assert:
  - `n_dpn` and `n_pros` are copied correctly.
  - `dpn_area_vox` equals Dpn-channel pixel count.
  - `pros_area_vox` equals Pros-channel pixel count.
  - `lin_area_vox` equals union of both channels.
  - per-cell Dpn and Pros territory counts produce correct averages and stds.
  - no `*_area_um2` columns are written.

### Simulation tests

- Build one tiny condition directory with one sim, one run, and two timepoints.
- Use actual LOCATIONS format, not the old recursive format.
- Include pop1, pop2, and pop3 cells with known voxel counts.
- Assert one output row per matched timepoint.
- Assert:
  - `n_dpn`, `n_gmc`, `n_neuron`, and `n_pros`.
  - total voxel areas per population.
  - total lineage voxel area.
  - population averages and stds are correct in voxels.
  - no `*_area_um2` columns are written.
  - rows are sorted by `(condition, sim_id, run_id, time_id)`.

### CLI tests

- `--kind exp` writes `metrics.csv`.
- `--kind sim` writes `timepoint_metrics.csv`.
- `--conditions` and `--sim-ids` filter simulation output.
- Missing required paths exit with a clear parser error.
- Simulation CLI test should assert the CSV is written from an iterator, not by
  requiring a giant DataFrame.

---

## What is not included

- Neuroblast division-event ledger.
- Statistical summaries across conditions.
- Plotting.
- New NPZ outputs.
- Reprocessing or modifying existing geometry tensors.

This step should stay tabular, deterministic, and small.
