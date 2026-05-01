from __future__ import annotations

import argparse
from pathlib import Path

from npa.exp_viz import (
    load_index,
    load_lineage_geo,
    load_mesh_npz,
    print_index_table,
    show_2d_post,
    show_2d_pre,
    show_3d,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_processed_dir() -> Path:
    return _repo_root() / "data" / "exp" / "processed"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize experimental lineage outputs.")
    parser.add_argument("--list", action="store_true", dest="list_rows")
    parser.add_argument("--row", type=int, default=None)
    parser.add_argument("--id", type=int, default=None, dest="lineage_id")
    parser.add_argument("--view", choices=("3d", "2d-pre", "2d-post"), default="3d")
    parser.add_argument("--rejected", action="store_true")
    return parser.parse_args(argv)


def _resolve_row(rows: list[dict], row: int | None, lineage_id: int | None) -> dict:
    if row is not None:
        if row < 0 or row >= len(rows):
            raise IndexError(f"--row out of range: {row}")
        return rows[row]
    if lineage_id is not None:
        for item in rows:
            if int(item["lineage_id"]) == lineage_id:
                return item
        raise ValueError(f"lineage_id not found: {lineage_id}")
    raise ValueError("No lineage selected. Pass --row or --id.")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    processed_dir = default_processed_dir()
    rows = load_index(processed_dir, rejected=args.rejected)

    if args.list_rows or (args.row is None and args.lineage_id is None):
        print_index_table(rows, rejected=args.rejected)
        return

    row = _resolve_row(rows, args.row, args.lineage_id)
    mesh_path = _repo_root() / row["mesh_path"]
    mesh = load_mesh_npz(mesh_path)

    if args.view == "3d":
        show_3d(mesh, row)
        return
    if args.view == "2d-pre":
        show_2d_pre(mesh, row)
        return
    if args.rejected:
        raise ValueError("2d-post view is unavailable for rejected lineages.")

    analysis_path = processed_dir / "analysis" / f'{row["genotype"]}.npz'
    geo = load_lineage_geo(analysis_path, int(row["analysis_row"]))
    show_2d_post(mesh, geo, row)


if __name__ == "__main__":
    main()
