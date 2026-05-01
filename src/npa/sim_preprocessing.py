from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

CELLS_PATTERN = re.compile(r".*_([0-9]{4})_([0-9]{6})\.CELLS\.json$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _to_repo_relative(path: Path) -> Path:
    resolved = path.resolve()
    root = _repo_root()
    try:
        return resolved.relative_to(root)
    except ValueError:
        return path


def index_sim_files(
    condition_dir: Path,
    sim_ids: list[str],
) -> dict[tuple[str, str], list[tuple[int, Path, Path]]]:
    indexed: dict[tuple[str, str], list[tuple[int, Path, Path]]] = {}
    for sim_id in sorted(sim_ids):
        sim_dir = condition_dir / sim_id
        if not sim_dir.is_dir():
            continue
        for cells_path in sorted(sim_dir.glob("*.CELLS.json")):
            match = CELLS_PATTERN.match(cells_path.name)
            if match is None:
                continue
            run_id = match.group(1)
            time_id = int(match.group(2))
            locs_path = cells_path.with_name(
                cells_path.name.replace(".CELLS.json", ".LOCATIONS.json")
            )
            if not locs_path.exists():
                continue
            key = (sim_id, run_id)
            indexed.setdefault(key, []).append((time_id, cells_path, locs_path))

    sorted_indexed: dict[tuple[str, str], list[tuple[int, Path, Path]]] = {}
    for key in sorted(indexed.keys()):
        sorted_indexed[key] = sorted(indexed[key], key=lambda item: item[0])
    return sorted_indexed


def _pop_map(cells_json: list[dict[str, Any]]) -> dict[int, int]:
    pop_by_id: dict[int, int] = {}
    for cell in cells_json:
        if "id" not in cell or "pop" not in cell:
            continue
        pop_by_id[int(cell["id"])] = int(cell["pop"])
    return pop_by_id


def _parse_voxels(
    locs_json: list[dict[str, Any]],
    canvas_size: int,
) -> tuple[list[tuple[int, list[tuple[int, int]]]], int, int]:
    """Parse location JSON into per-cell voxels with canvas-centering offset."""
    per_cell_voxels: list[tuple[int, list[tuple[int, int]]]] = []
    all_voxels: list[tuple[int, int]] = []
    for loc in locs_json:
        if "id" not in loc:
            continue
        cell_id = int(loc["id"])
        voxels: list[tuple[int, int]] = []
        for region_block in loc.get("location", []):
            for xyz in region_block.get("voxels", []):
                voxels.append((int(xyz[0]), int(xyz[1])))
        if not voxels:
            continue
        per_cell_voxels.append((cell_id, voxels))
        all_voxels.extend(voxels)
    if not all_voxels:
        return per_cell_voxels, 0, 0
    all_xy = np.asarray(all_voxels, dtype=np.float32)
    xmin, ymin = all_xy.min(axis=0)
    xmax, ymax = all_xy.max(axis=0)
    canvas_center = (canvas_size - 1) / 2.0
    dx = int(np.round(canvas_center - (xmin + xmax) / 2.0))
    dy = int(np.round(canvas_center - (ymin + ymax) / 2.0))
    return per_cell_voxels, dx, dy


def build_geo_tensor(
    cells_json: list[dict[str, Any]],
    locs_json: list[dict[str, Any]],
    canvas_size: int = 200,
) -> np.ndarray:
    if canvas_size <= 0:
        raise ValueError("canvas_size must be positive")
    geo = np.zeros((canvas_size, canvas_size, 2), dtype=np.float32)
    pop_by_id = _pop_map(cells_json)
    per_cell_voxels, dx, dy = _parse_voxels(locs_json, canvas_size)
    for cell_id, voxels in per_cell_voxels:
        pop = pop_by_id.get(cell_id)
        if pop is None:
            continue
        for x, y in voxels:
            sx, sy = x + dx, y + dy
            if 0 <= sx < canvas_size and 0 <= sy < canvas_size:
                if pop == 1:
                    geo[sy, sx, 0] = 1.0
                elif pop in {2, 3}:
                    geo[sy, sx, 1] = 1.0
    return geo


def build_raw_tensor(
    cells_json: list[dict[str, Any]],
    locs_json: list[dict[str, Any]],
    canvas_size: int = 200,
) -> np.ndarray:
    """(H, W, 3) float32: channel 0=pop1 (NB), channel 1=pop2, channel 2=pop3."""
    if canvas_size <= 0:
        raise ValueError("canvas_size must be positive")
    geo = np.zeros((canvas_size, canvas_size, 3), dtype=np.float32)
    pop_by_id = _pop_map(cells_json)
    per_cell_voxels, dx, dy = _parse_voxels(locs_json, canvas_size)
    for cell_id, voxels in per_cell_voxels:
        pop = pop_by_id.get(cell_id)
        if pop not in {1, 2, 3}:
            continue
        ch = pop - 1
        for x, y in voxels:
            sx, sy = x + dx, y + dy
            if 0 <= sx < canvas_size and 0 <= sy < canvas_size:
                geo[sy, sx, ch] = 1.0
    return geo


def build_label_map(
    cells_json: list[dict[str, Any]],
    locs_json: list[dict[str, Any]],
    canvas_size: int = 200,
) -> np.ndarray:
    """(H, W) int32 where each pixel value is cell_id (matching cells_json) or 0."""
    label_map = np.zeros((canvas_size, canvas_size), dtype=np.int32)
    pop_by_id = _pop_map(cells_json)
    per_cell_voxels, dx, dy = _parse_voxels(locs_json, canvas_size)
    for cell_id, voxels in per_cell_voxels:
        if cell_id not in pop_by_id:
            continue
        for x, y in voxels:
            sx, sy = x + dx, y + dy
            if 0 <= sx < canvas_size and 0 <= sy < canvas_size:
                label_map[sy, sx] = cell_id
    return label_map


def _load_json(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Corrupt JSON at {path}: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"Expected list JSON at {path}")
    return data


def _counts_from_cells(cells_json: list[dict[str, Any]]) -> np.ndarray:
    n_dpn = 0
    n_pros = 0
    for cell in cells_json:
        pop = cell.get("pop")
        if pop == 1:
            n_dpn += 1
        elif pop in {2, 3}:
            n_pros += 1
    return np.asarray([n_dpn, n_pros], dtype=np.int32)


def process_condition(
    condition_dir: Path,
    sim_ids: list[str],
    out_path: Path,
    canvas_size: int = 200,
) -> dict[str, Any]:
    indexed = index_sim_files(condition_dir=condition_dir, sim_ids=sim_ids)

    geos: list[np.ndarray] = []
    counts: list[np.ndarray] = []
    sim_id_out: list[str] = []
    run_id_out: list[str] = []
    time_id_out: list[int] = []
    row_records: list[dict[str, Any]] = []

    for (sim_id, run_id) in sorted(indexed.keys()):
        time_id, cells_path, locs_path = indexed[(sim_id, run_id)][-1]
        try:
            cells_json = _load_json(cells_path)
            locs_json = _load_json(locs_path)
        except ValueError as exc:
            print(f"  WARNING: skipping ({sim_id}, {run_id}): {exc}")
            continue
        counts_row = _counts_from_cells(cells_json)
        geos.append(build_geo_tensor(cells_json, locs_json, canvas_size=canvas_size))
        counts.append(counts_row)
        row_records.append(
            {
                "condition": condition_dir.name,
                "npz_path": _to_repo_relative(out_path),
                "npz_row": len(geos) - 1,
                "sim_id": sim_id,
                "run_id": run_id,
                "time_id": time_id,
                "n_nb": int(counts_row[0]),
                "n_progeny": int(counts_row[1]),
                "cells_path": _to_repo_relative(cells_path),
                "locs_path": _to_repo_relative(locs_path),
            }
        )
        sim_id_out.append(sim_id)
        run_id_out.append(run_id)
        time_id_out.append(time_id)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if geos:
        geo_arr = np.stack(geos, axis=0).astype(np.float32)
        counts_arr = np.stack(counts, axis=0).astype(np.int32)
    else:
        geo_arr = np.empty((0, canvas_size, canvas_size, 2), dtype=np.float32)
        counts_arr = np.empty((0, 2), dtype=np.int32)

    np.savez_compressed(
        out_path,
        geo=geo_arr,
        counts=counts_arr,
        sim_id=np.asarray(sim_id_out),
        run_id=np.asarray(run_id_out),
        time_id=np.asarray(time_id_out, dtype=np.int32),
        canvas_size=np.asarray(canvas_size, dtype=np.int32),
    )
    return {
        "condition": condition_dir.name,
        "n_runs": int(len(geos)),
        "npz_path": _to_repo_relative(out_path),
        "rows": row_records,
    }


def write_sim_index(records: list[dict[str, Any]], out_path: Path) -> None:
    rows = [
        {
            "condition": rec["condition"],
            "n_runs": int(rec["n_runs"]),
            "npz_path": Path(rec["npz_path"]).as_posix(),
        }
        for rec in records
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["condition", "n_runs", "npz_path"]).to_csv(
        out_path,
        index=False,
    )


def write_sim_run_index(records: list[dict[str, Any]], out_path: Path) -> None:
    rows = [
        {
            "condition": row["condition"],
            "npz_path": Path(row["npz_path"]).as_posix(),
            "npz_row": int(row["npz_row"]),
            "sim_id": str(row["sim_id"]),
            "run_id": str(row["run_id"]),
            "time_id": int(row["time_id"]),
            "n_nb": int(row["n_nb"]),
            "n_progeny": int(row["n_progeny"]),
            "cells_path": Path(row["cells_path"]).as_posix(),
            "locs_path": Path(row["locs_path"]).as_posix(),
        }
        for record in records
        for row in record.get("rows", [])
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        rows,
        columns=[
            "condition",
            "npz_path",
            "npz_row",
            "sim_id",
            "run_id",
            "time_id",
            "n_nb",
            "n_progeny",
            "cells_path",
            "locs_path",
        ],
    ).to_csv(out_path, index=False)
