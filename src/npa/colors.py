"""Canonical cell-type and rendering colors for the neurogen-plane-rotation analysis.

Edit this file to change colors everywhere — sim_viz, exp_viz, and all figure
scripts import from here (directly or via docs/tex_draft/_style.py).

Population mapping
------------------
  pop 1 = neuroblasts (NB)   → NB_COLOR
  pop 2 = GMCs               → GMC_COLOR
  pop 3 = neurons            → NEURON_COLOR
"""

# ── cell-type colors ───────────────────────────────────────────────────────────
NB_COLOR     = "#827191"   # neuroblasts  (pop 1)
GMC_COLOR    = "#549EC3"   # GMCs         (pop 2)
NEURON_COLOR = "#73BFB8"   # neurons      (pop 3)

# ── rendering helpers ──────────────────────────────────────────────────────────
SIM_HULL_COLOR = "#606060"   # cell-boundary outlines in simulation renders
EXP_HULL_COLOR = "#d4d4d4"   # cell-boundary outlines in experimental renders

# Prospero+ proxy used in experimental 2-channel geo (channel 1 = non-NB cells)
PROS_COLOR = NEURON_COLOR
