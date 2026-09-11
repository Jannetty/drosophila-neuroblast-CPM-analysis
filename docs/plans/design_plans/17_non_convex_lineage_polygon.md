# Non-Convex Lineage Polygon Plan

**Date:** 2026-05-13
**Goal:** Replace the convex hull lineage boundary with a projected-mesh-triangle-union
polygon that is connected but non-convex, to more faithfully represent each lineage's
actual projected silhouette.

---

## Motivation

The current `hull_polygon` function wraps the projected 2D vertices of the lineage mesh
in a convex hull (`MultiPoint(pts_2d).convex_hull`). This overfills concave regions:
pixels in the concave pockets of the hull are claimed as "inside" the lineage even
though the actual mesh does not occupy that space. A non-convex polygon derived from
the actual mesh triangles will produce a tighter, more biologically meaningful boundary
and may change how much territory each cell type is assigned near the lineage edge.

---

## Approach

Project the 3D lineage mesh faces (triangles) to 2D using the same PCA basis already
computed, then take `shapely.ops.unary_union` over all triangle polygons. Apply the
same `ds * 0.5` buffer already used in the convex-hull path to fill micro-gaps
between adjacent triangles. The result is a connected, non-convex `Polygon`.

If the union is not a `Polygon` (e.g. a `MultiPolygon` from a mesh with a very thin
neck projecting to disconnected pieces), fall back to the convex hull of the union
and record a warning — same fallback `hull_polygon` already uses.

The convex hull remains the default. A `--no-convex-hull` flag on `preprocess_exp.py`
enables the mesh-union path. This lets both output sets exist side by side for
comparison.

---

## Files changed

| File | Change |
|---|---|
| `src/npa/exp_preprocessing/geometry.py` | Add `mesh_polygon(pts_2d, faces, buffer_px)` |
| `src/npa/exp_preprocessing/pipeline.py` | Add `use_convex_hull: bool = True` to `process_exp_lineage` and `process_exp_lobe`; pass faces to `mesh_polygon` |
| `scripts/preprocess_exp.py` | Add `--no-convex-hull` CLI flag |
| `tests/test_exp_preprocessing.py` | Add tests for `mesh_polygon` |
| `docs/PIPELINE.md` | Document both polygon modes |

---

## Module implementations

### `src/npa/exp_preprocessing/geometry.py`

Add the new function alongside `hull_polygon`. Do not modify or remove `hull_polygon`.

```python
def mesh_polygon(
    pts_2d: np.ndarray,
    faces: np.ndarray,
    buffer_px: float = 0.0,
) -> Polygon:
    """Build a connected non-convex polygon from projected mesh triangles.

    Projects each triangle face to 2D and takes the union. Falls back to the
    convex hull if the union is not a single Polygon (e.g. disconnected mesh).
    """
    from shapely.ops import unary_union

    pts_2d = np.asarray(pts_2d, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    if pts_2d.ndim != 2 or pts_2d.shape[1] != 2 or len(pts_2d) < 3:
        raise ValueError("pts_2d must have shape (M, 2) with M >= 3")
    if faces.ndim != 2 or faces.shape[1] != 3 or len(faces) < 1:
        raise ValueError("faces must have shape (F, 3) with F >= 1")

    tris = []
    for tri in faces:
        verts = pts_2d[tri]
        p = Polygon(verts)
        if p.is_valid and p.area > 0:
            tris.append(p)

    if not tris:
        raise ValueError("no valid projected triangles to form mesh polygon")

    polygon = unary_union(tris)

    if buffer_px > 0:
        polygon = polygon.buffer(buffer_px).buffer(0)

    if polygon.is_empty or polygon.area == 0:
        raise ValueError("mesh polygon is empty after union/buffer")

    if not isinstance(polygon, Polygon):
        # Disconnected projection — fall back to convex hull
        polygon = polygon.convex_hull

    return polygon
```

The `from shapely.ops import unary_union` import is local because the rest of
`geometry.py` only imports `MultiPoint`, `Point`, `Polygon` from `shapely.geometry`
and `prep` from `shapely.prepared` — adding it at the module level would be fine too.

---

### `src/npa/exp_preprocessing/pipeline.py`

**Update imports** — add `mesh_polygon` alongside `hull_polygon`:

```python
from npa.exp_preprocessing.geometry import (
    canvas_frame_from_polygon,
    hull_polygon,
    mesh_polygon,
    pca_axes,
    project_2d,
    sphere_voronoi_rasterize,
)
```

**Update `process_exp_lineage` signature** — add `use_convex_hull`:

```python
def process_exp_lineage(
    lineage: ExpFilteredLineage | ExpRejectedLineage,
    mesh_out: Path,
    lineage_id: int,
    ds: float = 0.3,
    canvas_size: int = 200,
    *,
    compute_geo: bool = True,
    use_convex_hull: bool = True,
) -> dict[str, Any]:
```

**Replace polygon construction block** (currently lines 93–95 of `pipeline.py`):

```python
    mean, e1, e2 = pca_axes(lin_vertices)
    lin_pts_2d = project_2d(lin_vertices, mean, e1, e2)
    if use_convex_hull:
        lin_poly = hull_polygon(lin_pts_2d, buffer_px=ds * 0.5)
    else:
        lin_poly = mesh_polygon(lin_pts_2d, lin_faces, buffer_px=ds * 0.5)
```

**Update `process_exp_lobe` signature** — add `use_convex_hull`:

```python
def process_exp_lobe(
    lineage_wrl: Path,
    pros_wrl: Path,
    dpn_wrl: Path,
    genotype: str,
    lobe: str,
    mesh_dir: Path,
    *,
    lineage_id_start: int = 0,
    ds: float = 0.3,
    canvas_size: int = 200,
    use_convex_hull: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], ExpFilteredLobe]:
```

**Pass `use_convex_hull` to both `process_exp_lineage` calls** inside `process_exp_lobe`:

```python
        record = process_exp_lineage(
            lineage=lineage,
            mesh_out=mesh_out,
            lineage_id=lineage_id,
            ds=ds,
            canvas_size=canvas_size,
            compute_geo=True,
            use_convex_hull=use_convex_hull,
        )
```

and for rejected:

```python
        record = process_exp_lineage(
            lineage=lineage,
            mesh_out=mesh_out,
            lineage_id=-1,
            ds=ds,
            canvas_size=canvas_size,
            compute_geo=False,
            use_convex_hull=use_convex_hull,
        )
```

---

### `scripts/preprocess_exp.py`

**Add argument** to `parse_args`:

```python
    parser.add_argument(
        "--no-convex-hull",
        action="store_true",
        default=False,
        help="Use projected mesh-triangle union instead of convex hull for lineage boundary.",
    )
```

**Pass flag** in the `process_exp_lobe` call inside `main()`:

```python
        records, rejected_records, filtered = process_exp_lobe(
            lineage_wrl=triplet.lineage_wrl,
            pros_wrl=triplet.pros_wrl,
            dpn_wrl=triplet.dpn_wrl,
            genotype=triplet.genotype,
            lobe=triplet.lobe,
            mesh_dir=mesh_dir,
            lineage_id_start=lineage_id_next,
            ds=args.ds,
            canvas_size=args.canvas_size,
            use_convex_hull=not args.no_convex_hull,
        )
```

---

## Tests — `tests/test_exp_preprocessing.py`

### Test 1: basic shape and connectivity

A mesh polygon from a non-planar mesh should produce a valid Polygon with finite area
that contains less area than its convex hull.

```python
from npa.exp_preprocessing.geometry import mesh_polygon

def test_mesh_polygon_basic():
    # L-shaped point set — concave, so mesh_polygon should differ from convex hull
    # Triangle fan making an L-shape:
    #   (0,0)-(4,0)-(4,2) and (0,0)-(4,2)-(0,2): right rectangle strip
    #   (0,0)-(0,2)-(0,4) and (0,0)-(0,4)-(2,4): upper-left strip
    pts_2d = np.array(
        [[0,0],[4,0],[4,2],[0,2],[0,4],[2,4]], dtype=np.float32
    )
    faces = np.array(
        [[0,1,2],[0,2,3],[0,3,4],[0,4,5]], dtype=np.int32
    )
    poly = mesh_polygon(pts_2d, faces, buffer_px=0.0)
    assert isinstance(poly, Polygon)
    assert poly.is_valid
    assert poly.area > 0
    # The convex hull of these points is larger
    from shapely.geometry import MultiPoint
    ch = MultiPoint(pts_2d).convex_hull
    assert poly.area <= ch.area
```

### Test 2: buffer fills micro-gaps

With a positive buffer, all triangle gaps are filled and the result is a valid Polygon.

```python
def test_mesh_polygon_buffer():
    pts_2d = np.array(
        [[0,0],[2,0],[2,2],[0,2]], dtype=np.float32
    )
    faces = np.array([[0,1,2],[0,2,3]], dtype=np.int32)
    poly = mesh_polygon(pts_2d, faces, buffer_px=0.1)
    assert isinstance(poly, Polygon)
    assert poly.area > 0
```

### Test 3: degenerate faces are skipped

A face with collinear projected vertices (zero area) must not break the union.

```python
def test_mesh_polygon_degenerate_faces_ignored():
    # Three valid triangles + one degenerate (collinear)
    pts_2d = np.array(
        [[0,0],[4,0],[4,4],[0,4],[2,2],[2,0]], dtype=np.float32
    )
    # Face [0,4,5] → pts (0,0),(2,2),(2,0) — valid
    # Face [0,1,5] → pts (0,0),(4,0),(2,0) — degenerate (all y=0)
    faces = np.array([[0,1,2],[0,2,3],[0,4,5],[0,1,5]], dtype=np.int32)
    poly = mesh_polygon(pts_2d, faces, buffer_px=0.0)
    assert isinstance(poly, Polygon)
    assert poly.area > 0
```

### Test 4: fewer invalid inputs

```python
def test_mesh_polygon_bad_inputs():
    pts_2d = np.zeros((3, 2), dtype=np.float32)
    faces = np.zeros((1, 3), dtype=np.int32)
    # All faces project to zero area
    with pytest.raises(ValueError, match="no valid projected triangles"):
        mesh_polygon(pts_2d, faces, buffer_px=0.0)
```

---

## PIPELINE.md update

Update step 3 in the Experimental Preprocessing section:

> **Polygon construction** (`geometry.py`): For each kept lineage, the projected 2D
> vertices are used to define a boundary polygon with a `0.5 × ds` buffer.
>
> - **Default (convex hull):** `MultiPoint(pts_2d).convex_hull` — encloses all
>   projected vertices; overfills concave regions of the mesh.
> - **Non-convex (mesh-triangle union, `--no-convex-hull`):** `unary_union` of all
>   projected triangular faces — follows the actual mesh silhouette; connected but
>   non-convex. If the union is not a single `Polygon` (disconnected projection),
>   falls back to convex hull.
>
> The polygon is used for canvas sizing and as the rasterization mask.

Update `lin_poly_2d` row in the mesh NPZ table:

> `lin_poly_2d` — `(P, 2)` — Lineage polygon exterior (µm in PC1/PC2); P varies
> with polygon complexity; convex hull gives ~5–15 points, mesh-union can give
> hundreds.

---

## Validation checklist

- [ ] All four new `mesh_polygon` tests pass
- [ ] Existing 14 tests in `test_exp_preprocessing.py` still pass
- [ ] `uv run python scripts/preprocess_exp.py --no-convex-hull` completes without error; same number of kept lineages per genotype as the convex-hull run
- [ ] Spot-check: load one mesh NPZ from the `--no-convex-hull` run; `lin_poly_2d` has noticeably more vertices than the convex-hull version for a concave lineage
- [ ] Visual check: `visualize_exp_lineage.py --view 2d-pre` on a concave WT lineage shows the non-convex polygon tighter than the convex hull
- [ ] The convex-hull run (`preprocess_exp.py` with no flag) produces identical results to the current preprocessor
