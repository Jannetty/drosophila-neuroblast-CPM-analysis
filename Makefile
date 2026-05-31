UV     := uv run python
UV_NB  := uv run jupyter nbconvert --to notebook --execute --inplace

EXP_WRL_DIR          := data/exp/raw
EXP_PROC_DIR         := data/exp/processed
EXP_NC_PROC_DIR      := data/exp/processed_non_convex
SIM_SWEEP_DIR        := data/sim/sweep
SIM_SWEEP_PROC_DIR   := data/sim/processed_sweep
SIM_DECOUPLE_DIR     := data/sim/decoupling
SIM_DECOUPLE_PROC_DIR := data/sim/processed_decoupling
ADH_SWEEP_ROOT       := data/sim/decoupling_adhesion
ADH_PROC_DIR         := data/sim/processed_decoupling_adhesion
SIM_CALIB_DIR        := data/sim/calibrate_sweep
SIM_CALIB_PROC_DIR   := data/sim/processed_calibrate

TEX_DIR := docs/tex_draft

.PHONY: all preprocess-data \
        preprocess-exp extract-metrics-exp \
        preprocess-exp-nonconvex \
        preprocess-sweep-raw extract-metrics-sweep summarize-sweep \
        preprocess-decouple-raw extract-metrics-decouple summarize-decouple \
        preprocess-adh preprocess-adh-raw extract-metrics-adh \
        preprocess-calibrate analyze-calibrate plot-calibrate calibrate-clean \
        sweep-clean decouple-clean adh-clean nonconvex-clean clean \
        figures fig1 fig2 fig3 fig4 fig5 fig5-supp-table figS-wt-metrics \
        figS-2d-vs-3d \
        figures-convex figures-nonconvex

# ── Full pipeline (exp + all sim sweeps) ────────────────────────────────────
all: preprocess-data

preprocess-data: summarize-sweep summarize-decouple preprocess-adh preprocess-exp-nonconvex

# ── Experimental pipeline ────────────────────────────────────────────────────
preprocess-exp:
	$(UV) scripts/preprocess_exp.py \
		--wrl-dir $(EXP_WRL_DIR) \
		--out-dir $(EXP_PROC_DIR)

extract-metrics-exp: preprocess-exp
	$(UV) scripts/extract_metrics.py \
		--kind exp \
		--processed-dir $(EXP_PROC_DIR)

# ── Non-convex experimental pipeline ────────────────────────────────────────
preprocess-exp-nonconvex:
	$(UV) scripts/preprocess_exp.py \
		--no-convex-hull \
		--wrl-dir $(EXP_WRL_DIR) \
		--out-dir $(EXP_NC_PROC_DIR)
	$(UV) scripts/extract_metrics.py \
		--kind exp \
		--processed-dir $(EXP_NC_PROC_DIR)
	$(UV) scripts/extract_exp_nb_connectivity.py \
		--proc-dir $(EXP_NC_PROC_DIR)
	$(UV) scripts/summarize_metrics.py \
		--sim-metrics $(SIM_SWEEP_PROC_DIR)/sim_timepoint_metrics.csv \
		--exp-metrics $(EXP_NC_PROC_DIR)/metrics.csv

# ── Main sweep pipeline (figures 1–4) ───────────────────────────────────────
preprocess-sweep-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(SIM_SWEEP_DIR) \
		--out-dir $(SIM_SWEEP_PROC_DIR)

extract-metrics-sweep: preprocess-sweep-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(SIM_SWEEP_DIR) \
		--out-dir $(SIM_SWEEP_PROC_DIR)

summarize-sweep: extract-metrics-exp extract-metrics-sweep
	$(UV) scripts/summarize_metrics.py \
		--sim-metrics $(SIM_SWEEP_PROC_DIR)/sim_timepoint_metrics.csv \
		--exp-metrics $(EXP_PROC_DIR)/metrics.csv

# ── Decoupling sweep pipeline (figures 1–2 decoupling panels) ───────────────
preprocess-decouple-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(SIM_DECOUPLE_DIR) \
		--out-dir $(SIM_DECOUPLE_PROC_DIR)

extract-metrics-decouple: preprocess-decouple-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(SIM_DECOUPLE_DIR) \
		--out-dir $(SIM_DECOUPLE_PROC_DIR)

summarize-decouple: extract-metrics-exp extract-metrics-decouple
	$(UV) scripts/summarize_metrics.py \
		--sim-metrics $(SIM_DECOUPLE_PROC_DIR)/sim_timepoint_metrics.csv \
		--exp-metrics $(EXP_PROC_DIR)/metrics.csv

# ── Adhesion decoupling pipeline (figure 5) ─────────────────────────────────
preprocess-adh: extract-metrics-adh

preprocess-adh-raw:
	$(UV) scripts/preprocess_sim.py \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)

extract-metrics-adh: preprocess-adh-raw
	$(UV) scripts/extract_metrics.py \
		--kind sim \
		--sweep-root $(ADH_SWEEP_ROOT) \
		--out-dir $(ADH_PROC_DIR)
	$(UV) scripts/extract_adhesion_metrics.py \
		--proc-dir $(ADH_PROC_DIR)

# ── Calibration-sweep pipeline ──────────────────────────────────────────────
preprocess-calibrate:
	$(UV) scripts/preprocess_calibrate.py

analyze-calibrate: preprocess-calibrate
	$(UV) scripts/analyze_calibration_alignment.py

plot-calibrate: preprocess-calibrate
	$(UV) scripts/plot_calibration_sweep.py

calibrate-clean:
	rm -rf $(SIM_CALIB_PROC_DIR)

# ── Figure generation ────────────────────────────────────────────────────────
# Each target re-runs the panel script(s), embeds PNGs into the Inkscape SVG,
# and normalises hand-drawn font sizes.  Run from the repo root:
#   make figures        — rebuild all figures (fig1–fig5)
#   make fig1           — rebuild only Figure 1 panels + SVG
#
# After running, open the SVGs in Inkscape to realign panels as needed.
# The normalizer is not applied to fig4 (Panel A is a PNG embed, safe).

figures: fig1 fig2 fig3 fig4 fig5 figS-2d-vs-3d

figures-convex: export EXP_PROC_DIR = data/exp/processed
figures-convex: fig1 fig2 fig3 fig4 fig5 figS-2d-vs-3d

figures-nonconvex: export EXP_PROC_DIR = $(EXP_NC_PROC_DIR)
figures-nonconvex: fig1 fig2 fig3 fig4 fig5 figS-2d-vs-3d

fig1:
	$(UV_NB) $(TEX_DIR)/figure12_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig1_svg.py
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig1/fig1.svg

fig2:
	$(UV_NB) $(TEX_DIR)/figure12_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig2_svg.py
	$(UV) $(TEX_DIR)/_build_fig2_separateparts_svg.py
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig2/fig2.svg
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig2/fig2_separateparts.svg

fig3:
	$(UV) $(TEX_DIR)/figure3_paper_figures.py
	$(UV) $(TEX_DIR)/_build_fig3_svg.py
	$(UV) $(TEX_DIR)/_normalize_svg_fonts.py fig3/fig3.svg

fig4:
	$(UV) $(TEX_DIR)/_figure4_panel_a_draft.py
	$(UV_NB) $(TEX_DIR)/figure4_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig4_svg.py

fig5:
	$(UV_NB) $(TEX_DIR)/figure5_paper_figures.ipynb
	$(UV) $(TEX_DIR)/_build_fig5_svg.py

figS-2d-vs-3d:
	$(UV) scripts/make_supp_2d_vs_3d_metrics.py

figS-wt-metrics:
	$(UV_NB) $(TEX_DIR)/figure4_paper_figures.ipynb

fig5-supp-table:
	$(UV) scripts/generate_connectivity_ci_table.py \
		--proc-dir $(ADH_PROC_DIR) \
		--out-dir  $(TEX_DIR)/figures

# ── Clean targets ────────────────────────────────────────────────────────────
sweep-clean:
	rm -rf \
		$(SIM_SWEEP_PROC_DIR)/*.npz \
		$(SIM_SWEEP_PROC_DIR)/*.csv \
		$(SIM_SWEEP_PROC_DIR)/figures

decouple-clean:
	rm -rf \
		$(SIM_DECOUPLE_PROC_DIR)/*.npz \
		$(SIM_DECOUPLE_PROC_DIR)/*.csv \
		$(SIM_DECOUPLE_PROC_DIR)/figures

adh-clean:
	rm -rf $(ADH_PROC_DIR)/*.npz $(ADH_PROC_DIR)/*.csv $(ADH_PROC_DIR)/figures

nonconvex-clean:
	rm -rf $(EXP_NC_PROC_DIR)

clean: sweep-clean decouple-clean adh-clean nonconvex-clean
	rm -rf \
		$(EXP_PROC_DIR)/analysis \
		$(EXP_PROC_DIR)/meshes \
		$(EXP_PROC_DIR)/figures \
		$(EXP_PROC_DIR)/lineage_index.csv \
		$(EXP_PROC_DIR)/rejected_lineage_index.csv \
		$(EXP_PROC_DIR)/metrics.csv \
		$(EXP_PROC_DIR)/exp_summary.csv
