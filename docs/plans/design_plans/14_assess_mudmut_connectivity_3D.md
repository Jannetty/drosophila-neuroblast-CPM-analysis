# 14 — Assess NB connectivity in mudmut experimental lineages

## Goal

Compute the proportion of mudmut experimental lineages in which all neuroblasts (NBs)
are mutually in contact (i.e., form a single connected component), and compare that
fraction against the simulation results already shown in Figure 5 Panel E.

---

## Background and motivation

Figure 5 Panel E shows the fraction of *simulation* runs where all NBs are connected,
broken down by adhesion strength (J=50/40/20) and relative-rotation mode. We have no
corresponding number for the experimental mudmut lineages. Adding that number would let
us situate the biological observation within the simulation parameter space.

The existing `nb_connectivity` in `src/npa/metrics.py` works on the 2D pixel maps
produced by the simulation renderer. Experimental lineages are stored as 3D triangle
meshes (one mesh per cell, in `data/exp/processed/meshes/mudmut/*.npz`). A new
mesh-based connectivity check is needed.

---

## Data

- **Index**: `data/exp/processed/lineage_index.csv` — one row per lineage, columns
  `lineage_id`, `genotype`, `n_dpn`, `mesh_path`.
- **Meshes**: each `.npz` contains `dpn_{i}_vertices` (shape N×3, µm) and
  `dpn_{i}_faces` (shape M×3, int) for `i` in `0..n_dpn-1`, plus `dpn_volumes_um3`.
- **Scope**: mudmut only (`genotype == "mudmut"`); 59 lineages; `n_dpn` = 1–4.

Lineages with `n_dpn == 1` are trivially connected (one NB); flag them as
`nb_connected = True`, `nb_n_components = 1`.

---

## Algorithm — pairwise mesh-distance graph

For each lineage with `n_dpn ≥ 2`:

1. Load each NB mesh as a `trimesh.Trimesh` object.
2. For every pair `(i, j)`, compute the minimum surface-to-surface distance using
   `trimesh.proximity.closest_point` (or `trimesh.nearest.vertex_to_mesh_distance`).
   Two NBs are **adjacent** if `min_dist ≤ contact_threshold_um`.
3. Build an undirected graph over the `n_dpn` nodes with edges between adjacent pairs.
4. The lineage is **connected** (`nb_connected = True`) if the graph has exactly one
   connected component.

**Contact threshold**: `contact_threshold_um = 1.0 µm`. This is roughly one-third of
a voxel at ds=0.3 (voxel edge ≈ 3.3 µm) and is conservative — meshes are already
smoothed, so two touching cells will have surfaces within <1 µm of each other.
Store the threshold as a named constant so it can be revisited.

If trimesh minimum-distance turns out to be too slow (59 × up to 6 pairs each, all
small meshes — unlikely), fall back to centroid distance ≤
`sum_of_radii_estimate + contact_threshold_um` as a pre-filter before the full
surface query.

---

## Implementation

### 1. New function in `src/npa/metrics.py`

```python
def exp_nb_connectivity(mesh: dict, contact_threshold_um: float = 1.0) -> dict:
    """
    Connected-component analysis of NB cells in one experimental lineage.

    Parameters
    ----------
    mesh : dict
        Contents of the lineage .npz (keys dpn_0_vertices, dpn_0_faces, ...).
    contact_threshold_um : float
        Max surface-to-surface distance (µm) to count two NBs as adjacent.

    Returns
    -------
    dict with keys:
        nb_connected      : bool
        nb_n_components   : int
        nb_n_dpn          : int
    """
```

Import trimesh at the top of the function (not at module level) to avoid adding a
hard dependency to every importer of `metrics.py`.

### 2. New script `scripts/extract_exp_nb_connectivity.py`

- Reads `lineage_index.csv`, filters `genotype == "mudmut"`.
- Loads each mesh `.npz`, calls `exp_nb_connectivity`.
- Writes `data/exp/processed/exp_nb_connectivity.csv` with columns:
  `lineage_id`, `genotype`, `n_dpn`, `nb_connected`, `nb_n_components`.
- CLI: `uv run python scripts/extract_exp_nb_connectivity.py --proc-dir data/exp/processed`

### 3. Analysis in `docs/tex_draft/figure5_paper_figures.ipynb`

Add a new panel or standalone cell after Panel E that reports:

- **Overall fraction** of mudmut lineages with `nb_connected = True` (single number
  with 95% Wilson confidence interval).
- **Breakdown by `n_dpn`** (n_dpn=1 is always connected; n_dpn=2,3 are the
  interesting cases) as a small bar chart or table.
- Overlay the experimental fraction on the existing Panel E heatmap as a horizontal
  dashed reference line (or annotate in the figure caption if layout is too tight).

---

## Tests

Add to `tests/test_metrics.py`:

- `test_exp_nb_connectivity_single_nb`: one-cell lineage → `nb_connected=True`,
  `nb_n_components=1`.
- `test_exp_nb_connectivity_touching`: two tiny cubes whose surfaces are 0 µm apart
  → connected.
- `test_exp_nb_connectivity_separated`: two cubes whose surfaces are 5 µm apart →
  not connected.
- `test_exp_nb_connectivity_chain`: three cubes where A touches B and B touches C
  but A does not touch C → still connected (one component).

Use synthetic `trimesh.creation.box()` meshes rather than real lineage data.

---

## Output files

| File | Description |
|------|-------------|
| `data/exp/processed/exp_nb_connectivity.csv` | Per-lineage connectivity flags |

Columns: `lineage_id`, `genotype`, `n_dpn`, `nb_connected`, `nb_n_components`

---

## What this does NOT change

- `lineage_index.csv`, `metrics.csv`, `exp_summary.csv` — unchanged.
- The existing `nb_connectivity` function for simulation pixel maps — unchanged.
- Figure 5 Panels A–F outputs — the new panel/cell is additive.

---

## Open questions

1. Should the experimental connectivity fraction also be added to `exp_summary.csv`
   as a new aggregate column, or kept separate? (Separate CSV is cleaner for now.)
2. Is `contact_threshold_um = 1.0 µm` the right cutoff? Worth spot-checking two or
   three borderline lineages visually in the exp centroid viewer before locking in.
3. Should wt lineages also be run (they always have `n_dpn = 1`, so 100% connected —
   uninteresting, but could serve as a sanity check)?
