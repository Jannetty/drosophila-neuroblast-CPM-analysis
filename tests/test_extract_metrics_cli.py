import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "extract_metrics.py"
SPEC = importlib.util.spec_from_file_location("extract_metrics", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload))


def test_extract_metrics_cli_exp_writes_default_csv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()

    monkeypatch.setattr(
        MODULE,
        "extract_exp_metrics",
        lambda _processed: pd.DataFrame(
            [
                {
                    "lineage_id": 1,
                    "genotype": "wt",
                    "lobe": "lobe1",
                    "lineage_idx": 0,
                    "analysis_row": 0,
                    "ds": 0.3,
                    "n_dpn": 1,
                    "dpn_area_vox": 2,
                    "avg_dpn_area_vox": 2.0,
                    "std_dpn_area_vox": 0.0,
                    "n_pros": 1,
                    "pros_area_vox": 3,
                    "avg_pros_area_vox": 3.0,
                    "std_pros_area_vox": 0.0,
                    "lin_area_vox": 5,
                }
            ]
        ),
    )

    main(["--kind", "exp", "--processed-dir", str(processed)])

    out = processed / "metrics.csv"
    assert out.exists()
    assert "lineage_id" in out.read_text()


def test_extract_metrics_cli_sim_writes_filtered_default_csv(tmp_path: Path) -> None:
    sweep = tmp_path / "sweep"
    out_dir = tmp_path / "processed"
    keep = sweep / "condA" / "sim01"
    skip_cond = sweep / "condB" / "sim01"
    skip_sim = sweep / "condA" / "sim02"
    keep.mkdir(parents=True)
    skip_cond.mkdir(parents=True)
    skip_sim.mkdir(parents=True)
    cells = [{"id": 1, "pop": 1}]
    locs = [{"id": 1, "center": [0, 0, 0], "location": [{"region": "r", "voxels": [[0, 0, 0]]}]}]
    for sim_dir in (keep, skip_cond, skip_sim):
        _write_json(sim_dir / "x_0001_000001.CELLS.json", cells)
        _write_json(sim_dir / "x_0001_000001.LOCATIONS.json", locs)

    main(
        [
            "--kind",
            "sim",
            "--sweep-root",
            str(sweep),
            "--out-dir",
            str(out_dir),
            "--conditions",
            "condA",
            "--sim-ids",
            "sim01",
        ]
    )

    out = out_dir / "sim_timepoint_metrics.csv"
    assert out.exists()
    rows = pd.read_csv(out)
    assert rows["condition"].tolist() == ["condA"]
    assert rows["sim_id"].tolist() == ["sim01"]


def test_extract_metrics_cli_requires_paths() -> None:
    with pytest.raises(SystemExit):
        main(["--kind", "exp"])
    with pytest.raises(SystemExit):
        main(["--kind", "sim"])
