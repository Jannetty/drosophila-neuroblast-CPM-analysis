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

## Figure regeneration — keep SVGs in sync

Whenever you change anything that affects a figure — style parameters, cell-type
colors, panel scripts, compositors, data — regenerate the affected figure before
committing.  Use the Makefile targets:

```
make figures    # rebuild all figures (fig1–fig4)
make fig1       # figure 1 only (runs figure12_paper_figures.ipynb → compositor → font normalize)
make fig2       # figure 2 only (same notebook → compositor → font normalize)
make fig3       # figure 3 only (figure3_paper_figures.py → compositor → font normalize)
make fig4       # figure 4 only (panel_a script + figure4_paper_figures.ipynb → compositor)
```

Key files:
- **Colors**: `src/npa/colors.py` — single source; change here and run `make figures`
- **Font/style**: `docs/tex_draft/_style.py`
- **Compositors**: `docs/tex_draft/_build_fig{1,2,3,4}_svg.py`
- **Font normalizer**: `docs/tex_draft/_normalize_svg_fonts.py` (auto-run by make; excludes fig4)

After `make figures`, open the SVGs in Inkscape to realign panels if display
box sizes changed.

## Environment

Python managed with `uv`. Run scripts as `uv run python scripts/...` or
activate the venv first. Package name is `npa`.
