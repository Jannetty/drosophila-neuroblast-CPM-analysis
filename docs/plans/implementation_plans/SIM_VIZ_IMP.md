# Simulation Data Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement simulation visualization for raw snapshots and preprocessed NPZ tensors through one shared rendering primitive and a single CLI.

**Architecture:** Add a flat module `src/npa/sim_viz.py` with load helpers for the three contexts (`raw-any`, `raw-last`, `npz`) and a single `render_geo` function to paint `(H, W, 2)` tensors consistently. Add `scripts/visualize_sim.py` as a thin mode-dispatch CLI that validates mode-specific args, loads geo through the module helpers, and either saves or shows the figure.

**Tech Stack:** Python, numpy, pandas, matplotlib, argparse, pytest.

---

### Task 1: Add sim_viz module with shared rendering and load helpers

**Files:**
- Create: `src/npa/sim_viz.py`
- Create: `tests/test_sim_viz.py`

- [ ] **Step 1: Write failing tests for module behavior**

```python
def test_render_geo_nb_priority_and_return_axes(...)
def test_load_raw_snapshot_uses_build_geo_tensor(...)
def test_find_last_snapshot_uses_highest_time_id(...)
def test_load_sim_npz_row(...)
def test_print_sim_index_table_aligned(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_sim_viz.py -v`
Expected: FAIL with missing `npa.sim_viz` module.

- [ ] **Step 3: Implement minimal module**

```python
def load_sim_npz(npz_path: Path, row: int) -> np.ndarray: ...
def load_raw_snapshot(cells_path: Path, locs_path: Path) -> np.ndarray: ...
def find_last_snapshot(sim_dir: Path) -> tuple[Path, Path]: ...
def render_geo(geo: np.ndarray, ax=None, title: str = ""): ...
def load_sim_index(processed_dir: Path) -> list[dict]: ...
def print_sim_index_table(rows: list[dict]) -> None: ...
```

- [ ] **Step 4: Re-run module tests**

Run: `source .venv/bin/activate && pytest tests/test_sim_viz.py -v`
Expected: PASS.

---

### Task 2: Add visualize_sim CLI for all three contexts

**Files:**
- Create: `scripts/visualize_sim.py`
- Create: `tests/test_visualize_sim_cli.py`

- [ ] **Step 1: Write failing CLI tests**

```python
def test_visualize_sim_cli_raw_any_requires_cells_and_locs(...)
def test_visualize_sim_cli_raw_last_uses_find_last_snapshot(...)
def test_visualize_sim_cli_npz_saves_when_out(...)
def test_visualize_sim_cli_shows_when_no_out(...)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `source .venv/bin/activate && pytest tests/test_visualize_sim_cli.py -v`
Expected: FAIL with missing CLI script.

- [ ] **Step 3: Implement CLI dispatcher**

```python
python scripts/visualize_sim.py --mode raw-any --cells PATH --locs PATH
python scripts/visualize_sim.py --mode raw-last --sim-dir PATH
python scripts/visualize_sim.py --mode npz --npz PATH --row INT
```

Include shared flags `--title` and `--out`; mode-specific validation errors should be clear.

- [ ] **Step 4: Re-run CLI tests**

Run: `source .venv/bin/activate && pytest tests/test_visualize_sim_cli.py -v`
Expected: PASS.

---

### Task 3: Update live pipeline doc and full verification

**Files:**
- Modify: `docs/PIPELINE.md`

- [ ] **Step 1: Update Step 4 reality in PIPELINE**

Replace the “Not yet implemented” placeholder with actual command, module path, modes, and behavior.

- [ ] **Step 2: Run full test suite**

Run: `source .venv/bin/activate && pytest -v`
Expected: PASS.

