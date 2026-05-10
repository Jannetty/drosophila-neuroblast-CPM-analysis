#!/usr/bin/env python3
"""Extract NB spatial metrics for the adhesion decoupling sweep.

Reads the NPZ geo arrays produced by preprocess_sim.py and computes three
groups of metrics at the final timepoint for every run:
  - heterotypic contact fraction
  - NB exposure fraction
  - NB cohesion fraction
  - NB connectivity

Outputs three CSVs to --proc-dir:
  het_contact_metrics.csv
  nb_cohesion_metrics.csv
  nb_connectivity_metrics.csv

Usage:
    uv run python scripts/extract_adhesion_metrics.py \\
        --proc-dir data/sim/processed_decoupling_adhesion
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from npa.metrics import _condition_metadata, _sim_metadata, nb_connectivity


# ── Spatial metric functions (ported from notebooks/adhesion_comparison.ipynb) ─


def heterotypic_contact_fraction(geo: np.ndarray) -> dict:
    nb = geo[..., 0] > 0
    nonnb = geo[..., 1] > 0
    occ = nb | nonnb
    n_occ = int(occ.sum())
    if n_occ == 0:
        return dict(het_frac=np.nan, norm_het_frac=np.nan,
                    p_nb=np.nan, p_nonnb=np.nan, n_occupied=0)
    p_nb_val = float(nb[occ].mean())
    p_nonnb_val = float(nonnb[occ].mean())
    both_h = occ[:, :-1] & occ[:, 1:]
    het_h = both_h & (nb[:, :-1] ^ nb[:, 1:])
    both_v = occ[:-1, :] & occ[1:, :]
    het_v = both_v & (nb[:-1, :] ^ nb[1:, :])
    total = int(both_h.sum()) + int(both_v.sum())
    het = int(het_h.sum()) + int(het_v.sum())
    if total == 0:
        return dict(het_frac=np.nan, norm_het_frac=np.nan,
                    p_nb=p_nb_val, p_nonnb=p_nonnb_val, n_occupied=n_occ)
    hf = het / total
    expected = 2.0 * p_nb_val * p_nonnb_val
    norm_hf = (hf / expected) if expected > 0 else np.nan
    return dict(het_frac=hf, norm_het_frac=norm_hf,
                p_nb=p_nb_val, p_nonnb=p_nonnb_val, n_occupied=n_occ)


def nb_exposure_fraction(geo: np.ndarray) -> dict:
    nb = geo[..., 0] > 0
    nonnb = geo[..., 1] > 0
    emp = ~(nb | nonnb)
    n_exposed = n_contact = 0
    for nb_edge, emp_side, nonnb_side in [
        (nb[:, :-1] & ~nb[:, 1:],  emp[:, 1:],  nonnb[:, 1:]),
        (nb[:, 1:]  & ~nb[:, :-1], emp[:, :-1], nonnb[:, :-1]),
        (nb[:-1, :] & ~nb[1:, :],  emp[1:, :],  nonnb[1:, :]),
        (nb[1:, :]  & ~nb[:-1, :], emp[:-1, :], nonnb[:-1, :]),
    ]:
        n_exposed += int((nb_edge & emp_side).sum())
        n_contact += int((nb_edge & nonnb_side).sum())
    n_perimeter = n_exposed + n_contact
    if n_perimeter == 0:
        return dict(exposed_frac=np.nan, n_exposed=0, n_contact=0, n_perimeter=0)
    return dict(exposed_frac=n_exposed / n_perimeter,
                n_exposed=n_exposed, n_contact=n_contact, n_perimeter=n_perimeter)


def nb_cohesion_fraction(geo: np.ndarray) -> float:
    nb = geo[..., 0] > 0
    nonnb = geo[..., 1] > 0
    emp = ~(nb | nonnb)
    n_nb_nb = (
        int((nb[:, :-1] & nb[:, 1:]).sum()) +
        int((nb[:-1, :] & nb[1:, :]).sum())
    )
    n_exposed = n_contact = 0
    for nb_edge, emp_side, nonnb_side in [
        (nb[:, :-1] & ~nb[:, 1:],  emp[:, 1:],  nonnb[:, 1:]),
        (nb[:, 1:]  & ~nb[:, :-1], emp[:, :-1], nonnb[:, :-1]),
        (nb[:-1, :] & ~nb[1:, :],  emp[1:, :],  nonnb[1:, :]),
        (nb[1:, :]  & ~nb[:-1, :], emp[:-1, :], nonnb[:-1, :]),
    ]:
        n_exposed += int((nb_edge & emp_side).sum())
        n_contact += int((nb_edge & nonnb_side).sum())
    total = n_nb_nb + n_exposed + n_contact
    return n_nb_nb / total if total > 0 else np.nan


# ── Main ───────────────────────────────────────────────────────────────────────


def _build_metadata(run_idx: pd.DataFrame) -> pd.DataFrame:
    cond_meta = run_idx["condition"].map(_condition_metadata).apply(pd.Series)
    sim_meta = run_idx["sim_id"].map(_sim_metadata).apply(pd.Series)
    enriched = pd.concat([run_idx, cond_meta, sim_meta], axis=1)
    return enriched[
        ["condition", "sim_id", "adhesion", "div_stdev", "relrot", "relrot_mean",
         "critical_volume_mode", "regulatory_dynamic"]
    ].drop_duplicates()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--proc-dir", type=Path,
                   default=Path("data/sim/processed_decoupling_adhesion"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    run_idx = pd.read_csv(args.proc_dir / "sim_run_index.csv")
    meta = _build_metadata(run_idx)

    het_records: list[dict] = []
    exp_records: list[dict] = []
    coh_records: list[dict] = []
    conn_records: list[dict] = []

    for npz_path_str, group in run_idx.groupby("npz_path"):
        with np.load(Path(npz_path_str)) as d:
            geo_all = d["geo"]
        for _, row in group.iterrows():
            geo = geo_all[int(row["npz_row"])]
            base = {
                "condition": row["condition"],
                "sim_id": row["sim_id"],
                "run_id": row["run_id"],
            }
            het_records.append({**base, **heterotypic_contact_fraction(geo)})
            exp_records.append({**base, **nb_exposure_fraction(geo)})
            coh_records.append({**base, "nb_cohesion_frac": nb_cohesion_fraction(geo)})
            conn_records.append({**base, **nb_connectivity(geo)})

    for records, fname in [
        (het_records,  "het_contact_metrics.csv"),
        (exp_records,  "nb_exposure_metrics.csv"),
        (coh_records,  "nb_cohesion_metrics.csv"),
        (conn_records, "nb_connectivity_metrics.csv"),
    ]:
        df = pd.DataFrame(records).merge(meta, on=["condition", "sim_id"], how="left")
        out = args.proc_dir / fname
        df.to_csv(out, index=False)
        print(f"wrote {out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
