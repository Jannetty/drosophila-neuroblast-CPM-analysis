from pathlib import Path

import numpy as np
import pytest

from npa.exp_viz import DPN_COLOR, HULL_COLOR, load_index, load_lineage_geo, load_mesh_npz, show_2d_post


def test_load_index_kept_and_rejected(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,analysis_row\n"
        "1,wt,lobe1,2,3,4,meshes/wt/lobe1_2.npz,7\n"
    )
    (processed / "rejected_lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,rejection_reason\n"
        "0,wt,lobe1,5,0,2,meshes/rejected/wt/lobe1_5.npz,no_dpn\n"
    )

    kept = load_index(processed, rejected=False)
    rejected = load_index(processed, rejected=True)

    assert kept[0]["analysis_row"] == 7
    assert rejected[0]["rejection_reason"] == "no_dpn"


def test_load_mesh_npz_and_geo_slice(tmp_path: Path) -> None:
    mesh_path = tmp_path / "mesh.npz"
    np.savez_compressed(
        mesh_path,
        lin_vertices=np.zeros((1, 3), dtype=np.float32),
        lin_faces=np.zeros((1, 3), dtype=np.int32),
        dpn_centroids_2d_px=np.array([[2.0, 3.0]], dtype=np.float32),
        pros_centroids_2d_px=np.array([[4.0, 5.0]], dtype=np.float32),
        lin_poly_2d_px=np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32),
        ds=np.asarray(0.3, dtype=np.float32),
    )
    analysis_path = tmp_path / "wt.npz"
    geo = np.zeros((2, 8, 8, 2), dtype=np.float32)
    geo[1, 3, 4, 0] = 1.0
    np.savez_compressed(analysis_path, geo=geo, counts=np.zeros((2, 3)), lineage_ids=np.array([1, 2]))

    mesh = load_mesh_npz(mesh_path)
    lineage_geo = load_lineage_geo(analysis_path, analysis_row=1)

    assert np.isclose(float(mesh["ds"]), 0.3)
    assert lineage_geo.shape == (8, 8, 2)
    assert lineage_geo[3, 4, 0] == 1.0


def test_show_2d_post_reuses_precomputed_px(monkeypatch) -> None:
    class FakeAxes:
        def __init__(self) -> None:
            self.scatter_calls: list[tuple[np.ndarray, np.ndarray]] = []

        def imshow(self, *_args, **_kwargs) -> None:
            return None

        def scatter(self, x, y, **_kwargs) -> None:
            self.scatter_calls.append((np.asarray(x), np.asarray(y)))

        def set_aspect(self, *_args, **_kwargs) -> None:
            return None

        def set_title(self, *_args, **_kwargs) -> None:
            return None

    class FakeFigure:
        pass

    fake_ax = FakeAxes()
    monkeypatch.setattr("npa.exp_viz.plt.subplots", lambda **_kwargs: (FakeFigure(), fake_ax))
    monkeypatch.setattr("npa.exp_viz.plt.show", lambda: None)
    mesh = {
        "dpn_centroids_2d_px": np.array([[9.0, 10.0]], dtype=np.float32),
        "pros_centroids_2d_px": np.array([[11.0, 12.0]], dtype=np.float32),
    }
    geo = np.zeros((20, 20, 2), dtype=np.float32)
    row = {
        "lineage_id": 1,
        "genotype": "wt",
        "lobe": "lobe1",
        "lineage_idx": 0,
        "n_dpn": 1,
        "n_pros": 1,
    }

    show_2d_post(mesh, geo, row)

    assert len(fake_ax.scatter_calls) == 2
    np.testing.assert_allclose(fake_ax.scatter_calls[0][0], [9.0])
    np.testing.assert_allclose(fake_ax.scatter_calls[0][1], [10.0])
    np.testing.assert_allclose(fake_ax.scatter_calls[1][0], [11.0])
    np.testing.assert_allclose(fake_ax.scatter_calls[1][1], [12.0])


def _rgb(hex_color: str) -> np.ndarray:
    raw = hex_color.lstrip("#")
    return np.array([int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def _capture_image(monkeypatch) -> dict:
    captured: dict = {}

    class FakeAxes:
        def imshow(self, img, **_kwargs) -> None:
            captured["image"] = np.asarray(img, dtype=np.float32)

        def scatter(self, *_args, **_kwargs) -> None:
            return None

        def set_aspect(self, *_args, **_kwargs) -> None:
            return None

        def set_title(self, *_args, **_kwargs) -> None:
            return None

    class FakeFigure:
        pass

    monkeypatch.setattr("npa.exp_viz.plt.subplots", lambda **_kwargs: (FakeFigure(), FakeAxes()))
    monkeypatch.setattr("npa.exp_viz.plt.show", lambda: None)
    return captured


def _empty_row() -> dict:
    return {"lineage_id": 1, "genotype": "wt", "lobe": "lobe1", "lineage_idx": 0, "n_dpn": 0, "n_pros": 0}


def _empty_mesh() -> dict:
    return {
        "dpn_centroids_2d_px": np.zeros((0, 2), dtype=np.float32),
        "pros_centroids_2d_px": np.zeros((0, 2), dtype=np.float32),
    }


def test_show_2d_post_isolated_dpn_pixel_is_boundary(monkeypatch) -> None:
    captured = _capture_image(monkeypatch)
    geo = np.zeros((7, 7, 2), dtype=np.float32)
    geo[3, 3, 0] = 1.0  # single DPN pixel surrounded by background (label 0)
    show_2d_post(_empty_mesh(), geo, _empty_row())
    # label[3,3]=1 > all 4 neighbors label=0 → pixel is marked as boundary
    np.testing.assert_allclose(captured["image"][3, 3], _rgb(HULL_COLOR), atol=1e-6)


def test_show_2d_post_interior_dpn_pixel_not_boundary(monkeypatch) -> None:
    captured = _capture_image(monkeypatch)
    geo = np.zeros((9, 9, 2), dtype=np.float32)
    geo[1:6, 1:6, 0] = 1.0  # 5×5 DPN block; center (3,3) is fully interior
    show_2d_post(_empty_mesh(), geo, _empty_row())
    # label[3,3]=1 is not > any neighbor label=1 → pixel is not marked
    np.testing.assert_allclose(captured["image"][3, 3], _rgb(DPN_COLOR), atol=1e-6)


def test_show_2d_post_dpn_pros_boundary_falls_on_pros_side(monkeypatch) -> None:
    captured = _capture_image(monkeypatch)
    geo = np.zeros((7, 7, 2), dtype=np.float32)
    geo[:, :4, 0] = 1.0  # cols 0-3: DPN (label=1)
    geo[:, 4:, 1] = 1.0  # cols 4-6: Pros (label=2)
    show_2d_post(_empty_mesh(), geo, _empty_row())
    # col 3 (DPN side, label=1): 1 > 2 is False → not marked → stays DPN color
    np.testing.assert_allclose(captured["image"][3, 3], _rgb(DPN_COLOR), atol=1e-6)
    # col 4 (Pros side, label=2): 2 > 1 is True → marked as boundary → HULL color
    np.testing.assert_allclose(captured["image"][3, 4], _rgb(HULL_COLOR), atol=1e-6)
