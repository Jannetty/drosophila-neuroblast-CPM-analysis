from pathlib import Path

import importlib.util
import numpy as np
import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "preprocess_sim.py"
SPEC = importlib.util.spec_from_file_location("preprocess_sim", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def test_preprocess_sim_cli_requires_sweep_root() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_preprocess_sim_cli_writes_outputs_for_condition_subset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    sweep_root = tmp_path / "sweep"
    cond_a = sweep_root / "divMean0Stdev30_rotMean0Stdev30"
    cond_b = sweep_root / "divMean36Stdev30_rotMean0Stdev30"
    sim_a = cond_a / "sim41"
    sim_b = cond_b / "sim42"
    sim_a.mkdir(parents=True)
    sim_b.mkdir(parents=True)

    (sim_a / "x_0001_000001.CELLS.json").write_text('[{"id":1,"pop":1}]')
    (sim_a / "x_0001_000001.LOCATIONS.json").write_text(
        '[{"id":1,"center":[0,0,0],"location":[{"region":"DEFAULT","voxels":[[0,0,0]]}]}]'
    )
    (sim_b / "x_0001_000001.CELLS.json").write_text('[{"id":1,"pop":1}]')
    (sim_b / "x_0001_000001.LOCATIONS.json").write_text(
        '[{"id":1,"center":[1,1,0],"location":[{"region":"DEFAULT","voxels":[[1,1,0]]}]}]'
    )

    out_dir = tmp_path / "processed"
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    main(
        [
            "--sweep-root",
            str(sweep_root),
            "--out-dir",
            str(out_dir),
            "--conditions",
            "divMean0Stdev30_rotMean0Stdev30",
        ]
    )

    index_csv = out_dir / "sim_index.csv"
    run_index_csv = out_dir / "sim_run_index.csv"
    npz_a = out_dir / "divMean0Stdev30_rotMean0Stdev30.npz"
    npz_b = out_dir / "divMean36Stdev30_rotMean0Stdev30.npz"
    assert index_csv.exists()
    assert run_index_csv.exists()
    assert npz_a.exists()
    assert not npz_b.exists()
    with np.load(npz_a) as data:
        assert data["geo"].shape[0] == 1
    row_index = run_index_csv.read_text()
    assert "condition,npz_path,npz_row,sim_id,run_id,time_id,n_nb,n_progeny,cells_path,locs_path" in row_index
    assert "divMean0Stdev30_rotMean0Stdev30" in row_index
    assert ",0,sim41,0001,1,1,0," in row_index
