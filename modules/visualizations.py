"""
visualizations.py
=================

Every chart used by the dashboard, built with Matplotlib (and Seaborn for the
box plot). A single shared style keeps all figures consistent: muted colours,
minimal gridlines and readable labels.

Each function returns a Matplotlib figure that the app renders with
``st.pyplot(fig, use_container_width=True)``.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless-safe backend for Windows

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# ---------------------------------------------------------------------------
# Shared palette (muted, coordinated — no neon)
# ---------------------------------------------------------------------------
NAVY = "#2F4156"      # primary accent
SAGE = "#7C9885"      # secondary accent
SAGE_SOFT = "#8FA98F"  # box plot fill
TERRA = "#C1663E"     # outliers only
GREY = "#6E7276"      # secondary text
GRID = "#ECE9E3"      # gridlines
EDGE = "#DAD6CF"      # axis lines
TEXT = "#3A3D42"      # label text


def apply_chart_style() -> None:
    """Apply the shared Matplotlib style used by every chart."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.titleweight": "semibold",
            "axes.titlepad": 10,
            "axes.edgecolor": EDGE,
            "axes.linewidth": 1.0,
            "axes.labelcolor": TEXT,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": GREY,
            "ytick.color": GREY,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.frameon": False,
            "legend.fontsize": 8.5,
        }
    )


apply_chart_style()


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def score_histogram(scores, xlabel="Assessment score") -> plt.Figure:
    """Histogram of assessment scores with a median reference line."""
    values = np.asarray(scores, dtype=float)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))

    bins = np.arange(0, 105, 5)
    ax.hist(values, bins=bins, color=SAGE, edgecolor="white", linewidth=0.9, zorder=3)

    median = float(np.median(values))
    ax.axvline(
        median, color=NAVY, linestyle="--", linewidth=1.3, zorder=4,
        label=f"Median = {median:.1f}",
    )

    ax.set_xlabel("Assessment score")
    ax.set_ylabel("Number of students")
    ax.set_xlim(-2, 102)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
    ax.legend()
    fig.tight_layout()
    return fig


def scatter_hours_scores(
    hours,
    scores,
    outlier_mask=None,
    trend=None,
) -> plt.Figure:
    """Scatter plot of reported study hours against assessment scores.

    ``outlier_mask`` highlights IQR outliers in terracotta; ``trend`` is an
    optional ``(slope, intercept)`` pair drawn as a dashed trend line.
    """
    hours_array = np.asarray(hours, dtype=float)
    scores_array = np.asarray(scores, dtype=float)
    if outlier_mask is None:
        outlier_mask = np.zeros(hours_array.shape, dtype=bool)

    fig, ax = plt.subplots(figsize=(7.0, 4.0))

    normal = ~outlier_mask
    ax.scatter(
        hours_array[normal], scores_array[normal],
        s=34, color=NAVY, alpha=0.7, edgecolor="white", linewidth=0.6,
        label="Students", zorder=3,
    )
    if outlier_mask.any():
        ax.scatter(
            hours_array[outlier_mask], scores_array[outlier_mask],
            s=46, color=TERRA, edgecolor="white", linewidth=0.6,
            label="Potential outlier (IQR)", zorder=4,
        )
    if trend is not None and hours_array.size >= 2:
        slope, intercept = trend
        xs = np.linspace(hours_array.min(), hours_array.max(), 50)
        ax.plot(
            xs, slope * xs + intercept, color=SAGE, linestyle="--",
            linewidth=1.6, label="Linear trend", zorder=2,
        )

    ax.set_xlabel("Reported study hours per week")
    ax.set_ylabel("Assessment score")
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def score_boxplot(scores) -> plt.Figure:
    """Horizontal box plot (Seaborn) used to spot outliers."""
    values = np.asarray(scores, dtype=float)
    fig, ax = plt.subplots(figsize=(7.0, 2.7))

    sns.boxplot(
        x=values, ax=ax, color=SAGE_SOFT, width=0.42, linewidth=1.1,
        flierprops={
            "marker": "o", "markerfacecolor": TERRA, "markeredgecolor": TERRA,
            "markersize": 4.5, "alpha": 0.9,
        },
        medianprops={"color": "#243746", "linewidth": 1.8},
        boxprops={"edgecolor": "#5F7A65"},
        whiskerprops={"color": "#5F7A65"},
        capprops={"color": "#5F7A65"},
    )

    ax.set_xlabel("Assessment score")
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    fig.tight_layout()
    return fig


def course_bar_chart(series: "np.ndarray | pd.Series", ylabel: str, color=NAVY) -> plt.Figure:
    """Bar chart comparing courses (average score or average study hours)."""
    labels = list(series.index)
    values = np.asarray(series, dtype=float)

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    bars = ax.bar(labels, values, color=color, width=0.6, edgecolor="white", zorder=3)
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8.5, color=GREY)

    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
    top = values.max() if values.size else 0
    ax.set_ylim(0, top * 1.18 if top > 0 else 1)
    plt.setp(ax.get_xticklabels(), rotation=18, ha="right")
    fig.tight_layout()
    return fig
