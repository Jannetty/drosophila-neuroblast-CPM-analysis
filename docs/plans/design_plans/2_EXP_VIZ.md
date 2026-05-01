# Experimental Lineage Visualization Plan

**Date:** 2026-04-22
**Goal:** A minimal CLI visualization tool for inspecting individual experimental
lineages at all three preprocessing stages: 3D mesh, 2D projection pre-Voronoi,
and 2D Voronoi. Supports browsing both kept and rejected lineages without
polluting `lineage_index.csv`.

Reference: `~/bagherilab/neurogen-potts-analysis/scripts/visualize_lineage.py`
— adapt structure and UX, replace colors, drop `total_cells`/`volume_um3`.

---

## Colors

```python
HULL_COLOR = "#d4d4d4"   # light gray
DPN_COLOR  = "#8e77b5"   # purple (specified)
PROS_COLOR = "#259eae"   # teal-blue midpoint of #4a96b7 and #00a6a4
```

For 3D plotly traces, the hull uses `opacity=0.15` so the cells inside are visible.
Dpn is fully opaque. Pros uses `opacity=0.5`.

---

## Rejected lineage design

The current `lineage_index.csv` is kept clean — no rejected rows added.
Rejected lineages are handled by two additional outputs that the preprocessing
pipeline must be updated to produce:

**`data/exp/processed/rejected_lineage_index.csv`**

Columns: `lineage_id, genotype, lobe, lineage_idx, n_dpn, n_pros, mesh_path, rejection_reason`

`lineage_id` uses integer IDs in a separate namespace from kept lineages
(i.e., both start at 0; the `--rejected` flag selects which index is loaded).
`rejection_reason` is one of `disconnected` or `no_dpn`.
No `analysis_row` column — rejected lineages have no entry in the analysis NPZ.

**`data/exp/processed/meshes/rejected/{genotype}/{lobe}_{lineage_idx}.npz`**

Same format as kept mesh NPZs (all 3D vertex/face keys, centroids, and 2D
intermediate data). This allows full visualization of rejected lineages to
understand why they were filtered.

### Required update to EXP_PREPROCESSING

`pipeline.process_exp_lobe` must be extended to:
1. Call `process_exp_lineage` for rejected lineages too, saving mesh NPZs
   to `meshes/rejected/{genotype}/`.
2. Return rejected records (with `rejection_reason`) alongside kept records.

`scripts/preprocess_exp.py` must:
3. Write `rejected_lineage_index.csv` from collected rejected records.

---

## New files

```
src/npa/
    exp_viz.py                      ← new single-file module
scripts/
    visualize_exp_lineage.py        ← new CLI script
pyproject.toml                      ← add plotly dependency
```

---

## `src/npa/exp_viz.py`

Single module file — no subpackage. All rendering functions live here.

### Data loading

```python
def load_index(processed_dir: Path, rejected: bool) -> list[dict]:
    """
    Load lineage_index.csv (rejected=False) or rejected_lineage_index.csv (rejected=True).
    Returns list of row dicts.
    """

def load_mesh_npz(mesh_path: Path) -> dict:
    """
    Load a mesh NPZ and return numpy arrays keyed as stored.
    Caller accesses: lin_vertices, lin_faces, dpn_{i}_vertices/faces,
    pros_{j}_vertices/faces, dpn_centroids_2d, pros_centroids_2d, lin_poly_2d
    (µm coords for 2d-pre), dpn_centroids_2d_px, pros_centroids_2d_px,
    lin_poly_2d_px (pixel coords for 2d-post), and ds.
    """

def load_lineage_geo(analysis_npz: Path, analysis_row: int) -> np.ndarray:
    """
    Load geo slice (H, W, 2) for a single lineage from the stacked analysis NPZ.
    Uses analysis_row to index into geo array.
    Only called for kept lineages (rejected have no analysis_row).
    """
```

### Index table printing

```python
def print_index_table(rows: list[dict], rejected: bool) -> None:
    """
    Print a formatted table of all lineages in the index.
    Columns: row, lineage_id, genotype, lobe, lineage_idx, n_dpn, n_pros
    If rejected=True, append rejection_reason column.
    """
```

### 3D visualization — plotly, opens in browser

```python
def show_3d(mesh: dict, row: dict) -> None:
    """
    Render lineage hull, dpn meshes, and pros meshes as Mesh3d traces.

    Render order (for WebGL transparency):
      1. lineage hull  — HULL_COLOR, opacity=0.15
      2. dpn meshes    — DPN_COLOR, opacity=1.0, fully opaque (writes depth buffer)
      3. pros meshes   — PROS_COLOR, opacity=0.5, rendered last

    Each cell type is one legend group; only first trace in group shows in legend.
    Title: "{lineage_id} | {genotype} | {lobe} | lin_idx={lineage_idx} | dpn={n_dpn} pros={n_pros}"
    Scene aspectmode: "data".
    """
```

### 2D pre-Voronoi — matplotlib, shows hull + centroids

```python
def show_2d_pre(mesh: dict, row: dict) -> None:
    """
    Render the 2D projection before Voronoi tessellation.

    - Fill lin_poly_2d as a Shapely polygon with HULL_COLOR, alpha=0.2
    - Outline lin_poly_2d with HULL_COLOR, linewidth=1
    - Scatter dpn_centroids_2d as filled circles, DPN_COLOR, zorder=3
    - Scatter pros_centroids_2d as filled circles, PROS_COLOR, zorder=2
    - Equal aspect ratio. Axes labeled "PC1 (µm)" and "PC2 (µm)".
    - Title same format as show_3d.
    - Display with plt.show().
    """
```

### 2D post-Voronoi — matplotlib, shows geo array

```python
def show_2d_post(mesh: dict, geo: np.ndarray, row: dict) -> None:
    """
    Render the Voronoi-tessellated (H, W, 2) geo array.

    Build an RGB image:
      - background pixels (both channels 0): white
      - ch0==1 (dpn territory): DPN_COLOR
      - ch1==1 (pros territory): PROS_COLOR

    Overlay centroids using mesh["dpn_centroids_2d_px"] and
    mesh["pros_centroids_2d_px"] — pixel coordinates pre-computed at
    preprocessing time with the same ds used to build geo. Do not
    recompute from µm; do not hardcode ds.
    imshow with origin="upper". Equal aspect ratio.
    Title same format as show_3d.
    Display with plt.show().
    """
```

---

## `scripts/visualize_exp_lineage.py`

CLI entry point. No rendering logic — imports from `npa.exp_viz`.

### Interface

```
python scripts/visualize_exp_lineage.py --list [--rejected]

python scripts/visualize_exp_lineage.py (--row N | --id N) \
    [--view {3d,2d-pre,2d-post}] [--rejected]
```

`--view` defaults to `3d`. `--rejected` switches to the rejected lineage index.
`--id` matches against the integer `lineage_id` column (distinct from `--row`,
which is 0-based position in the printed table).

### Logic

```
1. Resolve processed_dir = data/exp/processed/ relative to repo root.
2. Load index via load_index(processed_dir, rejected=args.rejected).
3. If --list or no selection given: call print_index_table and exit.
4. Resolve selected row via --row (positional) or --id (search lineage_id column).
5. Load mesh NPZ via load_mesh_npz(row["mesh_path"]).
6. Dispatch on --view:
     3d      → show_3d(mesh, row)
     2d-pre  → show_2d_pre(mesh, row)
     2d-post → load analysis NPZ, call show_2d_post(mesh, geo, row)
               (only valid for kept lineages; raise clear error if --rejected)
```

---

## Dependency update

Add `plotly` to `pyproject.toml` dependencies. No other new dependencies —
matplotlib and numpy are already present.

---

## Validation checklist

- [ ] `--list` prints a readable table for both kept and rejected indexes
- [ ] `--row 0 --view 3d` opens browser with correct colors on first kept lineage
- [ ] `--row 0 --view 2d-pre` shows hull outline with dpn/pros centroids as points
- [ ] `--row 0 --view 2d-post` shows colored Voronoi grid with centroid dots overlaid
- [ ] `--rejected --row 0 --view 3d` visualizes a rejected lineage in 3D
- [ ] `--rejected --row 0 --view 2d-post` raises a clear error (no analysis data)
- [ ] Legend groups collapse correctly in plotly (one legend entry per cell type)
- [ ] Pros color is visually distinct from both dpn and hull in all three views
