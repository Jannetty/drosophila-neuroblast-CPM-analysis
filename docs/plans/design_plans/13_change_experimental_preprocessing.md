# Sphere-Weighted Experimental Preprocessing Plan

**Date:** 2026-05-10
**Goal:** Replace the standard Voronoi rasterizer with a sphere-weighted rasterizer
that uses each cell's 3D volume to estimate a 2D circle radius, then tessellates
outward from circle edges at equal speed — giving NBs (Dpn+) more territory in
proportion to their actual volume.

---

## Motivation

Standard (unweighted) Voronoi bisects exactly halfway between any two seed points
regardless of cell size. This systematically underestimates NB territory because NBs
are much larger than GMCs/neurons but the halfway rule treats them equally. The new
approach:

1. Converts 3D mesh volume → sphere radius → 2D circle (isotropic approximation)
2. Resolves circle overlaps with NB priority
3. Tessellates remaining hull pixels using an **additively weighted Voronoi**: each
   pixel outside all circles is assigned to the cell whose circle edge is nearest,
   i.e. argmin_i (||p − c_i|| − r_i). Larger circles have smaller weighted distances
   and claim proportionally more territory.

This is also called an **Apollonius diagram** or **offset Voronoi**.

---

## Mathematical formulation

For cell *i* with 3D mesh volume V_i µm³:

```
r_i (µm)  = (3 * V_i / (4π))^(1/3)      # sphere radius
r_i (px)  = r_i / ds                      # radius in canvas pixels
d_w(p, i) = ||p − c_i|| − r_i (px)       # additive weighted distance (negative inside circle)
```

**Pixel assignment rule (in priority order):**

1. If p is inside ≥1 NB (Dpn) circle — assign to the NB with minimum `||p − c_NB||`
   (i.e. closest NB center; breaks NB–NB overlap equidistantly)
2. Else if p is inside ≥1 non-NB (Pros) circle — assign to the Pros with minimum
   `||p − c_Pros||`
3. Else — assign to cell with minimum `d_w(p, i)` across all cells
   (additively weighted Voronoi; NB circles expand proportionally further)
4. Apply hull mask: pixels outside the lineage polygon stay 0

Cells with no meshes (n_dpn = 0 or n_pros = 0) are handled gracefully: skip the
absent type in all distance computations and assign its channel to all-zero.

---

## Files changed

| File | Change |
|---|---|
| `src/npa/exp_preprocessing/geometry.py` | Add `sphere_voronoi_rasterize`; keep `voronoi_rasterize` for existing tests then remove once tests are ported |
| `src/npa/exp_preprocessing/pipeline.py` | Add `_cell_volumes_um3`; pass volumes to `sphere_voronoi_rasterize`; save `dpn_volumes_um3`/`pros_volumes_um3` to mesh NPZ |
| `src/npa/exp_viz.py` | Update `show_2d_pre` to draw sphere circles at centroids |
| `tests/test_exp_preprocessing.py` | Port `voronoi_rasterize` tests to `sphere_voronoi_rasterize`; add overlap priority tests |
| `docs/PIPELINE.md` | Update rasterization description |

---

## Module implementations

### `src/npa/exp_preprocessing/geometry.py`

Add a new function alongside the existing ones. Do not remove `voronoi_rasterize`
until tests are ported.

```python
def sphere_voronoi_rasterize(
    lin_poly: Polygon,
    dpn_centroids_2d: np.ndarray,   # (n_dpn, 2) µm
    pros_centroids_2d: np.ndarray,  # (n_pros, 2) µm
    dpn_volumes_um3: np.ndarray,    # (n_dpn,) µm³
    pros_volumes_um3: np.ndarray,   # (n_pros,) µm³
    canvas_size: int,
    ds: float,
) -> np.ndarray:
    """
    Rasterize lineage polygon using additively weighted Voronoi seeded by
    sphere radii derived from 3D cell volumes. NB (Dpn) circles take priority
    over non-NB (Pros) circles; remaining hull pixels expand from circle edges
    at equal rate (larger radii claim more territory).

    Returns (canvas_size, canvas_size, 2) float32: ch0=Dpn, ch1=Pros territory.
    """
    xmin, ymin, nx, ny, row0, col0 = canvas_frame_from_polygon(lin_poly, canvas_size, ds)

    # --- pixel grid (µm coords) ---
    gy = ymin + (np.arange(ny, dtype=np.float64) + 0.5) * ds  # (ny,)
    gx = xmin + (np.arange(nx, dtype=np.float64) + 0.5) * ds  # (nx,)
    GY, GX = np.meshgrid(gy, gx, indexing="ij")               # (ny, nx) each

    # --- sphere radii in px ---
    def _radii_px(vols: np.ndarray) -> np.ndarray:
        vols = np.asarray(vols, dtype=np.float64).ravel()
        r_um = (3.0 * vols / (4.0 * np.pi)) ** (1.0 / 3.0)
        return r_um / ds  # convert µm → pixels

    # --- additive weighted distance field for one cell type ---
    def _aw_dist(centroids: np.ndarray, radii_px: np.ndarray) -> np.ndarray:
        # Returns shape (n_cells, ny, nx); negative inside circle
        centroids = np.asarray(centroids, dtype=np.float64).reshape(-1, 2)
        out = []
        for (cx, cy), r in zip(centroids, radii_px):
            d = np.sqrt((GY - cy) ** 2 + (GX - cx) ** 2) - r
            out.append(d)
        return np.stack(out, axis=0)  # (n, ny, nx)

    dpn_c  = np.asarray(dpn_centroids_2d,  dtype=np.float64).reshape(-1, 2)
    pros_c = np.asarray(pros_centroids_2d, dtype=np.float64).reshape(-1, 2)
    n_dpn  = len(dpn_c)
    n_pros = len(pros_c)

    # Compute per-type distance fields (only if cells exist)
    if n_dpn:
        dpn_r    = _radii_px(dpn_volumes_um3)
        dpn_dw   = _aw_dist(dpn_c, dpn_r)          # (n_dpn, ny, nx)
        inside_dpn   = dpn_dw.min(axis=0) < 0       # (ny, nx)
        nearest_dpn  = dpn_dw.argmin(axis=0)        # which NB is closest center
    else:
        inside_dpn  = np.zeros((ny, nx), dtype=bool)
        nearest_dpn = np.zeros((ny, nx), dtype=np.intp)

    if n_pros:
        pros_r    = _radii_px(pros_volumes_um3)
        pros_dw   = _aw_dist(pros_c, pros_r)        # (n_pros, ny, nx)
        inside_pros  = pros_dw.min(axis=0) < 0
        nearest_pros = pros_dw.argmin(axis=0)
    else:
        inside_pros  = np.zeros((ny, nx), dtype=bool)
        nearest_pros = np.zeros((ny, nx), dtype=np.intp)

    # Global additive weighted Voronoi (used outside all circles)
    if n_dpn and n_pros:
        all_dw = np.concatenate([dpn_dw, pros_dw], axis=0)  # (n_dpn+n_pros, ny, nx)
        global_nearest_is_dpn = all_dw.argmin(axis=0) < n_dpn
    elif n_dpn:
        global_nearest_is_dpn = np.ones((ny, nx), dtype=bool)
    else:
        global_nearest_is_dpn = np.zeros((ny, nx), dtype=bool)

    # --- priority assignment ---
    # Start with global weighted Voronoi result
    is_dpn_px = global_nearest_is_dpn.copy()
    # Override: pixels inside NB circles → NB wins
    is_dpn_px[inside_dpn] = True
    # Override: pixels inside only Pros circles → Pros wins
    is_dpn_px[inside_pros & ~inside_dpn] = False

    # --- hull mask ---
    prepared = prep(lin_poly)
    points = np.column_stack([GX.ravel(), GY.ravel()])
    hull_mask = np.fromiter(
        (prepared.contains(Point(float(x), float(y))) for x, y in points),
        dtype=bool,
        count=len(points),
    ).reshape(ny, nx)

    dpn_mask  = (is_dpn_px  & hull_mask).astype(np.float32)
    pros_mask = (~is_dpn_px & hull_mask).astype(np.float32)

    if not hull_mask.any():
        raise ValueError("lineage polygon did not cover any raster pixels")

    geo = np.zeros((canvas_size, canvas_size, 2), dtype=np.float32)
    geo[row0 : row0 + ny, col0 : col0 + nx, 0] = dpn_mask
    geo[row0 : row0 + ny, col0 : col0 + nx, 1] = pros_mask
    return geo
```

After tests pass, remove the old `voronoi_rasterize` and its `_centroid_stack` helper
(no longer used).

---

### `src/npa/exp_preprocessing/pipeline.py`

**Add volume extractor:**

```python
def _cell_volumes_um3(meshes: list[trimesh.Trimesh]) -> np.ndarray:
    """Return absolute mesh volumes (µm³) for each cell. Uses abs() to handle
    inverted-normal meshes where trimesh.volume is negative."""
    if not meshes:
        return np.empty((0,), dtype=np.float32)
    return np.asarray([abs(float(m.volume)) for m in meshes], dtype=np.float32)
```

**Update imports at top of file:**

Replace `voronoi_rasterize` with `sphere_voronoi_rasterize`:

```python
from npa.exp_preprocessing.geometry import (
    canvas_frame_from_polygon,
    hull_polygon,
    pca_axes,
    project_2d,
    sphere_voronoi_rasterize,
)
```

**Update `process_exp_lineage`:**

After the existing centroid computations (lines ~91–94), add volume extraction:

```python
dpn_volumes_um3  = _cell_volumes_um3(lineage.dpn_meshes)
pros_volumes_um3 = _cell_volumes_um3(lineage.pros_meshes)
```

Replace the `voronoi_rasterize` call:

```python
geo = sphere_voronoi_rasterize(
    lin_poly,
    dpn_centroids_2d,
    pros_centroids_2d,
    dpn_volumes_um3,
    pros_volumes_um3,
    canvas_size=canvas_size,
    ds=ds,
)
```

Add to `np.savez_compressed` call:

```python
dpn_volumes_um3=dpn_volumes_um3,
pros_volumes_um3=pros_volumes_um3,
```

The `counts` array format is unchanged — `counts[2]` remains the Dpn pixel count
(now reflects sphere-weighted territory rather than plain Voronoi territory).

---

## Mesh NPZ format change

Two new keys added:

| Key | Shape | dtype | Description |
|---|---|---|---|
| `dpn_volumes_um3` | (n_dpn,) | float32 | 3D mesh volume per Dpn cell |
| `pros_volumes_um3` | (n_pros,) | float32 | 3D mesh volume per Pros cell |

All existing keys are unchanged.

---

### `src/npa/exp_viz.py` — `show_2d_pre`

Draw sphere circles at centroid positions so the pre-Voronoi view shows the
initial radii rather than bare points.

Replace the centroid scatter calls in `show_2d_pre` with:

```python
from matplotlib.patches import Circle as MplCircle

def _sphere_radius_um(volume_um3: float) -> float:
    return (3.0 * volume_um3 / (4.0 * np.pi)) ** (1.0 / 3.0)

# In show_2d_pre, after loading mesh:
dpn_vols  = mesh.get("dpn_volumes_um3",  np.zeros(len(mesh["dpn_centroids_2d"])))
pros_vols = mesh.get("pros_volumes_um3", np.zeros(len(mesh["pros_centroids_2d"])))

for (cx, cy), vol in zip(mesh["dpn_centroids_2d"], dpn_vols):
    r = _sphere_radius_um(float(vol))
    ax.add_patch(MplCircle((cx, cy), r, color=DPN_COLOR, fill=True, alpha=0.4, zorder=3))
    ax.add_patch(MplCircle((cx, cy), r, color=DPN_COLOR, fill=False, linewidth=0.8, zorder=3))

for (cx, cy), vol in zip(mesh["pros_centroids_2d"], pros_vols):
    r = _sphere_radius_um(float(vol))
    ax.add_patch(MplCircle((cx, cy), r, color=PROS_COLOR, fill=True, alpha=0.3, zorder=2))
    ax.add_patch(MplCircle((cx, cy), r, color=PROS_COLOR, fill=False, linewidth=0.8, zorder=2))
```

Use `.get(..., fallback)` so old mesh NPZs (without volume keys) still render
with zero-radius dots.

---

## Tests — `tests/test_exp_preprocessing.py`

### Port existing test

Replace the `voronoi_rasterize` test with a `sphere_voronoi_rasterize` test.
Give both cells identical volumes (e.g. 10.0 µm³) so the sphere radii are equal
and the result should be nearly identical to the old plain Voronoi (boundary at
midpoint):

```python
from npa.exp_preprocessing.geometry import sphere_voronoi_rasterize

def test_sphere_voronoi_rasterize_basic():
    vertices = np.array(
        [[0,0,0],[4,0,0],[4,4,0],[0,4,0],[2,2,1]], dtype=np.float32
    )
    mean, e1, e2 = pca_axes(vertices)
    pts_2d = project_2d(vertices, mean, e1, e2)
    poly = hull_polygon(pts_2d, buffer_px=0.0)

    geo = sphere_voronoi_rasterize(
        poly,
        dpn_centroids_2d=np.array([[-1.0, 0.0]], dtype=np.float32),
        pros_centroids_2d=np.array([[1.0, 0.0]], dtype=np.float32),
        dpn_volumes_um3=np.array([10.0], dtype=np.float32),
        pros_volumes_um3=np.array([10.0], dtype=np.float32),
        canvas_size=20,
        ds=0.5,
    )

    assert geo.shape == (20, 20, 2)
    assert geo.dtype == np.float32
    # No pixel is claimed by both channels
    assert np.logical_and(geo[..., 0] > 0, geo[..., 1] > 0).sum() == 0
    assert geo.sum() > 0
```

### Add NB priority test

NB circle should take pixels even when Pros centroid is geometrically closer:

```python
def test_sphere_voronoi_nb_priority():
    """Pixel inside NB circle goes to NB even if Pros centroid is closer."""
    from shapely.geometry import box as shapely_box

    # 20x20 µm square polygon
    poly = shapely_box(0, 0, 10, 10)

    # NB at (5, 5) with large volume → radius ≈ 3.6 µm
    # Pros at (5.1, 5) — centroid barely 0.1 µm away from NB center
    # The pixel at (5, 5) is inside the NB circle; Pros circle is tiny (vol=1 µm³ → r≈0.62 µm)
    geo = sphere_voronoi_rasterize(
        poly,
        dpn_centroids_2d=np.array([[5.0, 5.0]], dtype=np.float32),
        pros_centroids_2d=np.array([[5.1, 5.0]], dtype=np.float32),
        dpn_volumes_um3=np.array([200.0], dtype=np.float32),
        pros_volumes_um3=np.array([1.0], dtype=np.float32),
        canvas_size=40,
        ds=0.25,
    )

    # Pixel at canvas center should be Dpn (inside NB circle), not Pros
    center_row = 40 // 2
    center_col = 40 // 2
    assert geo[center_row, center_col, 0] == 1.0, "center pixel must be NB territory"
    assert geo[center_row, center_col, 1] == 0.0
```

### Add larger-cell-gets-more-territory test

```python
def test_sphere_voronoi_larger_cell_claims_more():
    """NB with larger volume claims a larger fraction of hull pixels."""
    from shapely.geometry import box as shapely_box

    poly = shapely_box(0, 0, 10, 10)

    # Both cells at x-symmetry axis; NB has 8× the volume of Pros
    geo = sphere_voronoi_rasterize(
        poly,
        dpn_centroids_2d=np.array([[2.5, 5.0]], dtype=np.float32),
        pros_centroids_2d=np.array([[7.5, 5.0]], dtype=np.float32),
        dpn_volumes_um3=np.array([800.0], dtype=np.float32),
        pros_volumes_um3=np.array([100.0], dtype=np.float32),
        canvas_size=40,
        ds=0.25,
    )

    dpn_pixels  = geo[..., 0].sum()
    pros_pixels = geo[..., 1].sum()
    assert dpn_pixels > pros_pixels, "larger NB volume → more territory"
```

### Add canvas-exceeded error test (unchanged logic)

```python
def test_sphere_voronoi_canvas_exceeded():
    from shapely.geometry import box as shapely_box
    with pytest.raises(ValueError, match="exceeds canvas"):
        sphere_voronoi_rasterize(
            shapely_box(0, 0, 10, 10),
            dpn_centroids_2d=np.array([[1.0, 1.0]], dtype=np.float32),
            pros_centroids_2d=np.empty((0, 2), dtype=np.float32),
            dpn_volumes_um3=np.array([1.0], dtype=np.float32),
            pros_volumes_um3=np.empty((0,), dtype=np.float32),
            canvas_size=4,
            ds=1.0,
        )
```

---

## PIPELINE.md update

Update the description of the rasterization step:

> **Rasterization (sphere-weighted Voronoi):** Each cell's 3D mesh volume is used
> to estimate a 2D circle radius via the sphere assumption
> `r = (3V / 4π)^(1/3)`. Pixels inside any NB circle are assigned to the nearest
> NB center (NB–NB boundary splits equidistantly). Pixels inside only Pros circles
> are assigned to the nearest Pros center. Remaining hull pixels are assigned by
> additively weighted Voronoi: argmin_i (||p − c_i|| − r_i), which gives cells with
> larger radii proportionally more territory. The lineage convex hull remains the
> outer boundary.

---

## Re-run preprocessor

After implementing, re-run on all genotypes:

```bash
uv run python scripts/preprocess_exp.py
```

The new NPZs will have the two extra volume keys and updated `geo` arrays. All
downstream metric and figure scripts read `geo` with the same (N, H, W, 2) shape
and float32 dtype — no downstream changes needed.

---

## Validation checklist

- [ ] All three new tests pass: basic shape/dtype, NB priority, larger-volume→more-territory
- [ ] `voronoi_rasterize` test removed; no remaining import of `voronoi_rasterize` in tests
- [ ] `scripts/preprocess_exp.py` runs to completion on all genotypes without error
- [ ] `data/exp/processed/analysis/wt.npz`: `geo.shape` is `(N, 200, 200, 2)`; values in {0, 1}
- [ ] Spot-check: load one mesh NPZ and confirm `dpn_volumes_um3.shape[0]` matches `n_dpn`
- [ ] `show_2d_pre` for a WT lineage shows circles proportional to cell size, with NB visibly larger than Pros circles
- [ ] `show_2d_post` shows NB territory noticeably larger than under old Voronoi
- [ ] Composition panel figures (fig2) re-rendered and visually reasonable after re-running `make fig2`
