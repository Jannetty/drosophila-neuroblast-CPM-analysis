# Heterotypic Contact Fraction — Design Spec

**Date:** 2026-04-27
**Notebooks:** `notebooks/div26_systematic_analysis.ipynb`,
               `notebooks/mudmut_systematic_analysis.ipynb`

---

## Scientific motivation

Existing metrics (`lin_area_vox`, `n_pros`, `n_dpn`, `dpn_area_vox`,
`avg_dpn_area_vox`) capture the size and cell-type composition of a lineage but
not its spatial organisation. The hypothesis is that rotation distributions
affect which cells end up adjacent to which — even when total cell counts are
similar — because division-plane and apical-axis angles determine where daughter
cells are deposited relative to the parent NB.

Heterotypic contact fraction measures the degree to which NB and non-NB cells
are spatially intermixed vs. segregated. In a Cellular Potts Model this quantity
is directly tied to interfacial energy and is therefore a natural structural
readout.

---

## Metric definitions

### Raw heterotypic contact fraction (`het_frac`)

For a given geo tensor at the last timepoint:

1. Classify every pixel as one of three states:
   - **NB** — channel 0 > 0
   - **non-NB** — channel 1 > 0 (includes GMC and neuron; pop2 + pop3)
   - **empty** — both channels = 0
2. Scan all pairs of horizontally or vertically adjacent pixels (4-connectivity).
   Discard any pair where either pixel is empty.
3. Classify each occupied-pair contact:
   - **heterotypic** — one pixel is NB and the other is non-NB
   - **homotypic** — both pixels are the same type (NB-NB or non-NB-non-NB)
4. `het_frac = heterotypic_contacts / (heterotypic_contacts + homotypic_contacts)`

Range: [0, 1]. Higher = more intermixed.

**Channel mapping** (from `build_geo_tensor` in `sim_preprocessing.py`):
- Channel 0: pop1 (NB / deadpan-positive cells)
- Channel 1: pop2 + pop3 (GMC and neuron; all non-NB progeny)
- Pop4 (pros-positive cells) is not encoded in the stored geo tensor.

### Normalised heterotypic contact fraction (`norm_het_frac`)

`het_frac` is approximately size-invariant (both numerator and denominator grow
linearly with N occupied pixels), but its ceiling depends on the relative
proportions of NB and non-NB pixels. A lineage with few NBs cannot reach the
same `het_frac` as one with equal proportions even if spatial mixing is
identical. To remove this compositional confound:

```
p_nb    = NB_pixels / occupied_pixels
p_nonnb = nonNB_pixels / occupied_pixels
expected_het_frac = 2 × p_nb × p_nonnb
norm_het_frac = het_frac / expected_het_frac
```

`expected_het_frac` is the value that would arise from a random shuffle of the
same pixel labels. Thus:

| `norm_het_frac` | Interpretation |
|---|---|
| = 1 | mixing indistinguishable from random |
| > 1 | more mixed than random |
| < 1 | segregated (like types cluster) |

`norm_het_frac` is the primary comparison metric. `het_frac` is reported
alongside it for transparency.

**Edge case:** if `expected_het_frac = 0` (lineage contains only one cell type
at the last timepoint), set `norm_het_frac = NaN` for that run.

---

## Data source

Geo tensors are stored in condition NPZ files under
`data/sim/processed_div26/` (div26 notebook) or the corresponding path for the
mudmut notebook. Each NPZ has a `geo` array of shape `(n_runs, H, W, 2)`. The
row index for each `(condition, sim_id, run_id)` is looked up from
`sim_run_index.csv`.

Only the **last timepoint** is relevant. The geo tensors stored in the NPZ
files are the last-timepoint snapshots (one tensor per run), so no timepoint
filtering is needed beyond using the NPZ rather than the timepoint metrics CSV.

Compute is performed for **all** conditions and both VCV modes (not restricted
to `accepted_mm_conditions`), so that WT conditions can also be compared. The
`accepted_mm_conditions` filter is applied only for the per-section charts, not
during data collection.

---

## Implementation

### Step 1 — Function: `heterotypic_contact_fraction(geo)` (Section 0 helpers)

Add to the `s0-helpers` cell in both notebooks.

Input: `geo` — `(H, W, 2)` float32 array.
Returns: `dict` with keys `het_frac`, `norm_het_frac`, `p_nb`, `p_nonnb`,
`n_occupied` (useful for debugging and filtering).

Algorithm (fully vectorised with numpy):

```
nb    = geo[..., 0] > 0          # (H, W) bool
nonnb = geo[..., 1] > 0          # (H, W) bool
occ   = nb | nonnb

# Horizontal contacts: compare pixel (i,j) with (i,j+1)
a_h = occ[:, :-1] & occ[:, 1:]   # mask: both occupied
# Vertical contacts: compare pixel (i,j) with (i+1,j)
a_v = occ[:-1, :] & occ[1:, :]

For each shift direction:
    nb_left / nb_right / nb_top / nb_bottom  — NB status of each pixel in pair
    heterotypic_h = a_h & (nb[:, :-1] != nb[:, 1:])  # one NB, one not
    # (equivalently: XOR of nb masks where both occupied)

total_contacts     = a_h.sum() + a_v.sum()
het_contacts       = heterotypic_h.sum() + heterotypic_v.sum()
het_frac           = het_contacts / total_contacts  (NaN if total=0)

p_nb    = nb[occ].mean()
p_nonnb = nonnb[occ].mean()
expected = 2 * p_nb * p_nonnb
norm_het_frac = het_frac / expected  (NaN if expected=0)
```

---

### Step 2 — Compute cell (`s-het-compute`)

**Placement:** new cell after `s1b-output` (roundness filter), before Section 2+3
header. This ensures it runs with the full condition set (not just accepted), but
is positioned so the results are available for all subsequent sections.

**Logic:**

```
het_records = []

for each condition in ALL conditions (WT + mudmut, both VCV modes):
    rows = run_idx where condition matches
    group by npz_path (load each NPZ once):
        load geo array
        for each row:
            geo_i = geo[npz_row]
            result = heterotypic_contact_fraction(geo_i)
            append {condition, sim_id, run_id, het_frac, norm_het_frac,
                    p_nb, p_nonnb, n_occupied}

het_df = pd.DataFrame(het_records)
join regulatory_dynamic and critical_volume_mode from sim via sim_id
join tag / genotype from condition lookup tables

print summary table: mean ± SD of norm_het_frac grouped by (genotype, tag, vcv)
```

Save to `data/sim/processed_div26/het_contact_metrics.csv` so it can be
reloaded without re-running the compute step.

---

### Step 3 — Chart cell (`s-het-chart`)

**Placement:** immediately after `s-het-compute`.

Two figures:

**Figure A — By angle condition (primary comparison)**

Grouped box-and-whisker plot. Purpose: show whether rotation distributions
affect mixing.

- X-axis: all accepted mudmut tags, ordered by `(div_mean, rot_stdev, rot_mean)`
- Two box sets per tag: VCV=1 (solid fill) and VCV=0 (hatched), same colour per
  tag as the rest of the notebook (`MM_COND_COLORS`)
- Y-axis: `norm_het_frac` (0–~2 scale; reference line at y=1 for random mixing)
- WT values shown as horizontal reference lines (one per VCV, dotted) using
  the mean of `norm_het_frac` across all WT runs for that VCV mode
- No experimental reference (no exp analogue for this metric)
- Annotate each box median

**Figure B — By regulatory dynamic (secondary comparison)**

2-row × 5-column facet grid, same layout as `mudmut_facet_chart`.

- Same axes and reference line as Figure A
- X-axis within each panel: accepted mudmut tags
- Purpose: show whether regulatory dynamics affect mixing independently of
  angle conditions

Both figures saved to
`data/sim/processed_div26/figures/analysis/het_contact_*.png`.

---

## Chart conventions

- Y-axis: `norm_het_frac` (primary); `het_frac` optionally in a separate figure
  if the normalised and raw values tell different stories.
- Reference line at **y = 1**: random-mixing baseline (solid grey, labelled).
- WT reference lines: one per VCV mode (mean over all WT runs and conditions),
  shown as dotted horizontal lines with VCV annotated.
- Colour: same per-condition palette (`MM_COND_COLORS`) as the rest of the
  notebook; VCV=0 hatched, VCV=1 solid.

---

## Interpretation guidance

- **norm_het_frac > 1**: NBs and non-NB progeny are more intermixed than
  expected given their proportions. Consistent with random daughter-cell
  placement.
- **norm_het_frac < 1**: NBs and non-NB progeny are spatially segregated. May
  arise if repeated asymmetric divisions deposit progeny on one side of the NB,
  or if regulatory feedback keeps NB-adjacent space occupied by other NBs.
- **Variation across angle conditions with stable composition metrics**: the
  strongest evidence that rotation distribution affects spatial organisation
  independently of lineage size.
- **Correlation with `lin_area_vox` or `n_dpn`**: if `norm_het_frac` tracks
  another metric, the spatial effect may be a secondary consequence of size
  differences rather than rotation per se. Check the scatter plot between
  `norm_het_frac` and each composition metric.

---

## Open questions and known limitations

- **Pop4 (pros) not encoded:** pros-positive cells are excluded from the geo
  tensor. `het_frac` therefore measures NB ↔ (GMC + neuron) mixing only.
  If pros-positive cells occupy significant space they will show up as empty
  voxels, which could underestimate total contacts near the lineage boundary.
- **2D projection artefacts:** the geo tensor is a 2D projection of a 3D
  simulation. Cells overlapping in z are merged, potentially inflating
  apparent contact counts. This is a systematic bias shared by all conditions,
  so comparisons across conditions remain valid.
- **Timepoint:** only the last timepoint is analysed. Early-timepoint mixing
  patterns are not captured, though they could be computed from
  `sim_timepoint_metrics.csv` if desired.
- **WT conditions have no APICAL variation** in the div26 sweep, so any
  WT reference line represents only the DIV-mean effect. The WT reference
  is shown for orientation but should not be treated as a calibration target.
