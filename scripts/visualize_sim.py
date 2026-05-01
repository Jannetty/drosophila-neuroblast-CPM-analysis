from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from npa.sim_viz import (
    find_last_snapshot,
    load_raw_snapshot_full,
    load_sim_npz,
    print_sim_run_index_table,
    render_geo,
    render_raw,
    resolve_sim_npz_row,
    sim_run_index_for_npz,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize simulation geo tensors.")
    parser.add_argument("--mode", choices=("raw-any", "raw-last", "npz"), required=True)
    parser.add_argument("--cells", type=Path, default=None)
    parser.add_argument("--locs", type=Path, default=None)
    parser.add_argument("--sim-dir", type=Path, default=None)
    parser.add_argument("--npz", type=Path, default=None)
    parser.add_argument("--row", type=int, default=None)
    parser.add_argument("--sim-id", type=str, default=None)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--list", action="store_true", default=False, dest="list_rows")
    parser.add_argument("--title", type=str, default="")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--all-pops",
        action="store_true",
        default=False,
        help="Render all 3 population types separately (raw-any and raw-last only).",
    )
    return parser.parse_args(argv)


def _validate_mode_args(args: argparse.Namespace) -> None:
    if args.mode == "raw-any":
        if args.cells is None or args.locs is None:
            raise SystemExit("--mode raw-any requires --cells and --locs")
    elif args.mode == "raw-last":
        if args.sim_dir is None:
            raise SystemExit("--mode raw-last requires --sim-dir")
    elif args.mode == "npz":
        if args.npz is None:
            raise SystemExit("--mode npz requires --npz")
        if args.list_rows:
            return
        if args.row is None and (args.sim_id is None or args.run_id is None):
            raise SystemExit("--mode npz requires --row or both --sim-id and --run-id")


def _default_title(args: argparse.Namespace, source: Path) -> str:
    if args.title:
        return args.title
    if args.mode == "npz":
        return f"{source.name} row={args.row}"
    return source.name


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _validate_mode_args(args)

    if args.mode == "raw-any":
        assert args.cells is not None and args.locs is not None
        title = _default_title(args, args.cells)
        geo_raw, lmap = load_raw_snapshot_full(args.cells, args.locs)
        if args.all_pops:
            ax = render_raw(geo_raw, label_map=lmap, title=title)
        else:
            geo = np.stack([geo_raw[..., 0], np.clip(geo_raw[..., 1] + geo_raw[..., 2], 0, 1)], axis=-1)
            ax = render_geo(geo, label_map=lmap, title=title)
    elif args.mode == "raw-last":
        assert args.sim_dir is not None
        cells_path, locs_path = find_last_snapshot(args.sim_dir)
        title = _default_title(args, cells_path)
        geo_raw, lmap = load_raw_snapshot_full(cells_path, locs_path)
        if args.all_pops:
            ax = render_raw(geo_raw, label_map=lmap, title=title)
        else:
            geo = np.stack([geo_raw[..., 0], np.clip(geo_raw[..., 1] + geo_raw[..., 2], 0, 1)], axis=-1)
            ax = render_geo(geo, label_map=lmap, title=title)
    else:
        assert args.npz is not None
        if args.list_rows:
            print_sim_run_index_table(sim_run_index_for_npz(args.npz))
            return
        row = args.row
        if row is None:
            assert args.sim_id is not None and args.run_id is not None
            row = resolve_sim_npz_row(args.npz, args.sim_id, args.run_id)
        geo = load_sim_npz(args.npz, row)
        title = args.title if args.title else f"{args.npz.name} row={row}"
        ax = render_geo(geo, title=title)

    fig = ax.figure
    if args.out is not None:
        fig.savefig(args.out, dpi=150, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
