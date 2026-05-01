# Simulation Data Visualization Plan

**Date:** 2026-04-22
**Goal:** Visualize ARCADE simulation output at three levels — raw JSON at any
timepoint, raw JSON at the last timepoint only, and preprocessed NPZ. Keep the
module parallel in structure to `exp_viz.py` so patterns stay consistent across
experimental and simulation visualization.

---

## The three visualization contexts

| Context | Input | When useful |
|---|---|---|
| **Raw / any tick** | CELLS.json + LOCATIONS.json for a single time step | Debugging, watching growth over time |
| **Raw / last tick** | CELLS.json + LOCATIONS.json — last file pair in a sim directory | Quick sanity check without preprocessing |
| **Preprocessed** | NPZ produced by `preprocess_sim.py` | Analysis, comparing conditions |

The key design constraint: all three share the same rendering primitive. The
only difference is *how the data is loaded* before rendering. This avoids
duplication and keeps the rendering logic in one place.

---

## Color conventions

Reuse the colors already established in `exp_viz.py` so experimental and
simulation figures are visually consistent.

```python
HULL_COLOR = "#d4d4d4"   # lineage bounding convex hull
NB_COLOR   = "#8e77b5"   # pop == 1  (neuroblast)
PROS_COLOR = "#259eae"   # pop in {2, 3}  (progeny / pros-like)
```

---

## Module: `src/npa/sim_viz.py`

Flat module, mirrors `exp_viz.py`. No sub-packages.

### Data loading

```python
def load_sim_npz(npz_path: Path, row: int) -> np.ndarray:
    """Return geo[row] — shape (H, W, 2) — from a condition NPZ."""

def load_raw_snapshot(cells_path: Path, locs_path: Path) -> np.ndarray:
    """Load one CELLS/LOCATIONS pair, return geo tensor (H, W, 2).

    Calls build_geo_tensor from sim_preprocessing; canvas_size=200.
    This is the shared entry point for both the any-tick and last-tick
    raw contexts — the caller is responsible for picking which file pair.
    """

def find_last_snapshot(sim_dir: Path) -> tuple[Path, Path]:
    """Return (cells_path, locs_path) for the highest time_id in sim_dir.

    Thin wrapper around index_sim_files: resolves sim_dir → condition_dir
    and sim_id, calls index_sim_files, returns entries[-1] paths.
    Raises FileNotFoundError if no matched pairs exist.
    """
```

### Rendering

```python
def render_geo(
    geo: np.ndarray,
    ax: matplotlib.axes.Axes | None = None,
    title: str = "",
) -> matplotlib.axes.Axes:
    """Render a (H, W, 2) geo tensor as a 2D image.

    Channel 0 (NB) is painted NB_COLOR; channel 1 (pros) is painted
    PROS_COLOR. Overlapping pixels use NB_COLOR (NB takes priority).
    Returns the Axes so callers can further annotate or save.

    If ax is None, creates a new figure.
    """
```

A single `render_geo` function covers all three contexts because by the time
we reach rendering, every context has already produced the same (H, W, 2)
tensor. The canvas is always 200×200 (matching the preprocessing default).

### Index helpers (for preprocessed context)

```python
def load_sim_index(processed_dir: Path) -> list[dict]:
    """Load sim_index.csv, return list of row dicts."""

def print_sim_index_table(rows: list[dict]) -> None:
    """Print aligned table: row | condition | n_runs | npz_path."""
```

---

## Script: `scripts/visualize_sim.py`

CLI that covers all three contexts via a single `--mode` flag.

### Interface

```
python scripts/visualize_sim.py \
    --mode raw-any        # any tick: requires --cells and --locs
    --mode raw-last       # last tick: requires --sim-dir
    --mode npz            # preprocessed: requires --npz and --row

    # raw-any
    --cells PATH          # path to a .CELLS.json file
    --locs  PATH          # path to the matching .LOCATIONS.json file

    # raw-last
    --sim-dir PATH        # path to a single sim directory (e.g. .../sim41/)

    # npz
    --npz PATH            # path to a condition .npz file
    --row  INT            # row index within the NPZ

    # shared optional
    --title STR           # figure title (default: derived from input paths)
    --out   PATH          # save figure to this path instead of showing it
```

### Logic

```
1. Parse args; validate that required args for the chosen mode are present.
2. Load data:
   - raw-any  → load_raw_snapshot(cells, locs)
   - raw-last → find_last_snapshot(sim_dir) → load_raw_snapshot(cells, locs)
   - npz      → load_sim_npz(npz, row)
3. Call render_geo(geo, title=title).
4. If --out: fig.savefig(out, dpi=150, bbox_inches="tight")
   Else:      plt.show()
```

---

## What is NOT included

- 3D visualization — simulation output is already projected to 2D during
  preprocessing; a 3D viewer adds no analytical value here.
- Per-cell convex hulls — voxel painting is sufficient; hull computation
  belongs in a dedicated analysis step if ever needed.
- Animation / multi-tick loops — out of scope; use `--mode raw-any` in a
  notebook loop if needed.
- Statistical plots — those belong in a separate analysis module, not a
  visualization utility.

---

## Relationship to existing modules

```
sim_preprocessing.py   ←  sim_viz.py uses build_geo_tensor, index_sim_files
exp_viz.py             ←  sim_viz.py copies color constants and render pattern
scripts/preprocess_sim.py  ←  sim_viz.py --mode npz consumes its output
```

`sim_viz.py` depends on `sim_preprocessing.py` only for `build_geo_tensor`
and `index_sim_files`. No new shared state is introduced.

---

## Validation checklist

- [ ] `--mode raw-any` displays a cell with NB pixels in `NB_COLOR` and pros pixels in `PROS_COLOR`
- [ ] `--mode raw-last` selects the file with the highest time_id, not alphabetically first
- [ ] `--mode npz` renders the same geo as `--mode raw-last` for the same (sim, run) pair at the last tick
- [ ] `--out` saves a file; without it, `plt.show()` is called
- [ ] Missing required args for a mode exit with a clear error message
- [ ] `render_geo` returns an Axes and does not call `plt.show()` internally (caller controls display)
