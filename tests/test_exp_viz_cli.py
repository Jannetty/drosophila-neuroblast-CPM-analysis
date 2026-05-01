from pathlib import Path

import importlib.util
import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "visualize_exp_lineage.py"
)
SPEC = importlib.util.spec_from_file_location("visualize_exp_lineage", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def test_cli_lists_by_default(capsys, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,analysis_row\n"
        "0,wt,lobe1,0,1,1,meshes/wt/lobe1_0.npz,0\n"
    )
    (processed / "rejected_lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,rejection_reason\n"
    )
    monkeypatch.setattr(
        MODULE,
        "default_processed_dir",
        lambda: processed,
    )

    main([])
    output = capsys.readouterr().out
    assert "lineage_id" in output
    assert "wt" in output


def test_cli_rejected_2d_post_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,analysis_row\n"
    )
    (processed / "rejected_lineage_index.csv").write_text(
        "lineage_id,genotype,lobe,lineage_idx,n_dpn,n_pros,mesh_path,rejection_reason\n"
        "0,wt,lobe1,0,0,1,meshes/rejected/wt/lobe1_0.npz,no_dpn\n"
    )
    mesh_dir = processed / "meshes/rejected/wt"
    mesh_dir.mkdir(parents=True)
    (mesh_dir / "lobe1_0.npz").write_bytes(b"")
    monkeypatch.setattr(
        MODULE,
        "default_processed_dir",
        lambda: processed,
    )
    monkeypatch.setattr(
        MODULE,
        "load_mesh_npz",
        lambda _path: {
            "lin_vertices": [],
            "lin_faces": [],
            "dpn_centroids_2d": [],
            "pros_centroids_2d": [],
            "lin_poly_2d": [],
            "dpn_centroids_2d_px": [],
            "pros_centroids_2d_px": [],
            "lin_poly_2d_px": [],
            "ds": 0.3,
        },
    )

    with pytest.raises(ValueError, match="2d-post.*rejected"):
        main(["--rejected", "--row", "0", "--view", "2d-post"])
