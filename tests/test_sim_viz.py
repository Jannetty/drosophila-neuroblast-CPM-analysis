import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from npa.sim_viz import (
    HULL_COLOR,
    NB_COLOR,
    POP2_COLOR,
    POP3_COLOR,
    PROS_COLOR,
    find_last_snapshot,
    load_raw_snapshot_full,
    load_sim_npz,
    render_geo,
    render_raw,
)


def _rgb(hex_color: str) -> np.ndarray:
    return np.array([int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5)])


def test_render_geo_nb_priority_and_return_axes() -> None:
    # 9x9 canvas: NB block cols 1-3, pros block cols 5-7 (both 3 wide and 7 tall
    # so each has a pixel fully surrounded by the same label).
    # (4,2) is interior NB — all 4 neighbors are NB.
    # (4,6) is interior pros — all 4 neighbors are pros.
    # (4,2) also gets pros channel set → NB must still win (not a boundary).
    # (4,1) is NB adjacent to background at col 0 → boundary gray.
    geo = np.zeros((9, 9, 2), dtype=np.float32)
    geo[1:8, 1:4, 0] = 1.0   # NB block
    geo[1:8, 5:8, 1] = 1.0   # pros block
    geo[4, 2, 1] = 1.0        # overlap at interior NB pixel: NB must win

    fig, ax = plt.subplots()
    out_ax = render_geo(geo, ax=ax, title="x")

    assert out_ax is ax
    image = ax.images[0].get_array()
    np.testing.assert_allclose(image[4, 2], _rgb(NB_COLOR))     # interior NB (overlap → NB wins)
    np.testing.assert_allclose(image[4, 6], _rgb(PROS_COLOR))   # interior pros
    np.testing.assert_allclose(image[0, 0], [1, 1, 1])          # corner background
    np.testing.assert_allclose(image[4, 1], _rgb(HULL_COLOR))   # NB adjacent to background → gray
    plt.close(fig)


def test_render_geo_per_cell_outline_same_population() -> None:
    # Two NB cells separated by one background pixel then touching: per-cell outlines
    # distinguish them even though they're both pop NB.
    # Cell A: pixel (2,2), Cell B: pixel (2,4) — separated by (2,3)=background.
    # With connected components they get distinct labels → boundary between them and bg.
    geo = np.zeros((7, 7, 2), dtype=np.float32)
    geo[2, 2, 0] = 1.0  # NB cell A (isolated pixel → surrounded by background → boundary)
    geo[2, 4, 0] = 1.0  # NB cell B (isolated pixel → surrounded by background → boundary)

    fig, ax = plt.subplots()
    render_geo(geo, ax=ax)
    image = ax.images[0].get_array()
    # Both single-pixel NB cells are entirely boundary pixels (all neighbors are bg)
    np.testing.assert_allclose(image[2, 2], _rgb(HULL_COLOR))
    np.testing.assert_allclose(image[2, 4], _rgb(HULL_COLOR))
    plt.close(fig)


def test_render_geo_interior_pixel_is_not_boundary() -> None:
    # 5x5 NB block in a 9x9 canvas: center pixel (4,4) has all 4 neighbors also NB
    # → not a boundary → rendered as NB color, not HULL_COLOR.
    geo = np.zeros((9, 9, 2), dtype=np.float32)
    geo[2:7, 2:7, 0] = 1.0
    fig, ax = plt.subplots()
    render_geo(geo, ax=ax)
    image = ax.images[0].get_array()
    np.testing.assert_allclose(image[4, 4], _rgb(NB_COLOR))
    plt.close(fig)


def test_render_raw_colors_and_outline() -> None:
    geo_raw = np.zeros((9, 9, 3), dtype=np.float32)
    geo_raw[1:8, 1:4, 0] = 1.0  # pop1 block
    geo_raw[1:8, 5:8, 1] = 1.0  # pop2 block
    geo_raw[0, 0, 2] = 1.0       # single pop3 pixel → boundary

    fig, ax = plt.subplots()
    out_ax = render_raw(geo_raw, ax=ax, title="raw")

    assert out_ax is ax
    image = ax.images[0].get_array()
    np.testing.assert_allclose(image[4, 2], _rgb(NB_COLOR))    # interior pop1
    np.testing.assert_allclose(image[4, 6], _rgb(POP2_COLOR))  # interior pop2
    np.testing.assert_allclose(image[0, 0], _rgb(HULL_COLOR))  # single-pixel pop3 → boundary
    np.testing.assert_allclose(image[8, 4], [1, 1, 1])         # background not adjacent to any cell
    plt.close(fig)


def test_render_raw_with_label_map() -> None:
    # Passing an explicit label_map overrides connected-component computation.
    geo_raw = np.zeros((5, 5, 3), dtype=np.float32)
    geo_raw[2, 2, 0] = 1.0  # single pop1 pixel

    # Label map marks pixel (2,2) with a label surrounded by same label → NOT boundary.
    label_map = np.zeros((5, 5), dtype=np.int32)
    label_map[1:4, 1:4] = 1  # entire 3x3 block shares label 1

    fig, ax = plt.subplots()
    render_raw(geo_raw, ax=ax, label_map=label_map)
    image = ax.images[0].get_array()
    # (2,2) is pop1 and interior of label 1 → NB color, not boundary
    np.testing.assert_allclose(image[2, 2], _rgb(NB_COLOR))
    plt.close(fig)


def test_render_geo_per_cell_boundary_between_touching_nb_cells() -> None:
    # Two NB cells in adjacent columns — connected components alone would merge them
    # (all NB voxels form one component). A label_map with distinct IDs must produce
    # a boundary at the shared edge even though both cells are the same channel.
    geo = np.zeros((5, 4, 2), dtype=np.float32)
    geo[1:4, 0:2, 0] = 1.0  # NB cell A: cols 0-1
    geo[1:4, 2:4, 0] = 1.0  # NB cell B: cols 2-3
    label_map = np.zeros((5, 4), dtype=np.int32)
    label_map[1:4, 0:2] = 1
    label_map[1:4, 2:4] = 2

    fig, ax = plt.subplots()
    render_geo(geo, ax=ax, label_map=label_map)
    image = ax.images[0].get_array()
    # Boundary falls on the higher-label side (B=2 > A=1): col 2 is gray
    np.testing.assert_allclose(image[2, 2], _rgb(HULL_COLOR))
    # Col 1 (A's edge, lower label) is not on the boundary side → NB color
    np.testing.assert_allclose(image[2, 1], _rgb(NB_COLOR))
    plt.close(fig)


def test_load_raw_snapshot_full(tmp_path: Path) -> None:
    cells = [{"id": 1, "pop": 1}, {"id": 2, "pop": 2}, {"id": 3, "pop": 3}]
    locs = [
        {"id": 1, "center": [0, 0, 0], "location": [{"region": "x", "voxels": [[0, 0, 0]]}]},
        {"id": 2, "center": [0, 0, 0], "location": [{"region": "x", "voxels": [[2, 2, 0]]}]},
        {"id": 3, "center": [0, 0, 0], "location": [{"region": "x", "voxels": [[4, 4, 0]]}]},
    ]
    cells_path = tmp_path / "a.CELLS.json"
    locs_path = tmp_path / "a.LOCATIONS.json"
    cells_path.write_text(json.dumps(cells))
    locs_path.write_text(json.dumps(locs))

    geo_raw, lmap = load_raw_snapshot_full(cells_path, locs_path)
    assert geo_raw.shape == (200, 200, 3)
    assert lmap.shape == (200, 200)
    assert geo_raw[..., 0].sum() == 1.0
    assert geo_raw[..., 1].sum() == 1.0
    assert geo_raw[..., 2].sum() == 1.0
    # Each cell has a distinct non-zero label
    assert len({lmap[lmap > 0].flat[i] for i in range(lmap[lmap > 0].size)}) == 3


def test_find_last_snapshot_uses_highest_time_id(tmp_path: Path) -> None:
    condition_dir = tmp_path / "cond"
    sim_dir = condition_dir / "sim41"
    sim_dir.mkdir(parents=True)
    (sim_dir / "x_0001_000010.CELLS.json").write_text("[]")
    (sim_dir / "x_0001_000010.LOCATIONS.json").write_text("[]")
    (sim_dir / "x_0001_000200.CELLS.json").write_text("[]")
    (sim_dir / "x_0001_000200.LOCATIONS.json").write_text("[]")

    cells_path, locs_path = find_last_snapshot(sim_dir)
    assert cells_path.name.endswith("_000200.CELLS.json")
    assert locs_path.name.endswith("_000200.LOCATIONS.json")


def test_load_sim_npz(tmp_path: Path) -> None:
    npz_path = tmp_path / "cond.npz"
    geo = np.zeros((2, 5, 5, 2), dtype=np.float32)
    geo[1, 3, 4, 1] = 1.0
    np.savez_compressed(npz_path, geo=geo)
    out = load_sim_npz(npz_path, row=1)
    assert out.shape == (5, 5, 2)
    assert out[3, 4, 1] == 1.0
