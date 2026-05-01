import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "summarize_metrics.py"
SPEC = importlib.util.spec_from_file_location("summarize_metrics", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def test_summarize_metrics_cli_writes_default_outputs_and_filters(tmp_path: Path) -> None:
    sim_metrics = pd.DataFrame(
        [
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 1,
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
                "time_id": 4,
                "cells_path": "a",
                "locs_path": "b",
                "n_dpn": 12,
                "avg_dpn_area_vox": 120.0,
                "lin_area_vox": 520,
                "n_pros": 22,
                "dpn_area_vox": 1100,
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
                "genotype": "wt",
                "n_dpn": 4,
                "avg_dpn_area_vox": 70.0,
                "lin_area_vox": 500,
                "n_pros": 14,
                "dpn_area_vox": 200,
            },
        ]
    )

    sim_path = tmp_path / "sim_timepoint_metrics.csv"
    exp_path = tmp_path / "metrics.csv"
    sim_metrics.to_csv(sim_path, index=False)
    exp_metrics.to_csv(exp_path, index=False)

    main(
        [
            "--sim-metrics",
            str(sim_path),
            "--exp-metrics",
            str(exp_path),
            "--timepoint",
            "last",
            "--conditions",
            "divMean36Stdev30_rotMean0Stdev30",
            "--sim-ids",
            "sim43",
        ]
    )

    sim_out = tmp_path / "sim_metrics_last.csv"
    sim_summary_out = tmp_path / "sim_summary_last.csv"
    exp_summary_out = tmp_path / "exp_summary.csv"
    assert sim_out.exists()
    assert sim_summary_out.exists()
    assert exp_summary_out.exists()

    selected = pd.read_csv(sim_out)
    assert selected["condition"].tolist() == ["divMean36Stdev30_rotMean0Stdev30"]
    assert selected["sim_id"].tolist() == ["sim43"]
    assert selected["time_id"].tolist() == [4]

    sim_summary = pd.read_csv(sim_summary_out)
    assert sim_summary["n_runs"].tolist() == [1]
    assert sim_summary["regulatory_dynamic"].tolist() == ["VOL-ABM"]

    exp_summary = pd.read_csv(exp_summary_out)
    assert sorted(exp_summary["genotype"].tolist()) == ["mudmut", "wt"]
