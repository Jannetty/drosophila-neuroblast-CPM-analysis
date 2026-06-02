# Presentation 3D Lineage Viz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `docs/presentation/figures/lineage_viz.ipynb` — an interactive Plotly notebook that renders the median-volume WT lineage in 3D with presentation-quality styling, for static PNG export via the Plotly toolbar.

**Architecture:** Single self-contained notebook with a config cell (LINEAGE_ID, CAMERA) and a render cell. Uses existing `npa.exp_viz.load_mesh_npz` and `npa.colors` — no new source files. Directory `docs/presentation/figures/` is created new.

**Tech Stack:** Jupyter, Plotly (already installed), `npa` package (installed via `uv`). Run with `uv run jupyter notebook` or activate `.venv` first.

---

### Task 1: Create the notebook

**Files:**
- Create: `docs/presentation/figures/lineage_viz.ipynb`

- [ ] **Step 1: Create the output directory**

```bash
mkdir -p docs/presentation/figures
```

- [ ] **Step 2: Create the notebook file**

Write the following JSON to `docs/presentation/figures/lineage_viz.ipynb`:

```json
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## WT Lineage 3D Visualization\n",
    "\n",
    "Run with the `npa` venv active (`uv run jupyter notebook` or `. .venv/bin/activate`).\n",
    "\n",
    "**To adjust the angle:** edit `CAMERA` in the config cell and re-run the render cell.  \n",
    "**To save PNG:** use the camera icon (⬇) in the Plotly toolbar above the figure."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pathlib import Path\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "import plotly.graph_objects as go\n",
    "\n",
    "from npa.colors import NB_COLOR, PROS_COLOR, EXP_HULL_COLOR as HULL_COLOR\n",
    "from npa.exp_viz import load_index, load_mesh_npz\n",
    "\n",
    "REPO_ROOT = Path('../../../').resolve()\n",
    "PROCESSED_DIR = REPO_ROOT / 'data' / 'exp' / 'processed'\n",
    "\n",
    "# ── edit these two lines ─────────────────────────────────────────────────────\n",
    "LINEAGE_ID = None  # None = auto-pick median-volume WT; set to an int to override\n",
    "CAMERA = dict(eye=dict(x=1.5, y=1.5, z=1.0))  # increase values to zoom out; change ratios to rotate\n",
    "# ─────────────────────────────────────────────────────────────────────────────\n",
    "\n",
    "if LINEAGE_ID is None:\n",
    "    metrics = pd.read_csv(PROCESSED_DIR / 'metrics.csv')\n",
    "    wt = metrics[metrics['genotype'] == 'wt']\n",
    "    median_vol = wt['lin_area_vox'].median()\n",
    "    LINEAGE_ID = int(wt.loc[(wt['lin_area_vox'] - median_vol).abs().idxmin(), 'lineage_id'])\n",
    "\n",
    "index = load_index(PROCESSED_DIR, rejected=False)\n",
    "row = next(r for r in index if int(r['lineage_id']) == LINEAGE_ID)\n",
    "mesh_path = REPO_ROOT / row['mesh_path']\n",
    "print(f\"Lineage {LINEAGE_ID} | {row['genotype']} | {row['lobe']} | n_dpn={row['n_dpn']} n_pros={row['n_pros']}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "def _add_mesh_group(fig, mesh, prefix, color, opacity, name):\n",
    "    def _cell_index(k):\n",
    "        return int(k[len(prefix) + 1:-len('_vertices')])\n",
    "    keys = sorted(\n",
    "        (k for k in mesh if k.startswith(prefix) and k.endswith('_vertices')),\n",
    "        key=_cell_index,\n",
    "    )\n",
    "    for idx, v_key in enumerate(keys):\n",
    "        i = _cell_index(v_key)\n",
    "        f_key = f'{prefix}_{i}_faces'\n",
    "        vertices = np.asarray(mesh[v_key], dtype=np.float32)\n",
    "        faces = np.asarray(mesh[f_key], dtype=np.int32)\n",
    "        fig.add_trace(go.Mesh3d(\n",
    "            x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],\n",
    "            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],\n",
    "            color=color, opacity=opacity,\n",
    "            name=name, legendgroup=name, showlegend=(idx == 0),\n",
    "        ))\n",
    "\n",
    "mesh = load_mesh_npz(mesh_path)\n",
    "fig = go.Figure()\n",
    "\n",
    "lin_v = np.asarray(mesh['lin_vertices'], dtype=np.float32)\n",
    "lin_f = np.asarray(mesh['lin_faces'], dtype=np.int32)\n",
    "fig.add_trace(go.Mesh3d(\n",
    "    x=lin_v[:, 0], y=lin_v[:, 1], z=lin_v[:, 2],\n",
    "    i=lin_f[:, 0], j=lin_f[:, 1], k=lin_f[:, 2],\n",
    "    color=HULL_COLOR, opacity=0.10,\n",
    "    name='lineage hull', legendgroup='lineage hull', showlegend=True,\n",
    "))\n",
    "_add_mesh_group(fig, mesh, prefix='pros', color=PROS_COLOR, opacity=0.50, name='pros')\n",
    "_add_mesh_group(fig, mesh, prefix='dpn',  color=NB_COLOR,   opacity=1.00, name='DPN')\n",
    "\n",
    "fig.update_layout(\n",
    "    paper_bgcolor='white',\n",
    "    scene=dict(\n",
    "        xaxis=dict(visible=False),\n",
    "        yaxis=dict(visible=False),\n",
    "        zaxis=dict(visible=False),\n",
    "        bgcolor='white',\n",
    "        aspectmode='data',\n",
    "    ),\n",
    "    scene_camera=CAMERA,\n",
    "    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)', font=dict(size=14)),\n",
    "    width=1200,\n",
    "    height=800,\n",
    "    margin=dict(l=0, r=0, t=0, b=0),\n",
    ")\n",
    "fig.show()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
```

- [ ] **Step 3: Verify the notebook runs**

From the repo root with the venv active:

```bash
uv run jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=60 \
  docs/presentation/figures/lineage_viz.ipynb \
  --output /tmp/lineage_viz_test.ipynb 2>&1 | tail -5
```

Expected: no errors; last lines should mention "Writing". If `fig.show()` errors in headless mode, that is fine — the data-loading and figure-building cells above it must succeed. Alternatively, open the notebook interactively:

```bash
uv run jupyter notebook docs/presentation/figures/lineage_viz.ipynb
```

Run both cells in order. The output cell should display an interactive 3D figure with the lineage hull (light gray, transparent), pros cells (teal, semi-transparent), and DPN cell(s) (purple, solid). The printed line from Cell 1 should read something like:

```
Lineage 84 | wt | lobe7 | n_dpn=1 n_pros=43
```

- [ ] **Step 4: Commit**

```bash
git add docs/presentation/figures/lineage_viz.ipynb \
        docs/plans/design_plans/21_presentation_3d_lineage_viz.md \
        docs/plans/implementation_plans/21_presentation_3d_lineage_viz.md
git commit -m "feat: add presentation 3D lineage viz notebook (WT median-volume)"
```
