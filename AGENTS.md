# Agent instructions for neurogen-plane-rotation-analysis

## PIPELINE.md — keep it honest

`docs/PIPELINE.md` is the live record of what is actually built. It is not a
design doc — it describes current reality. Update it whenever you:

- Change the behavior of any preprocessing or visualization step
- Fix a bug that changes what a function produces or what it accepts
- Add or remove output keys from any NPZ or CSV
- Change a default parameter value (ds, canvas_size, thresholds, etc.)
- Implement a step that currently has a "Not yet implemented" placeholder
- Discover that the doc describes something incorrectly

Do not update the design plans in `docs/plans/design_plans/` — those are
frozen records of original intent. The user will explicitly request changes
to design plans when needed; agents executing tasks should not touch them.

## Code style

- Keep modules flat and minimal. Do not add abstractions beyond what the task requires.
- No comments unless the WHY is non-obvious. No docstrings that restate what the function name already says.
- Do not add error handling for scenarios that cannot happen.
- Default canvas_size is 200. Default ds is 0.3. Do not change these defaults without updating PIPELINE.md.

## Testing

- Tests in `tests/` serve as documentation of expected behavior. When you fix a
  bug, add a test that would have caught it.
- Use the actual LOCATIONS.json format in test fixtures:
  `{"id": 1, "center": [x,y,z], "location": [{"region": "...", "voxels": [[x,y,z], ...]}]}`
  Not the old recursive format with `"regions"` and `{"x":..., "y":...}` dicts.

## Running the pipelines

```
# Experimental preprocessing
python scripts/preprocess_exp.py --wrl-dir data/exp/wrl_files --out-dir data/exp/processed

# Simulation preprocessing
python scripts/preprocess_sim.py --sweep-root data/sim/bioparams_rotation_sweep/

# Experimental visualization
python scripts/visualize_exp_lineage.py --list
python scripts/visualize_exp_lineage.py --id <lineage_id> --view 3d
```

## Environment

Python managed with `uv`. Run scripts as `uv run python scripts/...` or
activate the venv first. Package name is `npa`.
