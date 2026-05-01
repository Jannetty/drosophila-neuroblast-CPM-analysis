# Setup File Refactor — Manuscript-Focused Cleanup

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Archive unused ARCADE simulation setup files, rename remaining setup files from opaque numbered identifiers (sim41.xml, sim61.xml) to manuscript-role names (vcv1_noreg.xml, vcv1_vol_abm.xml), and produce a directory structure that mirrors the data refactor in plan 9_DATA_REFACTOR.md so setup files and output data remain obviously paired.

**Architecture:** Four stages — (1) consolidate calibration setup files into a top-level `calibration/` directory; (2) archive unused sweep setup files; (3) create the new `sweep/` and `decoupling/` directory structure with renamed files; (4) update the shell scripts used to run the kept simulations. The archive step runs first. Later tasks assume each prior task is complete. All work is in `~/bagherilab/ARCADE/`.

**Tech Stack:** Shell (mv, cp, find), Python (for batch XML series-name update — optional). No new source code produced.

---

## Background

### Correspondence between ARCADE setup files and neurogen data

Setup files in ARCADE generate the raw JSON output files consumed by the neurogen-plane-rotation-analysis pipeline. The directory naming scheme is identical between repos but prefixed differently:

| ARCADE setup dir | neurogen data dir |
|---|---|
| `bioparams_setupfiles_<condition>/sim41/sim41.xml` | `bioparams_div26_sweep/<condition>/sim41/*.CELLS.json` |
| `setupfiles_wt_plane_rotation_decoupling/<cond>/sim61/sim61.xml` | `wt_plane_rotation_decoupling/<cond>/sim61/*.CELLS.json` |

After plan 9_DATA_REFACTOR.md is executed, the neurogen data layout will be:

```
data/sim/
├── sweep/<condition>/vcv1_noreg/   ← was bioparams_div26_sweep/<condition>/sim41/
├── sweep/<condition>/vcv1_vol_abm/ ← was bioparams_div26_sweep/<condition>/sim43/
├── decoupling/<condition>/vcv1_noreg/ ← was wt_plane_rotation_decoupling/<condition>/sim61/
└── ...
```

This plan produces a matching ARCADE layout:

```
~/bagherilab/ARCADE/
├── sweep/<condition>/vcv1_noreg/vcv1_noreg.xml
├── sweep/<condition>/vcv1_vol_abm/vcv1_vol_abm.xml
├── decoupling/<condition>/vcv1_noreg/vcv1_noreg.xml
└── ...
```

### What lives in ARCADE today

```
ARCADE/
├── calibration_wt_nb_growth_rate/             ← KEEP (consolidate into calibration/)
│   └── cal{01-05}/cal{01-05}.xml           (5 files)
├── calibration_wt_offset50_divMean0Stdev26/   ← KEEP (consolidate into calibration/)
│   └── sim{01-08}/sim{01-08}.xml           (8 files)
├── calibration_wt_offset50_v2_divMean0Stdev26/ ← KEEP (consolidate into calibration/)
│   └── sim{01-05}/sim{01-05}.xml           (5 files)
├── calibration_wt_offset50_v3_divMean0Stdev26/ ← KEEP (consolidate into calibration/)
│   └── sim{01-04}/sim{01-04}.xml           (4 files)
├── bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30/  ← KEEP
│   └── sim{41-45,51-55}/sim{41-45,51-55}.xml
├── bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/  ← KEEP (sim43, sim45 only)
│   └── sim{41-45,51-55}/sim{41-45,51-55}.xml
├── bioparams_setupfiles_wt_divMean0Stdev26/  ← KEEP (all 10 sims)
│   └── sim{61-65,71-75}/sim{61-65,71-75}.xml
├── bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev0/   ← ARCHIVE
│   (and 27 more unused bioparams_setupfiles_* dirs)
└── setupfiles_wt_plane_rotation_decoupling/  ← KEEP (rename to decoupling/)
    └── {12 conditions}/{sim61,sim71}/{sim61,sim71}.xml
```

### Sim-ID to new-name mapping (identical to plan 9)

**mudmut sweep (sim41–55) and WT sweep (sim61–75):**

| Old sim dir | New dir name | Role |
|---|---|---|
| `sim41` / `sim61` | `vcv1_noreg` | VCV=1, no regulation |
| `sim42` / `sim62` | `vcv1_nb_abm` | VCV=1, NB-contact (ABM) |
| `sim43` / `sim63` | `vcv1_vol_abm` | VCV=1, volume-based (ABM) |
| `sim44` / `sim64` | `vcv1_nb_pde` | VCV=1, NB-contact (PDE) |
| `sim45` / `sim65` | `vcv1_vol_pde` | VCV=1, volume-based (PDE) |
| `sim51` / `sim71` | `vcv0_noreg` | VCV=0, no regulation |
| `sim52` / `sim72` | `vcv0_nb_abm` | VCV=0, NB-contact (ABM) |
| `sim53` / `sim73` | `vcv0_vol_abm` | VCV=0, volume-based (ABM) |
| `sim54` / `sim74` | `vcv0_nb_pde` | VCV=0, NB-contact (PDE) |
| `sim55` / `sim75` | `vcv0_vol_pde` | VCV=0, volume-based (PDE) |

**decoupling sweep (sim61/sim71 within each of 12 conditions):**

| Old sim dir | New dir name |
|---|---|
| `sim61` | `vcv1_noreg` |
| `sim71` | `vcv0_noreg` |

---

## Proposed New Layout

```
~/bagherilab/ARCADE/
├── calibration/                               ← consolidated from 4 root-level calibration_* dirs
│   ├── calibration_wt_nb_growth_rate/
│   ├── calibration_wt_offset50_divMean0Stdev26/
│   ├── calibration_wt_offset50_v2_divMean0Stdev26/
│   └── calibration_wt_offset50_v3_divMean0Stdev26/
├── setup_file_archive/
│   ├── sweep_unused_conditions/              ← 28 bioparams_setupfiles_* dirs
│   └── mudmut_noadhesion_extra_sims/         ← sim41,42,44,51-55 from noadhesion dir
│
├── sweep/
│   ├── wt_divMean0Stdev26/
│   │   ├── vcv1_noreg/vcv1_noreg.xml         ← was sim61/sim61.xml
│   │   ├── vcv1_nb_abm/vcv1_nb_abm.xml       ← was sim62/sim62.xml
│   │   ├── vcv1_vol_abm/vcv1_vol_abm.xml     ← was sim63/sim63.xml
│   │   ├── vcv1_nb_pde/vcv1_nb_pde.xml       ← was sim64/sim64.xml
│   │   ├── vcv1_vol_pde/vcv1_vol_pde.xml     ← was sim65/sim65.xml
│   │   ├── vcv0_noreg/vcv0_noreg.xml         ← was sim71/sim71.xml
│   │   ├── vcv0_nb_abm/vcv0_nb_abm.xml       ← was sim72/sim72.xml
│   │   ├── vcv0_vol_abm/vcv0_vol_abm.xml     ← was sim73/sim73.xml
│   │   ├── vcv0_nb_pde/vcv0_nb_pde.xml       ← was sim74/sim74.xml
│   │   └── vcv0_vol_pde/vcv0_vol_pde.xml     ← was sim75/sim75.xml
│   ├── mudmut_divMean0Stdev26_rotMean0Stdev30/
│   │   ├── vcv1_noreg/vcv1_noreg.xml         ← was sim41/sim41.xml
│   │   ├── vcv1_nb_abm/vcv1_nb_abm.xml       ← was sim42/sim42.xml
│   │   ├── vcv1_vol_abm/vcv1_vol_abm.xml     ← was sim43/sim43.xml
│   │   ├── vcv1_nb_pde/vcv1_nb_pde.xml       ← was sim44/sim44.xml
│   │   ├── vcv1_vol_pde/vcv1_vol_pde.xml     ← was sim45/sim45.xml
│   │   ├── vcv0_noreg/vcv0_noreg.xml         ← was sim51/sim51.xml
│   │   ├── vcv0_nb_abm/vcv0_nb_abm.xml       ← was sim52/sim52.xml
│   │   ├── vcv0_vol_abm/vcv0_vol_abm.xml     ← was sim53/sim53.xml
│   │   ├── vcv0_nb_pde/vcv0_nb_pde.xml       ← was sim54/sim54.xml
│   │   └── vcv0_vol_pde/vcv0_vol_pde.xml     ← was sim55/sim55.xml
│   └── mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/
│       ├── vcv1_vol_abm/vcv1_vol_abm.xml     ← was sim43/sim43.xml
│       └── vcv1_vol_pde/vcv1_vol_pde.xml     ← was sim45/sim45.xml
│
└── decoupling/
    ├── wt_divMean0Stdev26/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev26_relrot/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean45Stdev26_relrot/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean90Stdev26_relrot/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev35/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev45/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev60/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev75/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev90/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev26_yoffset50/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    ├── wt_divMean0Stdev26_yoffset62/
    │   ├── vcv1_noreg/vcv1_noreg.xml
    │   └── vcv0_noreg/vcv0_noreg.xml
    └── wt_divMean0Stdev26_yoffset75/
        ├── vcv1_noreg/vcv1_noreg.xml
        └── vcv0_noreg/vcv0_noreg.xml
```

**Why condition directory names are kept:** Condition names like `mudmut_divMean0Stdev26_rotMean0Stdev30` appear as column values in the neurogen processed CSVs and as string constants in figure scripts. Renaming them would require changes across both repos. The sim-ID subdirectories are the cheap rename — they affect only the path-string metadata, which plan 9 already handles.

---

## Files Modified

| File | Change |
|---|---|
| `run_wt_plane_rotation_decoupling.sh` | Update path from `setupfiles_wt_plane_rotation_decoupling/` to `decoupling/` |
| `run_bioparams_div26_sweep.sh` | Update path from `bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30/sim{41-55}/` to `sweep/mudmut_.../vcv*/` |
| `run_bioparams_div26_sweep_noadhesion.sh` | Update path to `sweep/mudmut_..._noadhesion/vcv1_vol_abm/` and `vcv1_vol_pde/` |
| `run_bioparams_div26_sweep_vbcv1.sh` | Update paths to new sweep/ structure |

Shell scripts for non-manuscript conditions (`run_bioparams_rotation_sweep.sh`, `run_calibration_wt_offset50.sh`, etc.) reference directories that are being archived — they become obsolete and do not need updating.

---

## Tasks

### Task 1: Consolidate calibration setup files

The four `calibration_*` directories at the ARCADE root are kept (not archived) because their outputs may be needed for supplement figures. Move them under a single top-level `calibration/` directory for tidiness.

- [ ] **Step 1: Create calibration directory**

```bash
cd ~/bagherilab/ARCADE
mkdir -p calibration
```

- [ ] **Step 2: Move calibration directories**

```bash
mv calibration_wt_nb_growth_rate              calibration/
mv calibration_wt_offset50_divMean0Stdev26    calibration/
mv calibration_wt_offset50_v2_divMean0Stdev26 calibration/
mv calibration_wt_offset50_v3_divMean0Stdev26 calibration/
```

- [ ] **Step 3: Verify**

```bash
ls calibration/
```

Expected:
```
calibration_wt_nb_growth_rate
calibration_wt_offset50_divMean0Stdev26
calibration_wt_offset50_v2_divMean0Stdev26
calibration_wt_offset50_v3_divMean0Stdev26
```

```bash
ls calibration_* 2>/dev/null && echo "ERROR: stale dirs remain at root" || echo "OK"
```

Expected: `OK`

---

### Task 2: Archive unused bioparams sweep setup files (28 directories)

The three manuscript conditions are:
- `bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30`
- `bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion`
- `bioparams_setupfiles_wt_divMean0Stdev26`

Everything else goes to `setup_file_archive/sweep_unused_conditions/`.

- [ ] **Step 1: Create archive directory**

```bash
mkdir -p setup_file_archive/sweep_unused_conditions
```

- [ ] **Step 2: Move unused directories (28 total)**

```bash
KEEP="bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30
bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion
bioparams_setupfiles_wt_divMean0Stdev26"

for d in bioparams_setupfiles_*/; do
    d="${d%/}"
    skip=0
    for k in $KEEP; do [ "$d" = "$k" ] && skip=1 && break; done
    [ $skip -eq 0 ] && mv "$d" setup_file_archive/sweep_unused_conditions/
done
```

- [ ] **Step 3: Verify 28 directories were archived**

```bash
ls setup_file_archive/sweep_unused_conditions/ | wc -l
```

Expected: `28`

- [ ] **Step 4: Verify the 3 kept directories still exist**

```bash
for d in \
  bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30 \
  bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion \
  bioparams_setupfiles_wt_divMean0Stdev26; do
    [ -d "$d" ] && echo "OK  $d" || echo "MISSING  $d"
done
```

Expected: all three print `OK`.

---

### Task 3: Archive extra noadhesion setup files (keep only sim43, sim45)

For the noadhesion condition only `sim43` (vcv1_vol_abm) and `sim45` (vcv1_vol_pde) are used in Fig 5. The other 8 sim dirs in that directory go to archive.

- [ ] **Step 1: Create archive directory**

```bash
mkdir -p setup_file_archive/mudmut_noadhesion_extra_sims
```

- [ ] **Step 2: Move extra noadhesion sim directories**

```bash
NOADH=bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion
for s in sim41 sim42 sim44 sim51 sim52 sim53 sim54 sim55; do
    [ -d "$NOADH/$s" ] && mv "$NOADH/$s" setup_file_archive/mudmut_noadhesion_extra_sims/
done
```

- [ ] **Step 3: Verify only sim43 and sim45 remain**

```bash
ls bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/
```

Expected:
```
sim43
sim45
```

---

### Task 4: Create sweep/ directory and rename sweep setup files

Move and rename all kept bioparams setup files into the new `sweep/` directory, renaming sim directories and XML files to match the neurogen data naming.

- [ ] **Step 1: Create target directory structure**

```bash
mkdir -p sweep/wt_divMean0Stdev26
mkdir -p sweep/mudmut_divMean0Stdev26_rotMean0Stdev30
mkdir -p sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion
```

- [ ] **Step 2: Move and rename WT sweep sim directories (all 10 sims)**

```bash
SRC=bioparams_setupfiles_wt_divMean0Stdev26
DST=sweep/wt_divMean0Stdev26

mv "$SRC/sim61" "$DST/vcv1_noreg"  && mv "$DST/vcv1_noreg/sim61.xml" "$DST/vcv1_noreg/vcv1_noreg.xml"
mv "$SRC/sim62" "$DST/vcv1_nb_abm" && mv "$DST/vcv1_nb_abm/sim62.xml" "$DST/vcv1_nb_abm/vcv1_nb_abm.xml"
mv "$SRC/sim63" "$DST/vcv1_vol_abm"&& mv "$DST/vcv1_vol_abm/sim63.xml" "$DST/vcv1_vol_abm/vcv1_vol_abm.xml"
mv "$SRC/sim64" "$DST/vcv1_nb_pde" && mv "$DST/vcv1_nb_pde/sim64.xml" "$DST/vcv1_nb_pde/vcv1_nb_pde.xml"
mv "$SRC/sim65" "$DST/vcv1_vol_pde"&& mv "$DST/vcv1_vol_pde/sim65.xml" "$DST/vcv1_vol_pde/vcv1_vol_pde.xml"
mv "$SRC/sim71" "$DST/vcv0_noreg"  && mv "$DST/vcv0_noreg/sim71.xml" "$DST/vcv0_noreg/vcv0_noreg.xml"
mv "$SRC/sim72" "$DST/vcv0_nb_abm" && mv "$DST/vcv0_nb_abm/sim72.xml" "$DST/vcv0_nb_abm/vcv0_nb_abm.xml"
mv "$SRC/sim73" "$DST/vcv0_vol_abm"&& mv "$DST/vcv0_vol_abm/sim73.xml" "$DST/vcv0_vol_abm/vcv0_vol_abm.xml"
mv "$SRC/sim74" "$DST/vcv0_nb_pde" && mv "$DST/vcv0_nb_pde/sim74.xml" "$DST/vcv0_nb_pde/vcv0_nb_pde.xml"
mv "$SRC/sim75" "$DST/vcv0_vol_pde"&& mv "$DST/vcv0_vol_pde/sim75.xml" "$DST/vcv0_vol_pde/vcv0_vol_pde.xml"
rmdir "$SRC"
```

- [ ] **Step 3: Move and rename mudmut sweep sim directories (all 10 sims)**

```bash
SRC=bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30
DST=sweep/mudmut_divMean0Stdev26_rotMean0Stdev30

mv "$SRC/sim41" "$DST/vcv1_noreg"  && mv "$DST/vcv1_noreg/sim41.xml" "$DST/vcv1_noreg/vcv1_noreg.xml"
mv "$SRC/sim42" "$DST/vcv1_nb_abm" && mv "$DST/vcv1_nb_abm/sim42.xml" "$DST/vcv1_nb_abm/vcv1_nb_abm.xml"
mv "$SRC/sim43" "$DST/vcv1_vol_abm"&& mv "$DST/vcv1_vol_abm/sim43.xml" "$DST/vcv1_vol_abm/vcv1_vol_abm.xml"
mv "$SRC/sim44" "$DST/vcv1_nb_pde" && mv "$DST/vcv1_nb_pde/sim44.xml" "$DST/vcv1_nb_pde/vcv1_nb_pde.xml"
mv "$SRC/sim45" "$DST/vcv1_vol_pde"&& mv "$DST/vcv1_vol_pde/sim45.xml" "$DST/vcv1_vol_pde/vcv1_vol_pde.xml"
mv "$SRC/sim51" "$DST/vcv0_noreg"  && mv "$DST/vcv0_noreg/sim51.xml" "$DST/vcv0_noreg/vcv0_noreg.xml"
mv "$SRC/sim52" "$DST/vcv0_nb_abm" && mv "$DST/vcv0_nb_abm/sim52.xml" "$DST/vcv0_nb_abm/vcv0_nb_abm.xml"
mv "$SRC/sim53" "$DST/vcv0_vol_abm"&& mv "$DST/vcv0_vol_abm/sim53.xml" "$DST/vcv0_vol_abm/vcv0_vol_abm.xml"
mv "$SRC/sim54" "$DST/vcv0_nb_pde" && mv "$DST/vcv0_nb_pde/sim54.xml" "$DST/vcv0_nb_pde/vcv0_nb_pde.xml"
mv "$SRC/sim55" "$DST/vcv0_vol_pde"&& mv "$DST/vcv0_vol_pde/sim55.xml" "$DST/vcv0_vol_pde/vcv0_vol_pde.xml"
rmdir "$SRC"
```

- [ ] **Step 4: Move and rename mudmut noadhesion sim directories (sim43, sim45 only)**

```bash
SRC=bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion
DST=sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion

mv "$SRC/sim43" "$DST/vcv1_vol_abm" && mv "$DST/vcv1_vol_abm/sim43.xml" "$DST/vcv1_vol_abm/vcv1_vol_abm.xml"
mv "$SRC/sim45" "$DST/vcv1_vol_pde" && mv "$DST/vcv1_vol_pde/sim45.xml" "$DST/vcv1_vol_pde/vcv1_vol_pde.xml"
rmdir "$SRC"
```

- [ ] **Step 5: Verify sweep/ structure**

```bash
find sweep -type f -name "*.xml" | sort
```

Expected (22 files):
```
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv0_nb_abm/vcv0_nb_abm.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv0_nb_pde/vcv0_nb_pde.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv0_noreg/vcv0_noreg.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv0_vol_abm/vcv0_vol_abm.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv0_vol_pde/vcv0_vol_pde.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_nb_abm/vcv1_nb_abm.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_nb_pde/vcv1_nb_pde.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_noreg/vcv1_noreg.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_vol_abm/vcv1_vol_abm.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_vol_pde/vcv1_vol_pde.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/vcv1_vol_abm/vcv1_vol_abm.xml
sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/vcv1_vol_pde/vcv1_vol_pde.xml
sweep/wt_divMean0Stdev26/vcv0_nb_abm/vcv0_nb_abm.xml
sweep/wt_divMean0Stdev26/vcv0_nb_pde/vcv0_nb_pde.xml
sweep/wt_divMean0Stdev26/vcv0_noreg/vcv0_noreg.xml
sweep/wt_divMean0Stdev26/vcv0_vol_abm/vcv0_vol_abm.xml
sweep/wt_divMean0Stdev26/vcv0_vol_pde/vcv0_vol_pde.xml
sweep/wt_divMean0Stdev26/vcv1_nb_abm/vcv1_nb_abm.xml
sweep/wt_divMean0Stdev26/vcv1_nb_pde/vcv1_nb_pde.xml
sweep/wt_divMean0Stdev26/vcv1_noreg/vcv1_noreg.xml
sweep/wt_divMean0Stdev26/vcv1_vol_abm/vcv1_vol_abm.xml
sweep/wt_divMean0Stdev26/vcv1_vol_pde/vcv1_vol_pde.xml
```

```bash
find sweep -type f -name "*.xml" | wc -l
```

Expected: `22`

---

### Task 5: Create decoupling/ directory and rename decoupling setup files

- [ ] **Step 1: Create all 12 condition subdirectories in decoupling/**

```bash
for cond in \
  wt_divMean0Stdev26 \
  wt_divMean0Stdev26_relrot \
  wt_divMean45Stdev26_relrot \
  wt_divMean90Stdev26_relrot \
  wt_divMean0Stdev35 \
  wt_divMean0Stdev45 \
  wt_divMean0Stdev60 \
  wt_divMean0Stdev75 \
  wt_divMean0Stdev90 \
  wt_divMean0Stdev26_yoffset50 \
  wt_divMean0Stdev26_yoffset62 \
  wt_divMean0Stdev26_yoffset75; do
    mkdir -p "decoupling/$cond"
done
```

- [ ] **Step 2: Move and rename sim61/sim71 in each condition**

```bash
SRC=setupfiles_wt_plane_rotation_decoupling

for cond in \
  wt_divMean0Stdev26 \
  wt_divMean0Stdev26_relrot \
  wt_divMean45Stdev26_relrot \
  wt_divMean90Stdev26_relrot \
  wt_divMean0Stdev35 \
  wt_divMean0Stdev45 \
  wt_divMean0Stdev60 \
  wt_divMean0Stdev75 \
  wt_divMean0Stdev90 \
  wt_divMean0Stdev26_yoffset50 \
  wt_divMean0Stdev26_yoffset62 \
  wt_divMean0Stdev26_yoffset75; do
    mv "$SRC/$cond/sim61" "decoupling/$cond/vcv1_noreg"
    mv "decoupling/$cond/vcv1_noreg/sim61.xml" "decoupling/$cond/vcv1_noreg/vcv1_noreg.xml"
    mv "$SRC/$cond/sim71" "decoupling/$cond/vcv0_noreg"
    mv "decoupling/$cond/vcv0_noreg/sim71.xml" "decoupling/$cond/vcv0_noreg/vcv0_noreg.xml"
    rmdir "$SRC/$cond"
done
rmdir "$SRC"
```

- [ ] **Step 3: Verify decoupling/ structure**

```bash
find decoupling -type f -name "*.xml" | sort
```

Expected (24 files — 12 conditions × 2 sims):
```
decoupling/wt_divMean0Stdev26/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev26/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev26_relrot/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev26_relrot/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev26_yoffset50/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev26_yoffset50/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev26_yoffset62/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev26_yoffset62/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev26_yoffset75/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev26_yoffset75/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev35/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev35/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev45/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev45/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev60/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev60/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev75/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev75/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean0Stdev90/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean0Stdev90/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean45Stdev26_relrot/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean45Stdev26_relrot/vcv1_noreg/vcv1_noreg.xml
decoupling/wt_divMean90Stdev26_relrot/vcv0_noreg/vcv0_noreg.xml
decoupling/wt_divMean90Stdev26_relrot/vcv1_noreg/vcv1_noreg.xml
```

```bash
find decoupling -type f -name "*.xml" | wc -l
```

Expected: `24`

---

### Task 6: Update XML series name attributes (optional but recommended)

Each XML file contains a `series name` attribute that combines the old sim ID with the regulatory description, e.g. `sim41_mudmut_volume_none_detdiff`. This attribute prefixes output file names when the simulation is re-run. Updating it ensures that any future re-runs produce files named consistently with the new scheme (`vcv1_noreg_mudmut_volume_none_detdiff`). Skip this task if you never plan to re-run these simulations from these setup files.

- [ ] **Step 1: Run the series-name update script**

```python
# Save as /tmp/update_series_names.py and run:
# cd ~/bagherilab/ARCADE && python /tmp/update_series_names.py

import re
from pathlib import Path

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

PATTERN = re.compile(r'(name=")(' + '|'.join(SIM_ID_MAP.keys()) + r')(_)')

for xml_path in Path(".").glob("sweep/**/*.xml"):
    text = xml_path.read_text()
    new_text = PATTERN.sub(lambda m: m.group(1) + SIM_ID_MAP[m.group(2)] + m.group(3), text)
    if new_text != text:
        xml_path.write_text(new_text)
        print(f"updated {xml_path}")

for xml_path in Path(".").glob("decoupling/**/*.xml"):
    text = xml_path.read_text()
    new_text = PATTERN.sub(lambda m: m.group(1) + SIM_ID_MAP[m.group(2)] + m.group(3), text)
    if new_text != text:
        xml_path.write_text(new_text)
        print(f"updated {xml_path}")
```

- [ ] **Step 2: Spot-check one file**

```bash
grep 'series name' sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_noreg/vcv1_noreg.xml
```

Expected: contains `vcv1_noreg_mudmut_volume_none_detdiff` (not `sim41_`).

```bash
grep 'series name' decoupling/wt_divMean0Stdev26/vcv1_noreg/vcv1_noreg.xml
```

Expected: contains `vcv1_noreg_wt_volume_none_detdiff` (not `sim61_`).

---

### Task 7: Update run scripts for kept conditions

The three run scripts that invoke kept simulations need their setup file paths updated. Scripts for archived conditions are now obsolete — leave them as-is.

- [ ] **Step 1: Identify path references in the relevant scripts**

```bash
grep -n "bioparams_setupfiles\|setupfiles_wt_plane_rotation" \
  run_bioparams_div26_sweep.sh \
  run_bioparams_div26_sweep_noadhesion.sh \
  run_bioparams_div26_sweep_vbcv1.sh \
  run_wt_plane_rotation_decoupling.sh 2>/dev/null
```

- [ ] **Step 2: Update `run_wt_plane_rotation_decoupling.sh`**

Replace all occurrences of `setupfiles_wt_plane_rotation_decoupling/` with `decoupling/`:

```bash
sed -i '' 's|setupfiles_wt_plane_rotation_decoupling/|decoupling/|g' \
  run_wt_plane_rotation_decoupling.sh
```

Also replace `sim61/sim61.xml` → `vcv1_noreg/vcv1_noreg.xml` and `sim71/sim71.xml` → `vcv0_noreg/vcv0_noreg.xml`:

```bash
sed -i '' \
  's|sim61/sim61\.xml|vcv1_noreg/vcv1_noreg.xml|g;
   s|sim71/sim71\.xml|vcv0_noreg/vcv0_noreg.xml|g' \
  run_wt_plane_rotation_decoupling.sh
```

- [ ] **Step 3: Update `run_bioparams_div26_sweep.sh`**

Replace the directory prefix and each `simXX/simXX.xml` reference:

```bash
sed -i '' 's|bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30/|sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/|g' \
  run_bioparams_div26_sweep.sh
sed -i '' 's|bioparams_setupfiles_wt_divMean0Stdev26/|sweep/wt_divMean0Stdev26/|g' \
  run_bioparams_div26_sweep.sh

for old new in \
  "sim41/sim41.xml" "vcv1_noreg/vcv1_noreg.xml" \
  "sim42/sim42.xml" "vcv1_nb_abm/vcv1_nb_abm.xml" \
  "sim43/sim43.xml" "vcv1_vol_abm/vcv1_vol_abm.xml" \
  "sim44/sim44.xml" "vcv1_nb_pde/vcv1_nb_pde.xml" \
  "sim45/sim45.xml" "vcv1_vol_pde/vcv1_vol_pde.xml" \
  "sim51/sim51.xml" "vcv0_noreg/vcv0_noreg.xml" \
  "sim52/sim52.xml" "vcv0_nb_abm/vcv0_nb_abm.xml" \
  "sim53/sim53.xml" "vcv0_vol_abm/vcv0_vol_abm.xml" \
  "sim54/sim54.xml" "vcv0_nb_pde/vcv0_nb_pde.xml" \
  "sim55/sim55.xml" "vcv0_vol_pde/vcv0_vol_pde.xml" \
  "sim61/sim61.xml" "vcv1_noreg/vcv1_noreg.xml" \
  "sim71/sim71.xml" "vcv0_noreg/vcv0_noreg.xml"; do
    sed -i '' "s|$old|$new|g" run_bioparams_div26_sweep.sh
done
```

- [ ] **Step 4: Update `run_bioparams_div26_sweep_noadhesion.sh`**

```bash
sed -i '' \
  's|bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/|sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/|g;
   s|sim43/sim43\.xml|vcv1_vol_abm/vcv1_vol_abm.xml|g;
   s|sim45/sim45\.xml|vcv1_vol_pde/vcv1_vol_pde.xml|g' \
  run_bioparams_div26_sweep_noadhesion.sh
```

- [ ] **Step 5: Update `run_bioparams_div26_sweep_vbcv1.sh`**

```bash
sed -i '' \
  's|bioparams_setupfiles_mudmut_divMean0Stdev26_rotMean0Stdev30/|sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/|g;
   s|bioparams_setupfiles_wt_divMean0Stdev26/|sweep/wt_divMean0Stdev26/|g' \
  run_bioparams_div26_sweep_vbcv1.sh

for old new in \
  "sim41/sim41.xml" "vcv1_noreg/vcv1_noreg.xml" \
  "sim42/sim42.xml" "vcv1_nb_abm/vcv1_nb_abm.xml" \
  "sim43/sim43.xml" "vcv1_vol_abm/vcv1_vol_abm.xml" \
  "sim44/sim44.xml" "vcv1_nb_pde/vcv1_nb_pde.xml" \
  "sim45/sim45.xml" "vcv1_vol_pde/vcv1_vol_pde.xml" \
  "sim61/sim61.xml" "vcv1_noreg/vcv1_noreg.xml"; do
    sed -i '' "s|$old|$new|g" run_bioparams_div26_sweep_vbcv1.sh
done
```

- [ ] **Step 6: Verify no stale paths remain in updated scripts**

```bash
grep -n "bioparams_setupfiles\|setupfiles_wt_plane_rotation\|/sim[0-9][0-9]/sim[0-9][0-9]\.xml" \
  run_bioparams_div26_sweep.sh \
  run_bioparams_div26_sweep_noadhesion.sh \
  run_bioparams_div26_sweep_vbcv1.sh \
  run_wt_plane_rotation_decoupling.sh
```

Expected: no output.

---

### Task 8: Final verification

- [ ] **Step 1: Confirm no old setup directories remain at ARCADE root**

```bash
cd ~/bagherilab/ARCADE
ls -d bioparams_setupfiles_* setupfiles_* calibration_* 2>/dev/null && echo "ERROR: stale dirs" || echo "OK"
```

Expected: `OK`

- [ ] **Step 2: Confirm total XML file counts**

```bash
find sweep    -name "*.xml" | wc -l   # expected: 22
find decoupling -name "*.xml" | wc -l # expected: 24
find setup_file_archive -name "*.xml" | wc -l  # should be large (hundreds)
```

- [ ] **Step 3: Confirm 1-to-1 correspondence with neurogen data layout**

For each kept setup file in sweep/, there should be a corresponding data directory in the neurogen repo. Run from the neurogen repo root (adjust `ARCADE` path):

```bash
for xml in ~/bagherilab/ARCADE/sweep/**/**/*.xml; do
    # e.g. sweep/wt_divMean0Stdev26/vcv1_noreg/vcv1_noreg.xml
    rel="${xml#*/ARCADE/sweep/}"         # wt_divMean0Stdev26/vcv1_noreg/vcv1_noreg.xml
    cond=$(dirname "$rel" | cut -d/ -f1) # wt_divMean0Stdev26
    sim=$(dirname "$rel" | cut -d/ -f2)  # vcv1_noreg
    data_dir="data/sim/sweep/$cond/$sim"
    [ -d "$data_dir" ] && echo "OK  $data_dir" || echo "MISSING  $data_dir"
done
```

Expected: all `OK` (run this after plan 9_DATA_REFACTOR.md has also been executed).

---

## Summary of What Gets Archived

| Archived path (in ARCADE) | Original path | Reason |
|---|---|---|
| `setup_file_archive/sweep_unused_conditions/` (28 dirs) | `bioparams_setupfiles_*/` other conditions | Not used in manuscript or supplement |
| `setup_file_archive/mudmut_noadhesion_extra_sims/` (8 sim dirs) | `bioparams_setupfiles_*_noadhesion/sim41,42,44,51-55/` | Only vcv1_vol_abm and vcv1_vol_pde used in Fig 5 |

**Kept (22 sweep XML + 24 decoupling XML + 22 calibration XML = 68 files total):**
- `calibration/` — all four calibration studies consolidated from root (supplement figures)
- `sweep/wt_divMean0Stdev26/` — all 10 VCV configurations (main figures + WT VCV=0 supplement)
- `sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/` — all 10 VCV configurations (Figs 3, 4)
- `sweep/mudmut_divMean0Stdev26_rotMean0Stdev30_noadhesion/` — vcv1_vol_abm and vcv1_vol_pde only (Fig 5)
- `decoupling/` — all 12 conditions × 2 sims (Fig 2 + VCV=0 supplement)
