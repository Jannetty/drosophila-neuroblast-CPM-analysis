# Figure 2 Separate Lineage Row Panels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `make_figure2_lineages_panel()` so it can produce either the existing combined 4-row figure or a standalone single-row figure for each of the four decoupling rows, with both modes generated automatically on every `make fig2` run.

**Architecture:** Add a `rows: list[str] | None = None` parameter to `make_figure2_lineages_panel()` in notebook cell 11. When `rows` is given, filter `FIG2_LINEAGE_ROWS` to matching entries and use a shorter per-row layout (`figsize=(17.0, 7.0)`, `top=0.78`) that places the row title at `y=0.97` and subtitle at `y=0.86`, leaving a clear band above the axes before the per-column condition labels begin. Then add four unconditional save calls after the existing combined-panel save block.

**Tech Stack:** Python, matplotlib, Jupyter notebook (`nbformat` JSON), `NotebookEdit` tool for in-place cell editing.

---

## File map

| File | Change |
|---|---|
| `docs/tex_draft/figure12_paper_figures.ipynb` cell 11 | Modify function signature + layout logic; add per-row save calls |

No other files change. The Makefile already re-executes the notebook via `$(UV_NB)`, so `make fig2` picks up the new outputs automatically.

---

### Task 1: Add `rows` parameter and single-row layout to `make_figure2_lineages_panel()`

**Files:**
- Modify: `docs/tex_draft/figure12_paper_figures.ipynb` (cell 11)

- [ ] **Step 1: Locate the function signature and opening lines in the notebook**

  Cell 11 currently begins with:
  ```python
  def make_figure2_lineages_panel() -> tuple[plt.Figure, list[list[plt.Axes]]]:
      fig = plt.figure(figsize=(17.0, 26.0))
      outer = fig.add_gridspec(len(FIG2_LINEAGE_ROWS), 1, hspace=0.70)
      row_axes: list[list[plt.Axes]] = []

      for row_idx, (row_title, row_subtitle, conditions) in enumerate(FIG2_LINEAGE_ROWS):
  ```

  Use `NotebookEdit` on `docs/tex_draft/figure12_paper_figures.ipynb`, cell index 11, replacing those lines with:
  ```python
  def make_figure2_lineages_panel(rows: list[str] | None = None) -> tuple[plt.Figure, list[list[plt.Axes]]]:
      active_rows = [r for r in FIG2_LINEAGE_ROWS if r[0] in rows] if rows is not None else FIG2_LINEAGE_ROWS
      single_row = len(active_rows) == 1
      fig = plt.figure(figsize=(17.0, 7.0) if single_row else (17.0, 26.0))
      outer = fig.add_gridspec(len(active_rows), 1, hspace=0.70)
      row_axes: list[list[plt.Axes]] = []

      for row_idx, (row_title, row_subtitle, conditions) in enumerate(active_rows):
  ```

- [ ] **Step 2: Locate the `subplots_adjust` + `fig.text` block at the end of the function**

  Currently:
  ```python
      fig.subplots_adjust(left=0.055, right=0.992, top=0.985, bottom=0.055)
      for (row_title, row_subtitle, _), axes in zip(FIG2_LINEAGE_ROWS, row_axes):
          bbox = axes[0].get_position()
          fig.text(
              0.015,
              bbox.y1 + 0.040,
              row_title,
              fontsize=26,
              fontweight="bold",
              ha="left",
              va="bottom",
          )
          fig.text(
              0.015,
              bbox.y1 + 0.035,
              row_subtitle,
              fontsize=18,
              ha="left",
              va="top",
          )
      return fig, row_axes
  ```

  Replace with:
  ```python
      if single_row:
          fig.subplots_adjust(left=0.055, right=0.992, top=0.78, bottom=0.08)
          for (row_title, row_subtitle, _), axes in zip(active_rows, row_axes):
              fig.text(0.015, 0.97, row_title, fontsize=26, fontweight="bold", ha="left", va="bottom")
              fig.text(0.015, 0.86, row_subtitle, fontsize=18, ha="left", va="top")
      else:
          fig.subplots_adjust(left=0.055, right=0.992, top=0.985, bottom=0.055)
          for (row_title, row_subtitle, _), axes in zip(active_rows, row_axes):
              bbox = axes[0].get_position()
              fig.text(
                  0.015,
                  bbox.y1 + 0.040,
                  row_title,
                  fontsize=26,
                  fontweight="bold",
                  ha="left",
                  va="bottom",
              )
              fig.text(
                  0.015,
                  bbox.y1 + 0.035,
                  row_subtitle,
                  fontsize=18,
                  ha="left",
                  va="top",
              )
      return fig, row_axes
  ```

- [ ] **Step 3: Verify the cell parses cleanly**

  Run:
  ```bash
  uv run python -c "
  import json
  with open('docs/tex_draft/figure12_paper_figures.ipynb') as f:
      nb = json.load(f)
  src = ''.join(nb['cells'][11]['source'])
  compile(src, '<cell11>', 'exec')
  print('OK')
  "
  ```
  Expected output: `OK`

---

### Task 2: Add per-row save calls after the combined-panel save block

**Files:**
- Modify: `docs/tex_draft/figure12_paper_figures.ipynb` (cell 11)

- [ ] **Step 1: Locate the existing combined-panel save block**

  The block to append after currently ends with:
  ```python
  print(f"Saved: {figure2_examples_png}")
  print(f"Saved: {figure2_examples_pdf}")
  plt.show()
  ```

  Use `NotebookEdit` to replace that trailing `plt.show()` line with:
  ```python
  print(f"Saved: {figure2_examples_png}")
  print(f"Saved: {figure2_examples_pdf}")
  plt.show()

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

- [ ] **Step 2: Verify the cell parses cleanly again**

  Run:
  ```bash
  uv run python -c "
  import json
  with open('docs/tex_draft/figure12_paper_figures.ipynb') as f:
      nb = json.load(f)
  src = ''.join(nb['cells'][11]['source'])
  compile(src, '<cell11>', 'exec')
  print('OK')
  "
  ```
  Expected output: `OK`

---

### Task 3: Run the notebook and verify outputs

**Files:**
- Run: `docs/tex_draft/figure12_paper_figures.ipynb`

- [ ] **Step 1: Execute the notebook**

  Run:
  ```bash
  uv run jupyter nbconvert --to notebook --execute --inplace docs/tex_draft/figure12_paper_figures.ipynb
  ```
  Expected: exits 0. Last few lines of output should include:
  ```
  Saved: .../figures/figure2_wt_lineage_apical_panel.png
  Saved: .../figures/figure2_wt_lineage_spindle_panel.png
  Saved: .../figures/figure2_wt_lineage_offset_panel.png
  Saved: .../figures/figure2_wt_lineage_diff_panel.png
  ```

- [ ] **Step 2: Verify all 8 new files exist**

  Run:
  ```bash
  ls docs/tex_draft/figures/figure2_wt_lineage_*_panel.{png,pdf}
  ```
  Expected: 8 files —
  ```
  docs/tex_draft/figures/figure2_wt_lineage_apical_panel.pdf
  docs/tex_draft/figures/figure2_wt_lineage_apical_panel.png
  docs/tex_draft/figures/figure2_wt_lineage_diff_panel.pdf
  docs/tex_draft/figures/figure2_wt_lineage_diff_panel.png
  docs/tex_draft/figures/figure2_wt_lineage_offset_panel.pdf
  docs/tex_draft/figures/figure2_wt_lineage_offset_panel.png
  docs/tex_draft/figures/figure2_wt_lineage_spindle_panel.pdf
  docs/tex_draft/figures/figure2_wt_lineage_spindle_panel.png
  ```

- [ ] **Step 3: Verify the combined panel still exists and is fresh**

  Run:
  ```bash
  ls -lh docs/tex_draft/figures/figure2_wt_geometry_examples_panel.png
  ```
  Expected: file exists with a recent modification timestamp.

- [ ] **Step 4: Visual check of individual panels**

  Open each PNG in a viewer. For each:
  - Figure dimensions look roughly landscape (~17×7 in proportion, not tall)
  - Bold row title at the very top of the figure
  - Smaller parameter subtitle below it, with a clear gap before the column condition labels (e.g. "Base", "mean = 0")
  - Images sized appropriately with scale bars visible

- [ ] **Step 5: Commit**

  ```bash
  git add docs/tex_draft/figure12_paper_figures.ipynb \
          docs/tex_draft/figures/figure2_wt_lineage_apical_panel.png \
          docs/tex_draft/figures/figure2_wt_lineage_apical_panel.pdf \
          docs/tex_draft/figures/figure2_wt_lineage_spindle_panel.png \
          docs/tex_draft/figures/figure2_wt_lineage_spindle_panel.pdf \
          docs/tex_draft/figures/figure2_wt_lineage_offset_panel.png \
          docs/tex_draft/figures/figure2_wt_lineage_offset_panel.pdf \
          docs/tex_draft/figures/figure2_wt_lineage_diff_panel.png \
          docs/tex_draft/figures/figure2_wt_lineage_diff_panel.pdf \
          docs/plans/design_plans/18_fig2_separate_lineage_row_panels.md \
          docs/plans/implementation_plans/18_fig2_separate_lineage_row_panels.md
  git commit -m "feat: add per-row lineage panels for fig2; rows parameter on make_figure2_lineages_panel"
  ```
