# Experimental Lineage Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CLI visualization flow for kept/rejected experimental lineages and extend preprocessing outputs so rejected lineages are indexed and fully visualizable.

**Architecture:** Extend preprocessing to preserve rejected lineages as mesh NPZs plus a rejected index CSV, without mixing them into the kept analysis index. Add a new `npa.exp_viz` module for index/data loading and rendering helpers, and a thin script-level CLI dispatcher for list/select/view workflows.

**Tech Stack:** Python, numpy, pandas, matplotlib, plotly, trimesh, pytest.

---

### Task 1: Add rejected lineage preprocessing outputs

**Files:**
- Modify: `src/npa/exp_preprocessing/lineage_filter.py`
- Modify: `src/npa/exp_preprocessing/pipeline.py`
- Modify: `scripts/preprocess_exp.py`
- Test: `tests/test_exp_preprocessing.py`

- [ ] **Step 1: Write failing tests**

```python
def test_load_exp_filtered_lobe_tracks_rejected_lineages(...)
def test_write_rejected_lineage_index(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_exp_preprocessing.py -k rejected -v`
Expected: FAIL with missing rejected tracking and/or CSV writer behavior.

- [ ] **Step 3: Implement minimal rejected lineage flow**

```python
@dataclass(frozen=True)
class ExpRejectedLineage:
    lineage_idx: int
    lineage_mesh: trimesh.Trimesh
    dpn_meshes: list[trimesh.Trimesh]
    pros_meshes: list[trimesh.Trimesh]
    rejection_reason: str
```

Add `rejected` to `ExpFilteredLobe`, update filtering logic to populate rejected entries with reason (`disconnected`, `no_dpn`), process rejected entries to `meshes/rejected/{genotype}/...`, and write `rejected_lineage_index.csv`.

- [ ] **Step 4: Run focused tests**

Run: `source .venv/bin/activate && pytest tests/test_exp_preprocessing.py -k rejected -v`
Expected: PASS.

- [ ] **Step 5: Run full preprocessing tests**

Run: `source .venv/bin/activate && pytest tests/test_exp_preprocessing.py -v`
Expected: PASS.

---

### Task 2: Add visualization data/load/render module

**Files:**
- Create: `src/npa/exp_viz.py`
- Modify: `pyproject.toml`
- Test: `tests/test_exp_viz.py`

- [ ] **Step 1: Write failing tests**

```python
def test_load_index_kept_and_rejected(...)
def test_load_mesh_npz_and_geo_slice(...)
def test_show_2d_post_reuses_precomputed_px(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_exp_viz.py -v`
Expected: FAIL (module/functions missing).

- [ ] **Step 3: Implement module and dependency**

```python
def load_index(processed_dir: Path, rejected: bool) -> list[dict]: ...
def load_mesh_npz(mesh_path: Path) -> dict: ...
def load_lineage_geo(analysis_npz: Path, analysis_row: int) -> np.ndarray: ...
def print_index_table(rows: list[dict], rejected: bool) -> None: ...
def show_3d(mesh: dict, row: dict) -> None: ...
def show_2d_pre(mesh: dict, row: dict) -> None: ...
def show_2d_post(mesh: dict, geo: np.ndarray, row: dict) -> None: ...
```

Use the specified colors and opacities; in `show_2d_post` overlay `*_2d_px` values directly.

- [ ] **Step 4: Run visualization tests**

Run: `source .venv/bin/activate && pytest tests/test_exp_viz.py -v`
Expected: PASS.

---

### Task 3: Add visualization CLI entrypoint

**Files:**
- Create: `scripts/visualize_exp_lineage.py`
- Test: `tests/test_exp_viz_cli.py`

- [ ] **Step 1: Write failing CLI tests**

```python
def test_cli_lists_by_default(...)
def test_cli_rejected_2d_post_errors(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_exp_viz_cli.py -v`
Expected: FAIL (script missing and/or behavior mismatch).

- [ ] **Step 3: Implement CLI dispatcher**

```python
python scripts/visualize_exp_lineage.py --list [--rejected]
python scripts/visualize_exp_lineage.py (--row N | --id N) [--view {3d,2d-pre,2d-post}] [--rejected]
```

Default to listing when no selection is provided, resolve row by `--row` or `--id`, and raise a clear error for rejected `2d-post`.

- [ ] **Step 4: Run CLI tests**

Run: `source .venv/bin/activate && pytest tests/test_exp_viz_cli.py -v`
Expected: PASS.

---

### Task 4: End-to-end verification

**Files:**
- Modify: (none expected; only if fixes needed)

- [ ] **Step 1: Run full test suite**

Run: `source .venv/bin/activate && pytest -v`
Expected: PASS.

- [ ] **Step 2: Re-run preprocessing for updated indexes**

Run: `source .venv/bin/activate && python scripts/preprocess_exp.py`
Expected: PASS, with both `lineage_index.csv` and `rejected_lineage_index.csv` written.

