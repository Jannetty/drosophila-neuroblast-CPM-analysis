# Simulation Data Preprocessing Plan

**Date:** 2026-04-22
**Goal:** Preprocess ARCADE simulation output (CELLS.json / LOCATIONS.json pairs) into
per-condition analysis NPZ files. The path to the sweep directory is configurable
at runtime.

Reference: `~/bagherilab/neurogen-potts-analysis/scripts/process_simdata.py` and
`~/bagherilab/neurogen-potts-analysis/src/simdata_geo_helpers.py` — carry over the
voxelization and file-indexing logic, drop all sanity-check / visualization functions
(those belong in notebooks).

---

## Data structure

Input — one sweep root, N condition directories, each with M sim directories:

```
{sweep_root}/
    divMean0Stdev30_rotMean0Stdev30/
        sim41/
            2026-03-22-biosim41_..._0001_000000.CELLS.json
            2026-03-22-biosim41_..._0001_000000.LOCATIONS.json
            2026-03-22-biosim41_..._0001_000434.CELLS.json
            2026-03-22-biosim41_..._0001_000434.LOCATIONS.json
            ...
        sim42/ ...
        sim51/ ...
    divMean36Stdev30_rotMean0Stdev30/
        ...
```

- **Condition name** = directory name (e.g. `divMean36Stdev30_rotMean0Stdev30`)
- **Sim ID** = subdirectory name (e.g. `sim41`)
- **Run ID** = 4-digit field in filename (e.g. `0001`)
- **Time ID** = 6-digit field in filename (e.g. `000434`)
- Only the **last timepoint** per (sim_id, run_id) pair is used

---

## Output file specs

### Analysis NPZ (per condition)

Path: `{out_dir}/{condition_name}.npz`

| Key | Shape | dtype | Description |
|---|---|---|---|
| `geo` | (N, H, W, 2) | float32 | ch0=NB mask (pop==1), ch1=pros mask (pop in {2,3}) |
| `counts` | (N, 2) | int32 | [n_dpn, n_pros] per simulation run |
| `sim_id` | (N,) | str | e.g. `"sim41"` |
| `run_id` | (N,) | str | e.g. `"0001"` |
| `time_id` | (N,) | int32 | last timepoint index |
| `canvas_size` | scalar | int32 | canvas dimension used (H == W) |

Rows are sorted by (sim_id, run_id) for reproducibility.

### Condition index CSV

Path: `{out_dir}/sim_index.csv`

Columns: `condition, n_runs, npz_path`

One row per processed condition. `npz_path` is relative to repo root.
`n_runs` = total number of (sim_id, run_id) pairs processed.

---

## Module: `src/npa/sim_preprocessing.py`

Single flat file — not a package. The sim pipeline has three distinct operations
(file indexing, voxelization, orchestration) but each is compact enough that separate
files would add overhead without clarity. Mirrors `exp_viz.py` in staying flat.

### Functions

```python
CELLS_PATTERN = re.compile(r".*_([0-9]{4})_([0-9]{6})\.CELLS\.json$")


def index_sim_files(
    condition_dir: Path,
    sim_ids: list[str],
) -> dict[tuple[str, str], list[tuple[int, Path, Path]]]:
    """
    Scan condition_dir/{sim_id}/ for matched CELLS.json + LOCATIONS.json pairs.

    Returns {(sim_id, run_id): [(time_id, cells_path, locs_path), ...]}
    sorted ascending by time_id. Skips any CELLS file with no matching LOCATIONS file.

    sim_ids controls which subdirectories are visited; pass all present dirs
    if no filtering is needed.
    """


def build_geo_tensor(
    cells_json: list[dict],
    locs_json: list[dict],
    canvas_size: int = 200,
) -> np.ndarray:
    """
    Rasterize one simulation snapshot into a (canvas_size, canvas_size, 2) float32 tensor.

    Steps:
    1. Build {cell_id: pop} from cells_json.
    2. Collect all (x, y) voxel coordinates across all cells and regions.
    3. Compute bounding-box center; compute integer shift (dx, dy) to align it
       with canvas center ((canvas_size-1)/2, (canvas_size-1)/2).
    4. Paint shifted voxels:
         ch0 = 1.0 where pop == 1  (NB / dpn-like)
         ch1 = 1.0 where pop in {2, 3}  (pros-like)
       Skip any voxel shifted outside [0, canvas_size).

    Returns zeros tensor if no voxels are found.
    """


def process_condition(
    condition_dir: Path,
    sim_ids: list[str],
    out_path: Path,
    canvas_size: int = 200,
) -> dict:
    """
    Process all (sim_id, run_id) pairs in condition_dir, save NPZ to out_path.

    For each pair:
      - Take last entry (highest time_id) from index_sim_files.
      - Load CELLS.json and LOCATIONS.json.
      - Call build_geo_tensor.
      - Collect counts [n_dpn, n_pros] from cells_json (pop==1 and pop in {2,3}).

    Stack results sorted by (sim_id, run_id). Save NPZ with keys defined above.
    Return index record dict: {condition, n_runs, npz_path}.
    """
```

---

## Script: `scripts/preprocess_sim.py`

CLI entry point. No processing logic — imports from `npa.sim_preprocessing`.

### Interface

```
python scripts/preprocess_sim.py \
    --sweep-root PATH \
    [--out-dir PATH] \
    [--conditions divMean0Stdev30_rotMean0Stdev30 divMean36Stdev30_rotMean0Stdev30] \
    [--sim-ids sim41 sim42 sim51]
```

`--sweep-root` is required — no hardcoded default. This satisfies the requirement
that the data path is always explicitly set.

`--out-dir` defaults to `{sweep_root}/../processed/` (sibling of the sweep root)
so processed outputs land predictably next to raw data without cluttering it.

`--conditions` filters to a subset of condition directories; default is all
subdirectories of sweep-root.

`--sim-ids` filters to a subset of sim directories; default is all subdirectories
of each condition directory.

### Logic

```
1. Resolve sweep_root and out_dir (absolute paths).
2. Discover condition dirs: subdirectories of sweep_root, filtered by --conditions.
3. For each condition dir:
   a. Discover sim_ids: subdirectories of condition dir, filtered by --sim-ids.
   b. out_path = out_dir / f"{condition_dir.name}.npz"
   c. Call process_condition(condition_dir, sim_ids, out_path, canvas_size=200).
   d. Print summary: condition name, n_runs processed.
4. Write sim_index.csv from collected index records.
```

---

## Validation checklist

- [ ] `sim_index.csv` has one row per condition with no duplicates
- [ ] Each `{condition}.npz` has `geo.shape[0]` equal to `n_runs` in the index
- [ ] `geo` values are in {0.0, 1.0} — binary masks
- [ ] `counts[:, 0]` (n_dpn) > 0 for all rows (every sim should have at least one NB)
- [ ] `sim_id` and `run_id` columns are sorted and consistent across NPZ files
- [ ] `canvas_size` scalar matches the canvas dimension of `geo`
- [ ] Rerunning with `--conditions` subset produces identical NPZ content for those conditions
