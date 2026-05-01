# Implementation Plan: Heterotypic Contact Fraction

Implements the analysis described in
`docs/plans/analysis/2026-04-27-heterotypic-contact-fraction-design.md`.

---

## Scope

Add heterotypic contact fraction computation and charts to:

- `notebooks/div26_systematic_analysis.ipynb`

No changes to `src/` or `scripts/`. All new code lives in notebook cells.

---

## Cells to add / modify

| Cell ID | Action | Location |
|---|---|---|
| `s0-helpers` | add `heterotypic_contact_fraction` function | existing cell, append |
| `s-het-compute` | new code cell | after `s1b-output` |
| `s-het-chart-hdr` | new markdown cell | after `s-het-compute` |
| `s-het-chart-a` | new code cell — Figure A (by angle condition) | after header |
| `s-het-chart-b` | new code cell — Figure B (facet by regulatory dynamic) | after Figure A |

---

## Step 1 — Add `heterotypic_contact_fraction` to `s0-helpers`

Append the following function to the end of the `s0-helpers` cell.

```python
def heterotypic_contact_fraction(geo):
    """
    Compute het_frac and norm_het_frac from a (H, W, 2) geo tensor.
    Channel 0 = NB (pop1). Channel 1 = non-NB (pop2 + pop3).
    Returns dict with keys: het_frac, norm_het_frac, p_nb, p_nonnb, n_occupied.
    norm_het_frac = het_frac / (2 * p_nb * p_nonnb); NaN if only one type present.
    """
    nb    = geo[..., 0] > 0
    nonnb = geo[..., 1] > 0
    occ   = nb | nonnb

    n_occ = int(occ.sum())
    if n_occ == 0:
        return dict(het_frac=np.nan, norm_het_frac=np.nan,
                    p_nb=np.nan, p_nonnb=np.nan, n_occupied=0)

    p_nb_val    = float(nb[occ].mean())
    p_nonnb_val = float(nonnb[occ].mean())

    # horizontal contacts: pixel (i,j) vs (i,j+1)
    both_h = occ[:, :-1] & occ[:, 1:]
    het_h  = both_h & (nb[:, :-1] ^ nb[:, 1:])   # XOR: one NB, one not

    # vertical contacts: pixel (i,j) vs (i+1,j)
    both_v = occ[:-1, :] & occ[1:, :]
    het_v  = both_v & (nb[:-1, :] ^ nb[1:, :])

    total = int(both_h.sum()) + int(both_v.sum())
    het   = int(het_h.sum())  + int(het_v.sum())

    if total == 0:
        return dict(het_frac=np.nan, norm_het_frac=np.nan,
                    p_nb=p_nb_val, p_nonnb=p_nonnb_val, n_occupied=n_occ)

    hf       = het / total
    expected = 2.0 * p_nb_val * p_nonnb_val
    norm_hf  = (hf / expected) if expected > 0 else np.nan

    return dict(het_frac=hf, norm_het_frac=norm_hf,
                p_nb=p_nb_val, p_nonnb=p_nonnb_val, n_occupied=n_occ)
```

---

## Step 2 — Add compute cell `s-het-compute`

Insert a new code cell with `id = "s-het-compute"` immediately after
`s1b-output`.

The cell loads every geo tensor from every NPZ (WT and mudmut, both VCV modes),
computes `heterotypic_contact_fraction`, and builds `het_df`. Results are cached
to CSV so the NPZ loop does not re-run on every kernel restart.

```python
# ── Heterotypic contact fraction — compute for all conditions / VCVs ─────────
_HET_CSV = REPO_ROOT / 'data/sim/processed_div26/het_contact_metrics.csv'

if _HET_CSV.exists():
    het_df = pd.read_csv(_HET_CSV)
    print(f'Loaded cached het_contact_metrics.csv ({len(het_df)} rows)')
else:
    _sim_id_meta = (
        sim[['sim_id', 'regulatory_dynamic', 'critical_volume_mode', 'genotype']]
        .drop_duplicates('sim_id')
        .set_index('sim_id')
    )

    het_records = []
    for npz_path_str, group in run_idx.groupby('npz_path'):
        npz_path = REPO_ROOT / npz_path_str
        with np.load(npz_path) as _data:
            _geo_all = _data['geo']
        for _, row in group.iterrows():
            geo_i  = _geo_all[int(row['npz_row'])]
            result = heterotypic_contact_fraction(geo_i)
            het_records.append({
                'condition': row['condition'],
                'sim_id':    row['sim_id'],
                'run_id':    row['run_id'],
                **result,
            })

    het_df = pd.DataFrame(het_records)
    het_df = het_df.join(_sim_id_meta, on='sim_id')

    _cond_to_tag = {v: k for k, v in mm_cond_df['condition'].items()}
    het_df['tag'] = het_df['condition'].map(_cond_to_tag)  # NaN for WT rows

    het_df.to_csv(_HET_CSV, index=False)
    print(f'Computed and saved het_contact_metrics.csv ({len(het_df)} rows)')

# summary table
_summary = (
    het_df
    .groupby(['genotype', 'tag', 'critical_volume_mode'])['norm_het_frac']
    .agg(['mean', 'std'])
    .round(3)
)
print()
print(_summary.to_string())
```

---

## Step 3 — Add section header markdown `s-het-chart-hdr`

Insert a new markdown cell with `id = "s-het-chart-hdr"` after `s-het-compute`.

```markdown
---
## Section: Heterotypic Contact Fraction

**Question:** Do rotation distributions affect how intermixed NB and non-NB
cells are, independently of lineage size and composition?

**Metric:** `norm_het_frac = het_frac / (2 × p_NB × p_nonNB)`.
Values > 1 = more mixed than random; < 1 = segregated; = 1 = random mixing.
Reference line at y = 1 (random baseline). WT mean shown as dotted reference.

Only accepted mudmut conditions are shown. WT conditions appear as reference
lines only (mean across all WT runs, one per VCV mode).
```

---

## Step 4 — Add Figure A cell `s-het-chart-a`

Grouped box plot: one pair of boxes per accepted mudmut tag (VCV=1 solid,
VCV=0 hatched). X-axis ordered by `(div_mean, rot_stdev, rot_mean)`.

```python
# ── Figure A: norm_het_frac by angle condition ────────────────────────────────
het_mm = het_df[het_df['tag'].isin(accepted_mm_tags)].copy()
het_wt = het_df[het_df['genotype'] == 'wt']

wt_refs = het_wt.groupby('critical_volume_mode')['norm_het_frac'].mean()

tags_ordered = sorted(
    accepted_mm_tags,
    key=lambda t: (mm_cond_df.loc[t, 'div_mean'],
                   mm_cond_df.loc[t, 'rot_stdev'],
                   mm_cond_df.loc[t, 'rot_mean']),
)

n_tags     = len(tags_ordered)
box_w      = 0.14
inner_step = 0.18
offsets    = np.array([-inner_step / 2, inner_step / 2])  # VCV=0, VCV=1

fig, ax = plt.subplots(figsize=(max(10, n_tags * 1.8), 5))
ax.axhline(1.0, color='gray', linestyle='--', linewidth=1.2, zorder=1)

for vcv_idx, (vcv, sim_ids) in enumerate([(0, MM_VCV0_IDS), (1, MM_VCV1_IDS)]):
    for ti, tag in enumerate(tags_ordered):
        runs = het_mm[
            (het_mm['tag'] == tag) &
            (het_mm['critical_volume_mode'] == vcv)
        ]['norm_het_frac'].dropna()
        if runs.empty:
            continue
        x  = ti + offsets[vcv_idx]
        bp = ax.boxplot(
            [runs],
            positions=[x],
            widths=box_w,
            patch_artist=True,
            medianprops={'color': 'black', 'linewidth': 1.2},
            whiskerprops={'linewidth': 0.7},
            capprops={'linewidth': 0.7},
            flierprops={'marker': 'o', 'markersize': 1.5, 'linestyle': 'none'},
            manage_ticks=False,
            zorder=2,
        )
        bp['boxes'][0].set_facecolor(MM_COND_COLORS.get(tag, '#cccccc'))
        bp['boxes'][0].set_alpha(0.8)
        if vcv == 0:
            bp['boxes'][0].set_hatch('///')
        med       = float(np.median(runs))
        upper_cap = bp['caps'][1].get_ydata()[0]
        ax.text(x, upper_cap + 0.005, f'{med:.2f}',
                ha='center', va='bottom', fontsize=5, rotation=90)

for vcv, line_style in [(0, ':'), (1, '--')]:
    if vcv in wt_refs.index:
        ax.axhline(wt_refs[vcv], color='black', linestyle=line_style,
                   linewidth=1, label=f'WT mean VCV={vcv}')

ax.set_xticks(list(range(n_tags)))
ax.set_xticklabels(tags_ordered, rotation=45, ha='right', fontsize=8)
ax.set_ylabel('norm_het_frac')
ax.set_title('Heterotypic contact fraction (normalised) — mudmut by angle condition')
ax.grid(axis='y', alpha=0.3)

legend_handles = [
    Line2D([0], [0], color='gray', linestyle='--', label='random mixing (y=1)'),
    Line2D([0], [0], color='black', linestyle=':', label='WT mean VCV=0'),
    Line2D([0], [0], color='black', linestyle='--', label='WT mean VCV=1'),
] + [
    Patch(facecolor=MM_COND_COLORS.get(t, '#ccc'), alpha=0.8, label=f'{t} VCV=1')
    for t in tags_ordered
] + [
    Patch(facecolor=MM_COND_COLORS.get(t, '#ccc'), alpha=0.8, hatch='///',
          label=f'{t} VCV=0')
    for t in tags_ordered
]
ax.legend(handles=legend_handles, fontsize=6, loc='upper right', ncol=3)
plt.tight_layout()
fig.savefig(FIGURES_DIR / 'het_contact_by_condition.png', dpi=120, bbox_inches='tight')
plt.show()
```

---

## Step 5 — Add Figure B cell `s-het-chart-b`

2-row × 5-column facet grid by regulatory dynamic. Same layout as
`mudmut_facet_chart`. Y-axis = `norm_het_frac`.

```python
# ── Figure B: norm_het_frac faceted by regulatory dynamic ────────────────────
positions = list(range(len(tags_ordered)))

fig, axes = plt.subplots(2, len(REG_DYN_ORDER), figsize=(24, 8), sharey=True)

for ri, vcv in enumerate([0, 1]):
    for ci, reg_dyn in enumerate(REG_DYN_ORDER):
        ax = axes[ri, ci]
        ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, zorder=1)

        panel = het_mm[
            (het_mm['critical_volume_mode'] == vcv) &
            (het_mm['regulatory_dynamic']   == reg_dyn)
        ]

        data_by_tag = []
        for tag in tags_ordered:
            runs = panel[panel['tag'] == tag]['norm_het_frac'].dropna()
            data_by_tag.append(runs if not runs.empty else np.array([np.nan]))

        if all(np.all(np.isnan(d)) for d in data_by_tag):
            ax.set_visible(False)
            continue

        bp = ax.boxplot(
            data_by_tag,
            positions=positions,
            widths=0.6,
            patch_artist=True,
            medianprops={'color': 'black', 'linewidth': 1.5},
            whiskerprops={'linewidth': 0.8},
            capprops={'linewidth': 0.8},
            flierprops={'marker': 'o', 'markersize': 2, 'linestyle': 'none'},
            zorder=2,
        )
        for patch, tag in zip(bp['boxes'], tags_ordered):
            patch.set_facecolor(MM_COND_COLORS.get(tag, '#cccccc'))
            patch.set_alpha(0.75)

        for xi, (tag, d) in enumerate(zip(tags_ordered, data_by_tag)):
            if np.all(np.isnan(d)):
                continue
            med       = float(np.nanmedian(d))
            upper_cap = bp['caps'][2 * xi + 1].get_ydata()[0]
            ax.text(xi, upper_cap + 0.01, f'{med:.2f}',
                    ha='center', va='bottom', fontsize=5, rotation=90)

        ax.set_xticks(positions)
        ax.set_xticklabels(tags_ordered, rotation=45, ha='right', fontsize=6.5)
        ax.grid(axis='y', alpha=0.3)

        if ri == 0:
            ax.set_title(reg_dyn, fontsize=9, fontweight='bold')
        if ci == 0:
            ax.set_ylabel(f'VCV={vcv}\nnorm_het_frac', fontsize=8)

fig.suptitle('Heterotypic contact fraction (normalised) — by regulatory dynamic',
             fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES_DIR / 'het_contact_by_regdyn.png', dpi=120, bbox_inches='tight')
plt.show()
```

---

## Verification checklist

- [ ] `heterotypic_contact_fraction` returns `norm_het_frac` ≈ 1.0 for a
      checkerboard-pattern tensor (alternating NB / non-NB pixels).
- [ ] Returns `norm_het_frac` < 1 for a tensor with NB on the left half and
      non-NB on the right half (segregated).
- [ ] Returns `NaN` for a tensor containing only NB pixels (no non-NB).
- [ ] `s-het-compute` cache logic: deleting the CSV and re-running produces the
      same `het_df` as loading the cached version.
- [ ] Figure A renders one pair of boxes per accepted tag with correct hatch
      for VCV=0.
- [ ] Figure B renders without blank axes when all conditions are accepted.
