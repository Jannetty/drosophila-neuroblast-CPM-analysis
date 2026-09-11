# Analysis Pipeline

Live documentation of what is actually built. Updated when behavior changes.
Design intent lives in `docs/plans/design_plans/`; this file describes reality.

---

## Shared constants

| Name | Value | Where it matters |
|---|---|---|
| `canvas_size` | 200 | Both exp and sim preprocessing; all geo tensors are 200×200 |
| `ds` | 0.3 µm/px | Exp preprocessing only; controls raster pixel size |
| NB / dpn color | `#8e77b5` | Exp and sim visualization |
| Pros / pop2 color | `#259eae` | Exp and sim visualization |
| Pop3 color | `#1a7a8a` | Sim raw (`--all-pops`) only |
| Hull / lineage color | `#d4d4d4` | Exp visualization only |
| Sim cell boundary color | `#606060` | Sim visualization only |

`canvas_size` and `ds` are never read back from stored files during visualization —
they are re-supplied by the caller. The preprocessing scripts write `ds` into
every mesh NPZ as a scalar so its value is documented alongside the data, but
`exp_viz.py` does not read it back. **If you re-run preprocessing with a different
`ds` or `canvas_size`, re-run visualization too.**

---

## Step 1 — Experimental data preprocessing

**Run:** `python scripts/preprocess_exp.py [options]`

**Source:** `src/npa/exp_preprocessing/` (four files: `wrl_io.py`, `lineage_filter.py`,
`geometry.py`, `pipeline.py`)

### Input

```
data/exp/raw/
    wt/    lobe*_control_lineages.wrl, *_dpn.wrl, *_pros.wrl
    mudmut/        lobe*_mud_lineages.wrl, *_dpn.wrl, *_pros.wrl
    Nanobody/   lobe*_Nanobody_lineages.wrl, *_dpn.wrl, *_pros.wrl
```

Each lobe requires all three WRL files (`lineages`, `dpn`, `pros`). A missing
file is a hard error. WRL files are VRML 2.0 mesh files.

### What it does

**Parsing** (`wrl_io.py`): Regex-parses the VRML text to extract
`Coordinate { point [...] }` and `coordIndex [...]` blocks. Handles both the
single-shared-coordinate-block layout and the per-mesh layout. Polygonal faces
are fan-triangulated.

**Cell assignment** (`lineage_filter.py`): For each lobe, the three sets of
meshes (lineage hulls, Dpn cells, Pros cells) are loaded and cells are assigned
to lineages:

- **Pros → lineage**: bounding-box overlap. A pros cell is assigned to the
  lineage whose bbox contains ≥ 95 % of the pros cell's vertices. Unassigned if
  no lineage meets the threshold.
- **Dpn → lineage**: mesh containment sampling. 20 vertices are sampled from the
  dpn cell; the lineage that contains ≥ 60 % of the sample wins. A bounding-box
  pre-filter skips lineages with non-overlapping bboxes. Unassigned if no lineage
  meets the threshold.

**Rejection** (`lineage_filter.py`): A lineage is rejected before analysis if:
- **disconnected**: a secondary connected component has ≥ 50 faces and volume
  ≥ 5.0 (units match the WRL coordinate system). Small fragments are tolerated
  as reconstruction artifacts.
- **no_dpn**: zero Dpn cells were assigned to the lineage after the containment
  step.

Rejected lineages are processed (mesh NPZ is saved) but excluded from the
analysis NPZ and from `lineage_index.csv`. They appear in
`rejected_lineage_index.csv` with a `rejection_reason` column.

**Geometry** (`geometry.py`): For each kept lineage:
1. PCA on the lineage hull vertices → mean, e1 (PC1), e2 (PC2).
2. All vertices projected onto the e1–e2 plane.
3. Lineage boundary polygon, buffered by 0.5 × ds. Two modes (controlled by
   `--no-convex-hull` on `preprocess_exp.py`):
   - **Non-convex (`--no-convex-hull`) — production default:** `unary_union` of all projected triangle
     faces (`mesh_polygon`) — follows the actual mesh silhouette; connected but
     non-convex. If the projection is disconnected, falls back to convex hull.
     Used by `preprocess-data`, `preprocess-exp-nonconvex`, and `figures-nonconvex`.
   - **Convex hull (script default if `--no-convex-hull` is omitted):** `MultiPoint(pts_2d).convex_hull` — encloses all
     projected vertices; overfills concave regions of the mesh. Retained for
     comparison via `figures-convex`.
4. Sphere-weighted Voronoi rasterization (`sphere_voronoi_rasterize`): each
   cell's 3D mesh volume is used to compute an equivalent sphere radius r_i =
   (3V/(4π))^(1/3). Territory is assigned by additively weighted Voronoi —
   argmin_i(‖p−c_i‖−r_i) in µm — giving larger cells proportionally more
   area. Priority override: pixels inside any Dpn circle go to the nearest Dpn
   cell; pixels inside only Pros circles (and outside all Dpn circles) go to
   the nearest Pros cell. Output: (200, 200, 2) float32 geo tensor, channel 0
   = Dpn territory, channel 1 = Pros territory.
5. Pixel coordinates of centroids and the hull polygon are pre-computed at
   this step (in `_um_to_canvas_px`) and stored in the mesh NPZ. This prevents
   a ds mismatch between preprocessing and visualization.

### Outputs

```
data/exp/processed/
    meshes/
        {genotype}/        {lobe}_{lineage_idx}.npz   — one per kept lineage
        rejected/{genotype}/  {lobe}_{lineage_idx}.npz  — one per rejected lineage
    analysis/
        wt.npz             — stacked geo + counts for all wt lineages
        mudmut.npz
        nanobody.npz
    lineage_index.csv      — one row per kept lineage
    rejected_lineage_index.csv
```

**Mesh NPZ keys** (per lineage):

| Key | Shape | Description |
|---|---|---|
| `lin_vertices` | (V, 3) | Lineage hull vertices (3D, µm) |
| `lin_faces` | (F, 3) | Lineage hull faces |
| `dpn_{i}_vertices` | (V, 3) | i-th Dpn cell vertices |
| `dpn_{i}_faces` | (F, 3) | i-th Dpn cell faces |
| `pros_{i}_vertices` | (V, 3) | i-th Pros cell vertices |
| `pros_{i}_faces` | (F, 3) | i-th Pros cell faces |
| `dpn_centroids_3d` | (N_dpn, 3) | Mean vertex position per Dpn cell |
| `pros_centroids_3d` | (N_pros, 3) | Mean vertex position per Pros cell |
| `lin_poly_2d` | (P, 2) | Lineage polygon exterior (µm in PC1/PC2); P varies with complexity — convex hull ~5–125 pts, mesh-union can give hundreds |
| `dpn_centroids_2d` | (N_dpn, 2) | Dpn centroids in µm |
| `pros_centroids_2d` | (N_pros, 2) | Pros centroids in µm |
| `dpn_centroids_2d_px` | (N_dpn, 2) | Dpn centroids in canvas pixels |
| `pros_centroids_2d_px` | (N_pros, 2) | Pros centroids in canvas pixels |
| `lin_poly_2d_px` | (P, 2) | Lineage polygon in canvas pixels |
| `dpn_volumes_um3` | (N_dpn,) | Dpn cell volumes in µm³ (abs of trimesh volume) |
| `pros_volumes_um3` | (N_pros,) | Pros cell volumes in µm³ (abs of trimesh volume) |
| `pca_mean` | (3,) | PCA mean (3D) |
| `pca_e1`, `pca_e2` | (3,) | PC1 and PC2 axes |
| `ds` | scalar | Voxel size used for this lineage (µm) |

**Analysis NPZ keys** (per genotype):

| Key | Shape | dtype | Description |
|---|---|---|---|
| `geo` | (N, 200, 200, 2) | float32 | Stacked geo tensors, row order = lineage_index order |
| `counts` | (N, 3) | float32 | [n_dpn, n_pros, dpn_voxel_sum] |
| `lineage_ids` | (N,) | int32 | Global lineage ID |
| `ds` | scalar | float32 | Voxel size used |

**lineage_index.csv columns:** `lineage_id, genotype, lobe, lineage_idx, n_dpn, n_pros, mesh_path, analysis_row`

`analysis_row` is the row index into the genotype's analysis NPZ. This is the
link between the index CSV and the stacked geo tensors.

### CLI options

```
--wrl-dir     PATH    default: data/exp/raw
--out-dir     PATH    default: data/exp/processed
--genotypes   LIST    filter to subset (wt, mudmut, nanobody)
--lobes       LIST    filter to subset of lobe names
--ds          FLOAT   default: 0.3
--canvas-size INT     default: 200
```

---

## Step 2 — Experimental data visualization

**Run:** `python scripts/visualize_exp_lineage.py [options]`

**Source:** `src/npa/exp_viz.py`

### What it does

Loads from the outputs of Step 1 and displays one lineage at a time.

Three views:

| View | Flag | What it shows |
|---|---|---|
| 3D mesh | `--view 3d` (default) | Interactive Plotly figure: lineage hull (grey, 15% opacity), Dpn cells (purple, opaque), Pros cells (teal, 50% opacity) |
| 2D pre-rasterization | `--view 2d-pre` | Matplotlib: sphere circles (radius from cell volume) at projected centroid positions on lineage outline polygon (non-convex by default; convex hull when `--no-convex-hull` was omitted at preprocessing), coordinates in µm (PC1/PC2) |
| 2D post-rasterization | `--view 2d-post` | Matplotlib: geo tensor as an RGB image with centroid dots overlaid in pixel coordinates |

The `2d-post` view reads `geo` from the analysis NPZ (via `analysis_row`), not
from the mesh NPZ. This guarantees what you see is exactly what enters the
analysis. Centroid pixel coordinates come from the mesh NPZ (`dpn_centroids_2d_px`,
`pros_centroids_2d_px`), which were pre-computed during preprocessing to match
the same `ds` and `canvas_size`. Gray boundary lines (`#d4d4d4`) are drawn at region boundaries
(Dpn/Pros/background) using the same 1-pixel higher-label algorithm as
`sim_viz`: a pixel is marked if its label exceeds any 4-neighbor's label,
so boundaries fall within the higher-label region and background is never
overdrawn.

The `2d-post` view is unavailable for rejected lineages (they have no
`analysis_row`).

### CLI options

```
--list              print the lineage index table and exit
--row  INT          select lineage by table row
--id   INT          select lineage by lineage_id
--view 3d|2d-pre|2d-post   default: 3d
--rejected          operate on rejected_lineage_index.csv instead
```

---

## Step 3 — Simulation data preprocessing

**Run:** `python scripts/preprocess_sim.py --sweep-root PATH [options]`

**Source:** `src/npa/sim_preprocessing.py`

### Input

```
{sweep_root}/
    {condition_name}/
        {sim_id}/
            *_{run_id}_{time_id}.CELLS.json
            *_{run_id}_{time_id}.LOCATIONS.json
```

- **Condition name** = directory name under sweep root.
  New-style names include a genotype prefix and an optional rot suffix:
  `wt_divMean0Stdev26`, `mudmut_divMean0Stdev26_rotMean0Stdev30`.
  Old-style names (e.g. `divMean0Stdev30_rotMean0Stdev30`) also parse correctly.
  Active sweep root: `data/sim/sweep`.
- **Sim ID** = subdirectory name (e.g. `sim41`)
- **Run ID** = 4-digit field extracted by `r".*_([0-9]{4})_([0-9]{6})\.CELLS\.json$"`
- **Time ID** = 6-digit field from same pattern
- Only the **last timepoint** (highest time_id) per (sim_id, run_id) pair is used.
  Earlier timepoints are indexed but discarded.
- Each CELLS file must have a matching LOCATIONS file. Unpaired CELLS files are
  silently skipped.

**LOCATIONS.json format** (actual format from ARCADE output):
```json
[{"id": 1, "center": [x, y, z], "location": [{"region": "...", "voxels": [[x,y,z], ...]}]}]
```
The `"center"` field is ignored during rasterization. Only `"location"[*]["voxels"]`
is read. (An earlier recursive implementation incorrectly extracted phantom voxels
from `"center"` — that bug is fixed.)

**CELLS.json format:**
```json
[{"id": 1, "pop": 1, ...}, {"id": 2, "pop": 2, ...}]
```
- `pop == 1`: neuroblast (NB)
- `pop in {2, 3}`: progeny / pros-like

### What it does

For each (sim_id, run_id) pair, loads the last timepoint's CELLS and LOCATIONS
files, rasterizes into a (200, 200, 2) float32 geo tensor, and collects
population counts.

**Rasterization**: All voxel (x, y) coordinates across all cells are collected.
The bounding-box center of those coordinates is shifted to canvas center
(pixel 99.5 in a 200×200 canvas). Each voxel is then painted:
- Channel 0: pop == 1 (NB)
- Channel 1: pop in {2, 3} (progeny)

Voxels shifted outside [0, 200) are clipped silently.

**Corrupt files**: If a CELLS or LOCATIONS JSON file fails to parse (e.g.
truncated at 64 KB), the (sim_id, run_id) pair is skipped and a `WARNING` line
is printed to stdout identifying the pair and the corrupt file. Processing
continues for all remaining pairs.

### Outputs

```
{out_dir}/
    {condition_name}.npz    — one per condition
    sim_index.csv
    sim_run_index.csv
```

**Condition NPZ keys:**

| Key | Shape | dtype | Description |
|---|---|---|---|
| `geo` | (N, 200, 200, 2) | float32 | Stacked geo tensors |
| `counts` | (N, 2) | int32 | [n_nb, n_progeny] per run |
| `sim_id` | (N,) | str | e.g. `"sim41"` |
| `run_id` | (N,) | str | e.g. `"0001"` |
| `time_id` | (N,) | int32 | Last timepoint index |
| `canvas_size` | scalar | int32 | 200 |

Rows are sorted by (sim_id, run_id) for reproducibility. `n_runs` in
`sim_index.csv` reflects only the pairs that were successfully processed;
corrupt-file skips reduce this count.

**sim_index.csv columns:** `condition, n_runs, npz_path`

`npz_path` is relative to the repo root.

**sim_run_index.csv columns:** `condition, npz_path, npz_row, sim_id,
run_id, time_id, n_nb, n_progeny, cells_path, locs_path`

This row-level ledger has one record per saved NPZ row, using the same sorted
`(sim_id, run_id)` order as the stacked arrays. `cells_path` and `locs_path`
identify the last matched raw snapshot used for that row. Corrupt skipped runs
are omitted.

### CLI options

```
--sweep-root  PATH    required
--out-dir     PATH    default: {sweep_root}/../processed/
--conditions  LIST    filter to subset of condition directories
--sim-ids     LIST    filter to subset of sim subdirectories
```

Active invocation:
```
uv run python scripts/preprocess_sim.py \
    --sweep-root data/sim/sweep \
    --out-dir data/sim/processed_sweep
```

---

## Step 4 — Simulation data visualization

**Run:** `python scripts/visualize_sim.py --mode MODE [options]`

**Source:** `src/npa/sim_viz.py`, `scripts/visualize_sim.py`

### What it does

Renders simulation data as 2D RGB images. Three data-loading contexts:

| Context | Mode | Input |
|---|---|---|
| Raw / any tick | `--mode raw-any` | `--cells` + `--locs` JSON pair |
| Raw / last tick | `--mode raw-last` | `--sim-dir` containing CELLS/LOCATIONS snapshots |
| Preprocessed NPZ | `--mode npz` | `--npz` + `--row`, or `--npz` + `--sim-id` + `--run-id`; `--list` prints rows |

Two rendering functions, each draws gray per-cell outlines (`HULL_COLOR` `#606060`):

**`render_geo`** — 2-channel tensor view (NB + combined progeny):
- Channel 0 (NB/pop1): `#8e77b5`; channel 1 (progeny/pop2+3): `#259eae`
- NB takes priority on overlap
- Per-cell outlines (`#606060`, 1-px wide): in raw modes (`raw-any`,
  `raw-last`) the per-cell ID label map from the JSON is used directly. In
  `npz` mode, connected components on each channel mask are used (cell IDs
  are not stored in the NPZ). The boundary pixel is the one whose label
  exceeds its neighbor's — so boundaries fall within the higher-label cell
  and background pixels are never overdrawn.

**`render_raw`** — 3-channel raw view (pop1, pop2, pop3 separately):
- pop1 (NB): `#8e77b5`; pop2: `#259eae`; pop3: `#1a7a8a`
- NB takes priority on overlap
- Per-cell outlines use the exact cell IDs from the label map (when loaded from
  JSON via `load_raw_snapshot_full`), giving precise per-cell boundaries.

The rendering functions do not call `plt.show()` internally. The CLI controls
display behavior:
- with `--out PATH`, saves `fig.savefig(..., dpi=150, bbox_inches="tight")`
- without `--out`, calls `plt.show()`

### CLI options

```
--mode      raw-any|raw-last|npz   required
--cells     PATH   required for raw-any
--locs      PATH   required for raw-any
--sim-dir   PATH   required for raw-last
--npz       PATH   required for npz
--row       INT    select NPZ row directly
--sim-id    STR    select NPZ row via sim_run_index.csv (with --run-id)
--run-id    STR    select NPZ row via sim_run_index.csv (with --sim-id)
--list            print rows for --npz from sim_run_index.csv and exit
--all-pops         render all 3 pop types separately (raw-any and raw-last only)
--title     STR    optional figure title
--out       PATH   optional output image path
```

---

## Step 5 — Metrics extraction

**Run:** `python scripts/extract_metrics.py --kind KIND [options]`

**Source:** `src/npa/metrics.py`, `scripts/extract_metrics.py`

### What it does

Extracts voxel-only lineage metrics into CSV files. Area columns are stored only
in pixels/voxels. Each output row includes `ds` so real-unit areas can be
derived downstream with `area_um2 = area_vox * ds * ds`, but no `*_area_um2`
columns are written.

### Experimental metrics

**Run:** `python scripts/extract_metrics.py --kind exp --processed-dir data/exp/processed`

**Inputs:**
- `lineage_index.csv`
- `analysis/{genotype}.npz`
- `meshes/{genotype}/{lobe}_{lineage_idx}.npz`

**Output:** `data/exp/processed/metrics.csv`

**Columns:** `lineage_id, genotype, lobe, lineage_idx, analysis_row, ds,
n_dpn, dpn_area_vox, avg_dpn_area_vox, std_dpn_area_vox, n_pros,
pros_area_vox, avg_pros_area_vox, std_pros_area_vox, lin_area_vox`

Total Dpn/Pros/lineage areas come from the analysis `geo` mask. Per-cell Dpn
and Pros means/stds are computed by assigning occupied lineage pixels to the
nearest stored centroid from the mesh NPZ (`dpn_centroids_2d_px`,
`pros_centroids_2d_px`). The analysis NPZ does not store per-cell labels.

### Simulation metrics

**Run:** `python scripts/extract_metrics.py --kind sim --sweep-root data/sim/sweep --out-dir data/sim/processed_sweep`

**Inputs:** all matched `*.CELLS.json` / `*.LOCATIONS.json` pairs under the
sweep root, not only last timepoints.

**Output:** `data/sim/processed/timepoint_metrics.csv`

**Columns:** `condition, sim_id, run_id, time_id, cells_path, locs_path, ds,
n_dpn, dpn_area_vox, avg_dpn_area_vox, std_dpn_area_vox, n_pros,
pros_area_vox, avg_pros_area_vox, std_pros_area_vox, n_gmc, gmc_area_vox,
avg_gmc_area_vox, std_gmc_area_vox, n_neuron, neuron_area_vox,
avg_neuron_area_vox, std_neuron_area_vox, lin_area_vox`

Simulation metrics are computed directly from raw LOCATIONS voxel lists, not
from the centered 200×200 visualization canvas. The CLI streams one matched
timepoint at a time to CSV so large simulation directories are not accumulated
in memory.

### CLI options

```
--kind           exp|sim   required
--processed-dir  PATH      required for exp
--sweep-root     PATH      required for sim
--out-dir        PATH      sim output directory; default: {sweep_root}/../processed/
--out            PATH      optional explicit output CSV
--conditions     LIST      sim-only condition filter
--sim-ids        LIST      sim-only simulation directory filter
--ds             FLOAT     sim voxel size metadata; default: 0.3
```

---

## Step 6 — Comparison summaries

**Run:** `python scripts/summarize_metrics.py --sim-metrics PATH --exp-metrics PATH [options]`

**Source:** `src/npa/metrics.py`, `scripts/summarize_metrics.py`

### What it does

Builds comparison-ready CSVs on top of the existing metrics tables:

- a simulation run-level table for one selected timepoint
- a simulation summary table aggregated by `(condition, sim_id)`
- an experimental summary table aggregated by `genotype`

This step does not recompute raw metrics from JSON. It only reshapes and
summarizes the outputs from Step 5.

### Timepoint selection

`--timepoint last` selects the maximum `time_id` separately for each unique
`(condition, sim_id, run_id)`.

`--timepoint INT` keeps only rows whose `time_id` matches that integer. Runs
missing that timepoint are omitted from the selected simulation output.

### Inputs

- simulation input: `data/sim/processed_sweep/sim_timepoint_metrics.csv`
- experimental input: `data/exp/processed/metrics.csv`

The simulation metrics CSV can be large, so this step reads only the columns it
needs from `timepoint_metrics.csv`:

`condition, sim_id, run_id, time_id, n_dpn, avg_dpn_area_vox, lin_area_vox, n_pros, dpn_area_vox`

It does not load `cells_path` or `locs_path`.

### Outputs

Default outputs for `--timepoint last`:

```text
data/sim/processed_sweep/sim_metrics_last.csv
data/sim/processed_sweep/sim_summary_last.csv
data/exp/processed/exp_summary.csv
```

If `--timepoint` is an integer, the default simulation output names use
`sim_metrics_tXXXXXX.csv` and `sim_summary_tXXXXXX.csv`.

### Selected simulation rows

**Columns:** `condition, sim_id, run_id, time_id, div_mean, div_stdev, rot_mean,
rot_stdev, genotype, critical_volume_mode, regulatory_dynamic, n_dpn,
avg_dpn_area_vox, lin_area_vox, n_pros, dpn_area_vox`

Metadata columns are parsed from:

- `condition` names such as `divMean36Stdev30_rotMean0Stdev30`
- `sim_id` names such as `sim43`

`genotype` is parsed from the condition prefix (`wt_` / `mudmut_`), not from `sim_id` —
the `vcv*` sim ids are shared by both genotypes. Legacy `simNN` ids still supply it from
the series map.

`regulatory_dynamic` takes one of `NONE`, `NB-ABM`, `VOL-ABM`. PDE-like regulation
was removed from the model on 2026-08-20 and dropped from the dataset and figures on
2026-09-11 (see `docs/plans/design_plans/25_remove_pde_like.md`); the `NB-PDE` /
`VOL-PDE` labels survive only in the legacy `simNN` suffix decoder, for reading
archived data.

Simulation metadata follows the ledger in
`data/sim/bioparams_rotation_sweep/METADATA.md`.

### Simulation summary

**Columns:** `condition, sim_id, n_runs, div_mean, div_stdev, rot_mean,
rot_stdev, genotype, critical_volume_mode, regulatory_dynamic, n_dpn_mean,
n_dpn_std, avg_dpn_area_vox_mean, avg_dpn_area_vox_std, lin_area_vox_mean,
lin_area_vox_std, n_pros_mean, n_pros_std, dpn_area_vox_mean,
dpn_area_vox_std`

The summary groups selected simulation rows by `(condition, sim_id)`. Means and
standard deviations use the same population-standard-deviation convention as the
rest of the metrics code (`numpy.std(..., ddof=0)`).

### Experimental summary

**Columns:** `genotype, n_samples, n_dpn_mean, n_dpn_std,
avg_dpn_area_vox_mean, avg_dpn_area_vox_std, lin_area_vox_mean,
lin_area_vox_std, n_pros_mean, n_pros_std, dpn_area_vox_mean,
dpn_area_vox_std`

The summary groups experimental lineages by `genotype`.

### CLI options

```
--sim-metrics      PATH      required
--exp-metrics      PATH      required
--timepoint        last|INT  default: last
--sim-out          PATH      optional explicit selected-run output CSV
--sim-summary-out  PATH      optional explicit simulation summary CSV
--exp-summary-out  PATH      optional explicit experimental summary CSV
--conditions       LIST      optional simulation condition filter
--sim-ids          LIST      optional simulation ID filter
```

---

## Step 7 — Comparison figures

**Run:** `python scripts/plot_comparisons.py --mode MODE --metric METRIC --scale SCALE [options]`

**Source:** `src/npa/comparison_figures.py`, `scripts/plot_comparisons.py`

### What it does

Builds exploratory comparison figures from the selected-run simulation CSV and
the experimental summary CSV.

Each figure shows one metric at a time and supports:

- simulation box-and-whisker plots from per-run values
- WT and mudmut experimental mean lines
- WT and mudmut shaded `±1 SD` bands
- log-scaled y-axis

The first plotting workflow is static and script-driven. It does not depend on
notebooks and does not implement scalar similarity scoring.

### Inputs

- simulation input: `data/sim/processed_sweep/sim_metrics_last.csv`
- experimental input: `data/exp/processed/exp_summary.csv`

The main simulation distributions come from `sim_metrics_last.csv`, not from
the aggregated simulation summary CSV.

### Scales

Two plot scales are supported:

- `raw`: plot the metric values directly
- `foldchange`: divide simulation values and experimental reference values by
  the experimental WT mean for the same metric

If the experimental WT mean is zero for a metric, fold-change plotting raises a
clear error instead of drawing invalid values.

The y-axis is log-scaled in both modes. Axis labels explicitly indicate either:

- the raw unit (`cells`, `vox`, or `vox/cell`)
- or `fold change from WT mean`

### Modes

Three plotting modes are supported:

#### `intra`

Fix one `condition` and compare simulation categories across the x-axis.

Simulation categories are labeled from parsed sim metadata:

- genotype
- critical-volume mode
- regulatory dynamic

Example label style:

`MM-VCV1`
`VOL-ABM`

#### `inter-div-priority`

Fix one `sim_id` and compare parameter folders across the x-axis.

Condition labels are shown as compact two-line tags:

`D36S30`
`R0S30`

Rows are sorted by:

`rot_mean, rot_stdev, div_mean, div_stdev`

This keeps same-rotation groups local while comparing division changes within
those blocks.

#### `inter-rot-priority`

Fix one `sim_id` and compare parameter folders across the x-axis.

Condition labels use the same compact two-line tag format:

`D36S30`
`R0S30`

Rows are sorted by:

`div_mean, div_stdev, rot_mean, rot_stdev`

This keeps same-division groups local while comparing rotation changes within
those blocks.

### Outputs

By default, figures are written under:

```text
data/sim/processed_sweep/figures/comparisons/intra/
data/sim/processed_sweep/figures/comparisons/inter_div_priority/
data/sim/processed_sweep/figures/comparisons/inter_rot_priority/
```

Default filenames encode the mode, fixed selector, metric, and scale.

### CLI options

```
--mode         intra|inter-div-priority|inter-rot-priority   required
--metric       n_dpn|avg_dpn_area_vox|lin_area_vox|n_pros|dpn_area_vox   required
--scale        raw|foldchange   required
--condition    STR    required for intra
--sim-id       STR    required for both inter modes
--sim-metrics  PATH   default: data/sim/processed/sim_metrics_last.csv
--exp-summary  PATH   default: data/exp/processed/exp_summary.csv
--out          PATH   optional explicit output image path
```

---

## Step 8 — Experimental NB connectivity (mudmut)

**Run:** `python scripts/extract_exp_nb_connectivity.py [options]`

**Source:** `src/npa/metrics.py` (`exp_nb_connectivity`), `scripts/extract_exp_nb_connectivity.py`

### What it does

For each mudmut lineage, loads the 3D NB meshes from the preprocessed mesh NPZ and
determines whether all NB cells form a single connected component. Two NB cells are
considered adjacent if the minimum surface-to-surface distance between their 3D meshes
is ≤ `contact_threshold_um` (default 5.0 µm). Adjacency is tested pairwise using
`trimesh.proximity.closest_point`; the resulting adjacency graph is checked for
connectedness with `scipy.sparse.csgraph.connected_components`.

**Why 5.0 µm:** Dpn (Deadpan) is a nuclear marker, so the segmented meshes reflect
nucleus position rather than full cell extent. Two cells whose nuclei are up to ~5 µm
apart are likely touching at the cell-body level. This threshold was calibrated by
inspecting surface distances across all disconnected mudmut lineages and choosing a
value that captures biologically plausible nuclear-marker gaps while excluding clear
separations (> 5 µm).

Lineages with `n_dpn == 1` are trivially connected (no pairwise query performed).

### Input

- `data/exp/processed/lineage_index.csv` — lineage index (mudmut rows only)
- `data/exp/processed/meshes/mudmut/{lobe}_{lineage_idx}.npz` — mesh NPZs

### Output

`data/exp/processed/exp_nb_connectivity.csv`

**Columns:** `lineage_id, genotype, n_dpn, nb_connected, nb_n_components, nb_n_dpn`

| Column | Description |
|---|---|
| `lineage_id` | Global lineage ID (joins to `lineage_index.csv`) |
| `genotype` | Always `mudmut` |
| `n_dpn` | From `lineage_index.csv` |
| `nb_connected` | `True` if all NBs form one component |
| `nb_n_components` | Number of connected NB components |
| `nb_n_dpn` | NB count as seen by the function (cross-check against `n_dpn`) |

### CLI options

```
--proc-dir  PATH   default: data/exp/processed
```

### Analysis

Results are visualised in `docs/tex_draft/figure5_paper_figures.ipynb` (final section:
"Experimental mudmut NB connectivity"). Key result at the current threshold: 54/59
lineages (91.5%, 95% Wilson CI [81.6%, 96.3%]) have all NBs connected.

---

## Regulation parameter calibration sweep

**Run:** `make preprocess-calibrate && make analyze-calibrate && make plot-calibrate`

Data lives at `data/sim/calibrate_sweep/` — 48 condition folders, each containing
50 runs (CELLS + LOCATIONS JSON files directly in the folder, no sim_id subfolder).
A metadata file `conditions.csv` in the same directory maps each folder name to its
parameter values.

### Step A — `make preprocess-calibrate`

**Script:** `scripts/preprocess_calibrate.py`

Reads the flat folder structure (unlike the main sweep pipeline which expects a
`sim_id/` subfolder layer). For each condition, finds the last timepoint per run
by selecting the highest `time_id` in the filename.

**Output:**

- `data/sim/processed_calibrate/sim_metrics_last.csv` — one row per run

  | Column | Description |
  |---|---|
  | `condition` | Folder name (e.g. `vcv1_nb_abm_hm4p0`) |
  | `run_id` | 4-digit run ID string |
  | `time_id` | Timepoint integer (last timepoint only) |
  | `n_dpn` | NB count (pop 1) |
  | `dpn_area_vox` | Total NB voxel area |
  | `avg_dpn_area_vox` | Mean NB voxel area per cell |
  | `n_pros` | Progeny count (pop 2 + pop 3) |
  | `lin_area_vox` | Total lineage voxel area (NB + progeny) |

- `data/sim/processed_calibrate/sim_run_index.csv` — run → file path mapping

  Columns: `condition, run_id, time_id, cells_path, locs_path`

Area metrics are in raw voxels. Multiply by `DS_UM_PER_VOX² = 0.09` (µm²/vox)
to convert to µm².

### Step B — `make analyze-calibrate`

**Script:** `scripts/analyze_calibration_alignment.py`

For each condition × metric, computes alignment against experimental mudmut IQR.

**Output:** `data/sim/processed_calibrate/alignment_summary.csv` — one row per condition (48 rows + header).

Per-metric columns (5 metrics × 7 columns each):

| Suffix | Description |
|---|---|
| `_sim_median` | Median of sim runs (scaled to µm² for area metrics) |
| `_sim_q25`, `_sim_q75` | Sim IQR bounds |
| `_exp_q25`, `_exp_q75` | Exp mudmut IQR bounds |
| `_in_iqr` | `True` if sim median falls within exp mudmut Q25–Q75 |
| `_overlap_frac` | Jaccard overlap of sim IQR and exp IQR |

Plus `n_metrics_aligned` (0–5): count of metrics where `_in_iqr` is `True`.

### Step C — `make plot-calibrate`

**Script:** `scripts/plot_calibration_sweep.py`

**Output:** `docs/tex_draft/figures/calibrate_sweep_plots.pdf`

One page per condition (48 pages), ordered by `conditions.csv` row order. Each
page shows 5 metric subplots (1 row × 5 columns). Per subplot:

- Dark gray boxplot of sim runs (no fliers), log y-axis
- Red IQR band (axhspan Q25–Q75) + dashed median line for exp mudmut reference
- Page title includes folder name, VCV version, regulation type, mechanism, and parameter values

---

## Geometry-decoupling sweep conditions (figure 2)

The decoupling sweep lives at `data/sim/decoupling/` and is preprocessed with:

```
make summarize-decouple
```

which runs `preprocess_sim.py --sweep-root data/sim/decoupling --out-dir data/sim/processed_decoupling` followed by metric extraction and summarization.

The sweep explores four axes of geometry variation at `sim_id = vcv1_noreg` (VCV enabled):

| Sweep axis | Variable | Conditions |
|---|---|---|
| Apical axis reorientation | `div_mean` (relrot) | `wt_divMean0Stdev26`, `wt_divMean0Stdev26_relrot`, `wt_divMean45Stdev26_relrot`, `wt_divMean90Stdev26_relrot` |
| Spindle orientation range | `div_stdev` | `wt_divMean0Stdev26`, `wt_divMean0Stdev35`, `wt_divMean0Stdev45`, `wt_divMean0Stdev60`, `wt_divMean0Stdev75`, `wt_divMean0Stdev90` |
| Offset shift | `y_offset` | `wt_divMean0Stdev26` (86%), `wt_divMean0Stdev26_yoffset50` (50%), `wt_divMean0Stdev26_yoffset22` (22%), `wt_divMean0Stdev26_yoffset7` (7%) |
| Differentiation rule | GMC/NB identity rule at `y_offset=50%` | `wt_divMean0Stdev26_yoffset50` (basal GMC, default), `wt_divMean0Stdev26_yoffset50_randomnb` (random NB), `wt_divMean0Stdev26_yoffset50_apicalgmc` (apical GMC) |

Offset-shift and differentiation-rule conditions use a larger simulation canvas
than the 200×200 default. `decoupling_canvas_size()` in the notebook reads the
canvas size from each condition's sim config JSON.  Larger-canvas snapshots are
downsampled by factor 2 before cropping for display in the geometry-examples panel.

Counterfactual conditions (`*_counterfactual`) use `sim_id = vcv0_noreg` and are
visualised in the supplementary counterfactual figure only.

---

## Step 9 — Figure 5 supplemental connectivity table

**Run:** `make fig5-supp-table`

**Script:** `scripts/generate_connectivity_ci_table.py`

### What it does

Reads `nb_connectivity_metrics.csv` from the adhesion decoupling sweep and computes,
for each (regulatory dynamic × adhesion × relrot_label) cell, the fraction of runs
where all NBs formed one connected component and the 95% Wilson score confidence
interval.

**Wilson CI formula** (z = 1.96):

```
p_hat  = k / n
denom  = 1 + z² / n
center = (p_hat + z² / (2n)) / denom
margin = z * sqrt(p_hat * (1 - p_hat) / n + z² / (4n²)) / denom
ci     = [max(0, center − margin), min(1, center + margin)]
```

Lineages per cell: n = 50. Edge case n = 0 → all outputs NaN.

### Input

`data/sim/processed_decoupling_adhesion/nb_connectivity_metrics.csv`

### Outputs

| File | Description |
|---|---|
| `docs/tex_draft/figures/figure5_supp_connectivity_ci_table.csv` | Long-form CSV, 12 rows (1 reg dynamic × 3 adhesion × 4 relrot) |
| `docs/tex_draft/figures/figure5_supp_connectivity_ci_table.tex` | Wide LaTeX table fragment; one `tabular` environment for VOL-ABM |

**CSV columns:** `regulatory_dynamic, adhesion, relrot_label, n_connected, n_total, frac, ci_lo, ci_hi`

**LaTeX layout:** rows = adhesion (J=50/40/20), columns = relrot (off/0°/45°/90°),
cell = `frac [ci_lo, ci_hi]`.

### CLI options

```
--proc-dir  PATH   default: data/sim/processed_decoupling_adhesion
--out-dir   PATH   default: docs/tex_draft/figures
```

---

## Cross-step invariants

- `geo` tensors are always `(H, W, 2) float32` with values in {0.0, 1.0}.
  Channel 0 = NB/Dpn territory; channel 1 = Pros/progeny territory.
- `canvas_size = 200` is hardcoded in both preprocessing scripts. All downstream
  code can assume 200×200.
- Pixel coordinate arrays (`*_2d_px`) in exp mesh NPZs are computed with the
  same `ds` and `canvas_size` used to produce the geo tensor. Never recompute
  pixel coordinates with different parameters without rerunning preprocessing.
- `sim_viz.load_raw_snapshot` uses `_load_json` from `sim_preprocessing`, so
  a corrupt or truncated JSON file raises `ValueError` with a clear message
  identifying the file, consistent with the preprocessing pipeline.
- Cell/channel colors are shared between `exp_viz.py` and `sim_viz.py`
  (`NB_COLOR`/`DPN_COLOR` = `#8e77b5`, `PROS_COLOR` = `#259eae`). They are
  not imported — keep them in sync manually. Boundary colors differ: `exp_viz`
  uses `HULL_COLOR = #d4d4d4` for the lineage hull outline; `sim_viz` uses
  `HULL_COLOR = #606060` for 1-px per-cell boundaries.
