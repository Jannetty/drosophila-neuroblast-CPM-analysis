from __future__ import annotations

import numpy as np
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep


def pca_axes(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the mean and first two PCA axes for a (M, 3) vertex array."""
    vertices = np.asarray(vertices, dtype=np.float32)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or len(vertices) < 3:
        raise ValueError("vertices must have shape (M, 3) with M >= 3")
    mean = vertices.mean(axis=0)
    centered = vertices - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    return (
        mean.astype(np.float32),
        vt[0].astype(np.float32),
        vt[1].astype(np.float32),
    )


def project_2d(
    vertices: np.ndarray,
    mean: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
) -> np.ndarray:
    """Project 3D vertices onto the plane spanned by e1 and e2."""
    vertices = np.asarray(vertices, dtype=np.float32)
    rel = vertices - np.asarray(mean, dtype=np.float32)
    return np.column_stack([rel @ e1, rel @ e2]).astype(np.float32)


def hull_polygon(pts_2d: np.ndarray, buffer_px: float = 0.0) -> Polygon:
    """Compute a convex hull polygon from projected points and apply a buffer."""
    pts_2d = np.asarray(pts_2d, dtype=np.float32)
    if pts_2d.ndim != 2 or pts_2d.shape[1] != 2 or len(pts_2d) < 3:
        raise ValueError("pts_2d must have shape (M, 2) with M >= 3")

    polygon = MultiPoint(pts_2d).convex_hull
    if polygon.is_empty or polygon.area == 0:
        raise ValueError("projected lineage hull is empty")
    if buffer_px > 0:
        polygon = polygon.buffer(buffer_px).buffer(0)
    if polygon.is_empty or polygon.area == 0:
        raise ValueError("buffered lineage hull is empty")
    if not isinstance(polygon, Polygon):
        polygon = polygon.convex_hull
    return polygon



def mesh_polygon(
    pts_2d: np.ndarray,
    faces: np.ndarray,
    buffer_px: float = 0.0,
) -> Polygon:
    """Build a connected non-convex polygon from projected mesh triangles.

    Takes the unary_union of all valid (non-degenerate) projected triangle
    faces and applies a buffer. Falls back to convex hull if the union is
    not a single Polygon (e.g. disconnected projection).
    """
    pts_2d = np.asarray(pts_2d, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    if pts_2d.ndim != 2 or pts_2d.shape[1] != 2 or len(pts_2d) < 3:
        raise ValueError("pts_2d must have shape (M, 2) with M >= 3")
    if faces.ndim != 2 or faces.shape[1] != 3 or len(faces) < 1:
        raise ValueError("faces must have shape (F, 3) with F >= 1")

    tris = []
    for tri in faces:
        p = Polygon(pts_2d[tri])
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
        polygon = polygon.convex_hull

    return polygon


def canvas_frame_from_polygon(
    lin_poly: Polygon,
    canvas_size: int,
    ds: float,
) -> tuple[float, float, int, int, int, int]:
    """Return raster bounds and canvas offsets for a lineage polygon."""
    if canvas_size <= 0:
        raise ValueError("canvas_size must be positive")
    if ds <= 0:
        raise ValueError("ds must be positive")
    if lin_poly.is_empty:
        raise ValueError("lin_poly is empty")

    xmin, ymin, xmax, ymax = lin_poly.bounds
    pad = ds * 0.5
    xmin -= pad
    ymin -= pad
    xmax += pad
    ymax += pad

    nx = int(np.ceil((xmax - xmin) / ds))
    ny = int(np.ceil((ymax - ymin) / ds))
    if nx <= 0 or ny <= 0:
        raise ValueError("lineage polygon raster bounds are empty")
    if nx > canvas_size or ny > canvas_size:
        raise ValueError(
            f"rasterized lineage {ny}x{nx} exceeds canvas {canvas_size}x{canvas_size}"
        )

    row0 = (canvas_size - ny) // 2
    col0 = (canvas_size - nx) // 2
    return xmin, ymin, nx, ny, row0, col0



def sphere_voronoi_rasterize(
    lin_poly: Polygon,
    dpn_centroids_2d: np.ndarray,
    pros_centroids_2d: np.ndarray,
    dpn_volumes_um3: np.ndarray,
    pros_volumes_um3: np.ndarray,
    canvas_size: int,
    ds: float,
) -> np.ndarray:
    """
    Rasterize lineage polygon using additively weighted Voronoi seeded by sphere
    radii derived from 3D cell volumes.

    Priority (applied in order):
      1. Pixels inside any Dpn circle → nearest Dpn center wins
      2. Pixels inside only Pros circles → nearest Pros center wins
      3. All remaining hull pixels → argmin(||p − c_i|| − r_i) across all cells

    Returns (canvas_size, canvas_size, 2) float32: ch0=Dpn, ch1=Pros territory.
    """
    xmin, ymin, nx, ny, row0, col0 = canvas_frame_from_polygon(lin_poly, canvas_size, ds)

    xs = xmin + (np.arange(nx, dtype=np.float64) + 0.5) * ds  # (nx,) x coords in µm
    ys = ymin + (np.arange(ny, dtype=np.float64) + 0.5) * ds  # (ny,) y coords in µm
    GX, GY = np.meshgrid(xs, ys)                              # both (ny, nx)

    dpn_c  = np.asarray(dpn_centroids_2d,  dtype=np.float64).reshape(-1, 2)
    pros_c = np.asarray(pros_centroids_2d, dtype=np.float64).reshape(-1, 2)
    n_dpn  = len(dpn_c)
    n_pros = len(pros_c)

    def _radii_um(vols: np.ndarray) -> np.ndarray:
        v = np.asarray(vols, dtype=np.float64).ravel()
        return (3.0 * v / (4.0 * np.pi)) ** (1.0 / 3.0)

    def _aw_dist(centroids: np.ndarray, radii_um: np.ndarray) -> np.ndarray:
        # Returns (n_cells, ny, nx) in µm; negative value means pixel is inside circle
        return np.stack(
            [np.sqrt((GX - cx) ** 2 + (GY - cy) ** 2) - r
             for (cx, cy), r in zip(centroids, radii_um)],
            axis=0,
        )

    if n_dpn:
        dpn_dw     = _aw_dist(dpn_c,  _radii_um(dpn_volumes_um3))   # (n_dpn, ny, nx)
        inside_dpn = dpn_dw.min(axis=0) < 0
    else:
        dpn_dw     = None
        inside_dpn = np.zeros((ny, nx), dtype=bool)

    if n_pros:
        pros_dw     = _aw_dist(pros_c, _radii_um(pros_volumes_um3))  # (n_pros, ny, nx)
        inside_pros = pros_dw.min(axis=0) < 0
    else:
        pros_dw     = None
        inside_pros = np.zeros((ny, nx), dtype=bool)

    # Global additively weighted Voronoi — used for pixels outside all circles
    if n_dpn and n_pros:
        all_dw = np.concatenate([dpn_dw, pros_dw], axis=0)
        global_nearest_is_dpn = all_dw.argmin(axis=0) < n_dpn
    elif n_dpn:
        global_nearest_is_dpn = np.ones((ny, nx), dtype=bool)
    else:
        global_nearest_is_dpn = np.zeros((ny, nx), dtype=bool)

    # Priority assignment
    is_dpn_px = global_nearest_is_dpn.copy()
    is_dpn_px[inside_dpn] = True
    is_dpn_px[inside_pros & ~inside_dpn] = False

    # Hull mask
    points = np.column_stack([GX.ravel(), GY.ravel()])
    prepared_poly = prep(lin_poly)
    hull_mask = np.fromiter(
        (prepared_poly.contains(Point(float(x), float(y))) for x, y in points),
        dtype=bool,
        count=len(points),
    ).reshape(ny, nx)

    if not hull_mask.any():
        raise ValueError("lineage polygon did not cover any raster pixels")

    dpn_mask  = (is_dpn_px  & hull_mask).astype(np.float32)
    pros_mask = (~is_dpn_px & hull_mask).astype(np.float32)

    geo = np.zeros((canvas_size, canvas_size, 2), dtype=np.float32)
    geo[row0 : row0 + ny, col0 : col0 + nx, 0] = dpn_mask
    geo[row0 : row0 + ny, col0 : col0 + nx, 1] = pros_mask
    return geo

