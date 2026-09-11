# 25 — Remove PDE-like regulation

**Date:** 2026-09-11
**Supersedes:** `23_figure4_no_pde_variant.md`, `24_fig5_vol_abm_only_variant.md`
(both frozen; their variant outputs are now the only outputs)

---

## Why

PDE-like growth regulation was removed from the ARCADE model on 2026-08-20. Since
then the `PDELIKE` parameter has been inert: it is read by nothing in `src/`, and a
`*_pde` condition produces output byte-identical to its `*_abm` twin.

This was confirmed empirically. In the 2026-09-11 re-run, every `*_pde` condition
matched its `*_abm` counterpart per-seed — for example `VOL-ABM` and `VOL-PDE` in
`sweep/mudmut_divMean0Stdev50_rotMean0Stdev30` produced element-wise identical
`n_dpn` across all 50 seeds.

Figures that still plotted PDE as a distinct regulatory dynamic were therefore
showing duplicate columns. Four `*_pde` conditions in `output/sweep/` additionally
still held pre-2026-08-20 output, which is why they appeared to differ from their
`*_abm` twins: those baselines were stale, not distinct.

## What changed

**Dataset.** `data/sim/{sweep,decoupling,decoupling_adhesion}` replaced with the
2026-09-11 re-run, excluding every `*_pde` condition. 52 sim directories, matching
the 52 surviving setup XMLs. Previous contents (raw and processed) moved to
`data/archive/sim_prePDEremoval/`.

The re-run also carries the `makeDaughterStemCell` critical-volume fix: each cell
now takes its own birth volume as its critical volume, where previously both parent
and daughter took the daughter's. That affects NB-NB divisions only, so all WT
conditions are byte-identical to the previous dataset and mudmut `vcv1` conditions
shifted by 3–10% on endpoint metrics (all p > 0.37; main effects and trend
directions preserved).

**Simulation repo.** The 20 `*_pde` setup directories were deleted and the inert
`PDELIKE` parameter stripped from the remaining 52 XMLs, so setup files match the
model code. Every surviving XML had `PDELIKE=0`, so this changes no behaviour.

**Notebooks.** `figure4_paper_figures.ipynb` and `figure5_paper_figures.ipynb` no
longer reference PDE. The `FIG4_NO_PDE` / `FIG5_NO_PDE` env-var branches are gone
and their former no-PDE behaviour is now unconditional:

- fig4: `DYNAMIC_ORDER` and `PANEL_C_DYNAMICS` are `["NONE", "NB-ABM", "VOL-ABM"]`;
  labels shortened to `NB` / `Vol` and `NB contact` / `volume`.
- fig5: `REG_DYN_ORDER = ["VOL-ABM"]`; the connectivity heatmap uses the sequential
  white→green ramp with a linear norm (the diverging amber→green `TwoSlopeNorm`
  existed only to compare two dynamics); per-column titles dropped; x-axis label is
  `Division plane reference`; lineage panel titles are `J={adh}`.
- `_PANEL_SUFFIX` removed — panels write to their canonical unsuffixed names.

**Makefile.** `fig4-nopde` and `fig5-nopde` removed. `.NOTPARALLEL` is retained for
a different reason: `fig1` and `fig2` both execute `figure12_paper_figures.ipynb`
via `nbconvert --inplace` and would race under `-j`.

**Deleted outputs.** All 30 `*_noPDE*` / `*_ABM_only*` figure files, plus
`fig4/fig4_noPDE.svg` and `fig5/fig5_ABM_only.svg`.

## Also fixed here — sim genotype

`VCV_SIM_METADATA` hardcoded `"genotype": "mudmut"` for every `vcv*` sim_id, so all
500 WT rows in `sim_metrics_last.csv` were labelled mudmut. The `vcv*` ids are shared
by the wt and mudmut conditions and structurally cannot carry genotype; it now comes
from the condition prefix (`CONDITION_PATTERN` captures `wt|mudmut`), falling back to
the legacy `simNN` series map for conditions with no prefix.

Effect is confined to the label: grouping in `summarize_sim_comparison_rows` already
keys on `condition`, so row counts are unchanged (12 sweep, 28 decoupling) and every
non-genotype column is byte-identical. No paper figure reads the sim genotype column —
verified by rebuilding fig4 against the corrected CSVs and getting identical panels.
The one real consumer is `comparison_figures.py` (via `scripts/plot_comparisons.py`,
not in the Makefile), whose WT panels were labelled `MM-VCV1` and now read `WT-VCV1`.

## Not done here

The `.tex` prose still describes four regulatory regimes on two axes, and
`_results.tex` still makes PDE-specific claims. Left untouched deliberately — the
prose is being rewritten separately.

## Consequences to watch

Dropping two of five columns changes panel widths in fig4 (`_FIG4_B_WIDTH` and
`_FIG4_C_WIDTH` scale with `len(DYNAMIC_ORDER)`) and drops fig5's heatmap from two
subplots to one. The composited SVGs need their panel alignment checked in Inkscape.
Supplementary panels built from the fig4 notebook (`figS4_*`, `figS_wt_metrics_grid_panel`)
change shape for the same reason.
