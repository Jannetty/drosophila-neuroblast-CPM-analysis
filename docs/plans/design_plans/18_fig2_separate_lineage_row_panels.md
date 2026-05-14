# Design: Figure 2 — Separate Per-Row Lineage Panels

**Date:** 2026-05-14

## Overview

Split the four lineage example rows in `figure2_wt_geometry_examples_panel` into four individual figures (one per row), generated automatically as part of `make fig2`. The combined panel continues to exist unchanged for embedding in `fig2.svg`. Individual figures get better proportions and more breathing room between the row subtitle and the column-level condition titles.

## Section 1 — Function change

**File:** `docs/tex_draft/figure12_paper_figures.ipynb` (cell 11, `make_figure2_lineages_panel`)

Add parameter:
```python
def make_figure2_lineages_panel(rows: list[str] | None = None) -> tuple[plt.Figure, list[list[plt.Axes]]]:
```

- When `rows=None`: behavior unchanged — all 4 rows, `figsize=(17.0, 26.0)`, `subplots_adjust(top=0.985, bottom=0.055, left=0.055, right=0.992)`, title/subtitle placed at `bbox.y1 + 0.040` / `bbox.y1 + 0.035`.
- When `rows` is a 1-element list: filter `FIG2_LINEAGE_ROWS` to matching entries, switch to:
  - `figsize=(17.0, 7.0)`
  - `subplots_adjust(top=0.78, bottom=0.08, left=0.055, right=0.992)`
  - Title placed at `y=0.97` (figure coords, `va="bottom"`, `fontsize=26`, bold)
  - Subtitle placed at `y=0.86` (`va="top"`, `fontsize=18`)
  - This leaves a clear vertical band from `y=0.86` (subtitle bottom) to `y=0.78` (axes top) before the column titles begin — providing the requested breathing room between row subtitle and per-column condition labels.

## Section 2 — New output files

Four new PNG+PDF pairs saved in `docs/tex_draft/figures/`, generated unconditionally each notebook run:

| Row | Filename |
|---|---|
| Apical axis reorientation | `figure2_wt_lineage_apical_panel.{png,pdf}` |
| Spindle orientation range | `figure2_wt_lineage_spindle_panel.{png,pdf}` |
| Offset shift | `figure2_wt_lineage_offset_panel.{png,pdf}` |
| Differentiation rule | `figure2_wt_lineage_diff_panel.{png,pdf}` |

The existing `figure2_wt_geometry_examples_panel.{png,pdf}` continues to be generated unchanged (no-arg call to `make_figure2_lineages_panel()`).

## Section 3 — Notebook call site

At the bottom of cell 11, after the existing combined-panel save block, add:

```python
_FIG2_ROW_SLUGS = [
    ("Apical axis reorientation", "apical"),
    ("Spindle orientation range", "spindle"),
    ("Offset shift",              "offset"),
    ("Differentiation rule",      "diff"),
]
for _row_title, _slug in _FIG2_ROW_SLUGS:
    _row_fig, _ = make_figure2_lineages_panel(rows=[_row_title])
    _png = FIG_DIR / f"figure2_wt_lineage_{_slug}_panel.png"
    _pdf = FIG_DIR / f"figure2_wt_lineage_{_slug}_panel.pdf"
    _row_fig.savefig(_png, bbox_inches="tight", facecolor="white")
    _row_fig.savefig(_pdf, bbox_inches="tight", facecolor="white")
    plt.close(_row_fig)
    print(f"Saved: {_png}")
```

## Section 4 — Makefile

No change required. `make fig2` already re-executes the full notebook via `$(UV_NB)`, so the 4 new saves become default output automatically.

## Testing

- Run `make fig2` (or just execute cell 11 in the notebook).
- Verify 8 new files appear in `docs/tex_draft/figures/` (`figure2_wt_lineage_{apical,spindle,offset,diff}_panel.{png,pdf}`).
- Verify the combined `figure2_wt_geometry_examples_panel.png` is unchanged.
- Visually check each individual panel: title at top, subtitle below it, clear gap before column condition labels, images properly sized at ~17×7 in.
