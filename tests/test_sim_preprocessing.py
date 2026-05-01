import json
from pathlib import Path

import numpy as np
import pytest

from npa.sim_preprocessing import (
    build_geo_tensor,
    build_label_map,
    build_raw_tensor,
    index_sim_files,
    process_condition,
    write_sim_index,
    write_sim_run_index
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload))


def test_index_sim_files_pairs_and_sorts_last_timepoint(tmp_path: Path) -> None:
    condition_dir = tmp_path / "divMean0Stdev30_rotMean0Stdev30"
    sim_dir = condition_dir / "sim41"
    sim_dir.mkdir(parents=True)

    cells_a = sim_dir / "x_0001_000001.CELLS.json"
    locs_a = sim_dir / "x_0001_000001.LOCATIONS.json"
    cells_b = sim_dir / "x_0001_000434.CELLS.json"
    locs_b = sim_dir / "x_0001_000434.LOCATIONS.json"
    missing_locs_cells = sim_dir / "x_0002_000010.CELLS.json"
    for p in (cells_a, locs_a, cells_b, locs_b, missing_locs_cells):
        _write_json(p, [])

    indexed = index_sim_files(condition_dir, ["sim41"])

    assert list(indexed.keys()) == [("sim41", "0001")]
    assert [item[0] for item in indexed[("sim41", "0001")]] == [1, 434]


def test_build_geo_tensor_centers_and_channels() -> None:
    cells_json = [
        {"id": 1, "pop": 1},
        {"id": 2, "pop": 2},
        {"id": 3, "pop": 3},
    ]
    locs_json = [
        {"id": 1, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0], [1, 0, 0]]}]},
        {"id": 2, "center": [2, 2, 0], "location": [{"region": "DEFAULT", "voxels": [[2, 2, 0]]}]},
        {"id": 3, "center": [2, 1, 0], "location": [{"region": "DEFAULT", "voxels": [[2, 1, 0]]}]},
    ]

    geo = build_geo_tensor(cells_json, locs_json, canvas_size=5)

    assert geo.shape == (5, 5, 2)
    assert geo.dtype == np.float32
    assert np.all(np.logical_or(geo == 0.0, geo == 1.0))
    assert geo[..., 0].sum() == 2
    assert geo[..., 1].sum() == 2


def test_build_geo_tensor_ignores_center_field() -> None:
    cells_json = [{"id": 1, "pop": 1}]
    # center is [50, 50, 0] — must NOT produce a phantom voxel there
    locs_json = [
        {"id": 1, "center": [50, 50, 0], "location": [{"region": "DEFAULT", "voxels": [[10, 10, 0]]}]}
    ]

    geo = build_geo_tensor(cells_json, locs_json, canvas_size=21)

    # Only one real voxel at [10,10]; canvas center is 10 → shifts to [10,10]
    assert float(geo[..., 0].sum()) == 1.0
    assert geo[10, 10, 0] == 1.0


def test_build_geo_tensor_empty_voxels_returns_zeros() -> None:
    geo = build_geo_tensor(
        [{"id": 1, "pop": 1}],
        [{"id": 1, "center": [0, 0, 0], "location": []}],
        canvas_size=7,
    )
    assert geo.shape == (7, 7, 2)
    assert float(geo.sum()) == 0.0


def test_process_condition_uses_last_timepoint_and_sorts_rows(tmp_path: Path) -> None:
    condition_dir = tmp_path / "divMean36Stdev30_rotMean0Stdev30"
    (condition_dir / "sim42").mkdir(parents=True)
    (condition_dir / "sim41").mkdir(parents=True)
    out_path = tmp_path / "out" / f"{condition_dir.name}.npz"

    _write_json(
        condition_dir / "sim42" / "r_0001_000001.CELLS.json",
        [{"id": 1, "pop": 1}],
    )
    _write_json(
        condition_dir / "sim42" / "r_0001_000001.LOCATIONS.json",
        [{"id": 1, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0]]}]}],
    )
    _write_json(
        condition_dir / "sim41" / "r_0001_000010.CELLS.json",
        [{"id": 1, "pop": 1}, {"id": 2, "pop": 2}],
    )
    _write_json(
        condition_dir / "sim41" / "r_0001_000010.LOCATIONS.json",
        [
            {"id": 1, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0]]}]},
            {"id": 2, "center": [1, 1, 0], "location": [{"region": "DEFAULT", "voxels": [[1, 1, 0]]}]},
        ],
    )
    _write_json(
        condition_dir / "sim41" / "r_0001_000434.CELLS.json",
        [{"id": 1, "pop": 1}, {"id": 2, "pop": 2}, {"id": 3, "pop": 3}],
    )
    _write_json(
        condition_dir / "sim41" / "r_0001_000434.LOCATIONS.json",
        [
            {"id": 1, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0]]}]},
            {"id": 2, "center": [1, 1, 0], "location": [{"region": "DEFAULT", "voxels": [[1, 1, 0]]}]},
            {"id": 3, "center": [2, 2, 0], "location": [{"region": "DEFAULT", "voxels": [[2, 2, 0]]}]},
        ],
    )

    record = process_condition(condition_dir, ["sim42", "sim41"], out_path, canvas_size=9)

    assert record["condition"] == condition_dir.name
    assert record["n_runs"] == 2
    assert record["rows"] == [
        {
            "condition": condition_dir.name,
            "npz_path": out_path,
            "npz_row": 0,
            "sim_id": "sim41",
            "run_id": "0001",
            "time_id": 434,
            "n_nb": 1,
            "n_progeny": 2,
            "cells_path": condition_dir / "sim41" / "r_0001_000434.CELLS.json",
            "locs_path": condition_dir / "sim41" / "r_0001_000434.LOCATIONS.json",
        },
        {
            "condition": condition_dir.name,
            "npz_path": out_path,
            "npz_row": 1,
            "sim_id": "sim42",
            "run_id": "0001",
            "time_id": 1,
            "n_nb": 1,
            "n_progeny": 0,
            "cells_path": condition_dir / "sim42" / "r_0001_000001.CELLS.json",
            "locs_path": condition_dir / "sim42" / "r_0001_000001.LOCATIONS.json",
        },
    ]
    with np.load(out_path) as data:
        assert data["geo"].shape == (2, 9, 9, 2)
        assert data["counts"].dtype == np.int32
        assert data["sim_id"].tolist() == ["sim41", "sim42"]
        assert data["run_id"].tolist() == ["0001", "0001"]
        assert data["time_id"].tolist() == [434, 1]
        np.testing.assert_array_equal(data["counts"][0], np.array([1, 2], dtype=np.int32))


def test_process_condition_skips_corrupt_json_and_processes_remaining(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Corrupt CELLS/LOCATIONS files are skipped with a WARNING; valid runs still appear in output."""
    condition_dir = tmp_path / "divMean0Stdev0_rotMean0Stdev0"
    (condition_dir / "sim01").mkdir(parents=True)
    (condition_dir / "sim02").mkdir(parents=True)
    out_path = tmp_path / "out.npz"

    # sim01 — valid
    _write_json(
        condition_dir / "sim01" / "r_0001_000001.CELLS.json",
        [{"id": 1, "pop": 1}],
    )
    _write_json(
        condition_dir / "sim01" / "r_0001_000001.LOCATIONS.json",
        [{"id": 1, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0]]}]}],
    )

    # sim02 — corrupt (truncated) LOCATIONS file
    _write_json(
        condition_dir / "sim02" / "r_0001_000001.CELLS.json",
        [{"id": 1, "pop": 1}],
    )
    (condition_dir / "sim02" / "r_0001_000001.LOCATIONS.json").write_text("[{truncated")

    record = process_condition(condition_dir, ["sim01", "sim02"], out_path, canvas_size=5)

    # only the valid run is saved
    assert record["n_runs"] == 1
    with np.load(out_path) as data:
        assert data["sim_id"].tolist() == ["sim01"]

    # a warning identifying the corrupt run was printed
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "sim02" in out


def test_build_raw_tensor_three_channels() -> None:
    cells_json = [{"id": 1, "pop": 1}, {"id": 2, "pop": 2}, {"id": 3, "pop": 3}]
    locs_json = [
        {"id": 1, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0]]}]},
        {"id": 2, "center": [2, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[2, 0, 0]]}]},
        {"id": 3, "center": [4, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[4, 0, 0]]}]},
    ]
    geo = build_raw_tensor(cells_json, locs_json, canvas_size=9)
    assert geo.shape == (9, 9, 3)
    assert geo[..., 0].sum() == 1.0  # pop1
    assert geo[..., 1].sum() == 1.0  # pop2
    assert geo[..., 2].sum() == 1.0  # pop3


def test_build_label_map_assigns_cell_ids() -> None:
    cells_json = [{"id": 7, "pop": 1}, {"id": 8, "pop": 2}]
    locs_json = [
        {"id": 7, "center": [0, 0, 0], "location": [{"region": "DEFAULT", "voxels": [[0, 0, 0]]}]},
        {"id": 8, "center": [2, 2, 0], "location": [{"region": "DEFAULT", "voxels": [[2, 2, 0]]}]},
    ]
    lmap = build_label_map(cells_json, locs_json, canvas_size=5)
    assert lmap.shape == (5, 5)
    assert lmap.dtype == np.int32
    nonzero_ids = set(lmap[lmap > 0].tolist())
    assert nonzero_ids == {7, 8}


def test_build_label_map_empty_returns_zeros() -> None:
    lmap = build_label_map([], [], canvas_size=5)
    assert lmap.shape == (5, 5)
    assert lmap.sum() == 0


def test_write_sim_index_csv(tmp_path: Path) -> None:
    out_csv = tmp_path / "sim_index.csv"
    write_sim_index(
        [
            {
                "condition": "divMean0Stdev30_rotMean0Stdev30",
                "n_runs": 3,
                "npz_path": Path("data/sim/processed/divMean0Stdev30_rotMean0Stdev30.npz"),
            }
        ],
        out_csv,
    )
    text = out_csv.read_text()
    assert "condition,n_runs,npz_path" in text
    assert "divMean0Stdev30_rotMean0Stdev30,3,data/sim/processed/divMean0Stdev30_rotMean0Stdev30.npz" in text


def test_write_sim_run_index_csv(tmp_path: Path) -> None:
    out_csv = tmp_path / "sim_row_index.csv"
    write_sim_run_index(
        [
            {
                "rows": [
                    {
                        "condition": "divMean0Stdev30_rotMean0Stdev30",
                        "npz_path": Path("data/sim/processed/divMean0Stdev30_rotMean0Stdev30.npz"),
                        "npz_row": 5,
                        "sim_id": "sim41",
                        "run_id": "0006",
                        "time_id": 434,
                        "n_nb": 1,
                        "n_progeny": 17,
                        "cells_path": Path("data/sim/sweep/cond/sim41/x_0006_000434.CELLS.json"),
                        "locs_path": Path("data/sim/sweep/cond/sim41/x_0006_000434.LOCATIONS.json"),
                    }
                ]
            }
        ],
        out_csv,
    )

    text = out_csv.read_text()
    assert "condition,npz_path,npz_row,sim_id,run_id,time_id,n_nb,n_progeny,cells_path,locs_path" in text
    assert "divMean0Stdev30_rotMean0Stdev30,data/sim/processed/divMean0Stdev30_rotMean0Stdev30.npz,5,sim41,0006,434,1,17" in text
