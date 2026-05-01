# Simulation Data Preprocessing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a simulation preprocessing pipeline that converts sweep CELLS/LOCATIONS snapshots into per-condition NPZ tensors plus a condition index CSV.

**Architecture:** Implement a single flat processing module (`src/npa/sim_preprocessing.py`) for file indexing, per-snapshot voxel rasterization, and per-condition orchestration. Add a thin CLI (`scripts/preprocess_sim.py`) that handles discovery/filtering and delegates processing. Keep outputs deterministic by sorting rows by `(sim_id, run_id)`.

**Tech Stack:** Python, numpy, pandas, json, pathlib, pytest.

---

### Task 1: File indexing and rasterization primitives

**Files:**
- Create: `src/npa/sim_preprocessing.py`
- Create: `tests/test_sim_preprocessing.py`

- [ ] **Step 1: Write failing tests for indexing and rasterization**

```python
def test_index_sim_files_pairs_and_sorts_last_timepoint(...)
def test_build_geo_tensor_centers_and_channels(...)
def test_build_geo_tensor_empty_voxels_returns_zeros(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_sim_preprocessing.py -k "index_sim_files or build_geo_tensor" -v`
Expected: FAIL with missing `npa.sim_preprocessing`.

- [ ] **Step 3: Implement minimal indexing/rasterization code**

```python
CELLS_PATTERN = re.compile(r".*_([0-9]{4})_([0-9]{6})\.CELLS\.json$")
def index_sim_files(...): ...
def build_geo_tensor(...): ...
```

- [ ] **Step 4: Re-run focused tests**

Run: `source .venv/bin/activate && pytest tests/test_sim_preprocessing.py -k "index_sim_files or build_geo_tensor" -v`
Expected: PASS.

---

### Task 2: Condition-level orchestration and output writing

**Files:**
- Modify: `src/npa/sim_preprocessing.py`
- Modify: `tests/test_sim_preprocessing.py`

- [ ] **Step 1: Write failing tests for condition output**

```python
def test_process_condition_uses_last_timepoint_and_sorts_rows(...)
def test_write_sim_index_csv(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_sim_preprocessing.py -k "process_condition or sim_index" -v`
Expected: FAIL because `process_condition` / index writing behavior is missing.

- [ ] **Step 3: Implement condition processing and index CSV writer**

```python
def process_condition(...): ...
def write_sim_index(records: list[dict], out_path: Path) -> None: ...
```

- [ ] **Step 4: Re-run focused tests**

Run: `source .venv/bin/activate && pytest tests/test_sim_preprocessing.py -k "process_condition or sim_index" -v`
Expected: PASS.

---

### Task 3: CLI entrypoint for sweep processing

**Files:**
- Create: `scripts/preprocess_sim.py`
- Create: `tests/test_preprocess_sim_cli.py`

- [ ] **Step 1: Write failing CLI tests**

```python
def test_preprocess_sim_cli_requires_sweep_root(...)
def test_preprocess_sim_cli_writes_outputs_for_condition_subset(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_preprocess_sim_cli.py -v`
Expected: FAIL with missing CLI module/script behavior.

- [ ] **Step 3: Implement CLI logic**

```python
python scripts/preprocess_sim.py --sweep-root PATH [--out-dir PATH] [--conditions ...] [--sim-ids ...]
```

- [ ] **Step 4: Re-run CLI tests**

Run: `source .venv/bin/activate && pytest tests/test_preprocess_sim_cli.py -v`
Expected: PASS.

---

### Task 4: End-to-end verification

**Files:**
- Modify: none expected

- [ ] **Step 1: Run full test suite**

Run: `source .venv/bin/activate && pytest -v`
Expected: PASS.

