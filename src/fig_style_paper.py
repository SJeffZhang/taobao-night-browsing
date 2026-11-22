"""Professional academic-paper palette: muted, print-friendly, colour-blind safe."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# A calm, publication-style palette (not the maroon deck palette)
BLUE   = "#2E5A88"
ORANGE = "#D97742"
GREEN  = "#4A8B6F"
RED    = "#B0413E"
PURPLE = "#6A4C93"
GREY   = "#6B7280"
LIGHT  = "#D1D5DB"
DARK   = "#1F2937"


def apply():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#9CA3AF",
        "axes.linewidth": 0.8,
        "axes.labelcolor": DARK,
        "axes.titlecolor": DARK,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.color": DARK,
        "ytick.color": DARK,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "grid.color": "#E5E7EB",
        "grid.linewidth": 0.7,
        "font.size": 10,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
    })
