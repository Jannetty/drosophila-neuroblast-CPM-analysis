"""Preprocess calibration-sweep simulation output into a metrics CSV.

The calibrate_sweep file structure is flat: CELLS/LOCATIONS files sit
directly inside each condition folder (no sim_id subfolder), so the generic
preprocess_sim.py + extract_metrics.py chain cannot be used.

Outputs:
  data/sim/processed_calibrate/sim_metrics_last.csv   — one row per run
  data/sim/processed_calibrate/sim_run_index.csv      — run → file mapping
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIB_DIR  = REPO_ROOT / "data" / "sim" / "calibrate_sweep"
OUT_DIR    = REPO_ROOT / "data" / "sim" / "processed_calibrate"

CELLS_RE = re.compile(r".*_([0-9]{4})_([0-9]{6})\.CELLS\.json$")

METRICS_COLS = [
    "condition", "run_id", "time_id",
    "n_dpn", "dpn_area_vox", "avg_dpn_area_vox",
    "n_pros", "lin_area_vox",
]

INDEX_COLS = ["condition", "run_id", "time_id", "cells_path", "locs_path"]


def _condition_dirs() -> list[Path]:
    return sorted(p for p in CALIB_DIR.iterdir() if p.is_dir())


def _last_timepoint_files(
    condition_dir: Path,
) -> dict[str, tuple[int, Path, Path]]:
    """Return {run_id: (time_id, cells_path, locs_path)} for the last timepoint only."""
    best: dict[str, tuple[int, Path, Path]] = {}
    for cells_path in sorted(condition_dir.glob("*.CELLS.json")):
        m = CELLS_RE.match(cells_path.name)
        if m is None:
            continue
        run_id, time_id_str = m.group(1), int(m.group(2))
        locs_path = cells_path.with_name(
            cells_path.name.replace(".CELLS.json", ".LOCATIONS.json")
        )
        if not locs_path.exists():
            continue
        if run_id not in best or time_id_str > best[run_id][0]:
            best[run_id] = (time_id_str, cells_path, locs_path)
    return best


def _compute_metrics(cells_json: list[dict], locs_json: list[dict]) -> dict:
    pops: dict[int, int] = {
        int(c["id"]): int(c["pop"])
        for c in cells_json
        if "id" in c and "pop" in c
    }
    voxel_counts: dict[int, int] = {}
    for loc in locs_json:
        if "id" not in loc:
            continue
        cid = int(loc["id"])
        n = sum(len(rb.get("voxels", [])) for rb in loc.get("location", []))
        voxel_counts[cid] = voxel_counts.get(cid, 0) + n

    by_pop: dict[int, list[int]] = {1: [], 2: [], 3: []}
    for cid, pop in pops.items():
        if pop in by_pop:
            by_pop[pop].append(voxel_counts.get(cid, 0))

    dpn   = by_pop[1]
    pros  = by_pop[2] + by_pop[3]
    dpn_area  = int(sum(dpn))
    pros_area = int(sum(pros))
    avg_dpn   = float(np.mean(dpn)) if dpn else 0.0

    return {
        "n_dpn":          len(dpn),
        "dpn_area_vox":   dpn_area,
        "avg_dpn_area_vox": round(avg_dpn, 4),
        "n_pros":         len(pros),
        "lin_area_vox":   dpn_area + pros_area,
    }


def _to_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUT_DIR / "sim_metrics_last.csv"
    index_path   = OUT_DIR / "sim_run_index.csv"

    metrics_rows: list[dict] = []
    index_rows:   list[dict] = []

    for cond_dir in _condition_dirs():
        condition = cond_dir.name
        last = _last_timepoint_files(cond_dir)
        if not last:
            print(f"WARNING: no CELLS files found in {cond_dir} — skipping")
            continue
        for run_id in sorted(last):
            time_id, cells_path, locs_path = last[run_id]
            try:
                cells_json = json.loads(cells_path.read_text())
                locs_json  = json.loads(locs_path.read_text())
            except Exception as exc:
                print(f"  WARNING: skipping {condition} run {run_id}: {exc}")
                continue
            m = _compute_metrics(cells_json, locs_json)
            metrics_rows.append({
                "condition": condition,
                "run_id":    run_id,
                "time_id":   time_id,
                **m,
            })
            index_rows.append({
                "condition":  condition,
                "run_id":     run_id,
                "time_id":    time_id,
                "cells_path": _to_rel(cells_path),
                "locs_path":  _to_rel(locs_path),
            })
        print(f"{condition}: {len([r for r in metrics_rows if r['condition'] == condition])} runs")

    with open(metrics_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=METRICS_COLS)
        w.writeheader()
        w.writerows(metrics_rows)

    with open(index_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLS)
        w.writeheader()
        w.writerows(index_rows)

    print(f"\nWrote {len(metrics_rows)} rows to {metrics_path}")
    print(f"Wrote {len(index_rows)} rows to {index_path}")


if __name__ == "__main__":
    main()
