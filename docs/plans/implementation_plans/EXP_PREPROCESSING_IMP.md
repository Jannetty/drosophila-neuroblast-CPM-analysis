# Experimental WRL Preprocessing Implementation Plan

## Summary

Implement experimental WRL preprocessing as a compact `npa.exp_preprocessing`
package plus one CLI. The pipeline converts raw WRL triplets into per-lineage
mesh NPZs, per-genotype stacked analysis NPZs, and a global lineage index CSV.

## Documentation Updates

- In `docs/plans/design_plans/EXP_PREPROCESSING.md`, Pros assignment should use
  the old repo behavior: count the fraction of each Pros cell's vertices that
  fall inside each lineage bounding box.
- Keep Pros threshold at `min_fraction=0.95`.
- Keep Dpn assignment as sampled trimesh containment with `min_fraction=0.60`
  and `n_sample=20`.

## Implementation Changes

- Create package setup and skeleton:
  - `pyproject.toml`
  - `src/npa/exp_preprocessing/{__init__.py,wrl_io.py,lineage_filter.py,geometry.py,pipeline.py}`
  - `scripts/preprocess_exp.py`
- Use canonical genotype names `wt`, `mudmut`, and `nanobody`, with aliases from
  raw folders/files: `Control/control -> wt`, `Mud/mud -> mudmut`, and
  `Nanobody -> nanobody`.
- Implement `wrl_io.py` from the old parser behavior: regex Coordinate and
  `coordIndex` extraction, fan triangulation, `float32` vertices, `int32` faces,
  and compact `trimesh.Trimesh(process=False)` conversion.
- Implement `lineage_filter.py`:
  - Pros assignment: for each Pros mesh, choose the lineage bbox with the
    highest fraction of Pros vertices inside it; assign only if score is at
    least `0.95`.
  - Dpn assignment: sampled mesh containment against lineage meshes with bbox
    prefilter; assign only if score is at least `0.60`.
  - Reject disconnected lineages, then reject lineages with zero Dpn cells.
- Implement `geometry.py`:
  - PCA axes, 2D projection, convex lineage hull polygon, and Voronoi
    rasterization.
  - `geo[..., 0] = Dpn Voronoi territory`, `geo[..., 1] = Pros Voronoi
    territory`; `geo.sum(axis=-1)` represents projected lineage occupancy.
  - Raise `ValueError` if rasterized lineage bounds exceed `canvas_size`.
- Implement `pipeline.py`:
  - Process one lineage into mesh NPZ plus analysis record.
  - Stack records into `data/exp/processed/analysis/{genotype}.npz`.
  - Write counts as `[n_dpn, n_pros, dpn_voxel_sum]`.
- Implement CLI:
  - Defaults: `--wrl-dir data/exp/wrl_files`, `--out-dir data/exp/processed`,
    `--ds 0.3`, `--canvas-size 200`.
  - Support `--genotypes`, `--lobes`, and deterministic triplet discovery.
  - Write `data/exp/processed/lineage_index.csv` with `lineage_id, genotype,
    lobe, lineage_idx, n_dpn, n_pros, mesh_path, analysis_row`.

## Test Plan

- Unit-test WRL parsing with synthetic shared and per-mesh Coordinate blocks.
- Unit-test Pros vertex-fraction bbox assignment for full, partial, and outside
  cases.
- Unit-test Dpn containment assignment with tiny synthetic meshes where feasible.
- Unit-test PCA/projection/rasterization shape, dtype, channel exclusivity,
  centering, and oversized-canvas failure.
- Unit-test analysis stacking and lineage index row consistency.
- Smoke-test one real lobe after implementation, for example
  `uv run python scripts/preprocess_exp.py --genotypes wt --lobes lobe1`.

## Assumptions

- The design plan lives at `docs/plans/design_plans/EXP_PREPROCESSING.md`.
- `data/exp/processed/` outputs are generated artifacts, not source files.

