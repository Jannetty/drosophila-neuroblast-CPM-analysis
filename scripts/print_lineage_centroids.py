#!/usr/bin/env python3
"""Print lineage hull centroids in the original 3D coordinate space (µm).

Usage:
    uv run python scripts/print_lineage_centroids.py 0 29 30 46 48
    uv run python scripts/print_lineage_centroids.py --all
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("lineage_ids", nargs="*", type=int,
                   help="Lineage IDs to look up")
    p.add_argument("--all", action="store_true",
                   help="Print all lineages")
    p.add_argument("--proc-dir", type=Path, default=Path("data/exp/processed"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    index = pd.read_csv(args.proc_dir / "lineage_index.csv")

    if args.all:
        rows = index
    elif args.lineage_ids:
        rows = index[index["lineage_id"].isin(args.lineage_ids)].sort_values("lineage_id")
    else:
        print("Provide lineage IDs or --all.")
        return

    header = f"{'lineage_id':>10}  {'lobe':<10}  {'lineage_idx':>11}  {'x (µm)':>9}  {'y (µm)':>9}  {'z (µm)':>9}"
    print(header)
    print("-" * len(header))

    for _, row in rows.iterrows():
        with np.load(Path(row["mesh_path"])) as d:
            cx, cy, cz = d["pca_mean"]
        print(f"{int(row['lineage_id']):>10}  {row['lobe']:<10}  {int(row['lineage_idx']):>11}  {cx:>9.1f}  {cy:>9.1f}  {cz:>9.1f}")


if __name__ == "__main__":
    main()
