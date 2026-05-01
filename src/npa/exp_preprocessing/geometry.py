from __future__ import annotations

import numpy as np
from scipy.spatial import KDTree
from shapely.geometry import MultiPoint, Point, Polygon
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


def _centroid_stack(
    dpn_centroids_2d: np.ndarray,
    pros_centroids_2d: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    dpn = np.asarray(dpn_centroids_2d, dtype=np.float32).reshape(-1, 2)
    pros = np.asarray(pros_centroids_2d, dtype=np.float32).reshape(-1, 2)
    if len(dpn) + len(pros) == 0:
        raise ValueError("at least one cell centroid is required")
    centroids = np.vstack([dpn, pros]).astype(np.float32)
    is_dpn = np.zeros(len(centroids), dtype=bool)
    is_dpn[: len(dpn)] = True
    return centroids, is_dpn


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


def voronoi_rasterize(
    lin_poly: Polygon,
    dpn_centroids_2d: np.ndarray,
    pros_centroids_2d: np.ndarray,
    canvas_size: int,
    ds: float,
) -> np.ndarray:
    """
    Rasterize the lineage polygon and assign each inside pixel to the nearest
    Dpn or Pros centroid.
    """
    centroids, is_dpn = _centroid_stack(dpn_centroids_2d, pros_centroids_2d)
    xmin, ymin, nx, ny, row0, col0 = canvas_frame_from_polygon(
        lin_poly=lin_poly,
        canvas_size=canvas_size,
        ds=ds,
    )

    xs = xmin + (np.arange(nx, dtype=np.float32) + 0.5) * ds
    ys = ymin + (np.arange(ny, dtype=np.float32) + 0.5) * ds
    grid_x, grid_y = np.meshgrid(xs, ys)
    points = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    prepared = prep(lin_poly)
    inside = np.fromiter(
        (prepared.contains(Point(float(x), float(y))) for x, y in points),
        dtype=bool,
        count=len(points),
    )
    if not inside.any():
        raise ValueError("lineage polygon did not cover any raster pixels")

    tree = KDTree(centroids)
    inside_points = points[inside]
    _, nearest = tree.query(inside_points)

    flat_y, flat_x = np.where(inside.reshape(ny, nx))
    dpn_mask = np.zeros((ny, nx), dtype=np.float32)
    pros_mask = np.zeros((ny, nx), dtype=np.float32)
    nearest_is_dpn = is_dpn[nearest]
    dpn_mask[flat_y[nearest_is_dpn], flat_x[nearest_is_dpn]] = 1.0
    pros_mask[flat_y[~nearest_is_dpn], flat_x[~nearest_is_dpn]] = 1.0

    geo = np.zeros((canvas_size, canvas_size, 2), dtype=np.float32)
    geo[row0 : row0 + ny, col0 : col0 + nx, 0] = dpn_mask
    geo[row0 : row0 + ny, col0 : col0 + nx, 1] = pros_mask
    return geo

