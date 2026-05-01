# Experimental Data Preprocessing Plan

**Date:** 2026-04-21
**Goal:** Preprocess experimental WRL lineage files into two tiers of output:
- Per-lineage mesh NPZ files (heavy, visualization only)
- Per-genotype analysis NPZ files (lightweight, stacked, fast for downstream analysis)

Reference implementation: `~/bagherilab/neurogen-potts-analysis/src/` — use for logic,
but do not copy verbatim. Streamline and rename for experiment-specificity.

---

## Repository setup

### 1. Initialize Python environment

Create `pyproject.toml` at repo root:

```toml
[project]
name = "npa"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "numpy",
    "trimesh",
    "shapely",
    "scipy",
    "matplotlib",
    "pandas",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/npa"]
```

Run `uv venv` and `uv pip install -e .` from the repo root.

### 2. Create package skeleton

```
src/npa/
    __init__.py
    exp_preprocessing/
        __init__.py
        wrl_io.py
        lineage_filter.py
        geometry.py
        pipeline.py
scripts/
    preprocess_exp.py
```

---

## Output file specs

### Mesh NPZ (per lineage, viz only)

Path: `data/exp/processed/meshes/{genotype}/{lobe}_{lineage_idx}.npz`

| Key | Shape | dtype | Description |
|---|---|---|---|
| `lin_vertices` | (M, 3) | float32 | Lineage hull vertices |
| `lin_faces` | (F, 3) | int32 | Lineage hull faces |
| `dpn_{i}_vertices` | (V, 3) | float32 | Vertices for dpn cell i |
| `dpn_{i}_faces` | (G, 3) | int32 | Faces for dpn cell i |
| `pros_{j}_vertices` | (V, 3) | float32 | Vertices for pros cell j |
| `pros_{j}_faces` | (G, 3) | int32 | Faces for pros cell j |
| `dpn_centroids_3d` | (n_dpn, 3) | float32 | 3D centroids for all dpn cells |
| `pros_centroids_3d` | (n_pros, 3) | float32 | 3D centroids for all pros cells |
| `lin_poly_2d` | (P, 2) | float32 | Projected lineage hull polygon vertices |
| `dpn_centroids_2d` | (n_dpn, 2) | float32 | Projected dpn centroids in µm |
| `pros_centroids_2d` | (n_pros, 2) | float32 | Projected pros centroids in µm |
| `dpn_centroids_2d_px` | (n_dpn, 2) | float32 | Dpn centroids in canvas pixel coords |
| `pros_centroids_2d_px` | (n_pros, 2) | float32 | Pros centroids in canvas pixel coords |
| `lin_poly_2d_px` | (P, 2) | float32 | Hull polygon vertices in canvas pixel coords |
| `ds` | scalar | float32 | µm/pixel resolution used for this lineage's Voronoi |
| `pca_mean` | (3,) | float32 | PCA plane origin |
| `pca_e1` | (3,) | float32 | First principal axis |
| `pca_e2` | (3,) | float32 | Second principal axis |

### Analysis NPZ (per genotype, stacked)

Path: `data/exp/processed/analysis/{genotype}.npz`

| Key | Shape | dtype | Description |
|---|---|---|---|
| `geo` | (N, H, W, 2) | float32 | ch0=dpn Voronoi, ch1=pros Voronoi |
| `counts` | (N, 3) | float32 | [n_dpn, n_pros, dpn_voxel_sum] per lineage |
| `lineage_ids` | (N,) | int32 | Links rows to lineage_index.csv |
| `ds` | scalar | float32 | µm/pixel resolution (0.3) |

### Lineage index CSV

Path: `data/exp/processed/lineage_index.csv`

Columns: `lineage_id, genotype, lobe, lineage_idx, n_dpn, n_pros, mesh_path, analysis_row`

One row per accepted lineage across all genotypes. `analysis_row` is the row index
into that genotype's analysis NPZ. `mesh_path` is relative to repo root.

---

## Module implementations

### `src/npa/exp_preprocessing/wrl_io.py`

Parses VRML 2.0 files. No other responsibilities.

**Functions:**

```python
def load_vrml_meshes(path: Path) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Parse a WRL file and return a list of (vertices, faces) pairs.
    vertices: (M, 3) float32, faces: (F, 3) int32.
    Uses regex to extract Coordinate point blocks and coordIndex blocks.
    Handles fan triangulation (polygon faces with more than 3 vertices).
    """

def to_trimesh_list(meshes: list[tuple[np.ndarray, np.ndarray]]) -> list[trimesh.Trimesh]:
    """Convert (vertices, faces) pairs to trimesh.Trimesh objects."""
```

Regex patterns (carry over from reference implementation):
- Vertices: `r"Coordinate\s*\{[^}]*?point\s*\[([^\]]*)\]"`
- Faces: `r"coordIndex\s*\[([^\]]*)\]"`
- Values: `r"[-+]?\d*\.\d+|[-+]?\d+"`

---

### `src/npa/exp_preprocessing/lineage_filter.py`

Loads a lobe's three WRL files, assigns cells to lineages, and filters to valid lineages.

**Dataclasses:**

```python
@dataclass(frozen=True)
class ExpFilteredLineage:
    lineage_idx: int
    lineage_mesh: trimesh.Trimesh
    dpn_meshes: list[trimesh.Trimesh]   # assigned dpn cells
    pros_meshes: list[trimesh.Trimesh]  # assigned pros cells

@dataclass(frozen=True)
class ExpFilteredLobe:
    genotype: str
    lobe: str
    kept: list[ExpFilteredLineage]
    n_rejected_disconnected: int
    n_rejected_no_dpn: int
```

**Functions:**

```python
def load_exp_filtered_lobe(
    lineage_wrl: Path,
    pros_wrl: Path,
    dpn_wrl: Path,
    genotype: str,
    lobe: str,
) -> ExpFilteredLobe:
    """
    1. Parse all three WRL files via wrl_io.load_vrml_meshes + to_trimesh_list.
    2. Assign pros cells to lineages using the reference vertex-in-bounding-box
       rule: for each Pros cell, count the fraction of its vertices inside each
       lineage bounding box and assign to the best lineage if that fraction is
       >= 0.95. Reference: assign_cells_to_lineages_strict.
    3. Assign dpn cells to lineages using ray-cast containment
       (min_fraction=0.60, n_sample=20). Reference: assign_cells_to_lineages_by_containment.
    4. Reject lineages that are disconnected (reference: lineage_is_connected,
       min_faces=50, max_secondary_volume=5.0).
    5. Reject lineages with zero assigned dpn cells.
    6. Return ExpFilteredLobe with kept lineages and rejection counts.
    """
```

Cell assignment logic (carry over from reference, inline into this module — no need
for a separate helpers file):
- Pros vertex-in-bounding-box assignment: for each Pros cell, count the
  fraction of cell vertices inside each lineage bounding box
- Ray-cast containment: sample n_sample vertices per cell, cast rays, count inside
  fraction using trimesh.ray

---

### `src/npa/exp_preprocessing/geometry.py`

Pure geometric operations. No I/O, no trimesh dependencies — operates on numpy arrays only.
May be promoted to a shared top-level module when sim preprocessing is built.

**Functions:**

```python
def pca_axes(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute PCA axes of a (M, 3) vertex array via SVD.
    Returns (mean, e1, e2): mean shape (3,), e1/e2 shape (3,) unit vectors.
    e1 is the axis of greatest variance, e2 second greatest.
    """

def project_2d(
    vertices: np.ndarray,
    mean: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
) -> np.ndarray:
    """
    Project (M, 3) vertices onto the (e1, e2) plane.
    Returns (M, 2) float32 array of (u, v) coordinates.
    u = dot(vertex - mean, e1), v = dot(vertex - mean, e2).
    """

def hull_polygon(pts_2d: np.ndarray, buffer_px: float) -> shapely.Polygon:
    """
    Compute convex hull of (M, 2) projected points and apply a buffer.
    Returns a Shapely Polygon.
    """

def voronoi_rasterize(
    lin_poly: shapely.Polygon,
    dpn_centroids_2d: np.ndarray,
    pros_centroids_2d: np.ndarray,
    canvas_size: int,
    ds: float,
) -> np.ndarray:
    """
    Rasterize the lineage polygon and assign each pixel to nearest cell centroid.

    Steps:
    1. Compute pixel grid covering lin_poly bounding box at resolution ds µm/pixel.
    2. For each pixel inside lin_poly, find nearest centroid via scipy KDTree.
    3. Assign pixel to dpn channel (ch0) if nearest centroid is dpn, pros (ch1) otherwise.
    4. Pad/center the result onto a (canvas_size, canvas_size) canvas.

    Returns (canvas_size, canvas_size, 2) float32 array.
    canvas_size default: 200. ds default: 0.3.
    """
```

---

### `src/npa/exp_preprocessing/pipeline.py`

Orchestrates the above modules into file-producing operations.

**Functions:**

```python
def process_exp_lineage(
    lineage: ExpFilteredLineage,
    mesh_out: Path,
    ds: float = 0.3,
    canvas_size: int = 200,
) -> dict:
    """
    Process one lineage end-to-end:
    1. Compute PCA axes from lineage hull vertices.
    2. Project lineage hull and all cell vertices to 2D.
    3. Compute hull_polygon from projected lineage vertices.
    4. Compute dpn_centroids_2d and pros_centroids_2d (mean of projected cell vertices).
    5. Run voronoi_rasterize to produce (canvas_size, canvas_size, 2) geo.
    6. Compute dpn_centroids_3d and pros_centroids_3d (mean of 3D cell vertices).
    7. Compute pixel coordinates: apply the same canvas offset used in voronoi_rasterize
       to convert dpn_centroids_2d, pros_centroids_2d, and lin_poly_2d from µm into
       canvas pixel coords. Store as dpn_centroids_2d_px, pros_centroids_2d_px, lin_poly_2d_px.
    8. Save mesh NPZ to mesh_out (all 3D mesh data + 2D µm data + 2D pixel data + ds + PCA metadata).
    9. Return analysis dict: {geo, counts, lineage_id}.
    """

def process_exp_lobe(
    lineage_wrl: Path,
    pros_wrl: Path,
    dpn_wrl: Path,
    genotype: str,
    lobe: str,
    mesh_dir: Path,
    ds: float = 0.3,
    canvas_size: int = 200,
) -> list[dict]:
    """
    1. Call load_exp_filtered_lobe.
    2. For each kept lineage, call process_exp_lineage.
    3. Return list of analysis dicts (one per kept lineage) with genotype/lobe metadata.
    """

def stack_exp_analysis_npz(
    records: list[dict],
    out_path: Path,
    ds: float = 0.3,
) -> None:
    """
    Stack per-lineage analysis dicts into a single NPZ file.
    geo: (N, H, W, 2), counts: (N, 3), lineage_ids: (N,).
    """
```

---

### `scripts/preprocess_exp.py`

CLI entry point. Discovers WRL triplets, runs preprocessing, writes outputs.

**Interface:**

```
python scripts/preprocess_exp.py [--genotypes control mud nanobody] [--lobes lobe1 lobe2]
```

**Logic:**

1. Discover WRL triplets: for each genotype dir under `data/exp/wrl_files/`, find
   all `lobe{N}_{genotype}_lineages.wrl` and pair with matching `_dpn.wrl` and
   `_pros.wrl` files.
2. If `--genotypes` or `--lobes` supplied, filter to matching subset.
3. Create output dirs:
   - `data/exp/processed/meshes/{genotype}/`
   - `data/exp/processed/analysis/`
4. For each lobe, call `process_exp_lobe`. Print per-lobe summary
   (n kept, n rejected disconnected, n rejected no dpn).
5. After all lobes processed per genotype, call `stack_exp_analysis_npz`.
6. Collect all records and write `data/exp/processed/lineage_index.csv`.

---

## Validation checklist

After running `scripts/preprocess_exp.py` on all genotypes, verify:

- [ ] `lineage_index.csv` has one row per kept lineage with no duplicate `lineage_id`
- [ ] Every mesh path in `lineage_index.csv` points to an existing file
- [ ] Each `{genotype}.npz` has `geo.shape[0]` equal to the number of rows for that
      genotype in `lineage_index.csv`
- [ ] `geo` values are in {0.0, 1.0} — binary Voronoi masks
- [ ] `counts[:, 0]` (n_dpn) matches lineage_index `n_dpn` column for all rows
- [ ] No lineage has n_dpn == 0 (should have been filtered)
- [ ] Spot-check one mesh NPZ: load and confirm `lin_vertices` is float32 (M, 3)
      and `dpn_centroids_2d` has the right number of rows
