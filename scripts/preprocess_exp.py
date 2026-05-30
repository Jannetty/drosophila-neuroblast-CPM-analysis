from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from npa.exp_preprocessing.pipeline import (
    process_exp_lobe,
    stack_exp_analysis_npz,
    write_lineage_index,
    write_rejected_lineage_index,
)

GENOTYPE_ALIASES = {
    "control": "wt",
    "wt": "wt",
    "mud": "mudmut",
    "mudmut": "mudmut",
    "nanobody": "nanobody",
}

GENOTYPE_SPECS = {
    "wt": {
        "folder": "wt",
        "token": "control",
    },
    "mudmut": {
        "folder": "mudmut",
        "token": "mud",
    },
    "nanobody": {
        "folder": "Nanobody",
        "token": "Nanobody",
    },
}


@dataclass(frozen=True)
class WrlTriplet:
    genotype: str
    lobe: str
    lineage_wrl: Path
    pros_wrl: Path
    dpn_wrl: Path


def canonical_genotype(name: str) -> str:
    key = name.strip().lower()
    if key not in GENOTYPE_ALIASES:
        raise ValueError(f"Unsupported genotype: {name}")
    return GENOTYPE_ALIASES[key]


def lobe_sort_key(lobe: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", lobe)
    return (int(match.group(1)) if match else 0, lobe)


def display_path(path: Path) -> Path:
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def discover_wrl_triplets(wrl_dir: Path) -> list[WrlTriplet]:
    triplets: list[WrlTriplet] = []
    for genotype in ("wt", "mudmut", "nanobody"):
        spec = GENOTYPE_SPECS[genotype]
        folder = wrl_dir / spec["folder"]
        token = spec["token"]
        if not folder.exists():
            continue

        lineage_files = sorted(
            folder.glob(f"lobe*_{token}_lineages.wrl"),
            key=lambda path: lobe_sort_key(path.name.split("_", maxsplit=1)[0]),
        )
        for lineage_wrl in lineage_files:
            lobe = lineage_wrl.name.split("_", maxsplit=1)[0]
            pros_wrl = folder / f"{lobe}_{token}_pros.wrl"
            dpn_wrl = folder / f"{lobe}_{token}_dpn.wrl"
            if not pros_wrl.exists():
                raise FileNotFoundError(f"Missing Pros WRL for {lineage_wrl}: {pros_wrl}")
            if not dpn_wrl.exists():
                raise FileNotFoundError(f"Missing Dpn WRL for {lineage_wrl}: {dpn_wrl}")
            triplets.append(
                WrlTriplet(
                    genotype=genotype,
                    lobe=lobe,
                    lineage_wrl=lineage_wrl,
                    pros_wrl=pros_wrl,
                    dpn_wrl=dpn_wrl,
                )
            )

    return sorted(triplets, key=lambda item: (item.genotype, lobe_sort_key(item.lobe)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess experimental WRL lineage files into analysis NPZs."
    )
    parser.add_argument("--wrl-dir", type=Path, default=Path("data/exp/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/exp/processed"))
    parser.add_argument("--genotypes", nargs="+", default=None)
    parser.add_argument("--lobes", nargs="+", default=None)
    parser.add_argument("--ds", type=float, default=0.3)
    parser.add_argument("--canvas-size", type=int, default=200)
    parser.add_argument(
        "--no-convex-hull",
        action="store_true",
        default=False,
        help="Use projected mesh-triangle union instead of convex hull for lineage boundary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected_genotypes = (
        {canonical_genotype(name) for name in args.genotypes}
        if args.genotypes
        else None
    )
    selected_lobes = set(args.lobes) if args.lobes else None

    triplets = discover_wrl_triplets(args.wrl_dir)
    if selected_genotypes is not None:
        triplets = [item for item in triplets if item.genotype in selected_genotypes]
    if selected_lobes is not None:
        triplets = [item for item in triplets if item.lobe in selected_lobes]

    mesh_dir = args.out_dir / "meshes"
    analysis_dir = args.out_dir / "analysis"
    all_records = []
    all_rejected_records = []
    records_by_genotype: dict[str, list[dict]] = {
        "wt": [],
        "mudmut": [],
        "nanobody": [],
    }
    lineage_id_next = 0
    rejected_lineage_id_next = 0

    for triplet in triplets:
        print(f"[{triplet.genotype}] {triplet.lobe}: parsing and processing...")
        records, rejected_records, filtered = process_exp_lobe(
            lineage_wrl=triplet.lineage_wrl,
            pros_wrl=triplet.pros_wrl,
            dpn_wrl=triplet.dpn_wrl,
            genotype=triplet.genotype,
            lobe=triplet.lobe,
            mesh_dir=mesh_dir,
            lineage_id_start=lineage_id_next,
            ds=args.ds,
            canvas_size=args.canvas_size,
            use_convex_hull=not args.no_convex_hull,
        )
        for record in records:
            record["mesh_path"] = display_path(Path(record["mesh_path"]))
            record["analysis_row"] = len(records_by_genotype[triplet.genotype])
            records_by_genotype[triplet.genotype].append(record)
            all_records.append(record)
        for record in rejected_records:
            record["mesh_path"] = display_path(Path(record["mesh_path"]))
            record["lineage_id"] = rejected_lineage_id_next
            rejected_lineage_id_next += 1
            all_rejected_records.append(record)
        lineage_id_next += len(records)

        print(
            f"  kept {len(records)}/{filtered.n_lineages_total}; "
            f"rejected disconnected={filtered.n_rejected_disconnected}, "
            f"no_dpn={filtered.n_rejected_no_dpn}; "
            f"unassigned dpn={filtered.n_unassigned_dpn}, pros={filtered.n_unassigned_pros}"
        )

    for genotype, records in records_by_genotype.items():
        if selected_genotypes is not None and genotype not in selected_genotypes:
            continue
        stack_exp_analysis_npz(records, analysis_dir / f"{genotype}.npz", ds=args.ds)

    write_lineage_index(all_records, args.out_dir / "lineage_index.csv")
    write_rejected_lineage_index(
        all_rejected_records,
        args.out_dir / "rejected_lineage_index.csv",
    )
    print(f"Saved {len(all_records)} accepted lineages to {args.out_dir}")


if __name__ == "__main__":
    main()
