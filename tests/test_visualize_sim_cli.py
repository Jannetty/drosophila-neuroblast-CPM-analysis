from pathlib import Path

import importlib.util
import numpy as np
import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "visualize_sim.py"
SPEC = importlib.util.spec_from_file_location("visualize_sim", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def test_visualize_sim_cli_raw_any_requires_cells_and_locs() -> None:
    with pytest.raises(SystemExit):
        main(["--mode", "raw-any"])


def test_visualize_sim_cli_raw_last_uses_find_last_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []
    out_png = tmp_path / "out.png"
    monkeypatch.setattr(
        MODULE,
        "find_last_snapshot",
        lambda _sim_dir: (Path("a.CELLS.json"), Path("a.LOCATIONS.json")),
    )
    monkeypatch.setattr(
        MODULE,
        "load_raw_snapshot_full",
        lambda _cells, _locs: (np.zeros((200, 200, 3), dtype=np.float32), np.zeros((200, 200), dtype=np.int32)),
    )
    monkeypatch.setattr(
        MODULE,
        "render_geo",
        lambda geo, ax=None, label_map=None, title="": (calls.append(title), MODULE.plt.subplots()[1])[1],
    )
    monkeypatch.setattr(
        MODULE.plt.Figure,
        "savefig",
        lambda self, *_args, **_kwargs: calls.append("savefig"),
    )

    main(["--mode", "raw-last", "--sim-dir", str(tmp_path / "sim41"), "--out", str(out_png)])
    assert "savefig" in calls


def test_visualize_sim_cli_npz_shows_when_no_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    shown = {"called": False}
    monkeypatch.setattr(
        MODULE,
        "load_sim_npz",
        lambda _npz, _row: np.zeros((200, 200, 2), dtype=np.float32),
    )
    monkeypatch.setattr(
        MODULE,
        "render_geo",
        lambda geo, ax=None, title="": MODULE.plt.subplots()[1],
    )
    monkeypatch.setattr(MODULE.plt, "show", lambda: shown.__setitem__("called", True))

    npz = tmp_path / "cond.npz"
    np.savez_compressed(npz, geo=np.zeros((1, 200, 200, 2), dtype=np.float32))
    main(["--mode", "npz", "--npz", str(npz), "--row", "0"])
    assert shown["called"] is True


def test_visualize_sim_cli_npz_lists_rows(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    npz = tmp_path / "cond.npz"
    np.savez_compressed(npz, geo=np.zeros((2, 200, 200, 2), dtype=np.float32))
    (tmp_path / "sim_run_index.csv").write_text(
        "condition,npz_path,npz_row,sim_id,run_id,time_id,n_nb,n_progeny,cells_path,locs_path\n"
        f"cond,{npz},0,sim41,0001,434,1,2,a.CELLS.json,a.LOCATIONS.json\n"
        f"cond,{npz},1,sim54,0002,434,1,5,b.CELLS.json,b.LOCATIONS.json\n"
    )

    main(["--mode", "npz", "--npz", str(npz), "--list"])

    output = capsys.readouterr().out
    assert "npz_row" in output
    assert "sim54" in output
    assert "0002" in output


def test_visualize_sim_cli_npz_selects_row_by_sim_and_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[object] = []
    npz = tmp_path / "cond.npz"
    out_png = tmp_path / "out.png"
    np.savez_compressed(npz, geo=np.zeros((3, 200, 200, 2), dtype=np.float32))
    (tmp_path / "sim_run_index.csv").write_text(
        "condition,npz_path,npz_row,sim_id,run_id,time_id,n_nb,n_progeny,cells_path,locs_path\n"
        f"cond,{npz},0,sim41,0001,434,1,2,a.CELLS.json,a.LOCATIONS.json\n"
        f"cond,{npz},2,sim54,0002,434,1,5,b.CELLS.json,b.LOCATIONS.json\n"
    )
    monkeypatch.setattr(
        MODULE,
        "load_sim_npz",
        lambda _npz, row: (calls.append(row), np.zeros((200, 200, 2), dtype=np.float32))[1],
    )
    monkeypatch.setattr(
        MODULE,
        "render_geo",
        lambda geo, ax=None, title="": MODULE.plt.subplots()[1],
    )
    monkeypatch.setattr(
        MODULE.plt.Figure,
        "savefig",
        lambda self, *_args, **_kwargs: calls.append("savefig"),
    )

    main(
        [
            "--mode",
            "npz",
            "--npz",
            str(npz),
            "--sim-id",
            "sim54",
            "--run-id",
            "0002",
            "--out",
            str(out_png),
        ]
    )

    assert calls == [2, "savefig"]
