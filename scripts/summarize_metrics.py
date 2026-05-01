from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from npa.metrics import (
    build_selected_sim_metrics,
    read_sim_comparison_input,
    summarize_exp_comparison_metrics,
    summarize_sim_comparison_rows,
    write_exp_summary_csv,
    write_selected_sim_metrics_csv,
    write_sim_summary_csv,
)


def _parse_timepoint(value: str) -> str | int:
    if value == "last":
        return value
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--timepoint must be 'last' or an integer") from exc


def _timepoint_suffix(timepoint: str | int) -> str:
    if timepoint == "last":
        return "last"
    return f"t{int(timepoint):06d}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize simulation and experimental metric CSVs."
    )
    parser.add_argument("--sim-metrics", type=Path, required=True)
    parser.add_argument("--exp-metrics", type=Path, required=True)
    parser.add_argument("--timepoint", type=_parse_timepoint, default="last")
    parser.add_argument("--sim-out", type=Path, default=None)
    parser.add_argument("--sim-summary-out", type=Path, default=None)
    parser.add_argument("--exp-summary-out", type=Path, default=None)
    parser.add_argument("--conditions", nargs="+", default=None)
    parser.add_argument("--sim-ids", nargs="+", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    suffix = _timepoint_suffix(args.timepoint)

    sim_out = (
        args.sim_out
        if args.sim_out is not None
        else args.sim_metrics.parent / f"sim_metrics_{suffix}.csv"
    )
    sim_summary_out = (
        args.sim_summary_out
        if args.sim_summary_out is not None
        else args.sim_metrics.parent / f"sim_summary_{suffix}.csv"
    )
    exp_summary_out = (
        args.exp_summary_out
        if args.exp_summary_out is not None
        else args.exp_metrics.parent / "exp_summary.csv"
    )

    sim_metrics = read_sim_comparison_input(
        args.sim_metrics,
        conditions=args.conditions,
        sim_ids=args.sim_ids,
    )
    selected = build_selected_sim_metrics(sim_metrics, timepoint=args.timepoint)
    sim_summary = summarize_sim_comparison_rows(selected)

    exp_metrics = pd.read_csv(args.exp_metrics)
    exp_summary = summarize_exp_comparison_metrics(exp_metrics)

    write_selected_sim_metrics_csv(selected, sim_out)
    write_sim_summary_csv(sim_summary, sim_summary_out)
    write_exp_summary_csv(exp_summary, exp_summary_out)

    print(f"Saved {len(selected)} selected simulation rows to {sim_out}")
    print(f"Saved {len(sim_summary)} simulation summary rows to {sim_summary_out}")
    print(f"Saved {len(exp_summary)} experimental summary rows to {exp_summary_out}")


if __name__ == "__main__":
    main()
