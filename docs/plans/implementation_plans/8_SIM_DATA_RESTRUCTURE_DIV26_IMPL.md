# Implementation Plan: Sim Data Restructure for div26 Sweep

Implements the changes described in `8_SIM_DATA_RESTRUCTURE_DIV26.md`.

**Current state:**
- `data/sim/bioparams_div26_sweep/` already populated with CELLS/LOCATIONS files.
  Old `bioparams_rotation_sweep` data is on external hard drive and absent from repo.
- `SIM_SERIES_METADATA` in `metrics.py` already includes series 7 (wt, VBCV=0).
  A test for it already exists at `tests/test_metrics.py:363`.
- `CONDITION_PATTERN` still uses the old format and will produce all-NaN metadata
  for every condition in the new sweep.
- No `data/sim/processed_div26/` directory yet — it is created by running the pipeline.
- No METADATA.md for the new sweep yet.

**Only code change required:** `CONDITION_PATTERN` and `_condition_metadata` in
`src/npa/metrics.py`.

---

## Step 1 — Update `CONDITION_PATTERN` in `src/npa/metrics.py`

**File:** `src/npa/metrics.py`

**What to change:**

Replace the current pattern at line ~131:
```python
CONDITION_PATTERN = re.compile(
    r"^divMean(?P<div_mean>-?\d+)Stdev(?P<div_stdev>-?\d+)_rotMean(?P<rot_mean>-?\d+)Stdev(?P<rot_stdev>-?\d+)$"
)
```

With a pattern that:
1. Optionally matches a leading `{genotype}_` prefix (`wt_` or `mudmut_`).
2. Makes the `_rotMeanXStdevY` suffix optional.
3. Still matches old-style names (`divMean0Stdev30_rotMean0Stdev30`) so existing
   test fixtures do not need to change.

```python
CONDITION_PATTERN = re.compile(
    r"^(?:(?:wt|mudmut)_)?"
    r"divMean(?P<div_mean>-?\d+)Stdev(?P<div_stdev>-?\d+)"
    r"(?:_rotMean(?P<rot_mean>-?\d+)Stdev(?P<rot_stdev>-?\d+))?$"
)
```

**Also update `_condition_metadata`** at line ~408 to default `rot_mean` and
`rot_stdev` to 0 when the optional rot group is absent:

```python
def _condition_metadata(condition: str) -> dict[str, Any]:
    match = CONDITION_PATTERN.match(condition)
    if match is None:
        return {
            "div_mean": np.nan,
            "div_stdev": np.nan,
            "rot_mean": np.nan,
            "rot_stdev": np.nan,
        }
    rot_mean = match.group("rot_mean")
    rot_stdev = match.group("rot_stdev")
    return {
        "div_mean": int(match.group("div_mean")),
        "div_stdev": int(match.group("div_stdev")),
        "rot_mean": int(rot_mean) if rot_mean is not None else 0,
        "rot_stdev": int(rot_stdev) if rot_stdev is not None else 0,
    }
```

---

## Step 2 — Add tests for new condition name formats in `tests/test_metrics.py`

Add a test that covers all three condition name shapes: new WT (no rot suffix),
new mudmut (with genotype prefix and rot suffix), and old-style (no prefix).
Verify that old-style conditions still parse correctly.

```python
def test_condition_metadata_new_format() -> None:
    # new WT: genotype prefix, no rot params
    wt = _condition_metadata("wt_divMean0Stdev26")
    assert wt["div_mean"] == 0
    assert wt["div_stdev"] == 26
    assert wt["rot_mean"] == 0      # defaulted
    assert wt["rot_stdev"] == 0     # defaulted

    # new mudmut: genotype prefix + rot params
    mm = _condition_metadata("mudmut_divMean11Stdev26_rotMean11Stdev30")
    assert mm["div_mean"] == 11
    assert mm["div_stdev"] == 26
    assert mm["rot_mean"] == 11
    assert mm["rot_stdev"] == 30

    # old-style still parses
    old = _condition_metadata("divMean36Stdev30_rotMean0Stdev30")
    assert old["div_mean"] == 36
    assert old["div_stdev"] == 30
    assert old["rot_mean"] == 0
    assert old["rot_stdev"] == 30

    # unrecognized → all NaN
    bad = _condition_metadata("garbage")
    assert np.isnan(bad["div_mean"])
```

Note: `_condition_metadata` is a module-private function. Import it directly from
`npa.metrics` in the test (it is already importable; no need to expose it in
`__init__`).

---

## Step 3 — Write `data/sim/bioparams_div26_sweep/METADATA.md`

Document the new sweep so the human-readable ledger stays current.  Contents to cover:

- Sim-series lookup: 6x = wt/VCV1, 7x = wt/VCV0, 4x = mudmut/VCV1, 5x = mudmut/VCV0
- Regulatory-dynamic suffix key (same as old sweep: x1=NONE, x2=NB-ABM, x3=VOL-ABM,
  x4=NB-PDE, x5=VOL-PDE)
- Full condition listing with genotype, div distribution, and rot distribution
- Note that ticks=2161 / dt=0.01667 (≈1 min/tick) in this sweep vs ticks=434 /
  dt=0.083 (≈5 min/tick) in the old sweep

---

## Step 4 — Run the preprocessing pipeline

With code changes from Steps 1–2 in place, run in order:

```bash
# Preprocess: rasterize CELLS/LOCATIONS → per-condition NPZs
uv run python scripts/preprocess_sim.py \
    --sweep-root data/sim/bioparams_div26_sweep \
    --out-dir data/sim/processed_div26

# Extract metrics: stream all timepoints → timepoint_metrics.csv
uv run python scripts/extract_metrics.py --kind sim \
    --sweep-root data/sim/bioparams_div26_sweep \
    --out-dir data/sim/processed_div26

# Summarize: build sim_metrics_last.csv and sim_summary_last.csv
uv run python scripts/summarize_metrics.py \
    --sim-metrics data/sim/processed_div26/timepoint_metrics.csv \
    --exp-metrics data/exp/processed/metrics.csv \
    --sim-out data/sim/processed_div26/sim_metrics_last.csv \
    --sim-summary-out data/sim/processed_div26/sim_summary_last.csv \
    --exp-summary-out data/exp/processed/exp_summary.csv
```

Spot-check outputs:
- `sim_index.csv`: confirm all 8 conditions appear with non-zero `n_runs`
- `sim_run_index.csv`: spot-check a wt/VCV0 row (sim_id=sim7x) and a mudmut row
- `sim_metrics_last.csv`: confirm `genotype`, `critical_volume_mode`, `div_stdev`
  columns are populated (not NaN) for all rows
- `sim_summary_last.csv`: confirm wt rows with `critical_volume_mode=0` appear

---

## Step 5 — Update `PIPELINE.md`

Update the following sections to reflect the new sweep:

- **Step 3 CLI options / default paths**: note new default sweep root and
  `processed_div26` output dir.
- **Step 5 CLI example**: update `--sweep-root` to `data/sim/bioparams_div26_sweep`.
- **Step 6 CLI example**: update `--sim-metrics` path.
- Note that `processed/` (old sweep outputs) is absent from the working machine;
  `processed_div26/` is the active processed directory.

---

## Verification checklist

- [ ] `uv run python -m pytest tests/test_metrics.py -x` passes
- [ ] `uv run python -m pytest tests/ -x` passes (full suite)
- [ ] `sim_metrics_last.csv`: no NaN in `div_mean`, `div_stdev`, `genotype`,
      `critical_volume_mode` columns
- [ ] WT rows with `critical_volume_mode=0` appear in `sim_summary_last.csv`
- [ ] Old-style condition name still parses correctly (covered by new test)
