from __future__ import annotations

import argparse
from pathlib import Path

from npa.metrics import (
    extract_exp_metrics,
    iter_sim_timepoint_metrics,
    write_exp_metrics_csv,
    write_sim_timepoint_metrics_csv,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract lineage metrics CSVs.")
    parser.add_argument("--kind", choices=("exp", "sim"), required=True)
    parser.add_argument("--processed-dir", type=Path, default=None)
    parser.add_argument("--sweep-root", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--conditions", nargs="+", default=None)
    parser.add_argument("--sim-ids", nargs="+", default=None)
    parser.add_argument("--ds", type=float, default=0.3)
    return parser.parse_args(argv)


def _validate_args(args: argparse.Namespace) -> None:
    if args.kind == "exp":
        if args.processed_dir is None:
            raise SystemExit("--kind exp requires --processed-dir")
    else:
        if args.sweep_root is None:
            raise SystemExit("--kind sim requires --sweep-root")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _validate_args(args)

    if args.kind == "exp":
        assert args.processed_dir is not None
        out_path = args.out if args.out is not None else args.processed_dir / "metrics.csv"
        metrics = extract_exp_metrics(args.processed_dir)
        write_exp_metrics_csv(metrics, out_path)
        print(f"Saved {len(metrics)} experimental metric rows to {out_path}")
    else:
        assert args.sweep_root is not None
        out_dir = args.out_dir if args.out_dir is not None else args.sweep_root.parent / "processed"
        out_path = args.out if args.out is not None else out_dir / "sim_timepoint_metrics.csv"
        rows = iter_sim_timepoint_metrics(
            args.sweep_root,
            ds=args.ds,
            conditions=args.conditions,
            sim_ids=args.sim_ids,
        )
        write_sim_timepoint_metrics_csv(rows, out_path)
        print(f"Saved simulation timepoint metrics to {out_path}")


if __name__ == "__main__":
    main()
