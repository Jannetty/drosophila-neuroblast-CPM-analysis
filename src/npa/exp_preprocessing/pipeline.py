from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import trimesh

from npa.exp_preprocessing.geometry import (
    canvas_frame_from_polygon,
    hull_polygon,
    pca_axes,
    project_2d,
    voronoi_rasterize,
)
from npa.exp_preprocessing.lineage_filter import (
    ExpFilteredLineage,
    ExpFilteredLobe,
    ExpRejectedLineage,
    load_exp_filtered_lobe,
)


def _mesh_arrays(prefix: str, meshes: list[trimesh.Trimesh]) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for idx, mesh in enumerate(meshes):
        arrays[f"{prefix}_{idx}_vertices"] = np.asarray(
            mesh.vertices, dtype=np.float32
        )
        arrays[f"{prefix}_{idx}_faces"] = np.asarray(mesh.faces, dtype=np.int32)
    return arrays


def _centroids_3d(meshes: list[trimesh.Trimesh]) -> np.ndarray:
    if not meshes:
        return np.empty((0, 3), dtype=np.float32)
    return np.asarray([mesh.vertices.mean(axis=0) for mesh in meshes], dtype=np.float32)


def _centroids_2d(
    meshes: list[trimesh.Trimesh],
    mean: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
) -> np.ndarray:
    if not meshes:
        return np.empty((0, 2), dtype=np.float32)
    return np.asarray(
        [project_2d(mesh.vertices, mean, e1, e2).mean(axis=0) for mesh in meshes],
        dtype=np.float32,
    )


def _polygon_exterior_array(polygon: Any) -> np.ndarray:
    return np.asarray(polygon.exterior.coords, dtype=np.float32)


def _um_to_canvas_px(
    pts_um: np.ndarray,
    *,
    xmin: float,
    ymin: float,
    ds: float,
    row0: int,
    col0: int,
) -> np.ndarray:
    pts = np.asarray(pts_um, dtype=np.float32).reshape(-1, 2)
    out = np.empty_like(pts, dtype=np.float32)
    out[:, 0] = (pts[:, 0] - np.float32(xmin)) / np.float32(ds) + np.float32(col0)
    out[:, 1] = (pts[:, 1] - np.float32(ymin)) / np.float32(ds) + np.float32(row0)
    return out


def process_exp_lineage(
    lineage: ExpFilteredLineage | ExpRejectedLineage,
    mesh_out: Path,
    lineage_id: int,
    ds: float = 0.3,
    canvas_size: int = 200,
    *,
    compute_geo: bool = True,
) -> dict[str, Any]:
    """Process one filtered lineage and save its per-lineage mesh NPZ."""
    lin_vertices = np.asarray(lineage.lineage_mesh.vertices, dtype=np.float32)
    lin_faces = np.asarray(lineage.lineage_mesh.faces, dtype=np.int32)
    mean, e1, e2 = pca_axes(lin_vertices)
    lin_pts_2d = project_2d(lin_vertices, mean, e1, e2)
    lin_poly = hull_polygon(lin_pts_2d, buffer_px=ds * 0.5)

    dpn_centroids_3d = _centroids_3d(lineage.dpn_meshes)
    pros_centroids_3d = _centroids_3d(lineage.pros_meshes)
    dpn_centroids_2d = _centroids_2d(lineage.dpn_meshes, mean, e1, e2)
    pros_centroids_2d = _centroids_2d(lineage.pros_meshes, mean, e1, e2)
    xmin, ymin, _, _, row0, col0 = canvas_frame_from_polygon(
        lin_poly=lin_poly,
        canvas_size=canvas_size,
        ds=ds,
    )
    lin_poly_2d = _polygon_exterior_array(lin_poly)
    dpn_centroids_2d_px = _um_to_canvas_px(
        dpn_centroids_2d,
        xmin=xmin,
        ymin=ymin,
        ds=ds,
        row0=row0,
        col0=col0,
    )
    pros_centroids_2d_px = _um_to_canvas_px(
        pros_centroids_2d,
        xmin=xmin,
        ymin=ymin,
        ds=ds,
        row0=row0,
        col0=col0,
    )
    lin_poly_2d_px = _um_to_canvas_px(
        lin_poly_2d,
        xmin=xmin,
        ymin=ymin,
        ds=ds,
        row0=row0,
        col0=col0,
    )
    if compute_geo:
        geo = voronoi_rasterize(
            lin_poly,
            dpn_centroids_2d,
            pros_centroids_2d,
            canvas_size=canvas_size,
            ds=ds,
        )
    else:
        geo = np.zeros((canvas_size, canvas_size, 2), dtype=np.float32)
    counts = np.asarray(
        [
            lineage.n_dpn,
            lineage.n_pros,
            float(geo[..., 0].sum()),
        ],
        dtype=np.float32,
    )

    mesh_out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        mesh_out,
        lin_vertices=lin_vertices,
        lin_faces=lin_faces,
        **_mesh_arrays("dpn", lineage.dpn_meshes),
        **_mesh_arrays("pros", lineage.pros_meshes),
        dpn_centroids_3d=dpn_centroids_3d,
        pros_centroids_3d=pros_centroids_3d,
        lin_poly_2d=lin_poly_2d,
        dpn_centroids_2d=dpn_centroids_2d,
        pros_centroids_2d=pros_centroids_2d,
        dpn_centroids_2d_px=dpn_centroids_2d_px,
        pros_centroids_2d_px=pros_centroids_2d_px,
        lin_poly_2d_px=lin_poly_2d_px,
        ds=np.asarray(ds, dtype=np.float32),
        pca_mean=mean.astype(np.float32),
        pca_e1=e1.astype(np.float32),
        pca_e2=e2.astype(np.float32),
    )

    return {
        "geo": geo,
        "counts": counts,
        "lineage_id": int(lineage_id),
        "genotype": "",
        "lobe": "",
        "lineage_idx": int(lineage.lineage_idx),
        "n_dpn": lineage.n_dpn,
        "n_pros": lineage.n_pros,
        "mesh_path": mesh_out,
    }


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
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], ExpFilteredLobe]:
    """Filter and process all kept lineages from one lobe."""
    filtered = load_exp_filtered_lobe(
        lineage_wrl=lineage_wrl,
        pros_wrl=pros_wrl,
        dpn_wrl=dpn_wrl,
        genotype=genotype,
        lobe=lobe,
    )
    records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []

    for offset, lineage in enumerate(filtered.kept):
        lineage_id = lineage_id_start + offset
        mesh_out = mesh_dir / genotype / f"{lobe}_{lineage.lineage_idx}.npz"
        record = process_exp_lineage(
            lineage=lineage,
            mesh_out=mesh_out,
            lineage_id=lineage_id,
            ds=ds,
            canvas_size=canvas_size,
            compute_geo=True,
        )
        record.update(
            {
                "genotype": genotype,
                "lobe": lobe,
                "mesh_path": mesh_out,
                "analysis_row": -1,
            }
        )
        records.append(record)

    for lineage in filtered.rejected:
        mesh_out = mesh_dir / "rejected" / genotype / f"{lobe}_{lineage.lineage_idx}.npz"
        record = process_exp_lineage(
            lineage=lineage,
            mesh_out=mesh_out,
            lineage_id=-1,
            ds=ds,
            canvas_size=canvas_size,
            compute_geo=False,
        )
        record.update(
            {
                "genotype": genotype,
                "lobe": lobe,
                "mesh_path": mesh_out,
                "rejection_reason": lineage.rejection_reason,
            }
        )
        rejected_records.append(record)

    return records, rejected_records, filtered


def stack_exp_analysis_npz(
    records: list[dict[str, Any]],
    out_path: Path,
    ds: float = 0.3,
) -> None:
    """Stack per-lineage records into one genotype-level analysis NPZ."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if records:
        geo = np.stack([record["geo"] for record in records], axis=0).astype(np.float32)
        counts = np.stack([record["counts"] for record in records], axis=0).astype(
            np.float32
        )
        lineage_ids = np.asarray(
            [record["lineage_id"] for record in records], dtype=np.int32
        )
    else:
        geo = np.empty((0, 0, 0, 2), dtype=np.float32)
        counts = np.empty((0, 3), dtype=np.float32)
        lineage_ids = np.empty((0,), dtype=np.int32)

    np.savez_compressed(
        out_path,
        geo=geo,
        counts=counts,
        lineage_ids=lineage_ids,
        ds=np.asarray(ds, dtype=np.float32),
    )


def write_lineage_index(records: list[dict[str, Any]], out_path: Path) -> None:
    """Write the global lineage index CSV."""
    rows = []
    for record in records:
        rows.append(
            {
                "lineage_id": int(record["lineage_id"]),
                "genotype": record["genotype"],
                "lobe": record["lobe"],
                "lineage_idx": int(record["lineage_idx"]),
                "n_dpn": int(record["n_dpn"]),
                "n_pros": int(record["n_pros"]),
                "mesh_path": Path(record["mesh_path"]).as_posix(),
                "analysis_row": int(record["analysis_row"]),
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        rows,
        columns=[
            "lineage_id",
            "genotype",
            "lobe",
            "lineage_idx",
            "n_dpn",
            "n_pros",
            "mesh_path",
            "analysis_row",
        ],
    ).to_csv(out_path, index=False)


def write_rejected_lineage_index(records: list[dict[str, Any]], out_path: Path) -> None:
    """Write the rejected lineage index CSV."""
    rows = []
    for record in records:
        rows.append(
            {
                "lineage_id": int(record["lineage_id"]),
                "genotype": record["genotype"],
                "lobe": record["lobe"],
                "lineage_idx": int(record["lineage_idx"]),
                "n_dpn": int(record["n_dpn"]),
                "n_pros": int(record["n_pros"]),
                "mesh_path": Path(record["mesh_path"]).as_posix(),
                "rejection_reason": record["rejection_reason"],
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        rows,
        columns=[
            "lineage_id",
            "genotype",
            "lobe",
            "lineage_idx",
            "n_dpn",
            "n_pros",
            "mesh_path",
            "rejection_reason",
        ],
    ).to_csv(out_path, index=False)

