from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")

from npa.comparison_figures import (  # noqa: E402
    create_and_save_comparison_figure,
    default_output_path,
    draw_comparison_figure,
    load_exp_summary,
    load_sim_plotting_input,
    prepare_plot_data,
)


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    sim_metrics = pd.DataFrame(
        [
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
            {
                "condition": "divMean0Stdev30_rotMean0Stdev0",
                "sim_id": "sim43",
                "run_id": "0002",
                "time_id": 434,
                "div_mean": 0,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 0,
                "genotype": "mudmut",
                "critical_volume_mode": 1,
                "regulatory_dynamic": "VOL-ABM",
                "n_dpn": 6,
                "avg_dpn_area_vox": 220.0,
                "lin_area_vox": 1200,
                "n_pros": 32,
                "dpn_area_vox": 900,
            },
            {
                "condition": "divMean36Stdev30_rotMean0Stdev0",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 36,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 0,
                "genotype": "mudmut",
                "critical_volume_mode": 1,
                "regulatory_dynamic": "VOL-ABM",
                "n_dpn": 8,
                "avg_dpn_area_vox": 240.0,
                "lin_area_vox": 1400,
                "n_pros": 34,
                "dpn_area_vox": 1000,
            },
            {
                "condition": "divMean0Stdev30_rotMean0Stdev30",
                "sim_id": "sim43",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 0,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 30,
                "genotype": "mudmut",
                "critical_volume_mode": 1,
                "regulatory_dynamic": "VOL-ABM",
                "n_dpn": 10,
                "avg_dpn_area_vox": 260.0,
                "lin_area_vox": 1600,
                "n_pros": 36,
                "dpn_area_vox": 1100,
            },
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
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim54",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 36,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 30,
                "genotype": "mudmut",
                "critical_volume_mode": 0,
                "regulatory_dynamic": "NB-PDE",
                "n_dpn": 5,
                "avg_dpn_area_vox": 150.0,
                "lin_area_vox": 900,
                "n_pros": 20,
                "dpn_area_vox": 700,
            },
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim74",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 36,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 30,
                "genotype": "wt",
                "critical_volume_mode": 0,
                "regulatory_dynamic": "NB-PDE",
                "n_dpn": 3,
                "avg_dpn_area_vox": 140.0,
                "lin_area_vox": 850,
                "n_pros": 18,
                "dpn_area_vox": 600,
            },
            {
                "condition": "divMean36Stdev30_rotMean0Stdev30",
                "sim_id": "sim64",
                "run_id": "0001",
                "time_id": 434,
                "div_mean": 36,
                "div_stdev": 30,
                "rot_mean": 0,
                "rot_stdev": 30,
                "genotype": "wt",
                "critical_volume_mode": 1,
                "regulatory_dynamic": "VOL-ABM",
                "n_dpn": 4,
                "avg_dpn_area_vox": 145.0,
                "lin_area_vox": 870,
                "n_pros": 19,
                "dpn_area_vox": 620,
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


def test_prepare_plot_data_intra_and_inter_ordering(tmp_path: Path) -> None:
    sim_path, exp_path = _write_inputs(tmp_path)
    sim_df = load_sim_plotting_input(sim_path)
    exp_summary = load_exp_summary(exp_path)

    intra_df, intra_refs, anchor = prepare_plot_data(
        sim_df=sim_df,
        exp_summary=exp_summary,
        mode="intra",
        metric="n_dpn",
        scale="foldchange",
        condition="divMean36Stdev30_rotMean0Stdev30",
    )
    assert anchor == "divMean36Stdev30_rotMean0Stdev30"
    assert intra_df["plot_label"].tolist() == [
        "WT-VCV0\nNB-PDE",
        "WT-VCV1\nVOL-ABM",
        "MM-VCV0\nNB-PDE",
        "MM-VCV1\nVOL-ABM",
    ]
    assert intra_df["plot_value"].tolist() == [0.75, 1.0, 1.25, 3.0]
    assert intra_refs["wt"]["mean"] == 1.0
    assert intra_refs["mudmut"]["mean"] == 2.0

    div_df, _, _ = prepare_plot_data(
        sim_df=sim_df,
        exp_summary=exp_summary,
        mode="inter-div-priority",
        metric="n_dpn",
        scale="raw",
        sim_id="sim43",
    )
    assert div_df["plot_label"].drop_duplicates().tolist() == [
        "D0S30\nR0S0",
        "D36S30\nR0S0",
        "D0S30\nR0S30",
        "D36S30\nR0S30",
    ]

    rot_df, _, _ = prepare_plot_data(
        sim_df=sim_df,
        exp_summary=exp_summary,
        mode="inter-rot-priority",
        metric="n_dpn",
        scale="raw",
        sim_id="sim43",
    )
    assert rot_df["plot_label"].drop_duplicates().tolist() == [
        "D0S30\nR0S0",
        "D0S30\nR0S30",
        "D36S30\nR0S0",
        "D36S30\nR0S30",
    ]


def test_draw_and_save_comparison_figure(tmp_path: Path) -> None:
    sim_path, exp_path = _write_inputs(tmp_path)
    sim_df = load_sim_plotting_input(sim_path)
    exp_summary = load_exp_summary(exp_path)

    plot_df, refs, anchor = prepare_plot_data(
        sim_df=sim_df,
        exp_summary=exp_summary,
        mode="inter-div-priority",
        metric="avg_dpn_area_vox",
        scale="raw",
        sim_id="sim43",
    )
    fig = draw_comparison_figure(
        plot_df=plot_df,
        refs=refs,
        mode="inter-div-priority",
        metric="avg_dpn_area_vox",
        scale="raw",
        anchor=anchor,
    )
    ax = fig.axes[0]
    assert ax.get_yscale() == "log"
    assert ax.get_ylabel() == "avg_dpn_area_vox (vox/cell, log scale)"
    out = tmp_path / "figure.png"
    fig.savefig(out)
    assert out.exists()

    default_out = default_output_path(
        sim_metrics_path=sim_path,
        mode="inter-rot-priority",
        metric="n_dpn",
        scale="foldchange",
        sim_id="sim43",
    )
    assert default_out == tmp_path / "figures" / "comparisons" / "inter_rot_priority" / "inter_rot_priority_sim43_n_dpn_foldchange.png"

    saved = create_and_save_comparison_figure(
        sim_metrics_path=sim_path,
        exp_summary_path=exp_path,
        mode="intra",
        metric="n_pros",
        scale="foldchange",
        condition="divMean36Stdev30_rotMean0Stdev30",
    )
    assert saved.exists()

    fold_df, fold_refs, fold_anchor = prepare_plot_data(
        sim_df=sim_df,
        exp_summary=exp_summary,
        mode="intra",
        metric="n_pros",
        scale="foldchange",
        condition="divMean36Stdev30_rotMean0Stdev30",
    )
    fold_fig = draw_comparison_figure(
        plot_df=fold_df,
        refs=fold_refs,
        mode="intra",
        metric="n_pros",
        scale="foldchange",
        anchor=fold_anchor,
    )
    fold_ax = fold_fig.axes[0]
    assert fold_ax.get_yscale() == "log"
    assert fold_ax.get_ylabel() == "n_pros (fold change from WT mean, log scale)"
