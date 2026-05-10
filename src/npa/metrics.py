from __future__ import annotations

import csv
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import ndimage as _ndi
from scipy.spatial import KDTree

from npa.sim_preprocessing import _load_json, _to_repo_relative, index_sim_files

EXP_METRIC_COLUMNS = [
    "lineage_id",
    "genotype",
    "lobe",
    "lineage_idx",
    "analysis_row",
    "ds",
    "n_dpn",
    "dpn_area_vox",
    "avg_dpn_area_vox",
    "std_dpn_area_vox",
    "n_pros",
    "pros_area_vox",
    "avg_pros_area_vox",
    "std_pros_area_vox",
    "lin_area_vox",
]

SIM_METRIC_COLUMNS = [
    "condition",
    "sim_id",
    "run_id",
    "time_id",
    "cells_path",
    "locs_path",
    "ds",
    "n_dpn",
    "dpn_area_vox",
    "avg_dpn_area_vox",
    "std_dpn_area_vox",
    "n_pros",
    "pros_area_vox",
    "avg_pros_area_vox",
    "std_pros_area_vox",
    "n_gmc",
    "gmc_area_vox",
    "avg_gmc_area_vox",
    "std_gmc_area_vox",
    "n_neuron",
    "neuron_area_vox",
    "avg_neuron_area_vox",
    "std_neuron_area_vox",
    "lin_area_vox",
]

COMPARISON_METRIC_COLUMNS = [
    "n_dpn",
    "avg_dpn_area_vox",
    "lin_area_vox",
    "n_pros",
    "dpn_area_vox",
]

SIM_COMPARISON_INPUT_COLUMNS = [
    "condition",
    "sim_id",
    "run_id",
    "time_id",
    *COMPARISON_METRIC_COLUMNS,
]

SIM_COMPARISON_DTYPES: dict[str, str] = {
    "condition": "string",
    "sim_id": "string",
    "run_id": "string",
    "time_id": "int32",
    "n_dpn": "int32",
    "avg_dpn_area_vox": "float32",
    "lin_area_vox": "int32",
    "n_pros": "int32",
    "dpn_area_vox": "int32",
}

SIM_SELECTED_COLUMNS = [
    "condition",
    "sim_id",
    "run_id",
    "time_id",
    "div_mean",
    "div_stdev",
    "rot_mean",
    "rot_stdev",
    "genotype",
    "critical_volume_mode",
    "regulatory_dynamic",
    *COMPARISON_METRIC_COLUMNS,
]

SIM_SUMMARY_COLUMNS = [
    "condition",
    "sim_id",
    "n_runs",
    "div_mean",
    "div_stdev",
    "rot_mean",
    "rot_stdev",
    "genotype",
    "critical_volume_mode",
    "regulatory_dynamic",
    *[
        column
        for metric in COMPARISON_METRIC_COLUMNS
        for column in (f"{metric}_mean", f"{metric}_std")
    ],
]

EXP_SUMMARY_COLUMNS = [
    "genotype",
    "n_samples",
    *[
        column
        for metric in COMPARISON_METRIC_COLUMNS
        for column in (f"{metric}_mean", f"{metric}_std")
    ],
]

CONDITION_PATTERN = re.compile(
    r"^(?:(?:wt|mudmut)_)?"
    r"(?:adh(?P<adhesion>\d+)_)?"
    r"divMean(?P<div_mean>-?\d+)Stdev(?P<div_stdev>-?\d+)"
    r"(?:_rotMean(?P<rot_mean>-?\d+)Stdev(?P<rot_stdev>-?\d+))?"
    r"(?:_noadhesion|_relrotMean(?P<relrot_mean>\d+)|_relrot|_yoffset\d+)*$"
)

REGULATORY_DYNAMIC_BY_SUFFIX = {
    1: "NONE",
    2: "NB-ABM",
    3: "VOL-ABM",
    4: "NB-PDE",
    5: "VOL-PDE",
}

SIM_SERIES_METADATA = {
    4: {"genotype": "mudmut", "critical_volume_mode": 1},
    5: {"genotype": "mudmut", "critical_volume_mode": 0},
    6: {"genotype": "wt", "critical_volume_mode": 1},
    7: {"genotype": "wt", "critical_volume_mode": 0},
}


def _mean_std(values: list[int] | np.ndarray) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float32)
    if arr.size == 0:
        return np.nan, np.nan
    return float(arr.mean()), float(arr.std())


def _summary_metric_columns(metrics: list[str]) -> list[str]:
    columns: list[str] = []
    for metric in metrics:
        columns.extend([f"{metric}_mean", f"{metric}_std"])
    return columns


def _population_std(values: pd.Series) -> float:
    arr = values.to_numpy(dtype=np.float64, copy=False)
    if arr.size == 0:
        return np.nan
    return float(arr.std(ddof=0))


def _resolve_index_path(processed_dir: Path, path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    candidate = processed_dir / path
    if candidate.exists():
        return candidate
    return Path.cwd() / path


def _load_geo_cache(
    processed_dir: Path,
    genotype: str,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if genotype not in cache:
        with np.load(processed_dir / "analysis" / f"{genotype}.npz") as data:
            cache[genotype] = {
                "geo": np.asarray(data["geo"], dtype=np.float32),
                "ds": float(np.asarray(data["ds"]).item()),
            }
    return cache[genotype]


def _per_cell_counts_from_centroids(
    geo: np.ndarray,
    dpn_centroids_px: np.ndarray,
    pros_centroids_px: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    return (
        _counts_for_channel(geo[..., 0] > 0, dpn_centroids_px),
        _counts_for_channel(geo[..., 1] > 0, pros_centroids_px),
    )


def _counts_for_channel(mask: np.ndarray, centroids_px: np.ndarray) -> np.ndarray:
    centroids = np.asarray(centroids_px, dtype=np.float32).reshape(-1, 2)
    if len(centroids) == 0:
        return np.zeros(0, dtype=np.int32)
    rows, cols = np.where(mask)
    points = np.column_stack([cols.astype(np.float32), rows.astype(np.float32)])
    if len(points) == 0:
        return np.zeros(len(centroids), dtype=np.int32)
    _, nearest = KDTree(centroids).query(points)
    return np.bincount(nearest, minlength=len(centroids)).astype(np.int32)


def extract_exp_metrics(processed_dir: Path) -> pd.DataFrame:
    index = pd.read_csv(processed_dir / "lineage_index.csv")
    rows: list[dict[str, Any]] = []
    geo_cache: dict[str, dict[str, Any]] = {}

    for index_row in index.to_dict(orient="records"):
        genotype = str(index_row["genotype"])
        analysis_row = int(index_row["analysis_row"])
        loaded = _load_geo_cache(processed_dir, genotype, geo_cache)
        geo = loaded["geo"][analysis_row]
        ds = loaded["ds"]
        mesh_path = _resolve_index_path(processed_dir, str(index_row["mesh_path"]))
        with np.load(mesh_path) as mesh:
            dpn_counts, pros_counts = _per_cell_counts_from_centroids(
                geo,
                mesh["dpn_centroids_2d_px"],
                mesh["pros_centroids_2d_px"],
            )

        dpn_area_vox = int((geo[..., 0] > 0).sum())
        pros_area_vox = int((geo[..., 1] > 0).sum())
        lin_area_vox = int(((geo[..., 0] > 0) | (geo[..., 1] > 0)).sum())
        avg_dpn, std_dpn = _mean_std(dpn_counts)
        avg_pros, std_pros = _mean_std(pros_counts)
        rows.append(
            {
                "lineage_id": int(index_row["lineage_id"]),
                "genotype": genotype,
                "lobe": str(index_row["lobe"]),
                "lineage_idx": int(index_row["lineage_idx"]),
                "analysis_row": analysis_row,
                "ds": ds,
                "n_dpn": int(index_row["n_dpn"]),
                "dpn_area_vox": dpn_area_vox,
                "avg_dpn_area_vox": avg_dpn,
                "std_dpn_area_vox": std_dpn,
                "n_pros": int(index_row["n_pros"]),
                "pros_area_vox": pros_area_vox,
                "avg_pros_area_vox": avg_pros,
                "std_pros_area_vox": std_pros,
                "lin_area_vox": lin_area_vox,
            }
        )

    return pd.DataFrame(rows, columns=EXP_METRIC_COLUMNS)


def _condition_dirs(sweep_root: Path, requested: set[str] | None) -> list[Path]:
    dirs = [p for p in sweep_root.iterdir() if p.is_dir()]
    if requested is not None:
        dirs = [p for p in dirs if p.name in requested]
    return sorted(dirs, key=lambda p: p.name)


def _sim_ids(condition_dir: Path, requested: set[str] | None) -> list[str]:
    ids = [p.name for p in condition_dir.iterdir() if p.is_dir()]
    if requested is not None:
        ids = [name for name in ids if name in requested]
    return sorted(ids)


def _cell_pops(cells_json: list[dict[str, Any]]) -> dict[int, int]:
    pops: dict[int, int] = {}
    for cell in cells_json:
        if "id" in cell and "pop" in cell:
            pops[int(cell["id"])] = int(cell["pop"])
    return pops


def _voxel_counts_by_cell(locs_json: list[dict[str, Any]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for loc in locs_json:
        if "id" not in loc:
            continue
        n_voxels = 0
        for region_block in loc.get("location", []):
            n_voxels += len(region_block.get("voxels", []))
        counts[int(loc["id"])] = counts.get(int(loc["id"]), 0) + n_voxels
    return counts


def _sim_metric_row(
    *,
    condition: str,
    sim_id: str,
    run_id: str,
    time_id: int,
    cells_path: Path,
    locs_path: Path,
    ds: float,
    cells_json: list[dict[str, Any]],
    locs_json: list[dict[str, Any]],
) -> dict[str, Any]:
    pops = _cell_pops(cells_json)
    voxel_counts = _voxel_counts_by_cell(locs_json)
    by_pop = {1: [], 2: [], 3: []}
    for cell_id, pop in pops.items():
        if pop in by_pop:
            by_pop[pop].append(int(voxel_counts.get(cell_id, 0)))

    dpn = by_pop[1]
    gmc = by_pop[2]
    neuron = by_pop[3]
    pros = gmc + neuron
    avg_dpn, std_dpn = _mean_std(dpn)
    avg_gmc, std_gmc = _mean_std(gmc)
    avg_neuron, std_neuron = _mean_std(neuron)
    avg_pros, std_pros = _mean_std(pros)
    dpn_area = int(sum(dpn))
    gmc_area = int(sum(gmc))
    neuron_area = int(sum(neuron))
    pros_area = gmc_area + neuron_area
    return {
        "condition": condition,
        "sim_id": sim_id,
        "run_id": run_id,
        "time_id": int(time_id),
        "cells_path": _to_repo_relative(cells_path).as_posix(),
        "locs_path": _to_repo_relative(locs_path).as_posix(),
        "ds": float(ds),
        "n_dpn": len(dpn),
        "dpn_area_vox": dpn_area,
        "avg_dpn_area_vox": avg_dpn,
        "std_dpn_area_vox": std_dpn,
        "n_pros": len(pros),
        "pros_area_vox": pros_area,
        "avg_pros_area_vox": avg_pros,
        "std_pros_area_vox": std_pros,
        "n_gmc": len(gmc),
        "gmc_area_vox": gmc_area,
        "avg_gmc_area_vox": avg_gmc,
        "std_gmc_area_vox": std_gmc,
        "n_neuron": len(neuron),
        "neuron_area_vox": neuron_area,
        "avg_neuron_area_vox": avg_neuron,
        "std_neuron_area_vox": std_neuron,
        "lin_area_vox": dpn_area + pros_area,
    }


def iter_sim_timepoint_metrics(
    sweep_root: Path,
    ds: float = 0.3,
    conditions: list[str] | None = None,
    sim_ids: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    selected_conditions = set(conditions) if conditions else None
    selected_sim_ids = set(sim_ids) if sim_ids else None
    for condition_dir in _condition_dirs(sweep_root, selected_conditions):
        ids = _sim_ids(condition_dir, selected_sim_ids)
        indexed = index_sim_files(condition_dir, ids)
        for (sim_id, run_id), entries in indexed.items():
            for time_id, cells_path, locs_path in entries:
                try:
                    cells_json = _load_json(cells_path)
                    locs_json = _load_json(locs_path)
                except ValueError as exc:
                    print(f"  WARNING: skipping ({sim_id}, {run_id}, {time_id}): {exc}")
                    continue
                yield _sim_metric_row(
                    condition=condition_dir.name,
                    sim_id=sim_id,
                    run_id=run_id,
                    time_id=time_id,
                    cells_path=cells_path,
                    locs_path=locs_path,
                    ds=ds,
                    cells_json=cells_json,
                    locs_json=locs_json,
                )


def extract_sim_timepoint_metrics(
    sweep_root: Path,
    ds: float = 0.3,
    conditions: list[str] | None = None,
    sim_ids: list[str] | None = None,
) -> pd.DataFrame:
    rows = list(iter_sim_timepoint_metrics(sweep_root, ds, conditions, sim_ids))
    return pd.DataFrame(rows, columns=SIM_METRIC_COLUMNS)


def _require_metric_columns(df: pd.DataFrame, metrics: list[str]) -> None:
    missing = [metric for metric in metrics if metric not in df.columns]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing metric columns: {joined}")


def _condition_metadata(condition: str) -> dict[str, Any]:
    match = CONDITION_PATTERN.match(condition)
    if match is None:
        return {
            "adhesion": np.nan,
            "div_mean": np.nan,
            "div_stdev": np.nan,
            "rot_mean": np.nan,
            "rot_stdev": np.nan,
            "relrot": False,
            "relrot_mean": np.nan,
        }
    rot_mean = match.group("rot_mean")
    rot_stdev = match.group("rot_stdev")
    adh_str = match.group("adhesion")
    relrot_mean_str = match.group("relrot_mean")
    return {
        "adhesion": int(adh_str) if adh_str is not None else np.nan,
        "div_mean": int(match.group("div_mean")),
        "div_stdev": int(match.group("div_stdev")),
        "rot_mean": int(rot_mean) if rot_mean is not None else 0,
        "rot_stdev": int(rot_stdev) if rot_stdev is not None else 0,
        "relrot": "_relrot" in condition,
        "relrot_mean": int(relrot_mean_str) if relrot_mean_str is not None else np.nan,
    }


VCV_SIM_METADATA: dict[str, dict[str, Any]] = {
    "vcv1_noreg":   {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "NONE"},
    "vcv1_nb_abm":  {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "NB-ABM"},
    "vcv1_vol_abm": {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "VOL-ABM"},
    "vcv1_nb_pde":  {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "NB-PDE"},
    "vcv1_vol_pde": {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "VOL-PDE"},
    "vcv0_noreg":   {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "NONE"},
    "vcv0_nb_abm":  {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "NB-ABM"},
    "vcv0_vol_abm": {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "VOL-ABM"},
    "vcv0_nb_pde":  {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "NB-PDE"},
    "vcv0_vol_pde": {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "VOL-PDE"},
}


def _sim_metadata(sim_id: str) -> dict[str, Any]:
    if sim_id in VCV_SIM_METADATA:
        return dict(VCV_SIM_METADATA[sim_id])
    digits = "".join(ch for ch in sim_id if ch.isdigit())
    if len(digits) != 2:
        return {
            "genotype": "",
            "critical_volume_mode": np.nan,
            "regulatory_dynamic": "",
        }
    sim_num = int(digits)
    series = sim_num // 10
    suffix = sim_num % 10
    series_meta = SIM_SERIES_METADATA.get(series)
    dynamic = REGULATORY_DYNAMIC_BY_SUFFIX.get(suffix, "")
    if series_meta is None:
        return {
            "genotype": "",
            "critical_volume_mode": np.nan,
            "regulatory_dynamic": dynamic,
        }
    return {
        "genotype": str(series_meta["genotype"]),
        "critical_volume_mode": int(series_meta["critical_volume_mode"]),
        "regulatory_dynamic": dynamic,
    }


def read_sim_comparison_input(
    csv_path: Path,
    conditions: list[str] | None = None,
    sim_ids: list[str] | None = None,
) -> pd.DataFrame:
    df = pd.read_csv(
        csv_path,
        usecols=SIM_COMPARISON_INPUT_COLUMNS,
        dtype=SIM_COMPARISON_DTYPES,
    )
    if conditions:
        df = df.loc[df["condition"].isin(conditions)]
    if sim_ids:
        df = df.loc[df["sim_id"].isin(sim_ids)]
    return df.reset_index(drop=True)


def _select_sim_timepoint_rows(
    df: pd.DataFrame,
    timepoint: str | int = "last",
) -> pd.DataFrame:
    if str(timepoint) == "last":
        last_time = df.groupby(["condition", "sim_id", "run_id"])["time_id"].transform("max")
        return df.loc[df["time_id"] == last_time].copy()
    selected_time = int(timepoint)
    return df.loc[df["time_id"] == selected_time].copy()


def build_selected_sim_metrics(
    df: pd.DataFrame,
    timepoint: str | int = "last",
) -> pd.DataFrame:
    _require_metric_columns(df, COMPARISON_METRIC_COLUMNS)
    selected = _select_sim_timepoint_rows(df, timepoint=timepoint)
    if selected.empty:
        return pd.DataFrame(columns=SIM_SELECTED_COLUMNS)

    condition_meta = (
        selected["condition"].map(_condition_metadata).apply(pd.Series).reset_index(drop=True)
    )
    sim_meta = selected["sim_id"].map(_sim_metadata).apply(pd.Series).reset_index(drop=True)
    merged = pd.concat(
        [selected.reset_index(drop=True), condition_meta, sim_meta],
        axis=1,
    )
    merged = merged.sort_values(
        ["condition", "sim_id", "run_id", "time_id"],
        kind="stable",
    ).reset_index(drop=True)
    return merged.loc[:, SIM_SELECTED_COLUMNS]


def summarize_sim_comparison_rows(df: pd.DataFrame) -> pd.DataFrame:
    _require_metric_columns(df, COMPARISON_METRIC_COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=SIM_SUMMARY_COLUMNS)

    group_cols = [
        "condition",
        "sim_id",
        "div_mean",
        "div_stdev",
        "rot_mean",
        "rot_stdev",
        "genotype",
        "critical_volume_mode",
        "regulatory_dynamic",
    ]
    grouped = df.groupby(group_cols, dropna=False, sort=True)
    summary = grouped.agg(
        n_runs=("run_id", "size"),
        **{
            f"{metric}_mean": (metric, "mean")
            for metric in COMPARISON_METRIC_COLUMNS
        },
        **{
            f"{metric}_std": (metric, _population_std)
            for metric in COMPARISON_METRIC_COLUMNS
        },
    ).reset_index()
    return summary.loc[:, SIM_SUMMARY_COLUMNS]


def summarize_exp_comparison_metrics(df: pd.DataFrame) -> pd.DataFrame:
    _require_metric_columns(df, COMPARISON_METRIC_COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=EXP_SUMMARY_COLUMNS)

    summary = (
        df.groupby("genotype", sort=True)
        .agg(
            n_samples=("genotype", "size"),
            **{
                f"{metric}_mean": (metric, "mean")
                for metric in COMPARISON_METRIC_COLUMNS
            },
            **{
                f"{metric}_std": (metric, _population_std)
                for metric in COMPARISON_METRIC_COLUMNS
            },
        )
        .reset_index()
    )
    return summary.loc[:, EXP_SUMMARY_COLUMNS]


def nb_connectivity(geo: np.ndarray) -> dict[str, Any]:
    """
    Connected-component analysis of the NB pixel region at a single timepoint.

    Parameters
    ----------
    geo : ndarray, shape (H, W, 2)
        Channel 0: NB pixel map (>0 = NB occupied).
        Channel 1: non-NB cell pixel map (unused here).

    Returns
    -------
    dict with keys:
        nb_connected    : bool — True if all NB pixels form one connected component
        nb_n_components : int  — number of connected NB components (0 if no NBs)
        nb_n_pixels     : int  — total NB pixel count
    """
    nb_mask = geo[..., 0] > 0
    n_pixels = int(nb_mask.sum())
    if n_pixels == 0:
        return {"nb_connected": False, "nb_n_components": 0, "nb_n_pixels": 0}
    _, n_comp = _ndi.label(nb_mask)
    return {
        "nb_connected": n_comp == 1,
        "nb_n_components": n_comp,
        "nb_n_pixels": n_pixels,
    }


def write_exp_metrics_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, columns=EXP_METRIC_COLUMNS, index=False)


def write_exp_summary_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, columns=EXP_SUMMARY_COLUMNS, index=False)


def _csv_value(value: Any) -> Any:
    if isinstance(value, float) and not np.isfinite(value):
        return ""
    return value


def write_sim_timepoint_metrics_csv(
    rows: Iterable[dict[str, Any]],
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SIM_METRIC_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {col: _csv_value(row.get(col, "")) for col in SIM_METRIC_COLUMNS}
            )


def write_selected_sim_metrics_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, columns=SIM_SELECTED_COLUMNS, index=False)


def write_sim_summary_csv(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, columns=SIM_SUMMARY_COLUMNS, index=False)
