from npa.colors import NB_COLOR, GMC_COLOR, NEURON_COLOR, PROS_COLOR

FONT_SIZE_TITLE = 20
FONT_SIZE_LABEL = 16
FONT_SIZE_SMALL = 13

EXP_FILL_COLOR = "#f5b8b8"    # light red fill for experimental boxplots
EXP_MEDIAN_COLOR = "#c0392b"  # dark red for experimental median lines

RCPARAMS = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": FONT_SIZE_LABEL,
    "axes.titlesize": FONT_SIZE_TITLE,
    "axes.labelsize": FONT_SIZE_LABEL,
    "xtick.labelsize": FONT_SIZE_LABEL,
    "ytick.labelsize": FONT_SIZE_LABEL,
    "legend.fontsize": FONT_SIZE_LABEL,
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.dpi": 300,
}
