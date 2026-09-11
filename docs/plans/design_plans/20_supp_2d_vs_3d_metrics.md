# Supplemental 2D vs 3D Metrics Figure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a supplemental figure script that computes the five calibration metrics in both 2D (projected area) and 3D (mesh volume) for WT and mudmut lineages, outputs a comparison table (fold-changes + MWU p-values), and produces two histogram figures: one for WT lineages comparing 2D vs 3D representations, and an analogous one for mudmut lineages. Both figures use fold-change from each representation's own WT mean so 2D and 3D can be directly overlaid.

**Architecture:** Single standalone script `scripts/make_supp_2d_vs_3d_metrics.py`. Loads 2D metrics from the existing `metrics.csv` and 3D metrics directly from the preprocessed mesh NPZ files (already stored for every kept lineage at `data/exp/processed/meshes/{genotype}/{lobe}_{lineage_idx}.npz`). No new preprocessing step required.

**Tech Stack:** Python, numpy, pandas, trimesh (for lineage hull volume), scipy (MWU), matplotlib. All available in the uv environment. Run as `uv run python scripts/make_supp_2d_vs_3d_metrics.py`.

---

## Metric definitions

| Column name | 2D source | 3D source |
|---|---|---|
| `n_dpn` | `metrics.csv: n_dpn` | `len(npz["dpn_volumes_um3"])` |
| `dpn_area` | `metrics.csv: dpn_area_vox * ds²` (µm²) | `npz["dpn_volumes_um3"].sum()` (µm³) |
| `avg_dpn_area` | `metrics.csv: avg_dpn_area_vox * ds²` (µm²) | `npz["dpn_volumes_um3"].mean()` (µm³) |
| `lin_area` | `metrics.csv: lin_area_vox * ds²` (µm²) | `abs(trimesh.Trimesh(lin_vertices, lin_faces).volume)` (µm³) |
| `n_pros` | `metrics.csv: n_pros` | `len(npz["pros_volumes_um3"])` |

Only `wt` and `mudmut` genotypes are used (nanobody is excluded — it is not part of the calibration criteria comparison).

Fold-change for each metric = mudmut_mean / wt_mean (WT mean computed within each representation separately).

The histogram figures normalize per-lineage values by each representation's own WT mean: 2D values divided by WT 2D mean, 3D values divided by WT 3D mean. This keeps fold-change internally consistent (1.0 = WT level in that representation) and lets 2D and 3D be overlaid in the same panel despite different units (µm² vs µm³).

---

## File structure

| File | Action | Purpose |
|---|---|---|
| `scripts/make_supp_2d_vs_3d_metrics.py` | **Create** | Full standalone script |
| `docs/tex_draft/figures/figS_2d_vs_3d_wt_panel.pdf` | Generated | WT: 2D vs 3D histograms (PDF) |
| `docs/tex_draft/figures/figS_2d_vs_3d_wt_panel.png` | Generated | WT: 2D vs 3D histograms (PNG) |
| `docs/tex_draft/figures/figS_2d_vs_3d_mudmut_panel.pdf` | Generated | mudmut: 2D vs 3D histograms (PDF) |
| `docs/tex_draft/figures/figS_2d_vs_3d_mudmut_panel.png` | Generated | mudmut: 2D vs 3D histograms (PNG) |
| `docs/tex_draft/figures/figS_2d_vs_3d_metrics_table.csv` | Generated | Table data CSV |

---

## Task 1: Scaffold the script with path constants and CLI

**Files:**
- Create: `scripts/make_supp_2d_vs_3d_metrics.py`

- [ ] **Step 1: Write the scaffold**

```python
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import trimesh
from scipy.stats import mannwhitneyu

matplotlib.use("Agg")

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "docs" / "tex_draft"))
from _style import RCPARAMS, FONT_SIZE_TITLE, FONT_SIZE_LABEL

plt.rcParams.update(RCPARAMS)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROC_DIR = REPO_ROOT / "data" / "exp" / "processed"
FIG_DIR = REPO_ROOT / "docs" / "tex_draft" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

GENOTYPES = ["wt", "mudmut"]

WT_COLOR = "#4C72B0"
MUD_COLOR = "#DD8452"

METRICS = [
    ("n_dpn",       "# neuroblasts",          "fold-change from WT"),
    ("dpn_area",    "total NB area/vol",       "fold-change from WT"),
    ("avg_dpn_area","avg NB area/vol per cell","fold-change from WT"),
    ("lin_area",    "lineage area/vol",        "fold-change from WT"),
    ("n_pros",      "# non-neuroblasts",       "fold-change from WT"),
]
```

- [ ] **Step 2: Run to confirm imports work**

```bash
uv run python scripts/make_supp_2d_vs_3d_metrics.py
```

Expected: no output, no errors (no `main()` yet).

- [ ] **Step 3: Commit**

```bash
git add scripts/make_supp_2d_vs_3d_metrics.py
git commit -m "feat: scaffold supp 2d-vs-3d metrics script"
```

---

## Task 2: Load 2D metrics

**Files:**
- Modify: `scripts/make_supp_2d_vs_3d_metrics.py`

- [ ] **Step 1: Add `load_2d_metrics()` function**

Add this function after the constants block:

```python
def load_2d_metrics(proc_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(proc_dir / "metrics.csv")
    df = df[df["genotype"].isin(GENOTYPES)].copy()
    ds = df["ds"].values
    df["dpn_area"] = df["dpn_area_vox"] * ds * ds
    df["avg_dpn_area"] = df["avg_dpn_area_vox"] * ds * ds
    df["lin_area"] = df["lin_area_vox"] * ds * ds
    return df[["lineage_id", "genotype", "n_dpn", "dpn_area", "avg_dpn_area", "lin_area", "n_pros"]].copy()
```

- [ ] **Step 2: Write a test that verifies unit conversion**

Create `tests/test_supp_2d_vs_3d_metrics.py`:

```python
import pandas as pd
import numpy as np
from pathlib import Path

PROC_DIR = Path("data/exp/processed")


def test_load_2d_metrics_unit_conversion():
    """dpn_area_um2 should equal dpn_area_vox * ds^2."""
    import sys
    sys.path.insert(0, str(Path("scripts")))
    from make_supp_2d_vs_3d_metrics import load_2d_metrics

    df = load_2d_metrics(PROC_DIR)
    raw = pd.read_csv(PROC_DIR / "metrics.csv")
    raw = raw[raw["genotype"].isin(["wt", "mudmut"])].reset_index(drop=True)
    df = df.reset_index(drop=True)

    expected = raw["dpn_area_vox"] * raw["ds"] ** 2
    np.testing.assert_allclose(df["dpn_area"].values, expected.values, rtol=1e-5)


def test_load_2d_metrics_only_wt_mudmut():
    import sys
    sys.path.insert(0, str(Path("scripts")))
    from make_supp_2d_vs_3d_metrics import load_2d_metrics

    df = load_2d_metrics(PROC_DIR)
    assert set(df["genotype"].unique()) <= {"wt", "mudmut"}
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
uv run pytest tests/test_supp_2d_vs_3d_metrics.py -v
```

Expected: 2 tests pass.

- [ ] **Step 4: Commit**

```bash
git add scripts/make_supp_2d_vs_3d_metrics.py tests/test_supp_2d_vs_3d_metrics.py
git commit -m "feat: add load_2d_metrics for supp figure"
```

---

## Task 3: Load 3D metrics from mesh NPZ files

**Files:**
- Modify: `scripts/make_supp_2d_vs_3d_metrics.py`

The mesh NPZ files live at `data/exp/processed/meshes/{genotype}/{lobe}_{lineage_idx}.npz`. The `lineage_index.csv` has columns `lineage_id, genotype, lobe, lineage_idx` so we can reconstruct the path.

- [ ] **Step 1: Add `load_3d_metrics()` function**

```python
def load_3d_metrics(proc_dir: Path) -> pd.DataFrame:
    index = pd.read_csv(proc_dir / "lineage_index.csv")
    index = index[index["genotype"].isin(GENOTYPES)].copy()

    rows = []
    for _, row in index.iterrows():
        npz_path = proc_dir / "meshes" / row["genotype"] / f"{row['lobe']}_{row['lineage_idx']}.npz"
        npz = np.load(npz_path)
        dpn_vols = npz["dpn_volumes_um3"]
        pros_vols = npz["pros_volumes_um3"]
        mesh = trimesh.Trimesh(vertices=npz["lin_vertices"], faces=npz["lin_faces"], process=False)
        lin_vol = abs(float(mesh.volume))
        rows.append({
            "lineage_id": int(row["lineage_id"]),
            "genotype": row["genotype"],
            "n_dpn": len(dpn_vols),
            "dpn_area": float(dpn_vols.sum()),
            "avg_dpn_area": float(dpn_vols.mean()),
            "lin_area": lin_vol,
            "n_pros": len(pros_vols),
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Add test for 3D metric loading**

Add to `tests/test_supp_2d_vs_3d_metrics.py`:

```python
def test_load_3d_metrics_n_dpn_matches_index():
    """n_dpn from 3D should match lineage_index.csv n_dpn."""
    import sys
    sys.path.insert(0, str(Path("scripts")))
    from make_supp_2d_vs_3d_metrics import load_3d_metrics

    df3d = load_3d_metrics(PROC_DIR)
    index = pd.read_csv(PROC_DIR / "lineage_index.csv")
    index = index[index["genotype"].isin(["wt", "mudmut"])]
    merged = df3d.merge(index[["lineage_id", "n_dpn"]], on="lineage_id", suffixes=("_3d", "_idx"))
    assert (merged["n_dpn_3d"] == merged["n_dpn_idx"]).all(), "n_dpn mismatch between 3D mesh and index"


def test_load_3d_metrics_lin_area_positive():
    import sys
    sys.path.insert(0, str(Path("scripts")))
    from make_supp_2d_vs_3d_metrics import load_3d_metrics

    df3d = load_3d_metrics(PROC_DIR)
    assert (df3d["lin_area"] > 0).all(), "All lineage volumes should be positive"
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_supp_2d_vs_3d_metrics.py -v
```

Expected: 4 tests pass.

- [ ] **Step 4: Commit**

```bash
git add scripts/make_supp_2d_vs_3d_metrics.py tests/test_supp_2d_vs_3d_metrics.py
git commit -m "feat: add load_3d_metrics from mesh NPZ for supp figure"
```

---

## Task 4: Build comparison table

**Files:**
- Modify: `scripts/make_supp_2d_vs_3d_metrics.py`

- [ ] **Step 1: Add `build_table()` function**

```python
def _fmt_p(p: float) -> str:
    if p < 0.001:
        return "<0.001"
    if p < 0.01:
        return f"{p:.3f}"
    return f"{p:.2f}"


def build_table(df_2d: pd.DataFrame, df_3d: pd.DataFrame) -> pd.DataFrame:
    metric_labels = {
        "n_dpn":       "# neuroblasts (dpn)",
        "dpn_area":    "Total NB area/volume",
        "avg_dpn_area":"Avg NB area/volume",
        "lin_area":    "Lineage area/volume",
        "n_pros":      "# non-neuroblasts (pros)",
    }
    rows = []
    for col, label in metric_labels.items():
        for dim, df in [("2D", df_2d), ("3D", df_3d)]:
            wt_vals   = df.loc[df["genotype"] == "wt",     col].values.astype(float)
            mud_vals  = df.loc[df["genotype"] == "mudmut", col].values.astype(float)
            wt_mean   = wt_vals.mean()
            mud_mean  = mud_vals.mean()
            fc        = mud_mean / wt_mean
            _, p      = mannwhitneyu(wt_vals, mud_vals, alternative="two-sided")
            rows.append({
                "feature":    col,
                "metric":     label,
                "dim":        dim,
                "wt_mean":    wt_mean,
                "mudmut_mean":mud_mean,
                "fold_change":fc,
                "p_mwu":      p,
                "p_mwu_fmt":  _fmt_p(p),
            })
    return pd.DataFrame(rows)
```

- [ ] **Step 2: Add test for fold-change correctness**

Add to `tests/test_supp_2d_vs_3d_metrics.py`:

```python
def test_build_table_fold_change():
    """Fold-change should be mudmut_mean / wt_mean."""
    import sys
    sys.path.insert(0, str(Path("scripts")))
    from make_supp_2d_vs_3d_metrics import load_2d_metrics, load_3d_metrics, build_table

    df2d = load_2d_metrics(PROC_DIR)
    df3d = load_3d_metrics(PROC_DIR)
    tbl = build_table(df2d, df3d)

    row = tbl[(tbl["feature"] == "n_dpn") & (tbl["dim"] == "2D")].iloc[0]
    expected_fc = row["mudmut_mean"] / row["wt_mean"]
    assert abs(row["fold_change"] - expected_fc) < 1e-10
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_supp_2d_vs_3d_metrics.py -v
```

Expected: 5 tests pass.

- [ ] **Step 4: Commit**

```bash
git add scripts/make_supp_2d_vs_3d_metrics.py tests/test_supp_2d_vs_3d_metrics.py
git commit -m "feat: add build_table with fold-changes and MWU p-values"
```

---

## Task 5: Build per-genotype histogram panel (shared function)

**Files:**
- Modify: `scripts/make_supp_2d_vs_3d_metrics.py`

Each figure shows one genotype's 5 metrics. For each metric subplot: 2D distribution (solid fill) vs 3D distribution (hatched outline), both in fold-change from that representation's own WT mean. This puts 2D and 3D on the same scale (1.0 = WT level in each representation) despite having different raw units (µm² vs µm³).

Color encodes representation: `DIM2D_COLOR` (filled) for 2D, `DIM3D_COLOR` (hatched) for 3D.

- [ ] **Step 1: Add color constants and `make_genotype_histogram_panel()` function**

Add to the constants block:

```python
DIM2D_COLOR = "#4C72B0"   # 2D representation (filled)
DIM3D_COLOR = "#DD8452"   # 3D representation (hatched)
```

Add the figure function:

```python
def make_genotype_histogram_panel(
    df_2d: pd.DataFrame,
    df_3d: pd.DataFrame,
    genotype: str,
) -> plt.Figure:
    metric_cols = ["n_dpn", "dpn_area", "avg_dpn_area", "lin_area", "n_pros"]
    metric_titles = [
        "# neuroblasts\n(dpn)",
        "total NB\narea / volume",
        "avg NB area /\nvolume per cell",
        "lineage\narea / volume",
        "# non-neuroblasts\n(pros)",
    ]
    label = "WT" if genotype == "wt" else "mudmut"

    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    fig.suptitle(f"{label} lineages: 2D vs 3D representations", fontsize=FONT_SIZE_TITLE)

    for ax, col, title in zip(axes, metric_cols, metric_titles):
        wt_mean_2d = df_2d.loc[df_2d["genotype"] == "wt", col].mean()
        wt_mean_3d = df_3d.loc[df_3d["genotype"] == "wt", col].mean()

        vals_2d = (df_2d.loc[df_2d["genotype"] == genotype, col] / wt_mean_2d).values
        vals_3d = (df_3d.loc[df_3d["genotype"] == genotype, col] / wt_mean_3d).values

        all_vals = np.concatenate([vals_2d, vals_3d])
        lo, hi   = np.nanpercentile(all_vals, 2), np.nanpercentile(all_vals, 98)
        bins     = np.linspace(lo, hi, 20)

        ax.hist(vals_2d, bins=bins, alpha=0.5, color=DIM2D_COLOR, edgecolor=DIM2D_COLOR,
                linewidth=1.2, label="2D", density=True)
        ax.hist(vals_3d, bins=bins, alpha=0.0, color=DIM3D_COLOR, edgecolor=DIM3D_COLOR,
                linewidth=1.5, hatch="///", label="3D", density=True)

        ax.axvline(1.0, color="gray", linestyle="--", linewidth=1.0)
        ax.set_xlabel("fold-change from WT mean", fontsize=FONT_SIZE_LABEL - 2)
        ax.set_title(title, fontsize=FONT_SIZE_LABEL)
        ax.set_ylabel("density" if ax is axes[0] else "", fontsize=FONT_SIZE_LABEL - 2)

    handles = [
        plt.Rectangle((0,0),1,1, fc=DIM2D_COLOR, alpha=0.5, label="2D (area, µm²)"),
        plt.Rectangle((0,0),1,1, fc="none", ec=DIM3D_COLOR, hatch="///", linewidth=1.5, label="3D (volume, µm³)"),
    ]
    axes[-1].legend(handles=handles, loc="upper right", fontsize=FONT_SIZE_LABEL - 3, frameon=False)

    fig.tight_layout()
    return fig
```

- [ ] **Step 2: Run manually to verify both genotype figures render**

```bash
uv run python -c "
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from make_supp_2d_vs_3d_metrics import load_2d_metrics, load_3d_metrics, make_genotype_histogram_panel
df2 = load_2d_metrics(Path('data/exp/processed'))
df3 = load_3d_metrics(Path('data/exp/processed'))
make_genotype_histogram_panel(df2, df3, 'wt').savefig('/tmp/test_wt.pdf')
make_genotype_histogram_panel(df2, df3, 'mudmut').savefig('/tmp/test_mud.pdf')
print('saved ok')
"
```

Expected: prints "saved ok".

- [ ] **Step 3: Commit**

```bash
git add scripts/make_supp_2d_vs_3d_metrics.py
git commit -m "feat: add per-genotype 2D vs 3D histogram panel function"
```

---

## Task 6: Wire up `main()`, print table, save outputs

**Files:**
- Modify: `scripts/make_supp_2d_vs_3d_metrics.py`

- [ ] **Step 1: Add `print_table()` helper and `main()`**

```python
def print_table(tbl: pd.DataFrame) -> None:
    pivot_rows = []
    for feat in ["n_dpn", "dpn_area", "avg_dpn_area", "lin_area", "n_pros"]:
        r2 = tbl[(tbl["feature"] == feat) & (tbl["dim"] == "2D")].iloc[0]
        r3 = tbl[(tbl["feature"] == feat) & (tbl["dim"] == "3D")].iloc[0]
        pivot_rows.append({
            "Feature":          feat,
            "Biological metric":r2["metric"],
            "WT mean (2D)":     f"{r2['wt_mean']:.2f}",
            "mudmut mean (2D)": f"{r2['mudmut_mean']:.2f}",
            "FC (2D)":          f"{r2['fold_change']:.2f}×",
            "p (MWU) 2D":       r2["p_mwu_fmt"],
            "WT mean (3D)":     f"{r3['wt_mean']:.2f}",
            "mudmut mean (3D)": f"{r3['mudmut_mean']:.2f}",
            "FC (3D)":          f"{r3['fold_change']:.2f}×",
            "p (MWU) 3D":       r3["p_mwu_fmt"],
        })
    df_out = pd.DataFrame(pivot_rows)
    print(df_out.to_string(index=False))


def main() -> None:
    print("Loading 2D metrics …")
    df_2d = load_2d_metrics(PROC_DIR)
    print("Loading 3D metrics (trimesh volumes) …")
    df_3d = load_3d_metrics(PROC_DIR)

    tbl = build_table(df_2d, df_3d)
    print_table(tbl)

    csv_path = FIG_DIR / "figS_2d_vs_3d_metrics_table.csv"
    tbl.to_csv(csv_path, index=False)
    print(f"Table saved to {csv_path}")

    for genotype, stem in [("wt", "figS_2d_vs_3d_wt_panel"), ("mudmut", "figS_2d_vs_3d_mudmut_panel")]:
        fig = make_genotype_histogram_panel(df_2d, df_3d, genotype)
        for ext in ("pdf", "png"):
            out = FIG_DIR / f"{stem}.{ext}"
            fig.savefig(out, bbox_inches="tight")
            print(f"Figure saved to {out}")
        plt.close(fig)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full script end-to-end**

```bash
uv run python scripts/make_supp_2d_vs_3d_metrics.py
```

Expected: table printed to stdout (check fold-change directions: n_dpn ~+1.8×, dpn_area ~0.5×, avg_dpn_area ~0.35×, lin_area ~0.7×, n_pros ~0.75×), then four figure files saved under `docs/tex_draft/figures/`.

- [ ] **Step 3: Visually inspect both output figures**

Open `docs/tex_draft/figures/figS_2d_vs_3d_wt_panel.pdf`:
- WT 2D and WT 3D distributions should overlap closely (both centered near 1.0 by construction, but spreads may differ)
- No empty panels, no axis overflow

Open `docs/tex_draft/figures/figS_2d_vs_3d_mudmut_panel.pdf`:
- Both 2D and 3D mudmut peaks should be shifted from 1.0 in the same direction (e.g. dpn_area below 1.0 for both; n_dpn above 1.0 for both)
- The fold-changes should be numerically consistent with the printed table

- [ ] **Step 4: Commit final script**

```bash
git add scripts/make_supp_2d_vs_3d_metrics.py
git commit -m "feat: complete supp 2d-vs-3d metrics script with table and per-genotype histogram panels"
```

---

## Self-review checklist

- [x] **Spec coverage:** 5 metrics × 2 dimensions × {table, WT histogram figure, mudmut histogram figure} — all spec items have a corresponding task.
- [x] **No placeholders:** Every step has complete code.
- [x] **Type consistency:** `load_2d_metrics` and `load_3d_metrics` both return DataFrames with the same columns (`lineage_id, genotype, n_dpn, dpn_area, avg_dpn_area, lin_area, n_pros`) — `build_table` and `make_genotype_histogram_panel` expect exactly those column names.
- [x] **Normalization:** `make_genotype_histogram_panel` divides 2D values by WT 2D mean and 3D values by WT 3D mean separately — each representation normalized by its own WT reference so fold-change is internally consistent.
- [x] **Only wt/mudmut:** `GENOTYPES = ["wt", "mudmut"]` filter applied in both loaders.
- [x] **Lineage scope:** `load_3d_metrics` reads from `lineage_index.csv` which only contains kept lineages, so rejected lineages are automatically excluded.
- [x] **trimesh `process=False`:** Passes `process=False` to avoid trimesh silently modifying mesh topology; `abs()` handles sign convention.
