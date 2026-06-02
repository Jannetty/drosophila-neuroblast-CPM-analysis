# 3D Lineage Visualization — Presentation Figure

## Goal

A Jupyter notebook at `docs/presentation/figures/lineage_viz.ipynb` that renders one WT lineage as a styled 3D figure and exports it as a PNG for embedding in slide decks. Distinct from manuscript figures in `docs/tex_draft/`.

## Scope

- Single notebook, single figure (one lineage, one camera angle)
- Interactive Plotly render in notebook → manual PNG download via Plotly toolbar
- No new dependencies (no kaleido)
- User iterates by editing a config cell and re-running

## Notebook Structure

### Cell 1 — Config (the only cell the user edits)

```python
LINEAGE_ID = 84        # WT lineage closest to median lin_area_vox (~5592 vox, lobe7_11)
CAMERA = dict(eye=dict(x=1.5, y=1.5, z=1.0))   # edit to adjust viewing angle
```

`LINEAGE_ID` can be overridden to any row in `lineage_index.csv`. `CAMERA.eye` follows Plotly's convention: (0,0,2) is top-down, (2,0,0) is side-on from x, (1.5,1.5,1) is isometric-ish.

### Cell 2 — Render

Loads the NPZ mesh for the selected lineage, builds a Plotly `Figure` with:
- White background
- No axis labels, tick marks, gridlines, or background panes
- Lineage hull: `EXP_HULL_COLOR` (#d4d4d4), opacity 0.10
- Pros cells: `PROS_COLOR` (#73BFB8), opacity 0.50, one trace group
- DPN cells: `NB_COLOR` (#827191), opacity 1.00, one trace group
- Legend in top-left, `aspectmode="data"`
- Figure width 1200 px, height 800 px (16:9 slide panel)
- `scene_camera=CAMERA`

Calls `fig.show()`. User rotates to preferred angle, then clicks the camera icon in the Plotly toolbar to download PNG.

## Data

- Lineage index: `data/exp/processed/lineage_index.csv`
- Metrics (for median selection): `data/exp/processed/metrics.csv`
- Mesh files: `data/exp/processed/meshes/wt/<lobe>_<idx>.npz`
- Colors imported from `src/npa/colors.py`

## Median lineage selection

Computed at notebook load time:

```python
import pandas as pd
metrics = pd.read_csv("data/exp/processed/metrics.csv")
wt = metrics[metrics["genotype"] == "wt"]
median_vol = wt["lin_area_vox"].median()
default_id = wt.loc[(wt["lin_area_vox"] - median_vol).abs().idxmin(), "lineage_id"]
```

Currently resolves to lineage 84 (lobe7_11, n_pros=43, lin_area_vox=5592).

## Output location

`docs/presentation/figures/` — create this directory as part of implementation. It is separate from `docs/tex_draft/figures/`. PNGs downloaded via browser land in the user's Downloads folder.

## Out of scope

- Multiple views / panels
- Automatic PNG export (requires kaleido)
- mudmut or other genotypes
- Annotation overlays (cell count labels, scale bar)
