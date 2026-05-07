from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from scipy.ndimage import label as _scipy_label

from npa.sim_preprocessing import (
    _load_json,
    build_geo_tensor,
    build_label_map,
    build_raw_tensor,
    index_sim_files,
)

from npa.colors import NB_COLOR, GMC_COLOR as POP2_COLOR, NEURON_COLOR as POP3_COLOR, SIM_HULL_COLOR as HULL_COLOR, PROS_COLOR


def _hex_to_rgb01(hex_color: str) -> np.ndarray:
    vals = [int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5)]
    return np.asarray(vals, dtype=np.float32)


def _label_map_from_channels(*masks: np.ndarray) -> np.ndarray:
    """Connected-component labels across binary masks; later masks take priority on overlap."""
    result = np.zeros(masks[0].shape, dtype=np.int32)
    offset = 0
    for mask in masks:
        labeled, n = _scipy_label(mask > 0)
        result[labeled > 0] = labeled[labeled > 0] + offset
        offset += n
    return result


def _cell_boundary_mask(label_map: np.ndarray) -> np.ndarray:
    """Pixels whose label strictly exceeds any 4-neighbor's label.

    Gives 1-px-wide boundaries: for two touching cells the boundary falls on
    the higher-label side; background (label 0) is never marked.
    """
    mask = np.zeros(label_map.shape, dtype=bool)
    mask[:-1, :] |= label_map[:-1, :] > label_map[1:, :]
    mask[1:, :] |= label_map[1:, :] > label_map[:-1, :]
    mask[:, :-1] |= label_map[:, :-1] > label_map[:, 1:]
    mask[:, 1:] |= label_map[:, 1:] > label_map[:, :-1]
    return mask


def load_sim_npz(npz_path: Path, row: int) -> np.ndarray:
    with np.load(npz_path) as data:
        geo = np.asarray(data["geo"], dtype=np.float32)
    if row < 0 or row >= len(geo):
        raise IndexError(f"row out of range: {row}")
    return geo[row]


def _npz_paths_match(index_value: str, npz_path: Path) -> bool:
    indexed = Path(index_value)
    if indexed == npz_path or indexed.as_posix() == npz_path.as_posix():
        return True
    try:
        return indexed.resolve() == npz_path.resolve()
    except OSError:
        return False


def load_sim_run_index(processed_dir: Path) -> list[dict]:
    rows = pd.read_csv(processed_dir / "sim_run_index.csv", dtype=str)
    return rows.to_dict(orient="records")


def sim_run_index_for_npz(npz_path: Path) -> list[dict]:
    rows = load_sim_run_index(npz_path.parent)
    return [row for row in rows if _npz_paths_match(str(row["npz_path"]), npz_path)]


def resolve_sim_npz_row(npz_path: Path, sim_id: str, run_id: str) -> int:
    matches = [
        row
        for row in sim_run_index_for_npz(npz_path)
        if str(row["sim_id"]) == sim_id and str(row["run_id"]) == run_id
    ]
    if not matches:
        raise ValueError(f"No row found for sim_id={sim_id} run_id={run_id} in {npz_path}")
    if len(matches) > 1:
        raise ValueError(f"Multiple rows found for sim_id={sim_id} run_id={run_id} in {npz_path}")
    return int(matches[0]["npz_row"])


def print_sim_run_index_table(rows: list[dict]) -> None:
    header = (
        f"{'npz_row':>7}  {'sim_id':<8}  {'run_id':<8}  {'time_id':>7}  "
        f"{'n_nb':>5}  {'n_progeny':>10}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{int(row['npz_row']):>7}  {str(row['sim_id']):<8}  {str(row['run_id']):<8}  "
            f"{int(row['time_id']):>7}  {int(row['n_nb']):>5}  {int(row['n_progeny']):>10}"
        )


def load_raw_snapshot_full(cells_path: Path, locs_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Returns (geo_raw (H,W,3), label_map (H,W)) with per-cell IDs for all 3 pop types."""
    cells_json = _load_json(cells_path)
    locs_json = _load_json(locs_path)
    geo_raw = build_raw_tensor(cells_json=cells_json, locs_json=locs_json, canvas_size=200)
    lmap = build_label_map(cells_json=cells_json, locs_json=locs_json, canvas_size=200)
    return geo_raw, lmap


def find_last_snapshot(sim_dir: Path) -> tuple[Path, Path]:
    if not sim_dir.is_dir():
        raise FileNotFoundError(f"sim dir does not exist: {sim_dir}")
    sim_id = sim_dir.name
    condition_dir = sim_dir.parent
    indexed = index_sim_files(condition_dir=condition_dir, sim_ids=[sim_id])
    all_entries = [entry for key, values in indexed.items() if key[0] == sim_id for entry in values]
    if not all_entries:
        raise FileNotFoundError(f"No matched CELLS/LOCATIONS pairs in {sim_dir}")
    _, cells_path, locs_path = max(all_entries, key=lambda item: item[0])
    return cells_path, locs_path


def render_geo(
    geo: np.ndarray,
    ax: Axes | None = None,
    title: str = "",
    label_map: np.ndarray | None = None,
) -> Axes:
    geo = np.asarray(geo, dtype=np.float32)
    if geo.ndim != 3 or geo.shape[2] != 2:
        raise ValueError("geo must have shape (H, W, 2)")
    h, w, _ = geo.shape
    image = np.ones((h, w, 3), dtype=np.float32)
    image[geo[..., 1] > 0] = _hex_to_rgb01(PROS_COLOR)
    image[geo[..., 0] > 0] = _hex_to_rgb01(NB_COLOR)
    if label_map is None:
        label_map = _label_map_from_channels(geo[..., 1], geo[..., 0])
    image[_cell_boundary_mask(label_map)] = _hex_to_rgb01(HULL_COLOR)
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(image, origin="upper", interpolation="nearest")
    ax.set_aspect("equal", adjustable="box")
    if title:
        ax.set_title(title)
    return ax


def add_scale_bar(
    ax: Axes,
    pixels_per_um: float,
    length_um: float = 20,
    color: str = "white",
    lw: float = 2,
    fontsize: int = 7,
) -> None:
    """Horizontal scale bar in the bottom-right corner of a rendered lineage axes.

    Designed for axes produced by render_geo / render_raw (imshow with origin='upper'),
    where ylim[0] is the bottom edge of the image (large data value) and ylim[1] is
    the top edge (small / negative data value).
    """
    bar_px = length_um * pixels_per_um
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()   # inverted: ylim[0] ≈ canvas_size (bottom), ylim[1] ≈ 0 (top)
    margin = (ylim[0] - ylim[1]) * 0.05
    x1 = xlim[1] - margin
    x0 = x1 - bar_px
    y_bar  = ylim[0] - margin
    y_text = y_bar + margin * 0.6
    ax.plot([x0, x1], [y_bar, y_bar], color=color, linewidth=lw, solid_capstyle="butt")
    ax.text(
        (x0 + x1) / 2, y_text, f"{length_um:g} µm",
        ha="center", va="top", color=color, fontsize=fontsize,
    )


def render_raw(
    geo_raw: np.ndarray,
    ax: Axes | None = None,
    title: str = "",
    label_map: np.ndarray | None = None,
) -> Axes:
    """Render 3-channel raw tensor (pop1=NB, pop2, pop3) with per-cell outlines."""
    geo_raw = np.asarray(geo_raw, dtype=np.float32)
    if geo_raw.ndim != 3 or geo_raw.shape[2] != 3:
        raise ValueError("geo_raw must have shape (H, W, 3)")
    h, w, _ = geo_raw.shape
    image = np.ones((h, w, 3), dtype=np.float32)
    image[geo_raw[..., 2] > 0] = _hex_to_rgb01(POP3_COLOR)
    image[geo_raw[..., 1] > 0] = _hex_to_rgb01(POP2_COLOR)
    image[geo_raw[..., 0] > 0] = _hex_to_rgb01(NB_COLOR)
    if label_map is None:
        label_map = _label_map_from_channels(geo_raw[..., 2], geo_raw[..., 1], geo_raw[..., 0])
    image[_cell_boundary_mask(label_map)] = _hex_to_rgb01(HULL_COLOR)
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(image, origin="upper", interpolation="nearest")
    ax.set_aspect("equal", adjustable="box")
    if title:
        ax.set_title(title)
    return ax


