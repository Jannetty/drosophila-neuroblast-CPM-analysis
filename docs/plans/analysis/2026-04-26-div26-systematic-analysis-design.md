# div26 Systematic Analysis — Design Spec

**Date:** 2026-04-26
**Notebook:** `notebooks/div26_systematic_analysis.ipynb`
**Parallel to:** `notebooks/mudmut_systematic_analysis.ipynb`

---

## Scientific motivation

Same as the mudmut systematic analysis: identify which combinations of VCV mode,
regulatory dynamic, and angle distributions bring simulated mudmut lineages toward
the experimental mudmut phenotype. This notebook re-runs that analysis on the
`bioparams_div26_sweep` data, which uses:

- A division distribution standard deviation calibrated to experimental data
  (σ=26° instead of σ=30/43°).
- DIV mean variation (MU=0 vs MU=11).
- Apical-axis rotation variation for mudmut only (APICAL: SIGMA=0, 30; MU=0, 11).
- WT now run at both VCV=0 and VCV=1 (previously only VCV=1).

Key structural difference from the old sweep: **WT conditions do not vary the
APICAL distribution** (all WT conditions have APICAL=NORMAL(0,0)). The old
Section 1 sanity check — confirming that APICAL has no effect on WT — is therefore
no longer needed and is replaced by a simpler direct WT filter. The new WT VCV=0
data enables an additional WT VCV comparison not possible in the old sweep.

---

## Reference data

Same source as before: `data/exp/processed/exp_summary.csv`.

| Reference | Symbol | Role |
|---|---|---|
| Experimental WT mean | `wt_mean[m]` | Y-axis anchor (fold change = 0 in log scale) |
| Experimental WT SD | `wt_std[m]` | WT calibration band |
| Experimental mudmut mean | `mm_mean[m]` | Target reference line |
| Experimental mudmut SD | `mm_std[m]` | Target band (±1 SD) |

Direction of effect by metric is identical to the old analysis:

| Metric | Mudmut vs WT (exp) | Target direction |
|---|---|---|
| `lin_area_vox` | mudmut < WT | log FC < 0 |
| `n_pros` | mudmut < WT | log FC < 0 |
| `n_dpn` | mudmut > WT | log FC > 0 |
| `dpn_area_vox` | mudmut < WT | log FC < 0 |
| `avg_dpn_area_vox` | mudmut < WT | log FC < 0 |

---

## Simulation data

Loaded from `data/sim/processed_div26/sim_metrics_last.csv`.

### Simulation subsets

| Subset | sim_ids | genotype | VCV | Used in |
|---|---|---|---|---|
| WT VCV=1 | sim61–65 | wt | 1 | Section 1 |
| WT VCV=0 | sim71–75 | wt | 0 | Section 1 |
| Mudmut VCV=1 | sim41–45 | mudmut | 1 | Sections 1b, 2+3, 4, 5 |
| Mudmut VCV=0 | sim51–55 | mudmut | 0 | Sections 2+3, 4, 5 |

### Conditions

**WT (2 conditions):** DIV varies; APICAL is always NORMAL(0,0).

| Condition | Tag | DIV distribution |
|---|---|---|
| `wt_divMean0Stdev26` | D0S26 | NORMAL(MU=0, SIGMA=26) |
| `wt_divMean11Stdev26` | D11S26 | NORMAL(MU=11, SIGMA=26) |

**Mudmut (6 conditions):** 2 DIV means × 3 APICAL distributions.

| Condition | Tag | DIV | APICAL |
|---|---|---|---|
| `mudmut_divMean0Stdev26_rotMean0Stdev0`   | D0S26_R0S0   | NORMAL(0,26) | NORMAL(0,0)  |
| `mudmut_divMean0Stdev26_rotMean0Stdev30`  | D0S26_R0S30  | NORMAL(0,26) | NORMAL(0,30) |
| `mudmut_divMean0Stdev26_rotMean11Stdev30` | D0S26_R11S30 | NORMAL(0,26) | NORMAL(11,30)|
| `mudmut_divMean11Stdev26_rotMean0Stdev0`  | D11S26_R0S0  | NORMAL(11,26)| NORMAL(0,0)  |
| `mudmut_divMean11Stdev26_rotMean0Stdev30` | D11S26_R0S30 | NORMAL(11,26)| NORMAL(0,30) |
| `mudmut_divMean11Stdev26_rotMean11Stdev30`| D11S26_R11S30| NORMAL(11,26)| NORMAL(11,30)|

The 6 mudmut conditions form a 2×3 grid: DIV mean (0, 11) × APICAL (NORMAL(0,0),
NORMAL(0,30), NORMAL(11,30)). Sections 4a–4c exploit this structure to isolate
effects.

---

## Chart convention

Identical to the old analysis except for section-specific notes below.

**Y-axis (Sections 1, 2+3):** `log10(metric_value / wt_mean[metric])`.

**Y-axis (Section 4):** `log10(metric_value / mm_mean[metric])`, mudmut mean at 0.

**Reference lines (Sections 2+3, 4, 5):**
- Dotted line at y=0: experimental WT mean
- Solid line: experimental mudmut mean
- Shaded band: mudmut ±1 SD

**Reference lines (Section 1):**
- Dotted line at y=0: experimental WT mean
- Shaded band: WT ±1 SD (acceptance region)

**Bars:** mean log fold change across runs ± 1 SD. Annotated with numeric value.

**Figure layout (Sections 2+3, 4):** 2-row × 5-column sub-panel grid.
- Rows: VCV mode (top = VCV=0, bottom = VCV=1)
- Columns: regulatory dynamic (NONE | NB-ABM | VOL-ABM | NB-PDE | VOL-PDE)
- X-axis: accepted angle conditions

**Figure saving:** all figures saved to
`data/sim/processed_div26/figures/analysis/`, with filenames encoding the
section and metric.

---

## Shared utilities (Section 0)

Same three utilities as the old notebook:

```
fold_change_log(values, ref_mean)

draw_example_lineage(condition, sim_id, run_id=None, title=None)
    → looks up row via sim_run_index.csv in processed_div26/

nb_circularity(geo_tensor)
    → minimum NB circularity across components ≥ 50 voxels
```

Note: `draw_example_lineage` must point to
`data/sim/processed_div26/sim_run_index.csv` and the NPZ files under
`data/sim/processed_div26/`.

---

## Section 0 — Setup

- Load `data/sim/processed_div26/sim_metrics_last.csv` and
  `data/exp/processed/exp_summary.csv`
- Extract `wt_ref` and `mm_ref` dicts
- Print reference table (same as old notebook)
- Define shared utilities
- Print condition table with the 2×3 mudmut grid and 2-condition WT table

---

## Section 1 — DIV distribution filter (WT simulations)

**Question:** Which DIV distributions keep WT simulations within ±1 SD of
experimental WT for the top 3 metrics?

**Changes from old notebook:**
- No APICAL sanity check. WT conditions do not vary APICAL; the sanity check is
  vacuously true and is omitted entirely.
- There are only 2 DIV distributions to evaluate (D0S26 and D11S26), not 5.
- WT now has both VCV=0 (sim71–75) and VCV=1 (sim61–65). Both are shown
  together so we can see if VBCV mode affects whether WT tracks experimental WT.

**Charts:** one figure per metric (5 figures, top 3 priority). Each figure:
- X-axis groups: 2 DIV distributions (D0S26, D11S26)
- Bars within each group: one per (VCV, regulatory dynamic) combination — 10 bars
  total, with VCV=0 and VCV=1 bars visually distinguished (e.g. by hatch or
  lighter shade)
- Y-axis: log fold change from experimental WT mean
- WT ±1 SD band as acceptance region

**Filter criterion:** same as old — a DIV distribution is eliminated if any bar
falls outside WT ±1 SD on any of the top 3 metrics. The VCV dimension is
informational here; if only one VCV mode passes for a given DIV distribution,
note which one.

**Output cell:** `accepted_div_distributions` and `accepted_conditions` lists.
Because WT conditions have no APICAL variation, `accepted_conditions` for WT is
just the subset of the 2 WT conditions whose DIV distribution passed. For
downstream sections, `accepted_conditions` refers to the **mudmut conditions**
whose DIV distribution (`div_mean`, `div_stdev`) matches an accepted distribution.

**Visual gut-check:** `draw_example_lineage` for one WT sim at each accepted
DIV distribution to confirm cells look reasonable.

---

## Section 1b — NB roundness filter

Identical to the old notebook in structure. Applies to mudmut VCV=1 sims
(sim41–45) across `accepted_conditions`.

The two new APICAL distributions (NORMAL(0,30) and NORMAL(11,30)) may affect
roundness differently than NORMAL(0,0). The circularity distribution plots will
reveal whether any combination produces degenerate morphology.

**Threshold calibration cell:** same interactive markdown → code pattern.

**Output cell:** updated `accepted_conditions` with roundness exclusions.

---

## Section 2+3 — Regulatory dynamics and VCV (mudmut)

Identical structure to the old notebook. The only differences are:
- `accepted_conditions` now refers to the mudmut 6-condition grid (or accepted
  subset thereof).
- Up to 6 bars per panel on the x-axis instead of up to 9.

**Charts:** one figure per metric (5 figures). 2-row × 5-column grid.
Bars annotated with numeric log fold change values.

**Interpretation cells:** pre-written placeholder markdown.

---

## Section 4 — Angle distribution effects

**Y-axis shift to mudmut-anchored fold change** (same as old notebook).

The 6 mudmut conditions form a 2×3 grid by DIV mean and APICAL distribution.
Each sub-section isolates one axis of variation.

**4a — DIV mean effect:** restrict to conditions with APICAL=NORMAL(0,0)
(D0S26_R0S0 vs D11S26_R0S0, if both accepted). Isolates the effect of shifting
the DIV distribution mean from 0 to 11.

**4b — APICAL sigma effect:** restrict to conditions with DIV=D0S26 and compare
APICAL NORMAL(0,0) vs NORMAL(0,30) (D0S26_R0S0 vs D0S26_R0S30, if accepted).
Isolates the effect of adding apical-axis rotation spread. If D0S26 was not
accepted by Section 1, switch to D11S26 as the fixed DIV baseline (or skip if
neither accepted).

**4c — APICAL mean effect:** within DIV=D0S26 and APICAL sigma=30, compare
NORMAL(0,30) vs NORMAL(11,30) (D0S26_R0S30 vs D0S26_R11S30, if accepted).
Isolates the effect of biasing the apical rotation mean.

**4d — Full 2×3 grid (all accepted conditions):** show all accepted mudmut
conditions side by side. Organized on the x-axis in the natural 2×3 order:
D0S26_R0S0, D0S26_R0S30, D0S26_R11S30, D11S26_R0S0, D11S26_R0S30, D11S26_R11S30.
This gives the complete picture after the component effects in 4a–4c.

**Visual gut-checks:** `draw_example_lineage` for extreme accepted conditions
in each sub-section (e.g. highest vs lowest APICAL sigma, 0-mean vs biased-mean).

---

## Section 5 — Synthesis

Identical to old notebook. Ranked proximity table for top 3 metrics, combined
rank table, analyst interpretation cell.

The one structural note: because the mudmut conditions are now a factorial
2×3 design, the table has a natural additional column showing whether a DIV-mean
or APICAL shift (or both) is associated with higher rank. This is mentioned in the
interpretation cell template but not formally computed.

---

## Differences from `mudmut_systematic_analysis` summary

| Item | Old notebook | This notebook |
|---|---|---|
| Data source | `processed/sim_metrics_last.csv` | `processed_div26/sim_metrics_last.csv` |
| DIV σ values | 0, 30, 43 | 26 only |
| DIV mean values | 0, 36 | 0, 11 |
| APICAL distributions | 0, 30, 43 (with mudmut only) | 0, 30 sigma (with mudmut); mean 0 or 11 |
| WT conditions | 9 (same as mudmut) | 2 (DIV mean only) |
| WT APICAL sanity check | Yes (Section 1 preamble) | **Removed** |
| WT VCV=0 data | No | **Yes — shown in Section 1** |
| Section 1 condition count | 5 DIV distributions | 2 DIV distributions |
| Section 4 structure | 3 sub-sections (DIV-only, APICAL-only, both) | 4 sub-sections (DIV mean, APICAL sigma, APICAL mean, full grid) |
| Mudmut condition count | up to 9 | up to 6 |

---

## Open questions and known limitations

- **Roundness threshold:** must be calibrated visually in Section 1b.
- **Section 4b/4c availability:** depends on which conditions survive Sections 1
  and 1b.
- **WT VCV=0 interpretation:** if VCV=0 WT sims diverge substantially from VCV=1
  WT sims in Section 1, note which VCV mode is used as the accepted baseline going
  forward and why.
- **n_dpn direction:** reversed interpretation must be noted consistently.
- **Run count check:** a setup cell confirms consistent run counts across all
  (condition, sim_id) pairs.
