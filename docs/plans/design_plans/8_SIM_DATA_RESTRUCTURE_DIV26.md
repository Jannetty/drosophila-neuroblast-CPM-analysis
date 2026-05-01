# Design Plan: Sim Data Restructure for div26 Sweep

**Context:** The simulation parameter sets are changing. The new ARCADE setup files
split what was previously one monolithic sweep root (all genotypes, all conditions)
into per-genotype, per-parameter superfolders. WT now also runs with VBCV=0
(previously only VBCV=1 was run for WT). This document describes the changes needed
to the preprocessing and ingestion pipeline to accommodate the new structure.
Notebook changes are out of scope here.

---

## 1. What Changed in the Source Data

### Old ARCADE structure (one superfolder → many conditions → many genotypes mixed)

```
bioparams_setupfiles_divMean0Stdev30_rotMean0Stdev30/
    sim41/   ← mudmut, VBCV=1
    sim51/   ← mudmut, VBCV=0
    sim61/   ← wt, VBCV=1
    ...
```

The condition (parameter set) was encoded in the superfolder name. Genotype and VBCV
were encoded only in the sim_id series (4x=mudmut/VCV1, 5x=mudmut/VCV0, 6x=wt/VCV1),
decoded via a hardcoded lookup table in `metrics.py`.

### New ARCADE structure (one superfolder = one condition for one genotype)

```
bioparams_setupfiles_wt_divMean0Stdev26/
    sim61/   ← wt, VBCV=1
    sim71/   ← wt, VBCV=0 (NEW)

bioparams_setupfiles_wt_divMean11Stdev26/
    sim61/
    sim71/

bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev0/
    sim41/   ← mudmut, VBCV=1
    sim51/   ← mudmut, VBCV=0

bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30/
    sim41/
    sim51/

bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean11Stdev30/
    ...

bioparams_setupfiles_mudmut_divMean11Stdev26_rotMean0Stdev0/
    ...

bioparams_setupfiles_mudmut_divMean11Stdev26_rotMean0Stdev30/
    ...

bioparams_setupfiles_mudmut_divMean11Stdev26_rotMean11Stdev30/
    ...
```

Key differences:
- Genotype is now explicit in the superfolder name, not implicit in sim_id.
- WT conditions only have `divMeanXStdevY` (no rot params — rot distribution is
  not parameterized for WT in this sweep).
- Mudmut conditions have `divMeanXStdevY_rotMeanXStdevY`.
- VBCV is still encoded in sim_id series (6x = wt/VCV1, 7x = wt/VCV0; 4x = mudmut/VCV1,
  5x = mudmut/VCV0).
- Sim directories live directly under the superfolder (no condition subdirectory level).

---

## 2. Proposed Repo Data Directory Layout

To fit the existing `preprocess_sim.py` contract (`{sweep_root}/{condition}/{sim_id}/`),
data should be organized under a new sweep root with the ARCADE superfolder names
(minus the `bioparams_setupfiles_` prefix) as condition directories:

```
data/sim/
    bioparams_rotation_sweep/          ← existing data, unchanged
    bioparams_div26_sweep/             ← NEW
        wt_divMean0Stdev26/
            sim61/   ← CELLS/LOCATIONS files here
            sim71/
        wt_divMean11Stdev26/
            sim61/
            sim71/
        mudmut_divMean0Stdev26_rotMean0Stdev0/
            sim41/
            sim51/
        mudmut_divMean0Stdev26_rotMean0Stdev30/
            sim41/
            sim51/
        mudmut_divMean0Stdev26_rotMean11Stdev30/
            sim41/
            sim51/
        mudmut_divMean11Stdev26_rotMean0Stdev0/
            sim41/
            sim51/
        mudmut_divMean11Stdev26_rotMean0Stdev30/
            sim41/
            sim51/
        mudmut_divMean11Stdev26_rotMean11Stdev30/
            sim41/
            sim51/
        METADATA.md
    processed/                         ← existing processed outputs, unchanged
    processed_div26/                   ← NEW processed outputs for new sweep
```

---

## 3. Pipeline Step Changes

### Step 3 — `scripts/preprocess_sim.py` + `src/npa/sim_preprocessing.py`

**No structural changes needed.** The script already accepts an arbitrary
`--sweep-root`. Call it with `--sweep-root data/sim/bioparams_div26_sweep` and
it will iterate condition directories and produce per-condition NPZs as before.

**Invocation:**
```
uv run python scripts/preprocess_sim.py \
    --sweep-root data/sim/bioparams_div26_sweep \
    --out-dir data/sim/processed_div26
```

### Step 5 — `scripts/extract_metrics.py`

**No structural changes needed.** Call with the new sweep root:

```
uv run python scripts/extract_metrics.py --kind sim \
    --sweep-root data/sim/bioparams_div26_sweep \
    --out-dir data/sim/processed_div26
```

### Step 6 — `scripts/summarize_metrics.py` + `src/npa/metrics.py`

Two code changes required:

#### Change A: Extend `SIM_SERIES_METADATA` for sim7x (wt, VBCV=0)

Location: `src/npa/metrics.py`, the `SIM_SERIES_METADATA` dict.

Currently:
```python
SIM_SERIES_METADATA = {
    4: {"genotype": "mudmut", "critical_volume_mode": 1},
    5: {"genotype": "mudmut", "critical_volume_mode": 0},
    6: {"genotype": "wt",     "critical_volume_mode": 1},
}
```

Add:
```python
    7: {"genotype": "wt", "critical_volume_mode": 0},
```

#### Change B: Update `_condition_params` to handle new condition name format

Location: `src/npa/metrics.py`, `_condition_params` function.

Current regex expects exactly `divMeanXStdevY_rotMeanXStdevY` (all four parameters
required). New condition names:
- `wt_divMean0Stdev26` — genotype prefix, no rot suffix
- `mudmut_divMean0Stdev26_rotMean0Stdev30` — genotype prefix, with rot suffix

The updated regex should:
1. Optionally consume a leading `{genotype}_` prefix.
2. Make the `_rotMeanXStdevY` suffix optional, defaulting rot_mean=0, rot_stdev=0.

Proposed updated pattern:
```python
r"(?:(?:wt|mudmut)_)?divMean(?P<div_mean>\d+)Stdev(?P<div_stdev>\d+)"
r"(?:_rotMean(?P<rot_mean>\d+)Stdev(?P<rot_stdev>\d+))?"
```

When the rot group is absent, set `rot_mean=0, rot_stdev=0` explicitly so
downstream code (which reads those columns) does not see NaN.

Note: the old condition names (`divMean0Stdev30_rotMean0Stdev30`) still match
the updated regex, so the old sweep's processed CSVs remain valid without
reprocessing.

### Step 7 — `scripts/plot_comparisons.py` / `src/npa/comparison_figures.py`

No code changes needed. `genotype` and `critical_volume_mode` continue to be
derived from sim_id via `_sim_metadata`. `_condition_params` changes in Step 6
propagate automatically. Verify that the new condition label strings render
sensibly in figure axes — `intra` and `inter` modes format labels from the
parsed metadata columns, not the raw condition name.

---

## 4. New METADATA.md

Create `data/sim/bioparams_div26_sweep/METADATA.md` documenting:

- The sim_id lookup for the new series (sim6x/sim7x for wt; sim4x/sim5x for mudmut)
- The regulatory dynamic mapping (same suffix key as old sweep)
- The parameter tag convention for new condition names
- Which ARCADE superfolders map to which conditions

The format should mirror `data/sim/bioparams_rotation_sweep/METADATA.md`.

---

## 5. What Stays the Same

- `preprocess_sim.py` CLI and internals — no changes.
- `extract_metrics.py` CLI and internals — no changes.
- All experimental preprocessing (Steps 1–2) — unaffected.
- NPZ format, column names in all output CSVs — unchanged.
- `SIM_SERIES_METADATA` lookup for existing series (4x, 5x, 6x) — unchanged;
  only 7x is added.
- The old `bioparams_rotation_sweep` data and `processed/` directory — untouched.

---

## 6. Out of Scope (This Plan)

- Changes to `notebooks/mudmut_systematic_analysis.ipynb` — separate plan.
- Any changes to experimental preprocessing or visualization.
- Any changes to the `plot_comparisons.py` figure layout or metrics.
