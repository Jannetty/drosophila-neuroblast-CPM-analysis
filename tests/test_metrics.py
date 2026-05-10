import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from npa.metrics import (
    COMPARISON_METRIC_COLUMNS,
    EXP_METRIC_COLUMNS,
    EXP_SUMMARY_COLUMNS,
    SIM_COMPARISON_INPUT_COLUMNS,
    SIM_METRIC_COLUMNS,
    SIM_SELECTED_COLUMNS,
    SIM_SUMMARY_COLUMNS,
    _condition_metadata,
    build_selected_sim_metrics,
    extract_exp_metrics,
    extract_sim_timepoint_metrics,
    nb_connectivity,
    read_sim_comparison_input,
    summarize_exp_comparison_metrics,
    summarize_sim_comparison_rows,
    write_sim_timepoint_metrics_csv,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload))


def test_extract_exp_metrics_voxel_totals_means_and_stds(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    analysis = processed / "analysis"
    mesh_dir = processed / "meshes" / "wt"
    analysis.mkdir(parents=True)
    mesh_dir.mkdir(parents=True)
    (processed / "lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,analysis_row\n"
        "7,wt,lobe1,2,2,2,meshes/wt/lobe1_2.npz,0\n"
    )

    geo = np.zeros((1, 4, 6, 2), dtype=np.float32)
    geo[0, 1, 0:2, 0] = 1.0
    geo[0, 1, 2, 0] = 1.0
    geo[0, 2, 0, 0] = 1.0
    geo[0, 2, 1:4, 1] = 1.0
    geo[0, 2, 4, 1] = 1.0
    np.savez_compressed(
        analysis / "wt.npz",
        geo=geo,
        counts=np.asarray([[2, 2, 4]], dtype=np.float32),
        lineage_ids=np.asarray([7], dtype=np.int32),
        ds=np.asarray(0.3, dtype=np.float32),
    )
    np.savez_compressed(
        mesh_dir / "lobe1_2.npz",
        lin_poly_2d_px=np.asarray([[0, 0], [5, 0], [5, 3], [0, 3]], dtype=np.float32),
        dpn_centroids_2d_px=np.asarray([[0, 1], [2, 1]], dtype=np.float32),
        pros_centroids_2d_px=np.asarray([[2, 2], [4, 2]], dtype=np.float32),
    )

    out = extract_exp_metrics(processed)

    assert out.columns.tolist() == EXP_METRIC_COLUMNS
    row = out.iloc[0].to_dict()
    assert row["lineage_id"] == 7
    assert row["n_dpn"] == 2
    assert row["n_pros"] == 2
    assert row["dpn_area_vox"] == 4
    assert row["pros_area_vox"] == 4
    assert row["lin_area_vox"] == 8
    assert row["avg_dpn_area_vox"] == 2.0
    assert row["std_dpn_area_vox"] == 1.0
    assert row["avg_pros_area_vox"] == 2.0
    assert row["std_pros_area_vox"] == 1.0
    assert not any(col.endswith("_um2") for col in out.columns)


def test_extract_sim_timepoint_metrics_voxel_only_with_stds(tmp_path: Path) -> None:
    condition = tmp_path / "sweep" / "condA"
    sim_dir = condition / "sim01"
    sim_dir.mkdir(parents=True)
    cells = [
        {"id": 1, "pop": 1},
        {"id": 2, "pop": 1},
        {"id": 3, "pop": 2},
        {"id": 4, "pop": 2},
        {"id": 5, "pop": 3},
    ]
    locs_t1 = [
        {"id": 1, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[0, 0, 0], [1, 0, 0]]}]},
        {"id": 2, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[2, 0, 0]]}]},
        {"id": 3, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[3, 0, 0], [4, 0, 0], [5, 0, 0]]}]},
        {"id": 4, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[6, 0, 0]]}]},
        {"id": 5, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[7, 0, 0], [8, 0, 0]]}]},
    ]
    locs_t2 = [
        {"id": 1, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[0, 0, 0]]}]},
        {"id": 2, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[1, 0, 0]]}]},
        {"id": 3, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[2, 0, 0]]}]},
        {"id": 4, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[3, 0, 0]]}]},
        {"id": 5, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[4, 0, 0]]}]},
    ]
    _write_json(sim_dir / "x_0001_000001.CELLS.json", cells)
    _write_json(sim_dir / "x_0001_000001.LOCATIONS.json", locs_t1)
    _write_json(sim_dir / "x_0001_000002.CELLS.json", cells)
    _write_json(sim_dir / "x_0001_000002.LOCATIONS.json", locs_t2)

    out = extract_sim_timepoint_metrics(tmp_path / "sweep", ds=0.3)

    assert out.columns.tolist() == SIM_METRIC_COLUMNS
    assert out["time_id"].tolist() == [1, 2]
    row = out.iloc[0].to_dict()
    assert row["condition"] == "condA"
    assert row["sim_id"] == "sim01"
    assert row["run_id"] == "0001"
    assert row["n_dpn"] == 2
    assert row["dpn_area_vox"] == 3
    assert row["avg_dpn_area_vox"] == 1.5
    assert row["std_dpn_area_vox"] == 0.5
    assert row["n_gmc"] == 2
    assert row["gmc_area_vox"] == 4
    assert row["avg_gmc_area_vox"] == 2.0
    assert row["std_gmc_area_vox"] == 1.0
    assert row["n_neuron"] == 1
    assert row["neuron_area_vox"] == 2
    assert row["avg_neuron_area_vox"] == 2.0
    assert row["std_neuron_area_vox"] == 0.0
    assert row["n_pros"] == 3
    assert row["pros_area_vox"] == 6
    assert row["avg_pros_area_vox"] == 2.0
    np.testing.assert_allclose(row["std_pros_area_vox"], np.std([3, 1, 2]))
    assert row["lin_area_vox"] == 9
    assert not any(col.endswith("_um2") for col in out.columns)


def test_write_sim_timepoint_metrics_csv_streams_generator(tmp_path: Path) -> None:
    consumed: list[int] = []

    def rows():
        for i in range(2):
            consumed.append(i)
            row = {col: "" for col in SIM_METRIC_COLUMNS}
            row.update(
                {
                    "condition": "cond",
                    "sim_id": "sim01",
                    "run_id": f"{i + 1:04d}",
                    "time_id": i,
                    "ds": 0.3,
                    "n_dpn": 1,
                    "dpn_area_vox": 2,
                    "avg_dpn_area_vox": 2.0,
                    "std_dpn_area_vox": 0.0,
                    "avg_pros_area_vox": np.nan,
                    "std_pros_area_vox": np.nan,
                    "lin_area_vox": 2,
                }
            )
            yield row

    out_path = tmp_path / "sim_timepoint_metrics.csv"
    write_sim_timepoint_metrics_csv(rows(), out_path)

    assert consumed == [0, 1]
    with out_path.open(newline="") as f:
        written = list(csv.DictReader(f))
    assert len(written) == 2
    assert written[0]["run_id"] == "0001"
    assert written[0]["avg_pros_area_vox"] == ""
    assert written[0]["std_pros_area_vox"] == ""


def test_read_select_and_summarize_sim_comparison_metrics(tmp_path: Path) -> None:
    sim_metrics = pd.DataFrame(
        [
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 0,
                "cells_path": "a",
                "locs_path": "b",
                "n_dpn": 10,
                "avg_dpn_area_vox": 100.0,
                "lin_area_vox": 500,
                "n_pros": 20,
                "dpn_area_vox": 1000,
            },
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 5,
                "cells_path": "a",
                "locs_path": "b",
                "n_dpn": 12,
                "avg_dpn_area_vox": 110.0,
                "lin_area_vox": 520,
                "n_pros": 22,
                "dpn_area_vox": 1050,
            },
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0002",
                "time_id": 0,
                "cells_path": "a",
                "locs_path": "b",
                "n_dpn": 14,
                "avg_dpn_area_vox": 120.0,
                "lin_area_vox": 540,
                "n_pros": 24,
                "dpn_area_vox": 1100,
            },
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0002",
                "time_id": 7,
                "cells_path": "a",
                "locs_path": "b",
                "n_dpn": 16,
                "avg_dpn_area_vox": 130.0,
                "lin_area_vox": 560,
                "n_pros": 26,
                "dpn_area_vox": 1150,
            },
            {
                "condition": "divMean0Stdev0_rotMean34Stdev43",
                "sim_id": "sim64",
                "run_id": "0001",
                "time_id": 3,
                "cells_path": "a",
                "locs_path": "b",
                "n_dpn": 8,
                "avg_dpn_area_vox": 90.0,
                "lin_area_vox": 400,
                "n_pros": 18,
                "dpn_area_vox": 700,
            },
        ]
    )
    csv_path = tmp_path / "sim_timepoint_metrics.csv"
    sim_metrics.to_csv(csv_path, index=False)

    loaded = read_sim_comparison_input(csv_path, sim_ids=["sim43", "sim64"])
    assert loaded.columns.tolist() == SIM_COMPARISON_INPUT_COLUMNS
    assert loaded["run_id"].tolist()[0] == "0001"
    assert "cells_path" not in loaded.columns
    assert loaded["run_id"].dtype.name == "string"

    selected = build_selected_sim_metrics(loaded, timepoint="last")
    assert selected.columns.tolist() == SIM_SELECTED_COLUMNS
    assert selected[["condition", "sim_id", "run_id", "time_id"]].to_dict("records") == [
        {
            "condition": "divMean0Stdev0_rotMean34Stdev43",
            "sim_id": "sim64",
            "run_id": "0001",
            "time_id": 3,
        },
        {
            "condition": "divMean36Stdev30_rotMean0Stdev30",
            "sim_id": "sim43",
            "run_id": "0001",
            "time_id": 5,
        },
        {
            "condition": "divMean36Stdev30_rotMean0Stdev30",
            "sim_id": "sim43",
            "run_id": "0002",
            "time_id": 7,
        },
    ]

    sim43_row = selected.loc[selected["sim_id"] == "sim43"].iloc[0]
    assert sim43_row["div_mean"] == 36
    assert sim43_row["div_stdev"] == 30
    assert sim43_row["rot_mean"] == 0
    assert sim43_row["rot_stdev"] == 30
    assert sim43_row["genotype"] == "mudmut"
    assert sim43_row["critical_volume_mode"] == 1
    assert sim43_row["regulatory_dynamic"] == "VOL-ABM"

    explicit = build_selected_sim_metrics(loaded, timepoint=0)
    assert explicit["time_id"].tolist() == [0, 0]
    assert explicit["run_id"].tolist() == ["0001", "0002"]

    summary = summarize_sim_comparison_rows(selected)
    assert summary.columns.tolist() == SIM_SUMMARY_COLUMNS
    row = summary.loc[
        (summary["condition"] == "divMean36Stdev30_rotMean0Stdev30")
        & (summary["sim_id"] == "sim43")
    ].iloc[0]
    assert row["n_runs"] == 2
    assert row["n_dpn_mean"] == 14.0
    assert row["n_dpn_std"] == 2.0
    assert row["avg_dpn_area_vox_mean"] == 120.0
    assert row["avg_dpn_area_vox_std"] == 10.0
    assert row["lin_area_vox_mean"] == 540.0
    assert row["lin_area_vox_std"] == 20.0
    assert row["n_pros_mean"] == 24.0
    assert row["n_pros_std"] == 2.0
    assert row["dpn_area_vox_mean"] == 1100.0
    assert row["dpn_area_vox_std"] == 50.0


def test_summarize_exp_comparison_metrics_groups_by_genotype() -> None:
    exp_metrics = pd.DataFrame(
        [
            {
                "genotype": "mudmut",
                "n_dpn": 2,
                "avg_dpn_area_vox": 50.0,
                "lin_area_vox": 300,
                "n_pros": 10,
                "dpn_area_vox": 100,
            },
            {
                "genotype": "mudmut",
                "n_dpn": 4,
                "avg_dpn_area_vox": 70.0,
                "lin_area_vox": 500,
                "n_pros": 14,
                "dpn_area_vox": 200,
            },
            {
                "genotype": "wt",
                "n_dpn": 6,
                "avg_dpn_area_vox": 90.0,
                "lin_area_vox": 700,
                "n_pros": 18,
                "dpn_area_vox": 300,
            },
        ]
    )

    summary = summarize_exp_comparison_metrics(exp_metrics)

    assert summary.columns.tolist() == EXP_SUMMARY_COLUMNS
    mudmut = summary.loc[summary["genotype"] == "mudmut"].iloc[0]
    assert mudmut["n_samples"] == 2
    assert mudmut["n_dpn_mean"] == 3.0
    assert mudmut["n_dpn_std"] == 1.0
    assert mudmut["avg_dpn_area_vox_mean"] == 60.0
    assert mudmut["avg_dpn_area_vox_std"] == 10.0
    assert mudmut["lin_area_vox_mean"] == 400.0
    assert mudmut["lin_area_vox_std"] == 100.0
    assert mudmut["n_pros_mean"] == 12.0
    assert mudmut["n_pros_std"] == 2.0
    assert mudmut["dpn_area_vox_mean"] == 150.0
    assert mudmut["dpn_area_vox_std"] == 50.0
    assert summary.loc[summary["genotype"] == "wt", "n_samples"].item() == 1
    assert summary.loc[summary["genotype"] == "wt", "n_dpn_std"].item() == 0.0
    assert COMPARISON_METRIC_COLUMNS == [
        "n_dpn",
        "avg_dpn_area_vox",
        "lin_area_vox",
        "n_pros",
        "dpn_area_vox",
    ]


def test_condition_metadata_new_format() -> None:
    wt = _condition_metadata("wt_divMean0Stdev26")
    assert wt["div_mean"] == 0
    assert wt["div_stdev"] == 26
    assert wt["rot_mean"] == 0
    assert wt["rot_stdev"] == 0

    mm = _condition_metadata("mudmut_divMean11Stdev26_rotMean11Stdev30")
    assert mm["div_mean"] == 11
    assert mm["div_stdev"] == 26
    assert mm["rot_mean"] == 11
    assert mm["rot_stdev"] == 30

    old = _condition_metadata("divMean36Stdev30_rotMean0Stdev30")
    assert old["div_mean"] == 36
    assert old["div_stdev"] == 30
    assert old["rot_mean"] == 0
    assert old["rot_stdev"] == 30

    bad = _condition_metadata("garbage")
    assert np.isnan(bad["div_mean"])


def test_build_selected_sim_metrics_supports_future_wt_vcv0_series() -> None:
    sim_metrics = pd.DataFrame(
        [
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim74",
                "run_id": "0001",
                "time_id": 434,
                "n_dpn": 3,
                "avg_dpn_area_vox": 140.0,
                "lin_area_vox": 850,
                "n_pros": 18,
                "dpn_area_vox": 600,
            }
        ]
    )

    selected = build_selected_sim_metrics(sim_metrics, timepoint="last")

    row = selected.iloc[0]
    assert row["genotype"] == "wt"
    assert row["critical_volume_mode"] == 0
    assert row["regulatory_dynamic"] == "NB-PDE"


def test_nb_connectivity_single_blob() -> None:
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[3:6, 3:6, 0] = 1
    r = nb_connectivity(geo)
    assert r["nb_connected"] is True
    assert r["nb_n_components"] == 1
    assert r["nb_n_pixels"] == 9


def test_nb_connectivity_two_separate_blobs() -> None:
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[1:3, 1:3, 0] = 1   # blob A — 4 pixels
    geo[7:9, 7:9, 0] = 1   # blob B — 4 pixels, no adjacency with A
    r = nb_connectivity(geo)
    assert r["nb_connected"] is False
    assert r["nb_n_components"] == 2
    assert r["nb_n_pixels"] == 8


def test_nb_connectivity_no_nbs() -> None:
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[2:5, 2:5, 1] = 1   # only non-NB cells present
    r = nb_connectivity(geo)
    assert r["nb_connected"] is False
    assert r["nb_n_components"] == 0
    assert r["nb_n_pixels"] == 0


def test_nb_connectivity_single_pixel() -> None:
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[5, 5, 0] = 1
    r = nb_connectivity(geo)
    assert r["nb_connected"] is True
    assert r["nb_n_components"] == 1
    assert r["nb_n_pixels"] == 1


def test_nb_connectivity_l_shaped_blob_is_connected() -> None:
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[2:5, 2, 0] = 1   # vertical bar
    geo[4, 2:5, 0] = 1   # horizontal bar — L-shape, all touching
    r = nb_connectivity(geo)
    assert r["nb_connected"] is True
    assert r["nb_n_components"] == 1
