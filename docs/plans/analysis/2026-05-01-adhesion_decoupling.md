# Adhesion Decoupling Sweep — Plan

**Goal:** Generate and analyse a 3-factor ARCADE sweep that decouples differential NB-NB
adhesion, division-rotation spread (sigma), and relative-rotation mode for mudmut
VCV=1 VOL-ABM and VOL-PDE simulations. Primary outcome: do NBs end up spatially
clustered together at simulation endpoint?

**Architecture:** Four stages — (1) generate XML setup files in ARCADE; (2) run
simulations; (3) preprocess output and extend the metrics pipeline to include NB
connectivity; (4) analyse results in a new notebook. The analysis is an expansion of
the Figure 5 adhesion comparison.

---

## ARCADE adhesion model note

In ARCADE's CPM, the `:*` target in adhesion terms refers to the cell-medium
(extracellular space) interface, not cell-cell. The lines:

```xml
<potts.parameter term="adhesion" id="ADHESION" value="80" target="fly-stem-mudmut:*"/>
```

set the NB-medium adhesion energy to 80 (high cost for exposure to medium → cells
prefer to stay together with other cells). **Cell-cell adhesion** for any pair not
explicitly listed defaults to J=50 from ARCADE's built-in `potts.parameters.xml`.

The three levels in this sweep therefore are:
- **adh50** — no `fly-stem-mudmut:fly-stem-mudmut` line → default J=50 applies → no
  NB-NB preference over any other cell-cell pair
- **adh40** — explicit `value="40"` → NB-NB contact cheaper than default → NBs prefer
  each other over generic cell-cell contact
- **adh20** — explicit `value="20"` → stronger NB-NB preference

---

## Parameter space

Baseline (held fixed when not the varied factor): sigma=26, relrot=off,
`APICAL_AXIS_ROTATION_DISTRIBUTION` sigma=30.

| Factor | Levels |
|---|---|
| Adhesion J(NB,NB) | **adh50** (no diff — default applies), **adh40** (baseline), **adh20** (strong) |
| Div rotation sigma | 26, 45, 90 |
| Relative rotation | off, on mu=0, on mu=45, on mu=90 |
| Sim type | vcv1_vol_abm, vcv1_vol_pde |
| Runs | 50 per condition |

Total: 3 × 3 × 4 = **36 condition directories** × 2 sim types = **72 XML files**.
At 50 runs each: **3600 simulations**.

### What changes in each XML relative to the base mudmut vcv1_vol_abm template

**Adhesion:**

| Element | adh50 | adh40 | adh20 |
|---|---|---|---|
| `ADHESION fly-stem-mudmut:fly-stem-mudmut` | *(line absent — default J=50 applies)* | `value="40"` | `value="20"` |

**Div rotation sigma** (APICAL_AXIS_ROTATION_DISTRIBUTION sigma stays at 30):

| Element | sigma=26 | sigma=45 | sigma=90 |
|---|---|---|---|
| `DIV_ROTATION_DISTRIBUTION` | `NORMAL(MU=0,SIGMA=26)` | `NORMAL(MU=0,SIGMA=45)` | `NORMAL(MU=0,SIGMA=90)` |

**Relative rotation** (div sigma stays at 26):

| Element | off | on mu=0 | on mu=45 | on mu=90 |
|---|---|---|---|---|
| `DIV_ROTATION_IS_RELATIVE` | *(line absent)* | `value="1"` | `value="1"` | `value="1"` |
| `APICAL_AXIS_ROTATION_DISTRIBUTION` | `NORMAL(MU=0,SIGMA=30)` *(irrelevant)* | `NORMAL(MU=0,SIGMA=30)` | `NORMAL(MU=45,SIGMA=30)` | `NORMAL(MU=90,SIGMA=30)` |

For vol_pde vs vol_abm: only `PDELIKE` changes (0 → 1) and the `series name` attribute.

---

## Layout

### ARCADE setup files

```
~/bagherilab/ARCADE/decoupling_adhesion/
├── mudmut_adh50_divMean0Stdev26/
│   ├── vcv1_vol_abm/vcv1_vol_abm.xml
│   └── vcv1_vol_pde/vcv1_vol_pde.xml
├── mudmut_adh50_divMean0Stdev26_relrotMean0/
│   ├── vcv1_vol_abm/vcv1_vol_abm.xml
│   └── vcv1_vol_pde/vcv1_vol_pde.xml
├── mudmut_adh50_divMean0Stdev26_relrotMean45/
├── mudmut_adh50_divMean0Stdev26_relrotMean90/
├── mudmut_adh50_divMean0Stdev45/
...
└── mudmut_adh20_divMean0Stdev90_relrotMean90/
    ├── vcv1_vol_abm/vcv1_vol_abm.xml
    └── vcv1_vol_pde/vcv1_vol_pde.xml
```

### Neurogen data layout

```
data/sim/decoupling_adhesion/<condition>/<sim_id>/<run>*.{CELLS,LOCATIONS}.json
data/sim/processed_decoupling_adhesion/
├── sim_timepoint_metrics.csv
├── sim_run_index.csv
├── sim_metrics_last.csv
└── figures/
```

---

## Task 1 — Generate ARCADE setup files

Write and run a Python script that templates the 72 XML files from the existing
vcv1_vol_abm and vcv1_vol_pde XMLs.

**Script:** `/tmp/gen_adhesion_decoupling_xmls.py`

The base templates are:
- `~/bagherilab/ARCADE/sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_vol_abm/vcv1_vol_abm.xml`
- `~/bagherilab/ARCADE/sweep/mudmut_divMean0Stdev26_rotMean0Stdev30/vcv1_vol_pde/vcv1_vol_pde.xml`

Note: the base templates already contain an explicit `fly-stem-mudmut:fly-stem-mudmut`
line with `value="40"` (the adh40 case). The script removes it for adh50 and replaces
it for adh20. The templates also contain `APICAL_AXIS_ROTATION_DISTRIBUTION
NORMAL(MU=0,SIGMA=30)` — only the MU is modified for relrot mu=45/90.

```python
# /tmp/gen_adhesion_decoupling_xmls.py
# Run from anywhere: python3 /tmp/gen_adhesion_decoupling_xmls.py
import re
from pathlib import Path

ARCADE = Path.home() / "bagherilab" / "ARCADE"
OUT_ROOT = ARCADE / "decoupling_adhesion"

TEMPLATE_ABM = (ARCADE / "sweep" / "mudmut_divMean0Stdev26_rotMean0Stdev30"
                / "vcv1_vol_abm" / "vcv1_vol_abm.xml").read_text()
TEMPLATE_PDE = (ARCADE / "sweep" / "mudmut_divMean0Stdev26_rotMean0Stdev30"
                / "vcv1_vol_pde" / "vcv1_vol_pde.xml").read_text()

# adh50 = no NB-NB override (default J=50 from potts.parameters.xml)
# adh40 = baseline differential (existing template value)
# adh20 = strong differential
ADHESION_LEVELS = [50, 40, 20]
SIGMAS = [26, 45, 90]
# None = relative rotation off; int = relative rotation on with that MU
RELROT_MEANS = [None, 0, 45, 90]

ADH_OVERRIDE_PATTERN = re.compile(
    r'\s*<potts\.parameter term="adhesion" id="ADHESION" value="\d+"'
    r' target="fly-stem-mudmut:fly-stem-mudmut"/>\n'
)
ADH_OVERRIDE_TEMPLATE = (
    '            <potts.parameter term="adhesion" id="ADHESION" value="{adh}"'
    ' target="fly-stem-mudmut:fly-stem-mudmut"/>\n'
)
LAST_CELL_MEDIUM = re.compile(
    r'(<potts\.parameter term="adhesion" id="ADHESION" value="\d+"'
    r' target="fly-neuron:\*"/>)'
)

DIV_ROT_PATTERN = re.compile(
    r'(<population\.parameter id="proliferation/DIV_ROTATION_DISTRIBUTION"'
    r' value="NORMAL\(MU=0,SIGMA=)\d+(\)"/>)'
)

APICAL_ROT_PATTERN = re.compile(
    r'(id="proliferation/APICAL_AXIS_ROTATION_DISTRIBUTION"'
    r' value="NORMAL\(MU=)-?\d+(,SIGMA=\d+\)")'
)

DIV_ROTATION_IS_RELATIVE_LINE = (
    '                    <population.parameter'
    ' id="proliferation/DIV_ROTATION_IS_RELATIVE" value="1"/>\n'
)
RELROT_ANCHOR = re.compile(
    r'(<population\.parameter id="proliferation/APICAL_AXIS_RULESET")'
)


def apply_adhesion(xml: str, adh: int) -> str:
    xml = ADH_OVERRIDE_PATTERN.sub("", xml)
    if adh == 50:
        return xml  # no override — default J=50 from potts.parameters.xml applies
    return LAST_CELL_MEDIUM.sub(
        r'\1\n' + ADH_OVERRIDE_TEMPLATE.format(adh=adh), xml
    )


def apply_sigma(xml: str, sigma: int) -> str:
    return DIV_ROT_PATTERN.sub(r'\g<1>' + str(sigma) + r'\2', xml)


def apply_relrot(xml: str, relrot_mean: int | None) -> str:
    # Remove any existing DIV_ROTATION_IS_RELATIVE line
    xml = re.sub(
        r'\s*<population\.parameter id="proliferation/DIV_ROTATION_IS_RELATIVE"'
        r' value="\d+"/>\n',
        "\n", xml
    )
    if relrot_mean is None:
        return xml  # relative rotation off — APICAL_AXIS_ROTATION_DISTRIBUTION irrelevant
    # Enable relative rotation
    xml = RELROT_ANCHOR.sub(DIV_ROTATION_IS_RELATIVE_LINE + r'\1', xml)
    # Update the MU of APICAL_AXIS_ROTATION_DISTRIBUTION (sigma stays at 30)
    xml = APICAL_ROT_PATTERN.sub(rf'\g<1>{relrot_mean}\2', xml)
    return xml


def apply_series_name(xml: str, new_name: str) -> str:
    return re.sub(r'(name=")[^"]+(")', rf'\g<1>{new_name}\2', xml, count=1)


for adh in ADHESION_LEVELS:
    for sigma in SIGMAS:
        for relrot_mean in RELROT_MEANS:
            if relrot_mean is None:
                relrot_suffix = ""
                sigma_tag = f"sg{sigma}"
            else:
                relrot_suffix = f"_relrotMean{relrot_mean}"
                sigma_tag = f"sg{sigma}_relMu{relrot_mean}"

            cond_name = f"mudmut_adh{adh}_divMean0Stdev{sigma}{relrot_suffix}"

            for sim_type, template in [("vcv1_vol_abm", TEMPLATE_ABM),
                                        ("vcv1_vol_pde", TEMPLATE_PDE)]:
                series_name = f"{sim_type}_mudmut_adh{adh}_{sigma_tag}_detdiff"

                xml = template
                xml = apply_adhesion(xml, adh)
                xml = apply_sigma(xml, sigma)
                xml = apply_relrot(xml, relrot_mean)
                xml = apply_series_name(xml, series_name)

                out_dir = OUT_ROOT / cond_name / sim_type
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{sim_type}.xml"
                out_path.write_text(xml)
                print(f"wrote {out_path.relative_to(ARCADE)}")

print(f"\nTotal: {3 * 3 * 4 * 2} XML files across {3 * 3 * 4} conditions")
```

**Verify the script produces 72 files:**

```bash
find ~/bagherilab/ARCADE/decoupling_adhesion -name "*.xml" | wc -l
# expected: 72
```

**Spot-check four XMLs — one per relrot level at adh40, sigma=26:**

```bash
# relrot=off: no DIV_ROTATION_IS_RELATIVE line, MU irrelevant
grep "RELATIVE\|APICAL_AXIS_ROTATION_DISTRIBUTION\|series name" \
  ~/bagherilab/ARCADE/decoupling_adhesion/mudmut_adh40_divMean0Stdev26/vcv1_vol_abm/vcv1_vol_abm.xml
# expected: no RELATIVE line; series name: vcv1_vol_abm_mudmut_adh40_sg26_detdiff

# relrot=on mu=0: RELATIVE value="1", MU=0
grep "RELATIVE\|APICAL_AXIS_ROTATION_DISTRIBUTION\|series name" \
  ~/bagherilab/ARCADE/decoupling_adhesion/mudmut_adh40_divMean0Stdev26_relrotMean0/vcv1_vol_abm/vcv1_vol_abm.xml
# expected: RELATIVE value="1"; MU=0,SIGMA=30; series name: vcv1_vol_abm_mudmut_adh40_sg26_relMu0_detdiff

# relrot=on mu=45: RELATIVE value="1", MU=45
grep "RELATIVE\|APICAL_AXIS_ROTATION_DISTRIBUTION\|series name" \
  ~/bagherilab/ARCADE/decoupling_adhesion/mudmut_adh40_divMean0Stdev26_relrotMean45/vcv1_vol_abm/vcv1_vol_abm.xml
# expected: RELATIVE value="1"; MU=45,SIGMA=30

# relrot=on mu=90: RELATIVE value="1", MU=90
grep "RELATIVE\|APICAL_AXIS_ROTATION_DISTRIBUTION\|series name" \
  ~/bagherilab/ARCADE/decoupling_adhesion/mudmut_adh40_divMean0Stdev26_relrotMean90/vcv1_vol_abm/vcv1_vol_abm.xml
# expected: RELATIVE value="1"; MU=90,SIGMA=30
```

**Spot-check adhesion levels:**

```bash
# adh50: no NB-NB override, sigma=26
grep "fly-stem-mudmut:fly-stem-mudmut\|DIV_ROTATION_DISTRIBUTION\|series name" \
  ~/bagherilab/ARCADE/decoupling_adhesion/mudmut_adh50_divMean0Stdev26/vcv1_vol_abm/vcv1_vol_abm.xml
# expected: no fly-stem-mudmut:fly-stem-mudmut line; SIGMA=26

# adh20: override at 20, sigma=90, relrotMean90
grep "fly-stem-mudmut:fly-stem-mudmut\|DIV_ROTATION_DISTRIBUTION\|series name" \
  ~/bagherilab/ARCADE/decoupling_adhesion/mudmut_adh20_divMean0Stdev90_relrotMean90/vcv1_vol_abm/vcv1_vol_abm.xml
# expected: value="20"; SIGMA=90
```

**Confirm all 36 condition dirs exist with exactly 2 sim subdirs each:**

```bash
for cond in ~/bagherilab/ARCADE/decoupling_adhesion/*/; do
    n=$(ls "$cond" | wc -l)
    [[ $n -eq 2 ]] || echo "WRONG COUNT $n: $cond"
done
echo "check done"
```

---

## Task 2 — Create run script

Create `~/bagherilab/ARCADE/run_decoupling_adhesion.sh` modelled on
`run_wt_plane_rotation_decoupling.sh`.

Key differences from the decoupling script:
- `SETUP_ROOT="$SCRIPT_DIR/decoupling_adhesion"`
- `BASE_OUTPUT_DIR="$SCRIPT_DIR/output/decoupling_adhesion"`
- `CONDITION_DIRS` array lists all 36 condition names
- `find ... -name '*.xml'` glob (already correct in the decoupling script)

The 36 condition names are (copy-paste into the array):

```bash
CONDITION_DIRS=(
  # adh50 — no NB-NB differential (default J=50)
  "mudmut_adh50_divMean0Stdev26"            "mudmut_adh50_divMean0Stdev26_relrotMean0"
  "mudmut_adh50_divMean0Stdev26_relrotMean45"  "mudmut_adh50_divMean0Stdev26_relrotMean90"
  "mudmut_adh50_divMean0Stdev45"            "mudmut_adh50_divMean0Stdev45_relrotMean0"
  "mudmut_adh50_divMean0Stdev45_relrotMean45"  "mudmut_adh50_divMean0Stdev45_relrotMean90"
  "mudmut_adh50_divMean0Stdev90"            "mudmut_adh50_divMean0Stdev90_relrotMean0"
  "mudmut_adh50_divMean0Stdev90_relrotMean45"  "mudmut_adh50_divMean0Stdev90_relrotMean90"
  # adh40 — baseline differential
  "mudmut_adh40_divMean0Stdev26"            "mudmut_adh40_divMean0Stdev26_relrotMean0"
  "mudmut_adh40_divMean0Stdev26_relrotMean45"  "mudmut_adh40_divMean0Stdev26_relrotMean90"
  "mudmut_adh40_divMean0Stdev45"            "mudmut_adh40_divMean0Stdev45_relrotMean0"
  "mudmut_adh40_divMean0Stdev45_relrotMean45"  "mudmut_adh40_divMean0Stdev45_relrotMean90"
  "mudmut_adh40_divMean0Stdev90"            "mudmut_adh40_divMean0Stdev90_relrotMean0"
  "mudmut_adh40_divMean0Stdev90_relrotMean45"  "mudmut_adh40_divMean0Stdev90_relrotMean90"
  # adh20 — strong differential
  "mudmut_adh20_divMean0Stdev26"            "mudmut_adh20_divMean0Stdev26_relrotMean0"
  "mudmut_adh20_divMean0Stdev26_relrotMean45"  "mudmut_adh20_divMean0Stdev26_relrotMean90"
  "mudmut_adh20_divMean0Stdev45"            "mudmut_adh20_divMean0Stdev45_relrotMean0"
  "mudmut_adh20_divMean0Stdev45_relrotMean45"  "mudmut_adh20_divMean0Stdev45_relrotMean90"
  "mudmut_adh20_divMean0Stdev90"            "mudmut_adh20_divMean0Stdev90_relrotMean0"
  "mudmut_adh20_divMean0Stdev90_relrotMean45"  "mudmut_adh20_divMean0Stdev90_relrotMean90"
)
```

Default `--parallel` for this sweep: 6 (2 sim types × 3 adhesion levels running
simultaneously fits on a typical 8-core Mac).

---

## Task 3 — Run simulations

```bash
cd ~/bagherilab/ARCADE
./run_decoupling_adhesion.sh --dry-run   # verify paths before committing
./run_decoupling_adhesion.sh             # start the full run
```

Expected wall time: comparable to the WT decoupling study (same 50-run × 2-sim
structure per condition, 3× more conditions). Move output from
`~/bagherilab/ARCADE/output/decoupling_adhesion/` to
`data/sim/decoupling_adhesion/` in the neurogen repo when complete.

---

## Task 4 — Update metadata parsing in `src/npa/metrics.py`

Two parsers need updating to handle the new naming conventions.

### 4a — `CONDITION_PATTERN` (line 131)

The new condition names include `adh{N}_` and `_relrotMean{N}` segments. Update the
pattern to capture both:

```python
# OLD
CONDITION_PATTERN = re.compile(
    r"^(?:(?:wt|mudmut)_)?"
    r"divMean(?P<div_mean>-?\d+)Stdev(?P<div_stdev>-?\d+)"
    r"(?:_rotMean(?P<rot_mean>-?\d+)Stdev(?P<rot_stdev>-?\d+))?"
    r"(?:_noadhesion|_relrot|_yoffset\d+)*$"
)

# NEW
CONDITION_PATTERN = re.compile(
    r"^(?:(?:wt|mudmut)_)?"
    r"(?:adh(?P<adhesion>\d+)_)?"
    r"divMean(?P<div_mean>-?\d+)Stdev(?P<div_stdev>-?\d+)"
    r"(?:_rotMean(?P<rot_mean>-?\d+)Stdev(?P<rot_stdev>-?\d+))?"
    r"(?:_noadhesion|_relrotMean(?P<relrot_mean>\d+)|_yoffset\d+)*$"
)
```

Update `_condition_metadata` to extract both new groups:

```python
def _condition_metadata(condition: str) -> dict[str, Any]:
    match = CONDITION_PATTERN.match(condition)
    if match is None:
        return {
            "adhesion": np.nan,
            "div_mean": np.nan,
            "div_stdev": np.nan,
            "rot_mean": np.nan,
            "rot_stdev": np.nan,
            "relrot": False,
            "relrot_mean": np.nan,
        }
    rot_mean = match.group("rot_mean")
    rot_stdev = match.group("rot_stdev")
    adh_str = match.group("adhesion")
    relrot_mean_str = match.group("relrot_mean")
    return {
        "adhesion": int(adh_str) if adh_str is not None else np.nan,
        "div_mean": int(match.group("div_mean")),
        "div_stdev": int(match.group("div_stdev")),
        "rot_mean": int(rot_mean) if rot_mean is not None else 0,
        "rot_stdev": int(rot_stdev) if rot_stdev is not None else 0,
        "relrot": relrot_mean_str is not None,
        "relrot_mean": int(relrot_mean_str) if relrot_mean_str is not None else np.nan,
    }
```

### 4b — `_sim_metadata` (line 430)

The current implementation only handles `sim{NN}` style IDs (e.g. `sim41`). The new
sweep uses `vcv{0,1}_{noreg,nb_abm,nb_pde,vol_abm,vol_pde}` IDs, which already exist
in `processed_sweep` but may have been producing empty metadata. Add a vcv* branch:

```python
VCV_SIM_METADATA = {
    "vcv1_noreg":   {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "NONE"},
    "vcv1_nb_abm":  {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "NB-ABM"},
    "vcv1_vol_abm": {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "VOL-ABM"},
    "vcv1_nb_pde":  {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "NB-PDE"},
    "vcv1_vol_pde": {"genotype": "mudmut", "critical_volume_mode": 1, "regulatory_dynamic": "VOL-PDE"},
    "vcv0_noreg":   {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "NONE"},
    "vcv0_nb_abm":  {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "NB-ABM"},
    "vcv0_vol_abm": {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "VOL-ABM"},
    "vcv0_nb_pde":  {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "NB-PDE"},
    "vcv0_vol_pde": {"genotype": "mudmut", "critical_volume_mode": 0, "regulatory_dynamic": "VOL-PDE"},
}

def _sim_metadata(sim_id: str) -> dict[str, Any]:
    if sim_id in VCV_SIM_METADATA:
        return dict(VCV_SIM_METADATA[sim_id])
    digits = "".join(ch for ch in sim_id if ch.isdigit())
    if len(digits) != 2:
        return {"genotype": "", "critical_volume_mode": np.nan, "regulatory_dynamic": ""}
    # ... existing numeric-ID branch unchanged ...
```

Note: `genotype` is set to `mudmut` since this is a mudmut-only sweep. The WT sweep
(`processed_sweep`) also uses vcv* sim IDs — if genotype needs to vary by condition
there, infer it from the condition name rather than the sim ID.

**Verify the fix:**

```python
from npa.metrics import _sim_metadata, _condition_metadata
assert _sim_metadata("vcv1_vol_abm")["regulatory_dynamic"] == "VOL-ABM"
assert _sim_metadata("vcv1_vol_abm")["critical_volume_mode"] == 1
assert _condition_metadata("mudmut_adh40_divMean0Stdev26_relrotMean45")["adhesion"] == 40
assert _condition_metadata("mudmut_adh40_divMean0Stdev26_relrotMean45")["relrot"] is True
assert _condition_metadata("mudmut_adh40_divMean0Stdev26_relrotMean45")["relrot_mean"] == 45
assert _condition_metadata("mudmut_adh40_divMean0Stdev26_relrotMean45")["div_stdev"] == 26
assert _condition_metadata("mudmut_adh50_divMean0Stdev26")["adhesion"] == 50
assert _condition_metadata("mudmut_adh50_divMean0Stdev26")["relrot"] is False
```

---

## Task 5 — Preprocess simulation output

The existing `scripts/preprocess_sim.py` and `scripts/extract_metrics.py` accept a
`--sweep-root` argument and work on any directory with the standard
`<condition>/<sim_id>/<run>*.CELLS.json` layout.

Add Makefile targets for the new sweep (add to `Makefile`):

```makefile
ADH_SWEEP_ROOT := data/sim/decoupling_adhesion
ADH_PROC_DIR   := data/sim/processed_decoupling_adhesion

preprocess-adh: extract-metrics-adh

extract-metrics-adh: preprocess-adh-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)

preprocess-adh-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)

adh-clean:
	rm -rf $(ADH_PROC_DIR)/*.npz $(ADH_PROC_DIR)/*.csv $(ADH_PROC_DIR)/figures
```

Run after simulations are complete:

```bash
make preprocess-adh
```

**Smoke test — confirm CSVs have the right metadata:**

```python
import pandas as pd
df = pd.read_csv("data/sim/processed_decoupling_adhesion/sim_timepoint_metrics.csv")
print(df["condition"].unique()[:5])       # should include mudmut_adh* names
print(df["sim_id"].unique())              # should be vcv1_vol_abm, vcv1_vol_pde
print(df["adhesion"].dropna().unique())   # should be 50, 40, 20
print(df["div_stdev"].unique())           # should be 26, 45, 90
print(df["relrot_mean"].dropna().unique()) # should be 0, 45, 90
```

---

## Task 6 — Implement NB connectivity metric

### What it measures

At the simulation endpoint, are all NB cells (as pixel blobs in the 2D spatial grid)
reachable from each other through direct NB-NB pixel adjacency? This answers the
question "are the neuroblasts connected" as a binary outcome per run.

A single isolated NB pixel counts as connected (n_components = 1 even with 1 NB).
If every NB is in direct contact with at least one other NB and all NBs form a single
cluster, `nb_connected = True`.

### Implementation

Add to `src/npa/metrics.py`:

```python
from scipy import ndimage as _ndi

def nb_connectivity(geo: np.ndarray) -> dict[str, Any]:
    """
    Connectivity of the NB region at a single timepoint.

    Parameters
    ----------
    geo : ndarray, shape (H, W, 2)
        Channel 0: NB pixel map (>0 = NB occupied).
        Channel 1: non-NB cell pixel map.

    Returns
    -------
    dict with keys:
        nb_connected     : bool   — True if all NB pixels form one connected component
        nb_n_components  : int    — number of connected NB components (0 if no NBs)
        nb_n_pixels      : int    — total NB pixel count
    """
    nb_mask = geo[..., 0] > 0
    n_pixels = int(nb_mask.sum())
    if n_pixels == 0:
        return {"nb_connected": False, "nb_n_components": 0, "nb_n_pixels": 0}
    _, n_comp = _ndi.label(nb_mask)
    return {
        "nb_connected":    n_comp == 1,
        "nb_n_components": n_comp,
        "nb_n_pixels":     n_pixels,
    }
```

Note: `scipy.ndimage.label` uses 4-connectivity by default (no diagonal adjacency).
Use `structure=_ndi.generate_binary_structure(2, 2)` for 8-connectivity if you prefer
diagonal pixels to count as connected.

### Unit test

Add to `tests/test_metrics.py` (or a new `tests/test_nb_connectivity.py`):

```python
import numpy as np
from npa.metrics import nb_connectivity

def test_single_blob_connected():
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[3:6, 3:6, 0] = 1
    r = nb_connectivity(geo)
    assert r["nb_connected"] is True
    assert r["nb_n_components"] == 1

def test_two_separate_blobs_disconnected():
    geo = np.zeros((10, 10, 2), dtype=int)
    geo[1:3, 1:3, 0] = 1   # blob A
    geo[7:9, 7:9, 0] = 1   # blob B — no adjacency
    r = nb_connectivity(geo)
    assert r["nb_connected"] is False
    assert r["nb_n_components"] == 2

def test_no_nbs():
    geo = np.zeros((10, 10, 2), dtype=int)
    r = nb_connectivity(geo)
    assert r["nb_n_components"] == 0
    assert r["nb_connected"] is False
```

---

## Task 7 — Extract metrics for the adhesion decoupling sweep

Create `scripts/extract_adhesion_metrics.py`. This script loads the NPZ files produced
by `preprocess_sim.py`, applies `heterotypic_contact_fraction`, `nb_cohesion_fraction`,
and `nb_connectivity` to the final-timepoint geo array for every run, and saves three
CSVs to `data/sim/processed_decoupling_adhesion/`.

```python
#!/usr/bin/env python3
"""Extract NB spatial metrics for the adhesion decoupling sweep.

Usage:
    uv run python scripts/extract_adhesion_metrics.py \
        --proc-dir data/sim/processed_decoupling_adhesion
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import ndimage

# ── metric functions ──────────────────────────────────────────────────────────
# (paste heterotypic_contact_fraction, nb_exposure_fraction, nb_cohesion_fraction
#  from notebooks/adhesion_comparison.ipynb, plus nb_connectivity from Task 6)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--proc-dir", type=Path,
                   default=Path("data/sim/processed_decoupling_adhesion"))
    return p.parse_args()


def main():
    args = parse_args()
    run_idx = pd.read_csv(args.proc_dir / "sim_run_index.csv")

    het_records   = []
    coh_records   = []
    conn_records  = []

    for npz_path_str, group in run_idx.groupby("npz_path"):
        with np.load(Path(npz_path_str)) as d:
            geo_all = d["geo"]
        for _, row in group.iterrows():
            geo = geo_all[int(row["npz_row"])]
            base = {
                "condition": row["condition"],
                "sim_id":    row["sim_id"],
                "run_id":    row["run_id"],
            }
            het_records.append( {**base, **heterotypic_contact_fraction(geo)})
            coh_records.append( {**base, "nb_cohesion_frac": nb_cohesion_fraction(geo)})
            conn_records.append({**base, **nb_connectivity(geo)})

    # Merge condition metadata
    meta = run_idx[["condition", "sim_id", "adhesion", "div_stdev",
                     "relrot", "relrot_mean",
                     "critical_volume_mode", "regulatory_dynamic"]].drop_duplicates()

    for records, fname in [
        (het_records,  "het_contact_metrics.csv"),
        (coh_records,  "nb_cohesion_metrics.csv"),
        (conn_records, "nb_connectivity_metrics.csv"),
    ]:
        df = pd.DataFrame(records).merge(meta, on=["condition", "sim_id"], how="left")
        df.to_csv(args.proc_dir / fname, index=False)
        print(f"wrote {fname} ({len(df)} rows)")


if __name__ == "__main__":
    main()
```

Add to Makefile under `extract-metrics-adh`:

```makefile
extract-metrics-adh: preprocess-adh-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)
	$(UV) scripts/extract_adhesion_metrics.py \
		--proc-dir $(ADH_PROC_DIR)
```

**Sanity check after running:**

```python
import pandas as pd
conn = pd.read_csv("data/sim/processed_decoupling_adhesion/nb_connectivity_metrics.csv")
# How often are NBs connected, broken down by adhesion level:
print(conn.groupby("adhesion")["nb_connected"].mean().round(3))
# Expected: lower J (stronger differential) → more often connected
# How often by relrot_mean:
print(conn.groupby("relrot_mean", dropna=False)["nb_connected"].mean().round(3))
```

---

## Task 8 — Analysis notebook

Create `notebooks/adhesion_decoupling_analysis.ipynb`.

### Sections

**Section 1 — Metric overview**
For each of the three metrics (`norm_het_frac`, `nb_cohesion_frac`,
`nb_connected` fraction), show the distribution across all 36 conditions × 50 runs,
split by sim type (vol_abm vs vol_pde).

**Section 2 — Adhesion main effect**
Box plots: metric ~ adhesion level (adh50 / adh40 / adh20), at baseline sigma=26,
relrot=off. Two panels: vol_abm and vol_pde.
Expected: lower J → higher cohesion fraction, higher connectivity rate.

**Section 3 — Sigma sweep**
Line plots: metric ~ sigma (26 / 45 / 90), one line per adhesion level, at relrot=off.
Shows whether stronger adhesion compensates for higher rotation spread.

**Section 4 — Relative rotation sweep**
For each adhesion level, show metric across relrot conditions (off / mu=0 / mu=45 /
mu=90), at sigma=26. Shows how apical-axis alignment bias interacts with adhesion.
Expected: relative rotation with mu=0 increases clustering vs off; mu=90 sends
daughters perpendicular to apical axis, which may reduce clustering.

**Section 5 — NB connectivity heatmap**
Two heatmaps side by side (relrot=off vs relrot=on mu=0): rows = adhesion level,
columns = sigma. Cell value = fraction of runs where `nb_connected = True`. This is
the primary summary figure.

**Section 6 — Example lineages**
Show one representative end-state image per adhesion level (median `nb_cohesion_frac`
run) at sigma=26, relrot=off, to give visual intuition for what J=50 / J=40 / J=20
looks like.

---

## Open questions to resolve before execution

1. **Number of runs**: 50 runs × 72 XMLs = 3600 simulations. Consider reducing to
   25 runs for an initial exploratory pass (halves compute, still provides good
   distributions for the connectivity boolean).

2. **Sigma=0 control**: not included. Add `mudmut_adh{J}_divMean0Stdev0` conditions
   if you want a "perfectly aligned" reference.

3. **WT controls**: this sweep is mudmut-only. The existing
   `processed_sweep/wt_divMean0Stdev26/vcv1_noreg` data can serve as a reference for
   NB clustering without differential adhesion.
