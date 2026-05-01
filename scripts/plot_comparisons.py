from __future__ import annotations

import argparse
from pathlib import Path

from npa.comparison_figures import COMPARISON_MODES, SCALES, create_and_save_comparison_figure
from npa.metrics import COMPARISON_METRIC_COLUMNS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate comparison figures from processed CSVs.")
    parser.add_argument("--mode", choices=COMPARISON_MODES, required=True)
    parser.add_argument("--metric", choices=COMPARISON_METRIC_COLUMNS, required=True)
    parser.add_argument("--scale", choices=SCALES, required=True)
    parser.add_argument("--condition", type=str, default=None)
    parser.add_argument("--sim-id", type=str, default=None)
    parser.add_argument("--sim-metrics", type=Path, default=Path("data/sim/processed/sim_metrics_last.csv"))
    parser.add_argument("--exp-summary", type=Path, default=Path("data/exp/processed/exp_summary.csv"))
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def _validate_args(args: argparse.Namespace) -> None:
    if args.mode == "intra":
        if args.condition is None:
            raise SystemExit("--mode intra requires --condition")
        if args.sim_id is not None:
            raise SystemExit("--mode intra does not accept --sim-id")
    else:
        if args.sim_id is None:
            raise SystemExit(f"--mode {args.mode} requires --sim-id")
        if args.condition is not None:
            raise SystemExit(f"--mode {args.mode} does not accept --condition")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _validate_args(args)
    out_path = create_and_save_comparison_figure(
        sim_metrics_path=args.sim_metrics,
        exp_summary_path=args.exp_summary,
        mode=args.mode,
        metric=args.metric,
        scale=args.scale,
        condition=args.condition,
        sim_id=args.sim_id,
        out_path=args.out,
    )
    print(f"Saved comparison figure to {out_path}")


if __name__ == "__main__":
    main()
