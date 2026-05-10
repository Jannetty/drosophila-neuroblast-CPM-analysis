# Plan 11 — Mudmut div-distribution refactor: Stdev26 → Stdev50

## Motivation

The mudmut `DIV_ROTATION_DISTRIBUTION` is currently `NORMAL(MU=0,SIGMA=26)` everywhere.
Analysis of experimental data (see `explore_rotation_csvs.ipynb`) calibrated the
mudmut div standard deviation to **50°**, not 26°.  Separately, the
`decoupling_adhesion` sweep previously treated `div_stdev` as an independent variable
(levels 26 / 45 / 90); that dimension is being removed — all mudmut simulations will
now use `div_stdev = 50` uniformly.

This plan covers: ARCADE setup files → raw data directories → preprocessing pipeline
outputs → analysis notebooks.

---

## Scope summary

| Location | Before | After |
|---|---|---|
| `ARCADE/sweep/` mudmut dirs | `mudmut_divMean0Stdev26_rotMean0Stdev30[_noadhesion]` | `mudmut_divMean0Stdev50_rotMean0Stdev30[_noadhesion]` |
| `ARCADE/decoupling_adhesion/` | 36 conditions (3 adh × 3 stdev × 4 relrot) | 12 conditions (3 adh × 1 stdev × 4 relrot) |
| `data/sim/sweep/` mudmut dirs | same renames as ARCADE/sweep | same |
| `data/sim/processed_sweep/` | `mudmut_divMean0Stdev26_rotMean0Stdev30*.npz` | `mudmut_divMean0Stdev50_rotMean0Stdev30*.npz` |
| `data/sim/decoupling_adhesion/` | 36 raw-output dirs | 12 raw-output dirs |
| `data/sim/processed_decoupling_adhesion/` | 36-condition NPZ + CSVs | 12-condition NPZ + CSVs |
| WT data (`wt_divMean0Stdev26`, `data/sim/decoupling/`) | **unchanged** | **unchanged** |

---

## Part 1 — ARCADE setup files

### 1a. `~/bagherilab/ARCADE/sweep/`

Rename two condition directories and edit all XMLs within them.

**Directory rename:**
```
mudmut_divMean0Stdev26_rotMean0Stdev30           →  mudmut_divMean0Stdev50_rotMean0Stdev30
mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion →  mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion
```

**Expected directory tree after edit:**
```
ARCADE/sweep/
├── mudmut_divMean0Stdev50_rotMean0Stdev30/
│   ├── vcv0_nb_abm/vcv0_nb_abm.xml
│   ├── vcv0_nb_pde/vcv0_nb_pde.xml
│   ├── vcv0_noreg/vcv0_noreg.xml
│   ├── vcv0_vol_abm/vcv0_vol_abm.xml
│   ├── vcv0_vol_pde/vcv0_vol_pde.xml
│   ├── vcv1_nb_abm/vcv1_nb_abm.xml
│   ├── vcv1_nb_pde/vcv1_nb_pde.xml
│   ├── vcv1_noreg/vcv1_noreg.xml
│   ├── vcv1_vol_abm/vcv1_vol_abm.xml
│   └── vcv1_vol_pde/vcv1_vol_pde.xml
├── mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion/
│   ├── vcv1_vol_abm/vcv1_vol_abm.xml
│   └── vcv1_vol_pde/vcv1_vol_pde.xml
└── wt_divMean0Stdev26/          ← unchanged
    └── ... (10 sim-id subdirs)
```

**XML edits (12 files, one per sim-id subdirectory):**

In each XML, change the `DIV_ROTATION_DISTRIBUTION` parameter value only:
```xml
<!-- Before -->
<population.parameter id="proliferation/DIV_ROTATION_DISTRIBUTION" value="NORMAL(MU=0,SIGMA=26)"/>

<!-- After -->
<population.parameter id="proliferation/DIV_ROTATION_DISTRIBUTION" value="NORMAL(MU=0,SIGMA=50)"/>
```

Note: the sweep XML series names (e.g. `vcv1_vol_abm_mudmut_volume_volumeABM_detdiff`) do **not**
encode the stdev abbreviation, so no series name edits are needed in the sweep XMLs.

---

### 1b. `~/bagherilab/ARCADE/decoupling_adhesion/`

The 36-condition directory is replaced with 12 conditions — the `div_stdev` axis is
removed entirely; all conditions use `Stdev50`.

**Remove all 36 existing condition directories** (or archive — see Part 2):
```
mudmut_adh{20,40,50}_divMean0Stdev{26,45,90}[_relrotMean{0,45,90}]
```

**Create 12 new condition directories**, each containing `vcv1_vol_abm/` and
`vcv1_vol_pde/` subdirectories with one XML each:

```
ARCADE/decoupling_adhesion/
├── mudmut_adh20_divMean0Stdev50/
│   ├── vcv1_vol_abm/vcv1_vol_abm.xml
│   └── vcv1_vol_pde/vcv1_vol_pde.xml
├── mudmut_adh20_divMean0Stdev50_relrotMean0/
│   ├── vcv1_vol_abm/vcv1_vol_abm.xml
│   └── vcv1_vol_pde/vcv1_vol_pde.xml
├── mudmut_adh20_divMean0Stdev50_relrotMean45/
│   └── ...
├── mudmut_adh20_divMean0Stdev50_relrotMean90/
│   └── ...
├── mudmut_adh40_divMean0Stdev50/
│   └── ...
├── mudmut_adh40_divMean0Stdev50_relrotMean0/
│   └── ...
├── mudmut_adh40_divMean0Stdev50_relrotMean45/
│   └── ...
├── mudmut_adh40_divMean0Stdev50_relrotMean90/
│   └── ...
├── mudmut_adh50_divMean0Stdev50/
│   └── ...
├── mudmut_adh50_divMean0Stdev50_relrotMean0/
│   └── ...
├── mudmut_adh50_divMean0Stdev50_relrotMean45/
│   └── ...
└── mudmut_adh50_divMean0Stdev50_relrotMean90/
    └── ...
```

**How to produce each XML:** copy the corresponding `Stdev26` XML and apply two edits:
1. `DIV_ROTATION_DISTRIBUTION` value: `SIGMA=26` → `SIGMA=50`
2. Series name: `sg26` → `sg50` (the series name abbreviation used in decoupling_adhesion XMLs
   follows the pattern `..._mudmut_adh{X}_sg26[_relMu{Y}]_detdiff`)

Example before/after for `mudmut_adh50_divMean0Stdev50/vcv1_vol_abm/vcv1_vol_abm.xml`:
```xml
<!-- Before (from Stdev26 source) -->
<series name="vcv1_vol_abm_mudmut_adh50_sg26_detdiff" ...>
    ...
    <population.parameter id="proliferation/DIV_ROTATION_DISTRIBUTION" value="NORMAL(MU=0,SIGMA=26)"/>

<!-- After -->
<series name="vcv1_vol_abm_mudmut_adh50_sg50_detdiff" ...>
    ...
    <population.parameter id="proliferation/DIV_ROTATION_DISTRIBUTION" value="NORMAL(MU=0,SIGMA=50)"/>
```

**`run_decoupling_adhesion.sh`:** Replace the 36-entry `CONDITION_DIRS` array with
the 12 new names:
```bash
CONDITION_DIRS=(
    # adh50
    "mudmut_adh50_divMean0Stdev50"             "mudmut_adh50_divMean0Stdev50_relrotMean0"
    "mudmut_adh50_divMean0Stdev50_relrotMean45" "mudmut_adh50_divMean0Stdev50_relrotMean90"
    # adh40
    "mudmut_adh40_divMean0Stdev50"             "mudmut_adh40_divMean0Stdev50_relrotMean0"
    "mudmut_adh40_divMean0Stdev50_relrotMean45" "mudmut_adh40_divMean0Stdev50_relrotMean90"
    # adh20
    "mudmut_adh20_divMean0Stdev50"             "mudmut_adh20_divMean0Stdev50_relrotMean0"
    "mudmut_adh20_divMean0Stdev50_relrotMean45" "mudmut_adh20_divMean0Stdev50_relrotMean90"
)
```

---

## Part 2 — Raw simulation data directories

The existing raw data was produced with `SIGMA=26` and is no longer valid. Archive it
before running new simulations.

### 2a. Archive old sweep mudmut raw data
```
data/sim/sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/
  → data/archive/sim/sweep_unused_conditions/mudmut_divMean0Stdev26_rotMean0Stdev30/

data/sim/sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/
  → data/archive/sim/sweep_unused_conditions/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/
```

### 2b. Archive old decoupling_adhesion raw data
All 36 existing condition dirs under `data/sim/decoupling_adhesion/` move to archive:
```
data/sim/decoupling_adhesion/mudmut_adh{20,40,50}_divMean0Stdev{26,45,90}[_relrotMean{0,45,90}]/
  → data/archive/sim/decoupling_adhesion_stdev_sweep/  (one flat archive directory)
```

### 2c. Expected `data/sim/` state after simulations re-run

```
data/sim/
├── sweep/
│   ├── mudmut_divMean0Stdev50_rotMean0Stdev30/       ← new (re-run from Stdev50 XML)
│   ├── mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion/  ← new
│   └── wt_divMean0Stdev26/                            ← unchanged
├── decoupling_adhesion/
│   ├── mudmut_adh20_divMean0Stdev50/                  ← new (12 total)
│   ├── mudmut_adh20_divMean0Stdev50_relrotMean0/
│   ├── mudmut_adh20_divMean0Stdev50_relrotMean45/
│   ├── mudmut_adh20_divMean0Stdev50_relrotMean90/
│   ├── mudmut_adh40_divMean0Stdev50/
│   ├── mudmut_adh40_divMean0Stdev50_relrotMean0/
│   ├── mudmut_adh40_divMean0Stdev50_relrotMean45/
│   ├── mudmut_adh40_divMean0Stdev50_relrotMean90/
│   ├── mudmut_adh50_divMean0Stdev50/
│   ├── mudmut_adh50_divMean0Stdev50_relrotMean0/
│   ├── mudmut_adh50_divMean0Stdev50_relrotMean45/
│   └── mudmut_adh50_divMean0Stdev50_relrotMean90/
├── decoupling/                                        ← unchanged (WT)
├── processed_sweep/                                   ← regenerated (Part 3)
├── processed_decoupling/                              ← unchanged (WT)
└── processed_decoupling_adhesion/                     ← regenerated (Part 3)
```

---

## Part 3 — Preprocessing pipeline

No code changes are required to `scripts/preprocess_sim.py`,
`src/npa/metrics.py`, or `scripts/extract_adhesion_metrics.py`.
All three read condition names generically from directory names and parse
`div_stdev` values dynamically via regex.  The outputs will automatically
carry the correct `div_stdev=50` values once run on the new directories.

### 3a. Sweep preprocessing

Delete stale processed outputs, then re-run:
```bash
# Delete stale NPZ and index files for mudmut conditions
rm data/sim/processed_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30.npz
rm data/sim/processed_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion.npz
# Regenerate (wt_divMean0Stdev26.npz and index CSVs are also rebuilt by this command)
uv run python scripts/preprocess_sim.py --sweep-root data/sim/sweep --out-dir data/sim/processed_sweep
```

**Expected `data/sim/processed_sweep/` after re-run:**
```
processed_sweep/
├── mudmut_divMean0Stdev50_rotMean0Stdev30.npz          ← renamed
├── mudmut_divMean0Stdev50_rotMean0Stdev30_noadhesion.npz ← renamed
├── wt_divMean0Stdev26.npz                              ← unchanged
├── sim_index.csv                                       ← regenerated
└── sim_run_index.csv                                   ← regenerated
```

`sim_index.csv` and `sim_run_index.csv` will now contain rows with `div_stdev=50`
instead of `div_stdev=26` for the mudmut conditions.

### 3b. Decoupling-adhesion preprocessing

The full pipeline is:
```bash
make adh-clean
make preprocess-adh
```

(`adh-clean` removes all NPZ and CSV under `processed_decoupling_adhesion/`;
`preprocess-adh` runs `preprocess_sim.py` then `extract_metrics.py` then
`extract_adhesion_metrics.py` on `data/sim/decoupling_adhesion/`.)

**Expected `data/sim/processed_decoupling_adhesion/` after re-run:**
```
processed_decoupling_adhesion/
├── mudmut_adh20_divMean0Stdev50.npz
├── mudmut_adh20_divMean0Stdev50_relrotMean0.npz
├── mudmut_adh20_divMean0Stdev50_relrotMean45.npz
├── mudmut_adh20_divMean0Stdev50_relrotMean90.npz
├── mudmut_adh40_divMean0Stdev50.npz
├── mudmut_adh40_divMean0Stdev50_relrotMean0.npz
├── mudmut_adh40_divMean0Stdev50_relrotMean45.npz
├── mudmut_adh40_divMean0Stdev50_relrotMean90.npz
├── mudmut_adh50_divMean0Stdev50.npz
├── mudmut_adh50_divMean0Stdev50_relrotMean0.npz
├── mudmut_adh50_divMean0Stdev50_relrotMean45.npz
├── mudmut_adh50_divMean0Stdev50_relrotMean90.npz
├── het_contact_metrics.csv
├── nb_exposure_metrics.csv
├── nb_cohesion_metrics.csv
├── nb_connectivity_metrics.csv
├── sim_index.csv
└── sim_run_index.csv
```

All metric CSVs will carry `div_stdev=50` in every row (previously rows existed for
`div_stdev` ∈ {26, 45, 90}).

---

## Part 4 — Analysis notebooks

### 4a. `notebooks/adhesion_decoupling_analysis.ipynb`

This is the most significant notebook change.  The `div_stdev` dimension disappears
from the analysis; everywhere it was used as a filter or sweep variable, it must be
removed or collapsed.

**Cell 0 (intro markdown):** Update the description:
```
# Before
3-factor sweep decoupling NB-NB adhesion (J=50/40/20), division-rotation spread
(sigma=26/45/90), and relative-rotation mode (off / mu=0 / mu=45 / mu=90).

# After
2-factor sweep decoupling NB-NB adhesion (J=50/40/20) and relative-rotation mode
(off / mu=0 / mu=45 / mu=90).  Division-rotation spread is fixed at sigma=50.
```

**Cell 6 (constants block):** Remove `SIGMA_ORDER`; it is no longer a variable:
```python
# Remove this line:
SIGMA_ORDER  = [26, 45, 90]
```

**Cell 7 (`_cond_name` helper):** Remove the `sigma` parameter; hardcode 50:
```python
def _cond_name(adh, relrot_label):
    base = f'mudmut_adh{adh}_divMean0Stdev50'
    if relrot_label == 'off':
        return base
    mu = int(relrot_label.split('=')[1])
    return f'{base}_relrotMean{mu}'
```

**Cell 12 (baseline definition):** Remove the `div_stdev == 26` filter — with only
one stdev value in the data, the filter is redundant:
```python
# Before
_baseline = all_df[(all_df['div_stdev'] == 26) & (all_df['relrot_label'] == 'off')]

# After
_baseline = all_df[all_df['relrot_label'] == 'off']
```

**Cell 16 (sigma-sweep section):** This entire section swept metrics across
`div_stdev` ∈ {26, 45, 90}.  With stdev fixed, it no longer makes sense.
**Remove this section** (or replace with a single-stdev sanity check if desired).

**Cell 20 (relrot slice):** Remove the `div_stdev == 26` filter:
```python
# Before
_relrot_slice = all_df[all_df['div_stdev'] == 26]

# After
_relrot_slice = all_df
```

**Cell 24 (heatmap panel):** Currently produces an adhesion × stdev matrix.
With stdev fixed, this panel should become an adhesion × relrot matrix
(adhesion on one axis, relrot mode on the other).  Redesign the heatmap loop
accordingly.

**Cell 29 (visual examples):** Update hardcoded sigma:
```python
# Before
_SIGMA = 26

# After
_SIGMA = 50
```

---

### 4b. `notebooks/mudmut_systematic_analysis.ipynb`

This notebook references the sweep mudmut condition by its full directory name.
Audit every cell that contains `Stdev26` or `rotMean0Stdev30` and replace with
`Stdev50`.  The most likely locations:

- Any `ANGLE_CONDITIONS` dict or similar that lists `divMean0Stdev26_rotMean0Stdev30`
  as a condition tag → update tag and condition string to `Stdev50`
- Any hardcoded `div_std: 26` metadata → change to `div_std: 50`
- Any `_SIGMA = 26` or `sigma=26` references in commentary or plot labels → 50

Note: this notebook also references many other conditions (Stdev0, Stdev43, etc.)
that are part of a broader sweep not being changed.  Only lines referencing the
`mudmut_divMean0Stdev26_rotMean0Stdev30` condition need to change.

---

### 4c. Figure generation files (`docs/tex_draft/`)

Grep `docs/tex_draft/` for `Stdev26` and `sg26` to identify all affected lines.
Based on the current file listing, candidates are:

- `_figure4_build_notebook.py` — likely references `mudmut_divMean0Stdev26_rotMean0Stdev30`
  as the mudmut baseline condition; update to `Stdev50`
- `_figure5_build_notebook.py` — same

Update any hardcoded condition strings or NPZ paths that include `Stdev26` for mudmut
conditions.  WT condition strings (`wt_divMean0Stdev26`) in these files are **not**
changed.

---

## Part 5 — Out of scope / not changed

| Item | Reason |
|---|---|
| `wt_divMean0Stdev26` conditions everywhere | WT div stdev is unchanged |
| `data/sim/decoupling/` (WT decoupling) | WT only; not affected |
| `data/sim/processed_decoupling/` | WT only; not affected |
| `src/npa/metrics.py` | Regex-based; no hardcoded stdev values |
| `scripts/preprocess_sim.py` | Reads directory names generically |
| `scripts/extract_adhesion_metrics.py` | No hardcoded stdev filter values |
| `Makefile` | All paths are variable-based; no stdev in targets |
| `notebooks/decoupling_analysis.ipynb` | WT decoupling only |
| `notebooks/div26_single_condition.ipynb` | Single-condition WT analysis |
| `notebooks/div26_systematic_analysis.ipynb` | WT systematic analysis |
| `notebooks/yoffset_comparison.ipynb` | WT only |
| `docs/plans/` (all existing plans) | Frozen records; not updated |

---

## Execution order

1. Edit ARCADE setup files (Parts 1a, 1b) — no data dependency
2. Archive old raw data (Part 2)
3. Re-run sweep simulations with new Stdev50 XMLs
4. Re-run decoupling_adhesion simulations with new Stdev50 XMLs
5. Preprocess sweep outputs (Part 3a)
6. Preprocess decoupling_adhesion outputs (Part 3b)
7. Update `adhesion_decoupling_analysis.ipynb` (Part 4a)
8. Update `mudmut_systematic_analysis.ipynb` (Part 4b)
9. Update figure generation files (Part 4c)
