# Data Refactor — Manuscript-Focused Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Archive unused simulation and experimental data, rename remaining data from opaque numbered identifiers to manuscript-role names, and update all references (CSVs, figure scripts, Makefile) to match the new layout.

**Architecture:** Three stages — (1) archive unused raw data with no file renames; (2) rename kept data directories; (3) update every reference to the old names in processed CSVs, figure generation scripts, and the Makefile. The archive step is destructive, so it runs first and produces checkpoint git commits. Later tasks assume each prior task is complete.

**Tech Stack:** Python (pandas for CSV editing), shell (mv, find), sed for inline string replacement. No new source code needed.

---

## Background

### Why this refactor

The simulation sweep used a large combinatorial parameter grid during development. Simulation identifiers like `sim41`, `sim51`, `sim61` encode position in that grid, not scientific role. The manuscript uses only three conditions from that grid. The rest lives in `data/sim/bioparams_div26_sweep/` and `data/sim/wt_plane_rotation_decoupling/` alongside the used data, making provenance hard to read.

### Data used by manuscript figure scripts

All five figure generation scripts live in `docs/tex_draft/`:
- `paper_figures.ipynb` — Figures 1 and 2
- `figure3_paper_figures.py` — Figure 3
- `figure4_paper_figures.ipynb` — Figure 4
- `figure5_paper_figures.ipynb` — Figure 5

#### Experimental data (all from `data/exp/processed/`)
| File | Used by |
|---|---|
| `exp_summary.csv` | Figs 1, 3 |
| `lineage_index.csv` | Figs 1, 3, 4, 5 |
| `analysis/wt.npz` | Figs 1, 3 |
| `analysis/mudmut.npz` | Figs 3, 4, 5 |
| `meshes/wt/` | Fig 1 (experimental example lineages) |
| `meshes/mudmut/` | Fig 3 (experimental example lineages) |

**Not used by manuscript figure scripts:** `analysis/nanobody.npz`, `meshes/nanobody/`, `meshes/rejected/`.

#### Raw WRL files (`data/exp/wrl_files/`)
Used only to regenerate `data/exp/processed/` via `scripts/preprocess_exp.py`. The manuscript scripts do not load them directly.
- `Control/` → WT genotype (used)
- `Mud/` → mudmut genotype (used)
- `Nanobody/` → nanobody genotype (not in manuscript)

#### Simulation processed metadata (loaded directly by figure scripts)
| File | Used by |
|---|---|
| `data/sim/processed_div26/sim_metrics_last.csv` | Figs 1, 3, 4, 5 |
| `data/sim/processed_div26/sim_run_index.csv` | Figs 1, 3, 4, 5 |
| `data/sim/processed_decoupling/sim_metrics_last.csv` | Fig 2 |
| `data/sim/processed_decoupling/sim_run_index.csv` | Fig 2 |
| `data/sim/processed_adhesion/het_contact_metrics.csv` | Fig 5 |
| `data/sim/processed_adhesion/nb_exposure_metrics.csv` | Fig 5 |

The NPZ files in `processed_div26/` and `processed_decoupling/` are intermediate preprocessing outputs not loaded directly by figure scripts.

#### Raw simulation files (`data/sim/bioparams_div26_sweep/`)
Figure scripts load individual CELLS/LOCATIONS JSON files via the paths stored in `sim_run_index.csv`.

**Used (must keep):**
- `wt_divMean0Stdev26/sim61/` through `sim65/` — VCV=1, 5 regulatory dynamics, 100 runs each (Figs 1, 3; sim71–75 for supplement)
- `wt_divMean0Stdev26/sim71/` through `sim75/` — VCV=0, 5 regulatory dynamics, 100 runs each (supplement WT VCV=0 panels)
- `mudmut_divMean0Stdev26_rotMean0Stdev30/sim41/` through `sim55/` — 10 sim configs × 50 runs each (Figs 3, 4)
- `mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/sim43/`, `sim45/` — 2 sim configs × 50 runs each (Fig 5)

**Not used (archive):**
- All 28 other condition directories in `bioparams_div26_sweep/`
- `mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/sim41/`, `sim42/`, `sim44/`, `sim51/`–`sim55/` (8 extra noadhesion sims)

#### Raw simulation files (`data/sim/wt_plane_rotation_decoupling/`)
12 conditions, each with `sim61/` and `sim71/`. Figure 2 uses `sim61`; supplement uses `sim71`.

**Used (must keep):** Both `sim61/` and `sim71/` within all 12 conditions.
**Not used (archive):** nothing — all decoupling sims are kept.

---

## Proposed New Layout

```
data/
├── archive/
│   ├── exp/
│   │   ├── nanobody_raw/           ← wrl_files/Nanobody/
│   │   └── nanobody_processed/     ← processed/analysis/nanobody.npz
│   │                                  processed/meshes/nanobody/
│   │                                  processed/meshes/rejected/
│   └── sim/
│       ├── sweep_unused_conditions/ ← all 28 non-manuscript conditions from bioparams_div26_sweep/
│       └── mudmut_noadhesion_extra_sims/  ← noadhesion/sim41,42,44,51-55/
├── exp/
│   ├── raw/                         ← renamed from wrl_files/
│   │   ├── wt/                      ← renamed from Control/
│   │   └── mudmut/                  ← renamed from Mud/
│   ├── rotation_csvs/               ← unchanged
│   └── processed/                   ← unchanged
└── sim/
    ├── sweep/                       ← renamed from bioparams_div26_sweep/
    │   ├── wt_divMean0Stdev26/      ← condition name unchanged (used in CSV metadata)
    │   │   ├── vcv1_noreg/          ← renamed from sim61/  (main figures)
    │   │   ├── vcv1_nb_abm/         ← renamed from sim62/
    │   │   ├── vcv1_vol_abm/        ← renamed from sim63/
    │   │   ├── vcv1_nb_pde/         ← renamed from sim64/
    │   │   ├── vcv1_vol_pde/        ← renamed from sim65/
    │   │   ├── vcv0_noreg/          ← renamed from sim71/  (supplement)
    │   │   ├── vcv0_nb_abm/         ← renamed from sim72/
    │   │   ├── vcv0_vol_abm/        ← renamed from sim73/
    │   │   ├── vcv0_nb_pde/         ← renamed from sim74/
    │   │   └── vcv0_vol_pde/        ← renamed from sim75/
    │   ├── mudmut_divMean0Stdev26_rotMean0Stdev30/
    │   │   ├── vcv1_noreg/          ← renamed from sim41/
    │   │   ├── vcv1_nb_abm/         ← renamed from sim42/
    │   │   ├── vcv1_vol_abm/        ← renamed from sim43/
    │   │   ├── vcv1_nb_pde/         ← renamed from sim44/
    │   │   ├── vcv1_vol_pde/        ← renamed from sim45/
    │   │   ├── vcv0_noreg/          ← renamed from sim51/
    │   │   ├── vcv0_nb_abm/         ← renamed from sim52/
    │   │   ├── vcv0_vol_abm/        ← renamed from sim53/
    │   │   ├── vcv0_nb_pde/         ← renamed from sim54/
    │   │   └── vcv0_vol_pde/        ← renamed from sim55/
    │   └── mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/
    │       ├── vcv1_vol_abm/        ← renamed from sim43/
    │       └── vcv1_vol_pde/        ← renamed from sim45/
    ├── decoupling/                  ← renamed from wt_plane_rotation_decoupling/
    │   ├── wt_divMean0Stdev26/
    │   │   ├── vcv1_noreg/          ← renamed from sim61/  (main figures)
    │   │   └── vcv0_noreg/          ← renamed from sim71/  (supplement)
    │   ├── wt_divMean0Stdev26_relrot/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean45Stdev26_relrot/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean90Stdev26_relrot/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev35/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev45/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev60/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev75/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev90/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev26_yoffset50/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   ├── wt_divMean0Stdev26_yoffset62/
    │   │   ├── vcv1_noreg/
    │   │   └── vcv0_noreg/
    │   └── wt_divMean0Stdev26_yoffset75/
    │       ├── vcv1_noreg/
    │       └── vcv0_noreg/
    ├── processed_sweep/             ← renamed from processed_div26/
    ├── processed_decoupling/        ← unchanged
    └── processed_adhesion/          ← unchanged
```

**Why condition directory names are kept:** The `condition` column in `sim_run_index.csv` and `sim_metrics_last.csv` matches the condition directory name. Renaming condition directories requires either regenerating CSVs from scratch (expensive) or a precision search-and-replace across every row. The sim_id directories are cheaper to rename since only the path columns in the CSV need to change, not the `condition` column used as a filter key in figure scripts.

---

## Sim-ID Rename Mapping

### mudmut sweep (bioparams_div26_sweep → sweep)
| Old `sim_id` | New directory name | Role |
|---|---|---|
| `sim41` | `vcv1_noreg` | mudmut, VCV=1, no regulation |
| `sim42` | `vcv1_nb_abm` | mudmut, VCV=1, NB-contact (ABM) |
| `sim43` | `vcv1_vol_abm` | mudmut, VCV=1, volume-based (ABM) |
| `sim44` | `vcv1_nb_pde` | mudmut, VCV=1, NB-contact (PDE) |
| `sim45` | `vcv1_vol_pde` | mudmut, VCV=1, volume-based (PDE) |
| `sim51` | `vcv0_noreg` | mudmut, VCV=0, no regulation |
| `sim52` | `vcv0_nb_abm` | mudmut, VCV=0, NB-contact (ABM) |
| `sim53` | `vcv0_vol_abm` | mudmut, VCV=0, volume-based (ABM) |
| `sim54` | `vcv0_nb_pde` | mudmut, VCV=0, NB-contact (PDE) |
| `sim55` | `vcv0_vol_pde` | mudmut, VCV=0, volume-based (PDE) |

### WT sweep (bioparams_div26_sweep → sweep) — all 10 sims kept
| Old `sim_id` | New directory name | Role |
|---|---|---|
| `sim61` | `vcv1_noreg` | WT, VCV=1, no regulation (main figures) |
| `sim62` | `vcv1_nb_abm` | WT, VCV=1, NB-contact (ABM) |
| `sim63` | `vcv1_vol_abm` | WT, VCV=1, volume-based (ABM) |
| `sim64` | `vcv1_nb_pde` | WT, VCV=1, NB-contact (PDE) |
| `sim65` | `vcv1_vol_pde` | WT, VCV=1, volume-based (PDE) |
| `sim71` | `vcv0_noreg` | WT, VCV=0, no regulation (supplement) |
| `sim72` | `vcv0_nb_abm` | WT, VCV=0, NB-contact (ABM) |
| `sim73` | `vcv0_vol_abm` | WT, VCV=0, volume-based (ABM) |
| `sim74` | `vcv0_nb_pde` | WT, VCV=0, NB-contact (PDE) |
| `sim75` | `vcv0_vol_pde` | WT, VCV=0, volume-based (PDE) |

### Decoupling sweep (wt_plane_rotation_decoupling → decoupling) — both sims kept per condition
| Old `sim_id` | New directory name | Role |
|---|---|---|
| `sim61` | `vcv1_noreg` | WT decoupling, VCV=1, no regulation (main Fig 2) |
| `sim71` | `vcv0_noreg` | WT decoupling, VCV=0, no regulation (supplement) |

---

## Files Modified

| File | Change |
|---|---|
| `data/sim/processed_div26/sim_run_index.csv` | `cells_path`/`locs_path` updated for new dir names; `sim_id` column updated; `npz_path` updated |
| `data/sim/processed_div26/sim_metrics_last.csv` | `sim_id` column updated |
| `data/sim/processed_div26/sim_timepoint_metrics.csv` | `sim_id` column updated |
| `data/sim/processed_div26/sim_summary_last.csv` | `sim_id` column updated |
| `data/sim/processed_div26/sim_index.csv` | `sim_id` column updated |
| `data/sim/processed_decoupling/sim_run_index.csv` | `cells_path`/`locs_path` updated; `sim_id` updated; `npz_path` updated |
| `data/sim/processed_decoupling/sim_metrics_last.csv` | `sim_id` updated |
| `data/sim/processed_decoupling/sim_timepoint_metrics.csv` | `sim_id` updated |
| `data/sim/processed_decoupling/sim_summary_last.csv` | `sim_id` updated |
| `data/sim/processed_decoupling/sim_index.csv` | `sim_id` updated |
| `data/sim/processed_adhesion/het_contact_metrics.csv` | `sim_id` column updated |
| `data/sim/processed_adhesion/nb_exposure_metrics.csv` | `sim_id` column updated |
| `docs/tex_draft/paper_figures.ipynb` | `WT_SIM_ID`, `FIG2_SIM_ID`, dir path constants |
| `docs/tex_draft/figure3_paper_figures.py` | `MUD_SIM_ID`, `WT_SIM_ID`, config file path in `confirm_sim51_configuration()` |
| `docs/tex_draft/figure4_paper_figures.ipynb` | `SIM_MAP` sim_id strings |
| `docs/tex_draft/figure5_paper_figures.ipynb` | `SIM_MAP` sim_id strings |
| `Makefile` | `SIM_SWEEP_ROOT`, `SIM_PROC_DIR`, exp raw dir paths |
| `notebooks/adhesion_comparison.ipynb` | `SWEEP_ROOT`, `PROC_DIR` |
| `notebooks/decoupling_analysis.ipynb` | `SWEEP_ROOT`, `PROC_DIR` |
| `notebooks/div26_systematic_analysis.ipynb` | `SIM_METRICS_PATH`, `SIM_RUN_IDX_PATH` |
| `docs/PIPELINE.md` | update directory references |

---

## Tasks

### Task 1: Archive unused experimental data

**Files:**
- Move: `data/exp/wrl_files/Nanobody/` → `data/archive/exp/nanobody_raw/`
- Move: `data/exp/processed/analysis/nanobody.npz` → `data/archive/exp/nanobody_processed/analysis/nanobody.npz`
- Move: `data/exp/processed/meshes/nanobody/` → `data/archive/exp/nanobody_processed/meshes/nanobody/`
- Move: `data/exp/processed/meshes/rejected/` → `data/archive/exp/nanobody_processed/meshes/rejected/`

- [ ] **Step 1: Create archive directories**

```bash
mkdir -p data/archive/exp/nanobody_raw
mkdir -p data/archive/exp/nanobody_processed/analysis
mkdir -p data/archive/exp/nanobody_processed/meshes
```

- [ ] **Step 2: Move nanobody raw data**

```bash
mv data/exp/wrl_files/Nanobody data/archive/exp/nanobody_raw/
```

- [ ] **Step 3: Move nanobody processed data**

```bash
mv data/exp/processed/analysis/nanobody.npz data/archive/exp/nanobody_processed/analysis/
mv data/exp/processed/meshes/nanobody data/archive/exp/nanobody_processed/meshes/
mv data/exp/processed/meshes/rejected data/archive/exp/nanobody_processed/meshes/
```

- [ ] **Step 4: Verify no remaining nanobody or rejected paths under data/exp/**

```bash
find data/exp -name "*nanobody*" -o -name "*rejected*"
```
Expected: no output.

---

### Task 2: Archive unused simulation conditions from bioparams_div26_sweep

**Files:**
- Move 28 non-manuscript conditions out of `data/sim/bioparams_div26_sweep/`
- Move extra noadhesion sims (only sim43, sim45 needed for Fig 5)
- All 10 WT sims (sim61–65, sim71–75) are kept — no WT archiving

- [ ] **Step 1: Create archive directories**

```bash
mkdir -p data/archive/sim/sweep_unused_conditions
mkdir -p data/archive/sim/mudmut_noadhesion_extra_sims
```

- [ ] **Step 2: Move unused conditions (28 directories)**

The 3 conditions to keep are:
- `wt_divMean0Stdev26`
- `mudmut_divMean0Stdev26_rotMean0Stdev30`
- `mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion`

Move everything else:

```bash
cd data/sim/bioparams_div26_sweep

KEEP="wt_divMean0Stdev26 mudmut_divMean0Stdev26_rotMean0Stdev30 mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion"

for d in */; do
    d="${d%/}"
    skip=0
    for k in $KEEP; do
        [ "$d" = "$k" ] && skip=1 && break
    done
    [ $skip -eq 0 ] && mv "$d" ../../../archive/sim/sweep_unused_conditions/
done
```

- [ ] **Step 3: Move extra noadhesion sim directories (keep only sim43, sim45)**

```bash
for s in sim41 sim42 sim44 sim51 sim52 sim53 sim54 sim55; do
    [ -d "data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/$s" ] && \
    mv "data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/$s" \
       data/archive/sim/mudmut_noadhesion_extra_sims/
done
```

- [ ] **Step 4: Verify remaining sweep structure**

```bash
find data/sim/bioparams_div26_sweep -maxdepth 2 -type d | sort
```

Expected output (exact):
```
data/sim/bioparams_div26_sweep
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim41
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim42
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim43
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim44
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim45
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim51
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim52
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim53
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim54
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/sim55
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/sim43
data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/sim45
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim61
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim62
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim63
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim64
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim65
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim71
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim72
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim73
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim74
data/sim/bioparams_div26_sweep/wt_divMean0Stdev26/sim75
```

---

### Task 3: Verify decoupling directory completeness (no archiving needed)

Both `sim61` and `sim71` are kept in all 12 decoupling conditions — no moves required. This task is a pre-rename sanity check only.

- [ ] **Step 1: Confirm both sim_ids exist in each decoupling condition**

```bash
for cond in data/sim/wt_plane_rotation_decoupling/*/; do
    has61=$( [ -d "${cond}sim61" ] && echo yes || echo MISSING )
    has71=$( [ -d "${cond}sim71" ] && echo yes || echo MISSING )
    echo "$cond   sim61=$has61  sim71=$has71"
done
```

Expected: every line shows `sim61=yes  sim71=yes`. Any `MISSING` means the raw data was not produced for that condition and should be flagged before proceeding.

---

### Task 4: Rename raw sweep directories

Rename top-level directory and condition subdirectories. Internal file names (`2026-04-26-biosim41_...json`) are NOT renamed — they are provenance records.

- [ ] **Step 1: Rename sim directories within WT condition (all 10 sims)**

```bash
WT=data/sim/bioparams_div26_sweep/wt_divMean0Stdev26
mv "$WT/sim61" "$WT/vcv1_noreg"
mv "$WT/sim62" "$WT/vcv1_nb_abm"
mv "$WT/sim63" "$WT/vcv1_vol_abm"
mv "$WT/sim64" "$WT/vcv1_nb_pde"
mv "$WT/sim65" "$WT/vcv1_vol_pde"
mv "$WT/sim71" "$WT/vcv0_noreg"
mv "$WT/sim72" "$WT/vcv0_nb_abm"
mv "$WT/sim73" "$WT/vcv0_vol_abm"
mv "$WT/sim74" "$WT/vcv0_nb_pde"
mv "$WT/sim75" "$WT/vcv0_vol_pde"
```

- [ ] **Step 2: Rename sim directories within mudmut condition**

```bash
SWEEP=data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30
mv "$SWEEP/sim41" "$SWEEP/vcv1_noreg"
mv "$SWEEP/sim42" "$SWEEP/vcv1_nb_abm"
mv "$SWEEP/sim43" "$SWEEP/vcv1_vol_abm"
mv "$SWEEP/sim44" "$SWEEP/vcv1_nb_pde"
mv "$SWEEP/sim45" "$SWEEP/vcv1_vol_pde"
mv "$SWEEP/sim51" "$SWEEP/vcv0_noreg"
mv "$SWEEP/sim52" "$SWEEP/vcv0_nb_abm"
mv "$SWEEP/sim53" "$SWEEP/vcv0_vol_abm"
mv "$SWEEP/sim54" "$SWEEP/vcv0_nb_pde"
mv "$SWEEP/sim55" "$SWEEP/vcv0_vol_pde"
```

- [ ] **Step 3: Rename sim directories within mudmut_noadhesion condition**

```bash
NOADH=data/sim/bioparams_div26_sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion
mv "$NOADH/sim43" "$NOADH/vcv1_vol_abm"
mv "$NOADH/sim45" "$NOADH/vcv1_vol_pde"
```

- [ ] **Step 4: Rename bioparams_div26_sweep → sweep**

```bash
mv data/sim/bioparams_div26_sweep data/sim/sweep
```

- [ ] **Step 5: Rename wt_plane_rotation_decoupling → decoupling and sim61/sim71 → vcv1_noreg/vcv0_noreg within each condition**

```bash
for cond in data/sim/wt_plane_rotation_decoupling/*/; do
    [ -d "${cond}sim61" ] && mv "${cond}sim61" "${cond}vcv1_noreg"
    [ -d "${cond}sim71" ] && mv "${cond}sim71" "${cond}vcv0_noreg"
done
mv data/sim/wt_plane_rotation_decoupling data/sim/decoupling
```

- [ ] **Step 6: Rename processed_div26 → processed_sweep**

```bash
mv data/sim/processed_div26 data/sim/processed_sweep
```

- [ ] **Step 7: Rename exp/wrl_files → exp/raw, Control → wt, Mud → mudmut**

```bash
mv data/exp/wrl_files/Control data/exp/wrl_files/wt
mv data/exp/wrl_files/Mud data/exp/wrl_files/mudmut
mv data/exp/wrl_files data/exp/raw
```

- [ ] **Step 8: Verify new top-level structure**

```bash
find data -maxdepth 3 -type d | sort | grep -v ".DS_Store" | grep -v archive
```

Expected: paths use `sweep/`, `decoupling/`, `processed_sweep/`, `exp/raw/wt`, `exp/raw/mudmut`.

---

### Task 5: Update processed_sweep CSV files

The six CSV files in `data/sim/processed_sweep/` contain `sim_id` values (`sim41`, `sim51`, `sim61`) and `cells_path`/`locs_path`/`npz_path` strings that embed both the old directory name (`bioparams_div26_sweep`) and old sim_id directories (`sim41/`, etc.).

**Replacement table (old string → new string) for path columns:**

| Old | New |
|---|---|
| `data/sim/bioparams_div26_sweep/` | `data/sim/sweep/` |
| `/sim41/` | `/vcv1_noreg/` |
| `/sim42/` | `/vcv1_nb_abm/` |
| `/sim43/` | `/vcv1_vol_abm/` |
| `/sim44/` | `/vcv1_nb_pde/` |
| `/sim45/` | `/vcv1_vol_pde/` |
| `/sim51/` | `/vcv0_noreg/` |
| `/sim52/` | `/vcv0_nb_abm/` |
| `/sim53/` | `/vcv0_vol_abm/` |
| `/sim54/` | `/vcv0_nb_pde/` |
| `/sim55/` | `/vcv0_vol_pde/` |
| `/sim61/` | `/vcv1_noreg/` |
| `/sim62/` | `/vcv1_nb_abm/` |
| `/sim63/` | `/vcv1_vol_abm/` |
| `/sim64/` | `/vcv1_nb_pde/` |
| `/sim65/` | `/vcv1_vol_pde/` |
| `/sim71/` | `/vcv0_noreg/` |
| `/sim72/` | `/vcv0_nb_abm/` |
| `/sim73/` | `/vcv0_vol_abm/` |
| `/sim74/` | `/vcv0_nb_pde/` |
| `/sim75/` | `/vcv0_vol_pde/` |

**Replacement table for the `sim_id` column:**

| Old | New |
|---|---|
| `sim41` | `vcv1_noreg` |
| `sim42` | `vcv1_nb_abm` |
| `sim43` | `vcv1_vol_abm` |
| `sim44` | `vcv1_nb_pde` |
| `sim45` | `vcv1_vol_pde` |
| `sim51` | `vcv0_noreg` |
| `sim52` | `vcv0_nb_abm` |
| `sim53` | `vcv0_vol_abm` |
| `sim54` | `vcv0_nb_pde` |
| `sim55` | `vcv0_vol_pde` |
| `sim61` | `vcv1_noreg` |
| `sim62` | `vcv1_nb_abm` |
| `sim63` | `vcv1_vol_abm` |
| `sim64` | `vcv1_nb_pde` |
| `sim65` | `vcv1_vol_pde` |
| `sim71` | `vcv0_noreg` |
| `sim72` | `vcv0_nb_abm` |
| `sim73` | `vcv0_vol_abm` |
| `sim74` | `vcv0_nb_pde` |
| `sim75` | `vcv0_vol_pde` |

Write and run the following Python script (do not save it to the repo — run it once then delete):

- [ ] **Step 1: Run CSV update script for processed_sweep/**

```python
# run from repo root: uv run python /tmp/update_processed_sweep_csvs.py
import pandas as pd
from pathlib import Path

PROC = Path("data/sim/processed_sweep")

DIR_RENAMES = {
    "data/sim/bioparams_div26_sweep/": "data/sim/sweep/",
    "/sim41/": "/vcv1_noreg/",
    "/sim42/": "/vcv1_nb_abm/",
    "/sim43/": "/vcv1_vol_abm/",
    "/sim44/": "/vcv1_nb_pde/",
    "/sim45/": "/vcv1_vol_pde/",
    "/sim51/": "/vcv0_noreg/",
    "/sim52/": "/vcv0_nb_abm/",
    "/sim53/": "/vcv0_vol_abm/",
    "/sim54/": "/vcv0_nb_pde/",
    "/sim55/": "/vcv0_vol_pde/",
    "/sim61/": "/vcv1_noreg/",
    "/sim62/": "/vcv1_nb_abm/",
    "/sim63/": "/vcv1_vol_abm/",
    "/sim64/": "/vcv1_nb_pde/",
    "/sim65/": "/vcv1_vol_pde/",
    "/sim71/": "/vcv0_noreg/",
    "/sim72/": "/vcv0_nb_abm/",
    "/sim73/": "/vcv0_vol_abm/",
    "/sim74/": "/vcv0_nb_pde/",
    "/sim75/": "/vcv0_vol_pde/",
    # npz_path still references old processed_div26 name (now processed_sweep)
    "data/sim/processed_div26/": "data/sim/processed_sweep/",
}

SIM_ID_MAP = {
    "sim41": "vcv1_noreg", "sim42": "vcv1_nb_abm", "sim43": "vcv1_vol_abm",
    "sim44": "vcv1_nb_pde", "sim45": "vcv1_vol_pde",
    "sim51": "vcv0_noreg", "sim52": "vcv0_nb_abm", "sim53": "vcv0_vol_abm",
    "sim54": "vcv0_nb_pde", "sim55": "vcv0_vol_pde",
    "sim61": "vcv1_noreg", "sim62": "vcv1_nb_abm", "sim63": "vcv1_vol_abm",
    "sim64": "vcv1_nb_pde", "sim65": "vcv1_vol_pde",
    "sim71": "vcv0_noreg", "sim72": "vcv0_nb_abm", "sim73": "vcv0_vol_abm",
    "sim74": "vcv0_nb_pde", "sim75": "vcv0_vol_pde",
}

PATH_COLS = {"cells_path", "locs_path", "npz_path"}

for csv_path in sorted(PROC.glob("*.csv")):
    df = pd.read_csv(csv_path)
    changed = False

    if "sim_id" in df.columns:
        df["sim_id"] = df["sim_id"].map(lambda s: SIM_ID_MAP.get(s, s))
        changed = True

    for col in PATH_COLS & set(df.columns):
        for old, new in DIR_RENAMES.items():
            if df[col].str.contains(old.replace("/", "\\/"), regex=False).any():
                df[col] = df[col].str.replace(old, new, regex=False)
                changed = True

    if changed:
        df.to_csv(csv_path, index=False)
        print(f"updated {csv_path.name}")
```

- [ ] **Step 2: Verify a spot-check**

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/sim/processed_sweep/sim_run_index.csv')
print('sim_id unique:', sorted(df.sim_id.unique()))
print('cells_path sample:', df.cells_path.iloc[0])
"
```

Expected: `sim_id` values are `vcv0_noreg`, `vcv0_nb_abm`, ..., `vcv1_noreg`, `vcv1_nb_abm`, etc. Path starts with `data/sim/sweep/`.

---

### Task 6: Update processed_decoupling CSV files

Same approach. The decoupling run_index references `wt_plane_rotation_decoupling` and `sim61`.

- [ ] **Step 1: Run CSV update script for processed_decoupling/**

```python
# run from repo root: uv run python /tmp/update_decoupling_csvs.py
import pandas as pd
from pathlib import Path

PROC = Path("data/sim/processed_decoupling")

DIR_RENAMES = {
    "data/sim/wt_plane_rotation_decoupling/": "data/sim/decoupling/",
    "/sim61/": "/vcv1_noreg/",
    "/sim71/": "/vcv0_noreg/",
    # npz_path dir unchanged (still processed_decoupling/)
}

SIM_ID_MAP = {"sim61": "vcv1_noreg", "sim71": "vcv0_noreg"}

PATH_COLS = {"cells_path", "locs_path", "npz_path"}

for csv_path in sorted(PROC.glob("*.csv")):
    df = pd.read_csv(csv_path)
    changed = False

    if "sim_id" in df.columns:
        df["sim_id"] = df["sim_id"].map(lambda s: SIM_ID_MAP.get(s, s))
        changed = True

    for col in PATH_COLS & set(df.columns):
        for old, new in DIR_RENAMES.items():
            if df[col].str.contains(old.replace("/", "\\/"), regex=False).any():
                df[col] = df[col].str.replace(old, new, regex=False)
                changed = True

    if changed:
        df.to_csv(csv_path, index=False)
        print(f"updated {csv_path.name}")
```

- [ ] **Step 2: Spot-check**

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/sim/processed_decoupling/sim_run_index.csv')
print('sim_id unique:', sorted(df.sim_id.unique()))
print('cells_path sample:', df.cells_path.iloc[0])
"
```
Expected: `sim_id` values are `['vcv0_noreg', 'vcv1_noreg']`. Path starts with `data/sim/decoupling/`.

---

### Task 7: Update processed_adhesion CSV files

The adhesion CSVs have a `sim_id` column referencing `sim43` and `sim45`.

- [ ] **Step 1: Update sim_id column in both adhesion CSVs**

```python
# run from repo root: uv run python /tmp/update_adhesion_csvs.py
import pandas as pd
from pathlib import Path

SIM_ID_MAP = {"sim43": "vcv1_vol_abm", "sim45": "vcv1_vol_pde"}

for csv_path in Path("data/sim/processed_adhesion").glob("*.csv"):
    df = pd.read_csv(csv_path)
    if "sim_id" in df.columns:
        df["sim_id"] = df["sim_id"].map(lambda s: SIM_ID_MAP.get(s, s))
        df.to_csv(csv_path, index=False)
        print(f"updated {csv_path.name}")
```

- [ ] **Step 2: Spot-check**

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/sim/processed_adhesion/het_contact_metrics.csv')
print('sim_id unique:', sorted(df.sim_id.unique()))
"
```
Expected: `['vcv1_vol_abm', 'vcv1_vol_pde']`.

---

### Task 8: Update paper_figures.ipynb (Figures 1 and 2)

**File:** `docs/tex_draft/paper_figures.ipynb`

**Changes needed:**

In the Figure 1 cells:
```python
# OLD
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_run_index.csv"
WT_SIM_ID = "sim61"

# NEW
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_run_index.csv"
WT_SIM_ID = "vcv1_noreg"
```

In the Figure 2 cells:
```python
# OLD
DECOUPLING_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_decoupling" / "sim_metrics_last.csv"
DECOUPLING_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_decoupling" / "sim_run_index.csv"
FIG2_SIM_ID = "sim61"

# NEW
DECOUPLING_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_decoupling" / "sim_metrics_last.csv"
DECOUPLING_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_decoupling" / "sim_run_index.csv"
FIG2_SIM_ID = "vcv1_noreg"
```

- [ ] **Step 1: Edit paper_figures.ipynb** — change the four strings listed above (two path variables and two sim_id constants). Edit the notebook JSON directly or open in Jupyter and change the cell sources.

- [ ] **Step 2: Verify figure 1 cell runs without error** — in a Jupyter session or via `jupyter nbconvert --to notebook --execute` (skip if the raw data pipeline is already validated by other tasks).

---

### Task 9: Update figure3_paper_figures.py

**File:** `docs/tex_draft/figure3_paper_figures.py`

- [ ] **Step 1: Update path constants and sim IDs**

Edit lines 32–33 and 28–29:

```python
# OLD
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_run_index.csv"
WT_SIM_ID = "sim61"
MUD_SIM_ID = "sim51"

# NEW
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_run_index.csv"
WT_SIM_ID = "vcv1_noreg"
MUD_SIM_ID = "vcv0_noreg"
```

- [ ] **Step 2: Update `confirm_sim51_configuration()`** (line 327)

```python
# OLD
config_path = REPO_ROOT / "data" / "sim" / "bioparams_div26_sweep" / MUD_CONDITION / MUD_SIM_ID / "2026-04-26-biosim51_mudmut_volume_none_detdiff.json"

# NEW — file name is unchanged (provenance record), only directory path changes
config_path = REPO_ROOT / "data" / "sim" / "sweep" / MUD_CONDITION / MUD_SIM_ID / "2026-04-26-biosim51_mudmut_volume_none_detdiff.json"
```

Note: The actual JSON file at that path is named with `biosim51` — that's the provenance timestamp name and is NOT renamed.

- [ ] **Step 3: Verify the script runs to completion**

```bash
uv run python docs/tex_draft/figure3_paper_figures.py
```

Expected: prints config dict, then saves three PDF/PNG pairs to `docs/tex_draft/figures/`.

---

### Task 10: Update figure4_paper_figures.ipynb

**File:** `docs/tex_draft/figure4_paper_figures.ipynb`

- [ ] **Step 1: Update path constants**

```python
# OLD
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_run_index.csv"

# NEW
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_run_index.csv"
```

- [ ] **Step 2: Update SIM_MAP**

```python
# OLD
SIM_MAP: list[tuple[str, int, str]] = [
    ("sim41", 1, "NONE"),
    ("sim42", 1, "NB-ABM"),
    ("sim43", 1, "VOL-ABM"),
    ("sim44", 1, "NB-PDE"),
    ("sim45", 1, "VOL-PDE"),
    ("sim51", 0, "NONE"),
    ("sim52", 0, "NB-ABM"),
    ("sim53", 0, "VOL-ABM"),
    ("sim54", 0, "NB-PDE"),
    ("sim55", 0, "VOL-PDE"),
]

# NEW
SIM_MAP: list[tuple[str, int, str]] = [
    ("vcv1_noreg",   1, "NONE"),
    ("vcv1_nb_abm",  1, "NB-ABM"),
    ("vcv1_vol_abm", 1, "VOL-ABM"),
    ("vcv1_nb_pde",  1, "NB-PDE"),
    ("vcv1_vol_pde", 1, "VOL-PDE"),
    ("vcv0_noreg",   0, "NONE"),
    ("vcv0_nb_abm",  0, "NB-ABM"),
    ("vcv0_vol_abm", 0, "VOL-ABM"),
    ("vcv0_nb_pde",  0, "NB-PDE"),
    ("vcv0_vol_pde", 0, "VOL-PDE"),
]
```

- [ ] **Step 3: Verify the constants cell and data-loading cell run without error.**

---

### Task 11: Update figure5_paper_figures.ipynb

**File:** `docs/tex_draft/figure5_paper_figures.ipynb`

- [ ] **Step 1: Update path constants**

```python
# OLD
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_div26" / "sim_run_index.csv"
HET_METRICS_CSV  = REPO_ROOT / "data" / "sim" / "processed_adhesion" / "het_contact_metrics.csv"
EXP_METRICS_CSV  = REPO_ROOT / "data" / "sim" / "processed_adhesion" / "nb_exposure_metrics.csv"

# NEW
SIM_METRICS_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_metrics_last.csv"
SIM_RUN_INDEX_CSV = REPO_ROOT / "data" / "sim" / "processed_sweep" / "sim_run_index.csv"
HET_METRICS_CSV  = REPO_ROOT / "data" / "sim" / "processed_adhesion" / "het_contact_metrics.csv"
EXP_METRICS_CSV  = REPO_ROOT / "data" / "sim" / "processed_adhesion" / "nb_exposure_metrics.csv"
```

- [ ] **Step 2: Update SIM_MAP**

```python
# OLD
SIM_MAP: list[tuple[str, str, str]] = [
    ("sim43", "VOL-ABM", "volume (ABM)"),
    ("sim45", "VOL-PDE", "volume (PDE)"),
]

# NEW
SIM_MAP: list[tuple[str, str, str]] = [
    ("vcv1_vol_abm", "VOL-ABM", "volume (ABM)"),
    ("vcv1_vol_pde", "VOL-PDE", "volume (PDE)"),
]
```

- [ ] **Step 3: Verify the constants and data-loading cells run without error.**

---

### Task 12: Update Makefile

**File:** `Makefile`

- [ ] **Step 1: Update directory variables**

```makefile
# OLD
EXP_WRL_DIR    := data/exp/wrl_files
SIM_SWEEP_ROOT := data/sim/wt_plane_rotation_decoupling
SIM_PROC_DIR   := data/sim/processed_decoupling

# NEW
EXP_WRL_DIR    := data/exp/raw
SIM_SWEEP_ROOT := data/sim/decoupling
SIM_PROC_DIR   := data/sim/processed_decoupling
```

Note: `SIM_PROC_DIR` and the exp processed dir are unchanged. Only `EXP_WRL_DIR` and `SIM_SWEEP_ROOT` change.

- [ ] **Step 2: Verify**

```bash
make --dry-run preprocess-exp 2>&1 | head -10
```

Expected: shows command with `data/exp/raw` and `data/exp/processed` paths.

---

### Task 13: Update analysis notebooks

These are exploratory notebooks in `notebooks/` — not manuscript figure generators — but they reference old paths and will break silently after the rename.

- [ ] **Step 1: Update `notebooks/div26_systematic_analysis.ipynb`**

Find these lines (early data-loading cell):
```python
# OLD
SIM_METRICS_PATH = REPO_ROOT / 'data/sim/processed_div26/sim_metrics_last.csv'
SIM_RUN_IDX_PATH = REPO_ROOT / 'data/sim/processed_div26/sim_run_index.csv'

# NEW
SIM_METRICS_PATH = REPO_ROOT / 'data/sim/processed_sweep/sim_metrics_last.csv'
SIM_RUN_IDX_PATH = REPO_ROOT / 'data/sim/processed_sweep/sim_run_index.csv'
```

- [ ] **Step 2: Update `notebooks/adhesion_comparison.ipynb`**

```python
# OLD
SWEEP_ROOT = REPO_ROOT / 'data/sim/bioparams_div26_sweep'
PROC_DIR   = REPO_ROOT / 'data/sim/processed_div26'

# NEW
SWEEP_ROOT = REPO_ROOT / 'data/sim/sweep'
PROC_DIR   = REPO_ROOT / 'data/sim/processed_sweep'
```

Also update any literal `sim43`/`sim45` sim_id references in that notebook to `vcv1_vol_abm`/`vcv1_vol_pde`.

- [ ] **Step 3: Update `notebooks/decoupling_analysis.ipynb`**

```python
# OLD
SWEEP_ROOT = REPO_ROOT / 'data/sim/wt_plane_rotation_decoupling'
PROC_DIR   = REPO_ROOT / 'data/sim/processed_decoupling'

# NEW
SWEEP_ROOT = REPO_ROOT / 'data/sim/decoupling'
PROC_DIR   = REPO_ROOT / 'data/sim/processed_decoupling'
```

Also update any literal `sim61` sim_id references to `vcv1_noreg` and `sim71` to `vcv0_noreg`.

- [ ] **Step 4: Check remaining notebooks for old paths**

```bash
grep -rn "bioparams_div26_sweep\|processed_div26\|wt_plane_rotation_decoupling\|wrl_files\|sim41\|sim51\|sim61" notebooks/
```

Expected: no remaining hits after the edits above.

---

### Task 14: Update PIPELINE.md

**File:** `docs/PIPELINE.md`

- [ ] **Step 1: Update all directory path references**

Update any occurrences of:
- `bioparams_div26_sweep` → `sweep`
- `wt_plane_rotation_decoupling` → `decoupling`
- `processed_div26` → `processed_sweep`
- `wrl_files` → `raw` (and `Control` → `wt`, `Mud` → `mudmut`)
- `sim41`/`sim51`/`sim61` → their new names per the mapping table above

- [ ] **Step 2: Verify no stale path references remain**

```bash
grep -n "bioparams_div26_sweep\|wt_plane_rotation_decoupling\|processed_div26\|wrl_files" docs/PIPELINE.md
```

Expected: no output.

---

### Task 15: End-to-end smoke test

- [ ] **Step 1: Confirm all figure data paths resolve**

```bash
uv run python - <<'EOF'
from pathlib import Path
REPO = Path(".")

paths = [
    "data/sim/processed_sweep/sim_metrics_last.csv",
    "data/sim/processed_sweep/sim_run_index.csv",
    "data/sim/processed_decoupling/sim_metrics_last.csv",
    "data/sim/processed_decoupling/sim_run_index.csv",
    "data/sim/processed_adhesion/het_contact_metrics.csv",
    "data/sim/processed_adhesion/nb_exposure_metrics.csv",
    "data/exp/processed/exp_summary.csv",
    "data/exp/processed/lineage_index.csv",
    "data/exp/processed/analysis/wt.npz",
    "data/exp/processed/analysis/mudmut.npz",
]
for p in paths:
    full = REPO / p
    status = "OK" if full.exists() else "MISSING"
    print(f"{status}  {p}")
EOF
```
Expected: all `OK`.

- [ ] **Step 2: Confirm run_index paths point to real files (sample check)**

```bash
uv run python - <<'EOF'
import pandas as pd
from pathlib import Path
df = pd.read_csv("data/sim/processed_sweep/sim_run_index.csv")
sample = df.sample(10, random_state=42)
for _, row in sample.iterrows():
    for col in ["cells_path", "locs_path"]:
        p = Path(row[col])
        status = "OK" if p.exists() else "MISSING"
        print(f"{status}  {row['condition']}  {row['sim_id']}  {col}")
EOF
```
Expected: all `OK`.

- [ ] **Step 3: Run figure3 as an integration test**

```bash
uv run python docs/tex_draft/figure3_paper_figures.py
```
Expected: config dict printed, three figure pairs saved.

---

## Summary of What Gets Archived

| Archived path | Original path | Reason |
|---|---|---|
| `archive/exp/nanobody_raw/` | `exp/wrl_files/Nanobody/` | Not in manuscript or supplement |
| `archive/exp/nanobody_processed/` | `exp/processed/analysis/nanobody.npz`, `meshes/nanobody/`, `meshes/rejected/` | Not in manuscript or supplement |
| `archive/sim/sweep_unused_conditions/` (28 dirs) | `bioparams_div26_sweep/<other conditions>/` | Not used in any manuscript or supplement figure |
| `archive/sim/mudmut_noadhesion_extra_sims/` (8 sims) | `noadhesion/sim41,42,44,51–55/` | Only sim43 (vcv1_vol_abm) and sim45 (vcv1_vol_pde) used (Fig 5) |

**Kept (not archived):**
- All 10 WT sims in `bioparams_div26_sweep/wt_divMean0Stdev26/` (sim61–65, sim71–75) — supplement will include WT VCV=0 panels
- Both sim61 and sim71 in all 12 `wt_plane_rotation_decoupling/` conditions — supplement will include VCV=0 decoupling results
