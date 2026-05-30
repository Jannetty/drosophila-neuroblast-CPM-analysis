#!/usr/bin/env python3
"""Extract NB connectivity for mudmut experimental lineages.

For each mudmut lineage, loads the 3D NB meshes from the preprocessed NPZ and
determines whether all NB cells form a single connected component using pairwise
surface-to-surface distances (see npa.metrics.exp_nb_connectivity).

Output:
  data/exp/processed/exp_nb_connectivity.csv

Usage:
    uv run python scripts/extract_exp_nb_connectivity.py \\
        --proc-dir data/exp/processed
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from npa.metrics import exp_nb_connectivity


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--proc-dir", type=Path, default=Path("data/exp/processed"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    index = pd.read_csv(args.proc_dir / "lineage_index.csv")
    mudmut = index[index["genotype"] == "mudmut"].reset_index(drop=True)

    records: list[dict] = []
    for _, row in mudmut.iterrows():
        mesh_path = Path(row["mesh_path"])
        with np.load(mesh_path) as d:
            mesh = dict(d)
        result = exp_nb_connectivity(mesh)
        records.append({
            "lineage_id": int(row["lineage_id"]),
            "genotype": row["genotype"],
            "n_dpn": int(row["n_dpn"]),
            **result,
        })

    df = pd.DataFrame(records)
    out = args.proc_dir / "exp_nb_connectivity.csv"
    df.to_csv(out, index=False)

    n_connected = int(df["nb_connected"].sum())
    print(f"wrote {out} ({len(df)} lineages, {n_connected}/{len(df)} connected)")


if __name__ == "__main__":
    main()
