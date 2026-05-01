from __future__ import annotations

import argparse
from pathlib import Path

from npa.sim_preprocessing import process_condition, write_sim_index, write_sim_run_index


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess simulation CELLS/LOCATIONS data into condition NPZ files."
    )
    parser.add_argument("--sweep-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--conditions", nargs="+", default=None)
    parser.add_argument("--sim-ids", nargs="+", default=None)
    return parser.parse_args(argv)


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


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    sweep_root = args.sweep_root.resolve()
    if not sweep_root.is_dir():
        raise FileNotFoundError(f"sweep root does not exist: {sweep_root}")

    out_dir = (
        args.out_dir.resolve()
        if args.out_dir is not None
        else (sweep_root.parent / "processed").resolve()
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_conditions = set(args.conditions) if args.conditions else None
    selected_sim_ids = set(args.sim_ids) if args.sim_ids else None

    records: list[dict] = []
    for condition_dir in _condition_dirs(sweep_root, selected_conditions):
        sim_ids = _sim_ids(condition_dir, selected_sim_ids)
        out_path = out_dir / f"{condition_dir.name}.npz"
        record = process_condition(
            condition_dir=condition_dir,
            sim_ids=sim_ids,
            out_path=out_path,
            canvas_size=200,
        )
        records.append(record)
        print(f'{condition_dir.name}: n_runs={record["n_runs"]}')

    write_sim_index(records, out_dir / "sim_index.csv")
    write_sim_run_index(records, out_dir / "sim_run_index.csv")


if __name__ == "__main__":
    main()
