import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "plot_comparisons.py"
SPEC = importlib.util.spec_from_file_location("plot_comparisons", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    sim_metrics = pd.DataFrame(
        [
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 36,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 30,
                "genotype": "mudmut",
                "critical_volume_mode": 1,
                "regulatory_dynamic": "VOL-ABM",
                "n_dpn": 12,
                "avg_dpn_area_vox": 280.0,
                "lin_area_vox": 1800,
                "n_pros": 38,
                "dpn_area_vox": 1200,
            },
            {
                "condition": "divMean0Stdev30_rotMean0Stdev0",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 0,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 0,
                "genotype": "mudmut",
                "critical_volume_mode": 1,
                "regulatory_dynamic": "VOL-ABM",
                "n_dpn": 4,
                "avg_dpn_area_vox": 200.0,
                "lin_area_vox": 1000,
                "n_pros": 30,
                "dpn_area_vox": 800,
            },
        ]
    )
    exp_summary = pd.DataFrame(
        [
            {
                "genotype": "wt",
                "n_samples": 60,
                "n_dpn_mean": 4.0,
                "n_dpn_std": 1.0,
                "avg_dpn_area_vox_mean": 100.0,
                "avg_dpn_area_vox_std": 10.0,
                "lin_area_vox_mean": 500.0,
                "lin_area_vox_std": 50.0,
                "n_pros_mean": 20.0,
                "n_pros_std": 2.0,
                "dpn_area_vox_mean": 400.0,
                "dpn_area_vox_std": 40.0,
            },
            {
                "genotype": "mudmut",
                "n_samples": 59,
                "n_dpn_mean": 8.0,
                "n_dpn_std": 1.5,
                "avg_dpn_area_vox_mean": 160.0,
                "avg_dpn_area_vox_std": 16.0,
                "lin_area_vox_mean": 900.0,
                "lin_area_vox_std": 90.0,
                "n_pros_mean": 32.0,
                "n_pros_std": 3.0,
                "dpn_area_vox_mean": 800.0,
                "dpn_area_vox_std": 80.0,
            },
        ]
    )
    sim_path = tmp_path / "sim_metrics_last.csv"
    exp_path = tmp_path / "exp_summary.csv"
    sim_metrics.to_csv(sim_path, index=False)
    exp_summary.to_csv(exp_path, index=False)
    return sim_path, exp_path


def test_plot_comparisons_cli_writes_outputs_for_all_modes(tmp_path: Path) -> None:
    sim_path, exp_path = _write_inputs(tmp_path)

    main(
        [
            "--mode",
            "intra",
            "--condition",
            "divMean36Stdev30_rotMean0Stdev30",
            "--metric",
            "n_dpn",
            "--scale",
            "raw",
            "--sim-metrics",
            str(sim_path),
            "--exp-summary",
            str(exp_path),
        ]
    )
    assert (tmp_path / "figures" / "comparisons" / "intra" / "intra_divMean36Stdev30_rotMean0Stdev30_n_dpn_raw.png").exists()

    main(
        [
            "--mode",
            "inter-div-priority",
            "--sim-id",
            "sim43",
            "--metric",
            "n_dpn",
            "--scale",
            "foldchange",
            "--sim-metrics",
            str(sim_path),
            "--exp-summary",
            str(exp_path),
        ]
    )
    assert (tmp_path / "figures" / "comparisons" / "inter_div_priority" / "inter_div_priority_sim43_n_dpn_foldchange.png").exists()

    main(
        [
            "--mode",
            "inter-rot-priority",
            "--sim-id",
            "sim43",
            "--metric",
            "n_dpn",
            "--scale",
            "raw",
            "--sim-metrics",
            str(sim_path),
            "--exp-summary",
            str(exp_path),
        ]
    )
    assert (tmp_path / "figures" / "comparisons" / "inter_rot_priority" / "inter_rot_priority_sim43_n_dpn_raw.png").exists()


def test_plot_comparisons_cli_validates_required_selectors() -> None:
    with pytest.raises(SystemExit):
        main(["--mode", "intra", "--metric", "n_dpn", "--scale", "raw"])
    with pytest.raises(SystemExit):
        main(["--mode", "inter-div-priority", "--metric", "n_dpn", "--scale", "raw"])
