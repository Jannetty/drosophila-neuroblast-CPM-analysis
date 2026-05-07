UV     := uv run python
UV_NB  := uv run jupyter nbconvert --to notebook --execute --inplace

EXP_WRL_DIR    := data/exp/raw
EXP_PROC_DIR   := data/exp/processed
SIM_SWEEP_ROOT := data/sim/decoupling
SIM_PROC_DIR   := data/sim/processed_decoupling
ADH_SWEEP_ROOT := data/sim/decoupling_adhesion
ADH_PROC_DIR   := data/sim/processed_decoupling_adhesion

TEX_DIR := docs/tex_draft

.PHONY: all preprocess-data preprocess-simdata \
        preprocess-exp preprocess-sim preprocess-sim-raw \
        extract-metrics-exp extract-metrics-sim \
        summarize summarize-sim \
        preprocess-adh preprocess-adh-raw extract-metrics-adh \
        sim-clean adh-clean clean \
        figures fig1 fig2 fig3 fig4

# ── Full pipeline (exp + sim) ────────────────────────────────────────────
all: preprocess-data

preprocess-data: summarize

summarize: extract-metrics-exp extract-metrics-sim
	$(UV) scripts/summarize_metrics.py \
		--sim-metrics $(SIM_PROC_DIR)/sim_timepoint_metrics.csv \
		--exp-metrics $(EXP_PROC_DIR)/metrics.csv

extract-metrics-exp: preprocess-exp
	$(UV) scripts/extract_metrics.py \
		--kind exp \
		--processed-dir $(EXP_PROC_DIR)

extract-metrics-sim: preprocess-sim-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(SIM_SWEEP_ROOT) \
		--out-dir $(SIM_PROC_DIR)

preprocess-exp:
	$(UV) scripts/preprocess_exp.py \
		--wrl-dir $(EXP_WRL_DIR) \
		--out-dir $(EXP_PROC_DIR)

preprocess-sim-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(SIM_SWEEP_ROOT) \
		--out-dir $(SIM_PROC_DIR)

preprocess-sim: summarize-sim

# ── Sim-only pipeline (reuses existing exp metrics, does not rerun exp) ──
# Requires exp metrics to already exist at $(EXP_PROC_DIR)/metrics.csv.
preprocess-simdata: summarize-sim

summarize-sim: extract-metrics-sim
	$(UV) scripts/summarize_metrics.py \
		--sim-metrics $(SIM_PROC_DIR)/sim_timepoint_metrics.csv \
		--exp-metrics $(EXP_PROC_DIR)/metrics.csv

# ── Adhesion decoupling sweep ────────────────────────────────────────────
preprocess-adh: extract-metrics-adh

extract-metrics-adh: preprocess-adh-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)
	$(UV) scripts/extract_adhesion_metrics.py \
		--proc-dir $(ADH_PROC_DIR)

preprocess-adh-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)

adh-clean:
	rm -rf $(ADH_PROC_DIR)/*.npz $(ADH_PROC_DIR)/*.csv $(ADH_PROC_DIR)/figures

# ── Figure generation ────────────────────────────────────────────────────
# Each target re-runs the panel script(s), embeds PNGs into the Inkscape SVG,
# and normalises hand-drawn font sizes.  Run from the repo root:
#   make figures        — rebuild all figures
#   make fig1           — rebuild only Figure 1 panels + SVG
#
# After running, open the SVGs in Inkscape to realign panels as needed.
# The normalizer is not applied to fig4 (Panel A is a PNG embed, safe).

figures: fig1 fig2 fig3 fig4

fig1:
	$(UV_NB) $(TEX_DIR)/figure12_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig1_svg.py
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig1/fig1.svg

fig2:
	$(UV_NB) $(TEX_DIR)/figure12_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig2_svg.py
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig2/fig2.svg

fig3:
	$(UV) $(TEX_DIR)/figure3_paper_figures.py
	$(UV) $(TEX_DIR)/_build_fig3_svg.py
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig3/fig3.svg

fig4:
	$(UV) $(TEX_DIR)/_figure4_panel_a_draft.py
	$(UV_NB) $(TEX_DIR)/figure4_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig4_svg.py

# ── Clean targets ────────────────────────────────────────────────────────
sim-clean:
	rm -rf \
		$(SIM_PROC_DIR)/*.npz \
		$(SIM_PROC_DIR)/*.csv \
		$(SIM_PROC_DIR)/figures

clean: sim-clean
	rm -rf \
		$(EXP_PROC_DIR)/analysis \
		$(EXP_PROC_DIR)/meshes \
		$(EXP_PROC_DIR)/figures \
		$(EXP_PROC_DIR)/lineage_index.csv \
		$(EXP_PROC_DIR)/rejected_lineage_index.csv \
		$(EXP_PROC_DIR)/metrics.csv \
		$(EXP_PROC_DIR)/exp_summary.csv
