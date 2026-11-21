"""Shared matplotlib style for the mid-term deck figures (maroon palette)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MAROON = '#7C3A47'
MAROON_MID = '#A85D68'
ROSE = '#C98A95'
PINK = '#D8A7AF'
PALE = '#E7DAE0'
DARK = '#403737'
CHAR = '#4A4545'
GRAY = '#9A8F8F'


def apply():
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.edgecolor': '#B9ABAE',
        'axes.linewidth': 0.8,
        'axes.labelcolor': CHAR,
        'axes.titlecolor': DARK,
        'axes.titlesize': 10,
        'axes.labelsize': 9,
        'xtick.color': CHAR,
        'ytick.color': CHAR,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'grid.color': '#EFE7E9',
        'grid.linewidth': 0.7,
        'font.size': 9,
        'legend.frameon': False,
        'legend.fontsize': 8,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.dpi': 150,
    })
