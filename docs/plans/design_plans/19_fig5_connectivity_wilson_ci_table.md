# Design: Figure 5 — Supplemental Connectivity Wilson CI Table

**Date:** 2026-05-15

## Overview

Add a standalone script that reads the already-computed `nb_connectivity_metrics.csv`
from the adhesion decoupling sweep and produces a supplemental table showing, for
each (regulatory dynamic × adhesion × relrot) cell, the fraction of runs where all
NBs were connected along with its 95% Wilson confidence interval.

The table makes explicit that differences like VOL-PDE / J=50 / mu=45→mu=90
(0.48 → 0.58) are within sampling noise given n=50 runs per condition.

## Inputs

`data/sim/processed_decoupling_adhesion/nb_connectivity_metrics.csv`
(produced by `scripts/extract_adhesion_metrics.py`; already exists)

## Outputs

Two files written to `docs/tex_draft/figures/`:

| File | Description |
|---|---|
| `figure5_supp_connectivity_ci_table.csv` | Long-form machine-readable CSV with one row per (regulatory_dynamic, adhesion, relrot_label) |
| `figure5_supp_connectivity_ci_table.tex` | Wide-format LaTeX table fragment suitable for pasting into the supplement |

### CSV columns

`regulatory_dynamic, adhesion, relrot_label, n_connected, n_total, frac, ci_lo, ci_hi`

All numeric columns are rounded to 4 decimal places. `ci_lo` and `ci_hi` are the
95% Wilson CI bounds.

### LaTeX table layout

Two sub-tables (one per `regulatory_dynamic`), each with:

- Rows = adhesion (J=50, J=40, J=20)
- Columns = relrot_label (off, 0°, 45°, 90°)
- Cell content = `0.XX [0.XX, 0.XX]` (frac [ci\_lo, ci\_hi])

Header row labels the relrot column as the apical axis rotation mean.

## Script

**File:** `scripts/generate_connectivity_ci_table.py`

### Wilson CI formula

For k successes in n trials at confidence level 1−α (z = 1.96 for 95%):

```
p_hat  = k / n
denom  = 1 + z² / n
center = (p_hat + z² / (2n)) / denom
margin = z * sqrt(p_hat * (1 - p_hat) / n + z² / (4n²)) / denom
ci_lo  = max(0, center - margin)
ci_hi  = min(1, center + margin)
```

Edge cases: if `n == 0`, all output values are `nan`.

### CLI

```
uv run python scripts/generate_connectivity_ci_table.py \
    --proc-dir data/sim/processed_decoupling_adhesion \
    --out-dir  docs/tex_draft/figures
```

Both flags have the defaults shown above.

## Makefile

Add a new phony target `fig5-supp-table` declared alongside the other `fig5` targets:

```makefile
fig5-supp-table:
    $(UV) scripts/generate_connectivity_ci_table.py \
        --proc-dir $(ADH_PROC_DIR) \
        --out-dir  $(TEX_DIR)/figures
```

This target is independent of `fig5` (it only reads CSVs, no notebook re-run needed).
It is not added as a dependency of `fig5` — run it explicitly when the supplemental
table needs updating.

## PIPELINE.md

Add a new section "Step 9 — Figure 5 supplemental connectivity table" after Step 8.

## Testing

Run `make fig5-supp-table` and confirm:
- `docs/tex_draft/figures/figure5_supp_connectivity_ci_table.csv` — 24 data rows
  (2 reg dynamics × 3 adhesion × 4 relrot), correct columns
- `docs/tex_draft/figures/figure5_supp_connectivity_ci_table.tex` — two tabular
  environments; spot-check that VOL-PDE / J=50 / mu=45 shows `0.48 [0.33, 0.63]`
  and mu=90 shows `0.58 [0.43, 0.72]` (overlap confirms non-significance).
