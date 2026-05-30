from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib.patches import Circle as MplCircle
from matplotlib.patches import Polygon as PolygonPatch

from npa.colors import NB_COLOR as DPN_COLOR, PROS_COLOR, EXP_HULL_COLOR as HULL_COLOR


def _title(row: dict) -> str:
    return (
        f'{row["lineage_id"]} | {row["genotype"]} | {row["lobe"]} | '
        f'lin_idx={row["lineage_idx"]} | dpn={row["n_dpn"]} pros={row["n_pros"]}'
    )


def _hex_to_rgb01(hex_color: str) -> np.ndarray:
    raw = hex_color.lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    vals = [int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return np.asarray(vals, dtype=np.float32)


def load_index(processed_dir: Path, rejected: bool) -> list[dict]:
    filename = "rejected_lineage_index.csv" if rejected else "lineage_index.csv"
    path = processed_dir / filename
    rows = pd.read_csv(path)
    return rows.to_dict(orient="records")


def load_mesh_npz(mesh_path: Path) -> dict:
    with np.load(mesh_path) as data:
        return {key: data[key] for key in data.files}


def load_lineage_geo(analysis_npz: Path, analysis_row: int) -> np.ndarray:
    with np.load(analysis_npz) as data:
        geo = np.asarray(data["geo"], dtype=np.float32)
    if analysis_row < 0 or analysis_row >= len(geo):
        raise IndexError(f"analysis_row out of range: {analysis_row}")
    return geo[analysis_row]


def print_index_table(rows: list[dict], rejected: bool) -> None:
    fmt = f"{'row':>5}  {'lineage_id':>10}  {'genotype':<10}  {'lobe':<8}  {'lin_idx':>7}  {'n_dpn':>5}  {'n_pros':>6}"
    if rejected:
        fmt += f"  {'rejection_reason':<16}"
    print(fmt)
    print("-" * len(fmt))
    for row_idx, row in enumerate(rows):
        line = (
            f"{row_idx:>5}  {row['lineage_id']:>10}  {str(row['genotype']):<10}  "
            f"{str(row['lobe']):<8}  {row['lineage_idx']:>7}  {row['n_dpn']:>5}  {row['n_pros']:>6}"
        )
        if rejected:
            line += f"  {str(row['rejection_reason']):<16}"
        print(line)


def _add_mesh_group(
    fig: go.Figure,
    mesh: dict,
    prefix: str,
    color: str,
    opacity: float,
    name: str,
) -> None:
    def _cell_index(k: str) -> int:
        return int(k[len(prefix) + 1 : -len("_vertices")])

    keys = sorted(
        (k for k in mesh if k.startswith(prefix) and k.endswith("_vertices")),
        key=_cell_index,
    )
    for idx, v_key in enumerate(keys):
        i = _cell_index(v_key)
        f_key = f"{prefix}_{i}_faces"
        vertices = np.asarray(mesh[v_key], dtype=np.float32)
        faces = np.asarray(mesh[f_key], dtype=np.int32)
        fig.add_trace(
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=faces[:, 0],
                j=faces[:, 1],
                k=faces[:, 2],
                color=color,
                opacity=opacity,
                name=name,
                legendgroup=name,
                showlegend=(idx == 0),
            )
        )


def show_3d(mesh: dict, row: dict) -> None:
    fig = go.Figure()
    lin_vertices = np.asarray(mesh["lin_vertices"], dtype=np.float32)
    lin_faces = np.asarray(mesh["lin_faces"], dtype=np.int32)
    fig.add_trace(
        go.Mesh3d(
            x=lin_vertices[:, 0],
            y=lin_vertices[:, 1],
            z=lin_vertices[:, 2],
            i=lin_faces[:, 0],
            j=lin_faces[:, 1],
            k=lin_faces[:, 2],
            color=HULL_COLOR,
            opacity=0.15,
            name="lineage_hull",
            legendgroup="lineage_hull",
            showlegend=True,
        )
    )
    _add_mesh_group(fig, mesh, prefix="dpn", color=DPN_COLOR, opacity=1.0, name="dpn")
    _add_mesh_group(fig, mesh, prefix="pros", color=PROS_COLOR, opacity=0.5, name="pros")
    fig.update_layout(title=_title(row), scene={"aspectmode": "data"})
    fig.show()


def _sphere_radius_um(volume_um3: float) -> float:
    return (3.0 * float(volume_um3) / (4.0 * np.pi)) ** (1.0 / 3.0)


def show_2d_pre(mesh: dict, row: dict) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    lin_poly_2d = np.asarray(mesh["lin_poly_2d"], dtype=np.float32)
    ax.add_patch(
        PolygonPatch(
            lin_poly_2d,
            closed=True,
            facecolor=HULL_COLOR,
            edgecolor=HULL_COLOR,
            linewidth=1.0,
            alpha=0.2,
        )
    )
    dpn_centroids = np.asarray(mesh["dpn_centroids_2d"], dtype=np.float32).reshape(-1, 2)
    pros_centroids = np.asarray(mesh["pros_centroids_2d"], dtype=np.float32).reshape(-1, 2)
    dpn_vols  = np.asarray(mesh.get("dpn_volumes_um3",  np.zeros(len(dpn_centroids))),  dtype=np.float64).ravel()
    pros_vols = np.asarray(mesh.get("pros_volumes_um3", np.zeros(len(pros_centroids))), dtype=np.float64).ravel()

    for (cx, cy), vol in zip(pros_centroids, pros_vols):
        r = _sphere_radius_um(vol)
        ax.add_patch(MplCircle((cx, cy), r, color=PROS_COLOR, fill=True,  alpha=0.3, linewidth=0,   zorder=2))
        ax.add_patch(MplCircle((cx, cy), r, color=PROS_COLOR, fill=False, linewidth=0.8,             zorder=2))
    for (cx, cy), vol in zip(dpn_centroids, dpn_vols):
        r = _sphere_radius_um(vol)
        ax.add_patch(MplCircle((cx, cy), r, color=DPN_COLOR, fill=True,  alpha=0.4, linewidth=0,    zorder=3))
        ax.add_patch(MplCircle((cx, cy), r, color=DPN_COLOR, fill=False, linewidth=0.8,              zorder=3))

    ax.autoscale_view()
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("PC1 (µm)")
    ax.set_ylabel("PC2 (µm)")
    ax.set_title(_title(row))
    plt.show()


def show_2d_post(mesh: dict, geo: np.ndarray, row: dict) -> None:
    geo = np.asarray(geo, dtype=np.float32)
    if geo.ndim != 3 or geo.shape[2] != 2:
        raise ValueError("geo must have shape (H, W, 2)")

    h, w, _ = geo.shape
    image = np.ones((h, w, 3), dtype=np.float32)
    dpn_rgb = _hex_to_rgb01(DPN_COLOR)
    pros_rgb = _hex_to_rgb01(PROS_COLOR)
    dpn_mask = geo[..., 0] > 0
    pros_mask = geo[..., 1] > 0
    image[dpn_mask] = dpn_rgb
    image[pros_mask] = pros_rgb
    _label = np.zeros(geo.shape[:2], dtype=np.int8)
    _label[pros_mask] = 2
    _label[dpn_mask] = 1
    _boundary = np.zeros(geo.shape[:2], dtype=bool)
    _boundary[:-1, :] |= _label[:-1, :] > _label[1:, :]
    _boundary[1:, :] |= _label[1:, :] > _label[:-1, :]
    _boundary[:, :-1] |= _label[:, :-1] > _label[:, 1:]
    _boundary[:, 1:] |= _label[:, 1:] > _label[:, :-1]
    image[_boundary] = _hex_to_rgb01(HULL_COLOR)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(image, origin="upper")
    dpn_centroids_px = np.asarray(mesh["dpn_centroids_2d_px"], dtype=np.float32).reshape(-1, 2)
    pros_centroids_px = np.asarray(mesh["pros_centroids_2d_px"], dtype=np.float32).reshape(-1, 2)
    if len(dpn_centroids_px) > 0:
        ax.scatter(dpn_centroids_px[:, 0], dpn_centroids_px[:, 1], c=DPN_COLOR, s=18)
    if len(pros_centroids_px) > 0:
        ax.scatter(pros_centroids_px[:, 0], pros_centroids_px[:, 1], c=PROS_COLOR, s=18)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(_title(row))
    plt.show()
