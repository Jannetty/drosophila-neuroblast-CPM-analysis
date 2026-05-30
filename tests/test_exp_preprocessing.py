from pathlib import Path

import numpy as np
import pytest
import trimesh
from shapely.geometry import MultiPoint
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box

from npa.exp_preprocessing.geometry import (
    hull_polygon,
    mesh_polygon,
    pca_axes,
    project_2d,
    sphere_voronoi_rasterize,
)
from npa.exp_preprocessing.lineage_filter import (
    ExpFilteredLineage,
    ExpRejectedLineage,
    load_exp_filtered_lobe,
    assign_cells_to_lineages_by_containment,
    assign_cells_to_lineages_by_vertex_bbox,
)
from npa.exp_preprocessing.pipeline import (
    process_exp_lineage,
    stack_exp_analysis_npz,
    write_lineage_index,
    write_rejected_lineage_index,
)
from npa.exp_preprocessing.wrl_io import load_vrml_meshes, to_trimesh_list


def test_load_vrml_meshes_shared_coordinate_block(tmp_path: Path) -> None:
    path = tmp_path / "shared.wrl"
    path.write_text(
        """
        Shape {
          geometry IndexedFaceSet {
            coord Coordinate { point [
              0 0 0, 1 0 0, 1 1 0, 0 1 0, 0 0 1
            ] }
            coordIndex [ 0, 1, 2, 3, -1 ]
          }
        }
        Shape {
          geometry IndexedFaceSet {
            coordIndex [ 0, 1, 4, -1 ]
          }
        }
        """
    )

    meshes = load_vrml_meshes(path)

    assert len(meshes) == 2
    assert meshes[0][0].dtype == np.float32
    assert meshes[0][1].dtype == np.int32
    assert meshes[0][1].shape == (2, 3)
    assert meshes[1][1].shape == (1, 3)


def test_load_vrml_meshes_multiple_coordinate_blocks(tmp_path: Path) -> None:
    path = tmp_path / "multiple.wrl"
    path.write_text(
        """
        Shape {
          geometry IndexedFaceSet {
            coord Coordinate { point [0 0 0, 1 0 0, 0 1 0] }
            coordIndex [0, 1, 2, -1]
          }
        }
        Shape {
          geometry IndexedFaceSet {
            coord Coordinate { point [10 0 0, 11 0 0, 10 1 0] }
            coordIndex [0, 1, 2, -1]
          }
        }
        """
    )

    meshes = load_vrml_meshes(path)

    assert len(meshes) == 2
    assert np.allclose(meshes[1][0][0], [10, 0, 0])
    assert len(to_trimesh_list(meshes)) == 2


def test_assign_cells_to_lineages_by_vertex_bbox() -> None:
    lineage_a = trimesh.creation.box(extents=(2, 2, 2), transform=np.eye(4))
    lineage_b = trimesh.creation.box(
        extents=(2, 2, 2),
        transform=trimesh.transformations.translation_matrix([5, 0, 0]),
    )
    inside_a = trimesh.creation.box(extents=(0.5, 0.5, 0.5))
    inside_b = trimesh.creation.box(
        extents=(0.5, 0.5, 0.5),
        transform=trimesh.transformations.translation_matrix([5, 0, 0]),
    )
    outside = trimesh.creation.box(
        extents=(0.5, 0.5, 0.5),
        transform=trimesh.transformations.translation_matrix([20, 0, 0]),
    )

    assignments, scores = assign_cells_to_lineages_by_vertex_bbox(
        [inside_a, inside_b, outside], [lineage_a, lineage_b], min_fraction=0.95
    )

    assert assignments.tolist() == [0, 1, -1]
    assert scores[:2].tolist() == [1.0, 1.0]
    assert scores[2] == 0.0


def test_assign_cells_to_lineages_by_containment() -> None:
    lineage = trimesh.creation.box(extents=(4, 4, 4))
    cell = trimesh.creation.box(extents=(1, 1, 1))

    assignments, scores = assign_cells_to_lineages_by_containment(
        [cell], [lineage], min_fraction=0.60, n_sample=20
    )

    assert assignments.tolist() == [0]
    assert scores[0] >= 0.60


def test_geometry_rasterization_channels_and_canvas_error() -> None:
    vertices = np.array(
        [
            [0, 0, 0],
            [4, 0, 0],
            [4, 4, 0],
            [0, 4, 0],
            [2, 2, 1],
        ],
        dtype=np.float32,
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
    assert np.logical_and(geo[..., 0] > 0, geo[..., 1] > 0).sum() == 0
    assert geo.sum() > 0

    with pytest.raises(ValueError, match="exceeds canvas"):
        sphere_voronoi_rasterize(
            box(0, 0, 10, 10),
            dpn_centroids_2d=np.array([[1.0, 1.0]], dtype=np.float32),
            pros_centroids_2d=np.empty((0, 2), dtype=np.float32),
            dpn_volumes_um3=np.array([1.0], dtype=np.float32),
            pros_volumes_um3=np.empty((0,), dtype=np.float32),
            canvas_size=4,
            ds=1.0,
        )


def test_sphere_voronoi_rasterize_basic() -> None:
    vertices = np.array(
        [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [2, 2, 1]],
        dtype=np.float32,
    )
    mean, e1, e2 = pca_axes(vertices)
    pts_2d = project_2d(vertices, mean, e1, e2)
    poly = hull_polygon(pts_2d, buffer_px=0.0)

    # Equal volumes → result should be near the plain-Voronoi split
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
    assert np.logical_and(geo[..., 0] > 0, geo[..., 1] > 0).sum() == 0
    assert geo.sum() > 0


def test_sphere_voronoi_nb_priority() -> None:
    # NB centroid at (5, 5) with large volume (r ≈ 3.6 µm).
    # Pros centroid at (5.1, 5) — only 0.1 µm away from NB center, so the
    # Pros centroid is geometrically closer to the center pixel, but the
    # center pixel is inside the NB circle → NB must win.
    poly = box(0, 0, 10, 10)
    geo = sphere_voronoi_rasterize(
        poly,
        dpn_centroids_2d=np.array([[5.0, 5.0]], dtype=np.float32),
        pros_centroids_2d=np.array([[5.1, 5.0]], dtype=np.float32),
        dpn_volumes_um3=np.array([200.0], dtype=np.float32),
        pros_volumes_um3=np.array([1.0], dtype=np.float32),
        canvas_size=50,
        ds=0.25,
    )

    # Pixel closest to canvas center should be NB territory
    cy, cx = geo.shape[0] // 2, geo.shape[1] // 2
    assert geo[cy, cx, 0] == 1.0, "center pixel must be NB territory"
    assert geo[cy, cx, 1] == 0.0


def test_sphere_voronoi_larger_cell_claims_more() -> None:
    # NB at left, Pros at right, NB has 8× the volume.
    # NB must claim more hull pixels than Pros.
    poly = box(0, 0, 10, 10)
    geo = sphere_voronoi_rasterize(
        poly,
        dpn_centroids_2d=np.array([[2.5, 5.0]], dtype=np.float32),
        pros_centroids_2d=np.array([[7.5, 5.0]], dtype=np.float32),
        dpn_volumes_um3=np.array([800.0], dtype=np.float32),
        pros_volumes_um3=np.array([100.0], dtype=np.float32),
        canvas_size=50,
        ds=0.25,
    )

    assert np.logical_and(geo[..., 0] > 0, geo[..., 1] > 0).sum() == 0
    assert geo[..., 0].sum() > geo[..., 1].sum(), "larger NB volume must claim more pixels"


def test_sphere_voronoi_canvas_exceeded() -> None:
    with pytest.raises(ValueError, match="exceeds canvas"):
        sphere_voronoi_rasterize(
            box(0, 0, 10, 10),
            dpn_centroids_2d=np.array([[1.0, 1.0]], dtype=np.float32),
            pros_centroids_2d=np.empty((0, 2), dtype=np.float32),
            dpn_volumes_um3=np.array([1.0], dtype=np.float32),
            pros_volumes_um3=np.empty((0,), dtype=np.float32),
            canvas_size=4,
            ds=1.0,
        )


def test_stack_and_lineage_index(tmp_path: Path) -> None:
    records = [
        {
            "geo": np.zeros((4, 4, 2), dtype=np.float32),
            "counts": np.array([1, 2, 3], dtype=np.float32),
            "lineage_id": 7,
            "genotype": "wt",
            "lobe": "lobe1",
            "lineage_idx": 2,
            "n_dpn": 1,
            "n_pros": 2,
            "mesh_path": Path("data/exp/processed/meshes/wt/lobe1_2.npz"),
            "analysis_row": 0,
        }
    ]

    npz_path = tmp_path / "wt.npz"
    csv_path = tmp_path / "lineage_index.csv"
    stack_exp_analysis_npz(records, npz_path, ds=0.3)
    write_lineage_index(records, csv_path)

    with np.load(npz_path) as data:
        assert data["geo"].shape == (1, 4, 4, 2)
        assert data["counts"].shape == (1, 3)
        assert data["lineage_ids"].tolist() == [7]
        assert np.isclose(float(data["ds"]), 0.3)

    text = csv_path.read_text()
    assert "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,analysis_row" in text
    assert "7,wt,lobe1,2,1,2,data/exp/processed/meshes/wt/lobe1_2.npz,0" in text


def test_process_exp_lineage_writes_pixel_coordinates_and_ds(tmp_path: Path) -> None:
    lineage_mesh = trimesh.creation.box(extents=(4.0, 4.0, 2.0))
    dpn_mesh = trimesh.creation.box(
        extents=(0.6, 0.6, 0.6),
        transform=trimesh.transformations.translation_matrix([-0.8, 0.0, 0.0]),
    )
    pros_mesh = trimesh.creation.box(
        extents=(0.6, 0.6, 0.6),
        transform=trimesh.transformations.translation_matrix([0.8, 0.0, 0.0]),
    )
    lineage = ExpFilteredLineage(
        lineage_idx=0,
        lineage_mesh=lineage_mesh,
        dpn_meshes=[dpn_mesh],
        pros_meshes=[pros_mesh],
    )
    mesh_out = tmp_path / "mesh.npz"
    ds = 0.5
    canvas_size = 20

    process_exp_lineage(
        lineage=lineage,
        mesh_out=mesh_out,
        lineage_id=3,
        ds=ds,
        canvas_size=canvas_size,
    )

    with np.load(mesh_out) as data:
        assert np.isclose(float(data["ds"]), ds)
        assert "dpn_centroids_2d_px" in data
        assert "pros_centroids_2d_px" in data
        assert "lin_poly_2d_px" in data

        lin_poly_2d = data["lin_poly_2d"]
        xmin, ymin = lin_poly_2d.min(axis=0) - ds * 0.5
        xmax, ymax = lin_poly_2d.max(axis=0) + ds * 0.5
        nx = int(np.ceil((xmax - xmin) / ds))
        ny = int(np.ceil((ymax - ymin) / ds))
        row0 = (canvas_size - ny) // 2
        col0 = (canvas_size - nx) // 2

        def to_px(pts_um: np.ndarray) -> np.ndarray:
            pts = np.asarray(pts_um, dtype=np.float32)
            out = np.empty_like(pts, dtype=np.float32)
            out[:, 0] = (pts[:, 0] - xmin) / ds + col0
            out[:, 1] = (pts[:, 1] - ymin) / ds + row0
            return out

        np.testing.assert_allclose(data["dpn_centroids_2d_px"], to_px(data["dpn_centroids_2d"]))
        np.testing.assert_allclose(
            data["pros_centroids_2d_px"],
            to_px(data["pros_centroids_2d"]),
        )
        np.testing.assert_allclose(data["lin_poly_2d_px"], to_px(data["lin_poly_2d"]))


def test_load_exp_filtered_lobe_tracks_rejected_lineages(monkeypatch: pytest.MonkeyPatch) -> None:
    lineage_meshes = [
        trimesh.creation.box(extents=(3, 3, 3)),
        trimesh.creation.box(extents=(3, 3, 3)),
    ]
    pros_meshes = [trimesh.creation.box(extents=(0.5, 0.5, 0.5))]
    dpn_meshes = [trimesh.creation.box(extents=(0.5, 0.5, 0.5))]

    monkeypatch.setattr(
        "npa.exp_preprocessing.lineage_filter.load_vrml_meshes",
        lambda _path: [],
    )

    call_count = {"n": 0}

    def fake_to_trimesh_list(_meshes: list[tuple[np.ndarray, np.ndarray]]) -> list[trimesh.Trimesh]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return lineage_meshes
        if call_count["n"] == 2:
            return pros_meshes
        return dpn_meshes

    monkeypatch.setattr("npa.exp_preprocessing.lineage_filter.to_trimesh_list", fake_to_trimesh_list)
    monkeypatch.setattr(
        "npa.exp_preprocessing.lineage_filter.assign_cells_to_lineages_by_vertex_bbox",
        lambda *_args, **_kwargs: (np.array([0], dtype=np.int32), np.array([1.0], dtype=np.float32)),
    )
    monkeypatch.setattr(
        "npa.exp_preprocessing.lineage_filter.assign_cells_to_lineages_by_containment",
        lambda *_args, **_kwargs: (np.array([0], dtype=np.int32), np.array([1.0], dtype=np.float32)),
    )
    monkeypatch.setattr(
        "npa.exp_preprocessing.lineage_filter.lineage_is_connected",
        lambda mesh, **_kwargs: bool(mesh is lineage_meshes[1]),
    )

    filtered = load_exp_filtered_lobe(
        lineage_wrl=Path("lineages.wrl"),
        pros_wrl=Path("pros.wrl"),
        dpn_wrl=Path("dpn.wrl"),
        genotype="wt",
        lobe="lobe1",
    )

    assert len(filtered.kept) == 0
    assert len(filtered.rejected) == 2
    assert filtered.rejected[0].lineage_idx == 0
    assert filtered.rejected[0].rejection_reason == "disconnected"
    assert filtered.rejected[1].lineage_idx == 1
    assert filtered.rejected[1].rejection_reason == "no_dpn"


def test_write_rejected_lineage_index(tmp_path: Path) -> None:
    records = [
        {
            "lineage_id": 4,
            "genotype": "wt",
            "lobe": "lobe1",
            "lineage_idx": 3,
            "n_dpn": 0,
            "n_pros": 2,
            "mesh_path": Path("data/exp/processed/meshes/rejected/wt/lobe1_3.npz"),
            "rejection_reason": "no_dpn",
        }
    ]
    out_csv = tmp_path / "rejected_lineage_index.csv"
    write_rejected_lineage_index(records, out_csv)

    text = out_csv.read_text()
    assert (
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,rejection_reason"
        in text
    )
    assert "4,wt,lobe1,3,0,2,data/exp/processed/meshes/rejected/wt/lobe1_3.npz,no_dpn" in text


def test_process_exp_lineage_allows_empty_centroids_when_mesh_only(tmp_path: Path) -> None:
    lineage = ExpRejectedLineage(
        lineage_idx=2,
        lineage_mesh=trimesh.creation.box(extents=(4.0, 4.0, 2.0)),
        dpn_meshes=[],
        pros_meshes=[],
        rejection_reason="disconnected",
    )
    out_path = tmp_path / "rejected_mesh.npz"
    record = process_exp_lineage(
        lineage=lineage,
        mesh_out=out_path,
        lineage_id=0,
        ds=0.3,
        canvas_size=20,
        compute_geo=False,
    )

    assert record["geo"].shape == (20, 20, 2)
    assert float(record["counts"][2]) == 0.0
    with np.load(out_path) as data:
        assert data["dpn_centroids_2d"].shape == (0, 2)
        assert data["pros_centroids_2d"].shape == (0, 2)
        assert data["dpn_centroids_2d_px"].shape == (0, 2)
        assert data["pros_centroids_2d_px"].shape == (0, 2)


# --- mesh_polygon tests ---


def test_mesh_polygon_basic() -> None:
    # L-shaped face set: two rectangles sharing a corner vertex.
    # pts form an L; convex hull would add the upper-right corner region.
    pts_2d = np.array(
        [[0, 0], [4, 0], [4, 2], [0, 2], [0, 4], [2, 4]], dtype=np.float32
    )
    faces = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]], dtype=np.int32)
    poly = mesh_polygon(pts_2d, faces, buffer_px=0.0)
    assert isinstance(poly, ShapelyPolygon)
    assert poly.is_valid
    assert poly.area > 0
    ch = MultiPoint(pts_2d).convex_hull
    assert poly.area <= ch.area


def test_mesh_polygon_buffer() -> None:
    # Square split into two triangles — buffer should produce a valid Polygon.
    pts_2d = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], dtype=np.float32)
    faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
    poly = mesh_polygon(pts_2d, faces, buffer_px=0.1)
    assert isinstance(poly, ShapelyPolygon)
    assert poly.area > 0


def test_mesh_polygon_degenerate_faces_ignored() -> None:
    # Mix of valid triangles and a degenerate collinear face; should not raise.
    pts_2d = np.array(
        [[0, 0], [4, 0], [4, 4], [0, 4], [2, 2], [2, 0]], dtype=np.float32
    )
    # [0,1,5] has all y<=0 with (0,0),(4,0),(2,0) — area == 0, degenerate
    faces = np.array([[0, 1, 2], [0, 2, 3], [0, 4, 5], [0, 1, 5]], dtype=np.int32)
    poly = mesh_polygon(pts_2d, faces, buffer_px=0.0)
    assert poly.is_valid
    assert poly.area > 0


def test_mesh_polygon_bad_inputs() -> None:
    # All faces project to the same point → zero area → no valid triangles
    pts_2d = np.zeros((3, 2), dtype=np.float32)
    faces = np.zeros((1, 3), dtype=np.int32)
    with pytest.raises(ValueError, match="no valid projected triangles"):
        mesh_polygon(pts_2d, faces, buffer_px=0.0)

