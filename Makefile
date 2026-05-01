UV := uv run python

EXP_WRL_DIR    := data/exp/raw
EXP_PROC_DIR   := data/exp/processed
SIM_SWEEP_ROOT := data/sim/decoupling
SIM_PROC_DIR   := data/sim/processed_decoupling

.PHONY: all preprocess-data preprocess-simdata \
        preprocess-exp preprocess-sim preprocess-sim-raw \
        extract-metrics-exp extract-metrics-sim \
        summarize summarize-sim \
        sim-clean clean

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
