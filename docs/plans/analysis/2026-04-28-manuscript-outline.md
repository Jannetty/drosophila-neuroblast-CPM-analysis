# Manuscript Outline — neurogen-plane-rotation-analysis / ARCADE

## Working premise

This paper should read as a mechanistic modeling paper grounded in experimental morphology, not as a claim that the model has uniquely identified the real biological regulator. The safest version of the central message is:

> In a calibrated CPM of developing *Drosophila* neuroblast lineages, lineage morphology depends strongly on asymmetric division geometry and intergenerational axis persistence; mutant overgrowth can be constrained by volume-sensitive growth regulation only when division thresholds scale with birth size; and preferential NB-NB adhesion is not required to keep mutant neuroblasts adjacent.

Good candidate titles:

1. `Division geometry and size-dependent growth regulation shape developing Drosophila neuroblast lineages in a calibrated Cellular Potts model`
2. `A calibrated Cellular Potts model links asymmetric division geometry to neuroblast lineage morphology and mud mutant overgrowth control`
3. `How division geometry and size-dependent feedback shape wild-type and mud mutant neuroblast lineages`

## Figure rules

- Use color only in cartoons and lineage renderings.
- For lineage renderings, show cell-cell boundaries and lineage links between related cells.
- Use distinct colors for NB, GMC, and neuron in simulation lineage panels.
- Keep quantitative plots grayscale when possible, using line style, point shape, hatching, and panel layout instead of color.
- Important limitation: the processed experimental data in this repo separates Dpn-positive cells from Pros-positive progeny, not GMC vs neuron. Three-class lineage renderings are therefore straightforward for simulations, but not currently supported for experimental lineages unless another annotation layer exists.

## What is already supported vs what needs caution

### Strongly supported by current repo outputs

- WT calibration to endpoint WT metrics is in range.
- Persistent relative rotation drives loss of NB edge exposure and increased mixing.
- Moving the WT division offset toward 50/50 strongly disrupts sorted lineage morphology.
- Unregulated mudmut simulations massively overgrow.
- With `VOLUME_BASED_CRITICAL_VOLUME=0`, the candidate regulatory mechanisms do not adequately constrain mudmut overgrowth.
- With `VOLUME_BASED_CRITICAL_VOLUME=1`, volume-based regulation, especially the volume-PDE-like regime, can bring mudmut outputs near the experimental range.
- Removing preferential NB-NB adhesion changes mixing and NB exposure very little.

### Claims that need softer wording or extra support

- `Increasing variance around a fixed axis is not sufficient to drive unsorted morphologies` is too strong as written.
  Current decoupling summaries show:
  - baseline `wt_divMean0Stdev26`: `norm_het_frac ≈ 0.0229`, `exposed_frac ≈ 0.5891`
  - `stdev45`: `norm_het_frac ≈ 0.0266`, `exposed_frac ≈ 0.5220`
  - `stdev90`: `norm_het_frac ≈ 0.0497`, `exposed_frac ≈ 0.1056`
  A safer claim is that biologically sized variance increases appear modest, but extreme variance can still disrupt sorting.
- `Differential adhesion is not required to keep neuroblasts together` is directionally supported, but the current metrics are indirect.
  This would be much stronger with a direct NB clustering metric:
  - number of NB connected components
  - mean nearest-neighbor distance between NBs
  - fraction of runs in which all NBs remain in one cluster
- `Offset is crucial independently of lineage size` needs careful framing because the offset-50 perturbation changes daughter size and inflates lineage area. The normalized spatial metrics help, but we should explicitly acknowledge the size confound.

## Proposed paper shape

## Abstract skeleton

1. Asymmetric neuroblast division generates distinct daughter identities and reproducible lineage morphology, but it is unclear which geometric features of division are required for those outcomes.
2. We built a calibrated spatiotemporal CPM of WT and `mud` mutant *Drosophila* neuroblast lineages, constrained by experimental endpoint morphology and measured WT division-angle variability.
3. The model predicts that maintaining an asymmetric division offset and consistent relative orientation across generations is important for preserving NB edge localization, that unregulated `mud` lineages overgrow dramatically, and that volume-sensitive growth control can suppress that overgrowth only after rejecting a fixed-threshold sizer null hypothesis and allowing division thresholds to scale with birth size.
4. Preferential NB-NB adhesion is not necessary to reproduce NB adjacency in mutant lineages, suggesting that birth geometry and limited subsequent displacement may be sufficient.

## Introduction

### Paragraph 1 — biological motivation

- Introduce asymmetric cell division as a mechanism that simultaneously maintains stem cells and generates differentiated progeny.
- Tie this to developmental robustness and disorders of brain growth.
- Mention that neurogenesis is a useful system because geometry, size asymmetry, and fate asymmetry are tightly linked.

### Paragraph 2 — system

- Introduce the *Drosophila* larval brain neuroblast lineage:
  - NB self-renews
  - GMC is born basally
  - GMC divides once more to produce terminal progeny
- Make clear that WT lineages have a stereotyped morphology, including peripheral NB placement.

### Paragraph 3 — mutant perturbation and open questions

- Introduce `mud` mutants as a perturbation of spindle orientation / division plane.
- Explain the core biological ambiguity:
  - daughter fate is classically linked to basal determinant segregation
  - but geometry itself may influence differentiation dynamics and emergent lineage morphology
- State the unresolved questions:
  - How much do offset and rotational persistence matter for WT lineage morphology?
  - What kind of regulation is needed to prevent mutant overgrowth?
  - Is extra NB-NB adhesion necessary to keep mutant neuroblasts adjacent?

### Paragraph 4 — modeling approach and headline results

- Introduce the calibrated CPM as a way to isolate geometry, size control, and adhesion.
- End with a restrained summary of the three major findings.

## Results

### Result 1 — A calibrated CPM recapitulates expected WT lineage composition and scale

Key message:
The model is sufficiently calibrated to serve as a mechanistic testbed for spatial hypotheses.

What to say:

- Briefly define the WT rule set:
  - NB divides at `1.166x` initial size in the base calibration
  - default split offset is asymmetric (88% down apical axis from the top of the cell)
  - default WT division-angle variation is centered at zero with experimental-scale spread of stdev 26.
  - differentiation cascade: larger apical cell remains stem, smaller basal cell becomes GMC which divides symmetrically one more time when it has doubled in size to become two neurons. neurons do not grow or divide.
- Anchor calibration to the experimental WT summaries in `data/exp/processed/exp_summary.csv`.
- Cite the exact parameter documentation in methods (will be brought over from ARADE):
  - [PARAMETERS_EXPLAINED.md](/Users/skjannetty/bagherilab/ARCADE/PARAMETERS_EXPLAINED.md)
- Emphasize that endpoint non-spatial metrics were the calibration target, not a fit to the spatial readouts used later.

Suggested figure content:

- main-text figure, not supplement
- include both schema and WT calibration here so readers know the model before the perturbations start

Potential Figure 1:

- `A` cartoon of WT NB division and lineage progression
- `B` cartoon of modeled geometry: apical axis, offset division point, perpendicular plane, stochastic rotation
- `C` calibration plot comparing experimental WT and simulated WT for the five endpoint metrics
- `D` representative WT simulation lineage renderings
- `E` representative experimental WT lineage panel if it reads clearly enough

Existing assets to reuse:

- [sec1_wt_filter_lin_area_vox.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/sec1_wt_filter_lin_area_vox.png)
- [sec1_wt_filter_n_pros.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/sec1_wt_filter_n_pros.png)
- [sec1_wt_filter_n_dpn.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/sec1_wt_filter_n_dpn.png)

Potential supplement:

- histogram / density of the experimental WT division-angle measurements with fitted mean and SD
- calibration sweeps from ARCADE

### Result 2 — Intergenerational rotation bias and division offset shape WT lineage sorting

Key message:
WT lineage sorting is sensitive to the geometry of successive divisions, especially persistent relative rotation and daughter-size asymmetry.

Recommended subsection split:

#### 2A. Persistent relative rotation internalizes the NB

- Compare baseline WT to relative-rotation mean shifts.
- Use normalized heterotypic contact and NB exposure as primary spatial readouts.
- Phrase as a model prediction, not a direct biological proof.

#### 2B. Increased variance around a fixed axis has weaker effects at moderate levels, but extreme variance is still disruptive

- Do not claim “no effect.”
- Current data support:
  - `26 -> 45` gives a modest change
  - `26 -> 90` gives a strong change
- This is still interesting and actually sharper:
  moderate jitter is tolerated, but persistent bias or very large dispersion is not.

#### 2C. Moving the division offset toward 50/50 strongly alters lineage morphology

- This is where the offset result belongs.
- Explicitly state that offset changes both geometry and daughter size.
- Use normalized spatial metrics and matched-cell-count reasoning, but acknowledge that the perturbation is not a pure geometric perturbation.

Potential Figure 2:

- `A` lineage cartoon explaining the three decoupling manipulations:
  - relative rotation mean
  - fixed-axis variance
  - split offset
- `B` representative lineage renders for baseline, relrot45/90, stdev45/90, yoffset50
- `C` normalized heterotypic contact across conditions
- `D` NB exposure across conditions
- `E` composition control panel showing which perturbations also changed lineage size / cell count

Existing assets to reuse:

- [rotation_mean_relrot_lineages.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_decoupling/figures/rotation_mean_relrot_lineages.png)
- [stdev_sweep_lineages.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_decoupling/figures/stdev_sweep_lineages.png)
- [y-offset_lineages.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_decoupling/figures/y-offset_lineages.png)
- [norm_het_frac_decoupling.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_decoupling/figures/norm_het_frac_decoupling.png)
- [exposed_frac_decoupling.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_decoupling/figures/exposed_frac_decoupling.png)

Critical wording note:

- If we keep this as one result section, the narrative should be:
  - persistent mean rotation matters
  - observed-to-moderate stochastic variance matters less
  - extreme stochastic variance can still disrupt sorting
  - symmetricized division offset is also highly disruptive

### Result 3 — An unregulated mudmut model predicts severe lineage overgrowth

Key message:
Introducing mutant division geometry without added regulation is enough to produce large deviations from experimental mutant morphology.

What to say:

- Define the mudmut approximation carefully:
  - a subset of divisions become symmetric
  - daughter NBs inherit rotated apical axes from the parent
  - mutant lineages can accumulate multiple NBs
- This is the natural bridge from WT geometry to mutant growth control.

Potential Figure 3:

- `A` cartoon of the mudmut rule set and symmetric-division branch
- `B` representative unregulated mudmut lineages vs WT
- `C` endpoint metric comparison showing that unregulated mudmut exceeds both experimental mudmut and, in many cases, WT
- `D` highlight the two mutant-specific features motivating regulatory hypotheses:
  smaller NBs and increased NB number

Existing assets to reuse:

- [sec23_lin_area_vox.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/sec23_lin_area_vox.png)
- [sec23_n_pros.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/sec23_n_pros.png)
- [sec23_n_dpn.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/sec23_n_dpn.png)
- [single_cond_regulatory.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_div26/figures/analysis/single_cond_regulatory.png)

### Result 4 — Candidate regulatory dynamics behave as expected in WT but constrain mudmut growth only when division thresholds scale with birth size

Key message:
The key mechanistic distinction is not just the regulatory dynamic, but whether the cells are modeled as fixed-threshold sizers or as cells whose division thresholds depend on birth size. In the manuscript, `VCV=0` should be framed as a null-hypothesis test: could the smaller birth size of mutant NBs, and therefore the extra time needed to reach a shared absolute division threshold, already be sufficient to help constrain overgrowth?

Recommended subsection split:

#### 4A. WT sanity check

- All regulatory mechanisms leave WT broadly near the calibration target.
- This is a control, not a headline.

#### 4B. Under fixed critical volumes, candidate mechanisms do not sufficiently suppress mutant growth

- This is the negative result section.
- Explicit framing: `VCV=0` asks whether birth-size differences affect only interdivision time, not the division threshold itself.
- Motivate this as the simplest built-in growth brake available to mutant NBs:
  they are born smaller, so perhaps the added time required to reach a common absolute threshold could already limit expansion.
- Then show that this null hypothesis fails:
  even with candidate repressive dynamics, delaying growth to a fixed threshold is not enough to keep mudmut lineages in range.
- NB-contact regulation is especially worth showing because it almost works in some summary metrics but does not meet the target.

#### 4C. Under birth-size-dependent thresholds, volume-based regulation constrains mutant overgrowth

- This is the positive result section.
- Explicit framing: `VCV=1` asks whether birth-size differences also propagate into the next division threshold, so that smaller mutant NBs remain deeper in the repressive regime across generations.
- Volume-PDE-like likely deserves the strongest emphasis because it appears to be the cleanest match.

Potential Figure 4:

- `A` schematic contrasting `VCV=0` and `VCV=1`
- in caption/text, define the biological logic clearly:
  `VCV=0` = fixed-threshold sizer null hypothesis
  `VCV=1` = birth-size memory in the division threshold
- `B` grid of endpoint metrics by regulatory dynamic and VCV mode
- `C` representative lineages for:
  - unregulated mudmut
  - NB-contact regulation
  - volume-ABM
  - volume-PDE
- `D` direct comparison of the best-performing VCV0 vs VCV1 conditions against experimental mudmut bands

What would strengthen this figure a lot:

- time-course plots of lineage area, NB count, and mean NB size for the best-regulated and unregulated mutant conditions
- a panel showing why `VCV=1` changes behavior:
  e.g. NB size distributions over generations or division-threshold trajectories

### Result 5 — Preferential NB-NB adhesion is not required to maintain mutant NB adjacency

Key message:
Mutant NB proximity appears to emerge largely from birth geometry and limited subsequent displacement, not from a strong requirement for special NB-NB adhesion.

Important caution:

- The current evidence is suggestive but indirect.
- Mean absolute paired change after removing differential adhesion is very small:
  - `norm_het_frac` mean absolute paired delta `≈ 0.0016`
  - `exposed_frac` mean absolute paired delta `≈ 0.0098`
- Those are good supporting numbers, but the claim is specifically about NB clustering, so a direct clustering metric would make this section much stronger.

Potential Figure 5:

- `A` paired lineage renders with and without differential NB-NB adhesion
- `B` paired quantitative comparison of heterotypic contact
- `C` paired quantitative comparison of NB exposure
- `D` direct NB-clustering metric

Existing assets to reuse:

- [het_adhesion_by_divmean_mudmut.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_adhesion/figures/analysis/het_adhesion_by_divmean_mudmut.png)
- [het_adhesion_by_regdyn_mudmut.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_adhesion/figures/analysis/het_adhesion_by_regdyn_mudmut.png)
- [nb_exposure_by_divmean_mudmut.png](/Users/skjannetty/bagherilab/neurogen-plane-rotation-analysis/data/sim/processed_adhesion/figures/analysis/nb_exposure_by_divmean_mudmut.png)

## Discussion

Keep the discussion tightly tied to what the model can and cannot conclude.

### Discussion point 1

- Geometric inheritance across generations can be enough to preserve or disrupt lineage-scale sorting.
- This is a useful conceptual bridge between spindle orientation phenotypes and emergent tissue morphology.

### Discussion point 2

- Size-sensitive feedback alone is not enough unless cells retain memory of their birth size in the division threshold.
- This suggests that how division competence is encoded can be as important as how growth is repressed.

### Discussion point 3

- NB clustering in mudmut lineages may be an emergent consequence of origin geometry.
- If this holds after direct clustering analysis, it reduces the need to posit special mutant-specific adhesion.

### Discussion point 4

- State limitations clearly:
  - 2D projected analysis of an inherently 3D biological system
  - simulation rules are stylized, not molecularly explicit
  - endpoint calibration does not prove correct intermediate dynamics
  - experimental lineage data in this repo do not distinguish GMC vs neuron states

### Discussion point 5

- End on the value of the framework:
  it lets us separate geometry, growth control, and adhesion in ways that are difficult experimentally.

## Conclusion

Keep this short:

- WT lineage morphology in the model depends on maintaining asymmetric division geometry and consistent interdivision orientation.
- Mudmut geometry alone predicts overgrowth.
- Volume-sensitive regulation can restrain that overgrowth only when division thresholds track birth size.
- Preferential NB-NB adhesion appears dispensable for NB adjacency.

## Main figure slate

### Figure 1 — System, model, and WT calibration

- purpose: teach the biology and establish model credibility
- likely main message: the calibration is good enough to test spatial hypotheses

### Figure 2 — WT geometry decoupling

- purpose: isolate the effects of persistent relative rotation, variance, and offset
- likely main message: asymmetric offset and intergenerational orientation persistence preserve sorted morphology

### Figure 3 — Why mutant growth needs regulation

- purpose: show that geometric mutant rules alone massively overgrow
- likely main message: regulation must be invoked; unregulated mudmut is not plausible

### Figure 4 — Why `VCV=1` changes everything

- purpose: compare regulatory regimes under fixed vs birth-size-dependent thresholds
- likely main message: a fixed-threshold sizer null hypothesis is insufficient; volume-based regulation works only when threshold scales with birth size

### Figure 5 — Adhesion is optional

- purpose: test whether extra NB-NB adhesion is necessary
- likely main message: no, or at least not strongly, given current model behavior

## Likely supplement slate

- `S1` experimental preprocessing and lineage inclusion / exclusion summary
- `S2` experimental WT division-angle distribution and fit
- `S3` ARCADE calibration sweeps from [PARAMETERS_EXPLAINED.md](/Users/skjannetty/bagherilab/ARCADE/PARAMETERS_EXPLAINED.md)
- `S4` offset-50 calibration details from [PARAMETERS_y50_EXPLAINED.md](/Users/skjannetty/bagherilab/ARCADE/PARAMETERS_y50_EXPLAINED.md)
- `S5` full metric grids for all regulatory dynamics and conditions
- `S6` roundness / morphology sanity checks
- `S7` full no-adhesion comparison grids

## Highest-priority work tonight

### 1. Add a direct NB clustering metric for the adhesion result

Without this, the adhesion section is a little weaker than the rest of the paper.

Best options:

- number of NB connected components
- fraction of NBs in the largest NB cluster
- mean pairwise NB centroid distance
- nearest-neighbor NB distance

### 2. Reframe or extend the fixed-axis variance result

Two options:

1. rewrite the claim now:
   moderate variance has limited effect, but extreme variance disrupts sorting
2. run an extra sigma sweep tonight:
   `26, 35, 45, 60, 75, 90`

If we want the stronger claim, we need more than `26, 45, 90`.

### 3. Add time-course plots for the regulatory-rescue result

This will help the paper a lot because the endpoint plots alone do not show how the rescue happens.

Most useful trajectories:

- lineage area
- NB count
- average NB size
- maybe average progeny count

### 4. Decide whether to compute an experimental analogue of NB edge exposure

If feasible from the processed experimental meshes or the post-Voronoi tensors, this would strengthen the WT-sorting story by putting the experimental and simulated morphology on the same axis.

### 5. Make the offset-50 interpretation explicitly confound-aware

Best support options:

- show normalized spatial metrics
- show matched-cell-count comparison
- if possible, add an area-matched timepoint comparison or another control that isolates geometry more cleanly

## Recommended writing tone

- Keep the paper framed around sufficiency and necessity within the model.
- Prefer:
  - `the model predicts`
  - `is sufficient in the model`
  - `was not required to reproduce`
- Avoid:
  - `demonstrates that biology does X`
  - `proves the real regulator is Y`

## Final recommendation on section order

This is the order I would currently use in the manuscript:

1. WT system + calibration
2. WT geometry decoupling
3. Unregulated mudmut overgrowth
4. Regulatory mechanisms and the importance of birth-size-dependent thresholds
5. Adhesion test
6. Discussion

That order keeps the story cumulative:
first geometry in WT, then mutant failure, then rescue logic, then adhesion as the clean final mechanistic test.
