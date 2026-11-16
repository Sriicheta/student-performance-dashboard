"""
analysis.py
===========

Higher-level analysis built on Pandas and the NumPy statistics module:

- overall metrics for the Overview page
- course-wise aggregation with ``groupby``
- correlation report with plain-language interpretation
- simple linear regression (trend line)
- automatically generated summary text
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .statistics import (
    GRADE_ORDER,
    calculate_score_statistics,
    correlation_before_and_after_outliers,
    grade_for_score,
    strength_label,
)


# ---------------------------------------------------------------------------
# Overview metrics
# ---------------------------------------------------------------------------
def overall_metrics(df: pd.DataFrame) -> dict:
    """Key numbers for the Overview page, computed from the current data."""
    scores = df["score"].to_numpy(dtype=float)
    hours = df["study_hours"].to_numpy(dtype=float)
    stats = calculate_score_statistics(scores)
    return {
        "n": int(len(df)),
        "n_courses": int(df["course"].nunique()),
        "avg_score": stats["mean"],
        "avg_hours": float(np.mean(hours)) if hours.size else float("nan"),
        "highest": stats["max"],
        "lowest": stats["min"],
        "stats": stats,
    }


def overview_paragraph(metrics: dict) -> str:
    """A short, auto-generated statistical summary paragraph."""
    stats = metrics["stats"]
    return (
        f"The dataset currently contains **{metrics['n']} student records** across "
        f"**{metrics['n_courses']} course(s)**. Assessment scores average "
        f"**{metrics['avg_score']:.1f}** with a standard deviation of "
        f"**{stats['std_dev']:.1f}**, ranging from **{metrics['lowest']:.0f}** to "
        f"**{metrics['highest']:.0f}**. Students report an average of "
        f"**{metrics['avg_hours']:.1f} study hours per week**. The middle 50% of "
        f"scores fall between **{stats['q1']:.1f}** and **{stats['q3']:.1f}** "
        f"(interquartile range **{stats['iqr']:.1f}**). Every number on this "
        "dashboard is recalculated from the records currently in the dataset, so "
        "adding, editing, deleting or filtering records updates it immediately."
    )


# ---------------------------------------------------------------------------
# Course aggregation (Pandas GroupBy)
# ---------------------------------------------------------------------------
def course_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-course statistics using Pandas GroupBy."""
    summary = (
        df.groupby("course")
        .agg(
            students=("student_id", "count"),
            avg_score=("score", "mean"),
            median_score=("score", "median"),
            std_score=("score", "std"),
            avg_study_hours=("study_hours", "mean"),
            highest_score=("score", "max"),
            lowest_score=("score", "min"),
        )
        .round(2)
        .sort_values("avg_score", ascending=False)
    )
    summary["std_score"] = summary["std_score"].fillna(0.0)
    return summary


def grade_distribution(df: pd.DataFrame) -> pd.Series:
    """Count of students per grade, ordered O -> F."""
    grades = df["score"].map(grade_for_score)
    counts = grades.value_counts().reindex(GRADE_ORDER).fillna(0).astype(int)
    return counts[counts > 0]


# ---------------------------------------------------------------------------
# Study hours vs scores
# ---------------------------------------------------------------------------
def regression_line(hours, scores):
    """Fit a simple least-squares line and return ``(slope, intercept)``."""
    hours_array = np.asarray(hours, dtype=float)
    scores_array = np.asarray(scores, dtype=float)
    if hours_array.size < 2:
        return 0.0, 0.0
    slope, intercept = np.polyfit(hours_array, scores_array, 1)
    return float(slope), float(intercept)


def correlation_report(df: pd.DataFrame) -> dict:
    """Full study-hours/score report, including interpretation labels."""
    hours = df["study_hours"].to_numpy(dtype=float)
    scores = df["score"].to_numpy(dtype=float)

    report = correlation_before_and_after_outliers(hours, scores)
    report["label_all"] = strength_label(report["r_all"])
    report["label_excl"] = strength_label(report["r_excl"])

    # Did excluding outliers make the association weaker, stronger, or similar?
    change = abs(report["r_excl"]) - abs(report["r_all"])
    if report["n_outliers"] == 0 or report["r_all"] != report["r_all"]:
        report["change_label"] = "remains similar"
    elif change > 0.03:
        report["change_label"] = "becomes stronger"
    elif change < -0.03:
        report["change_label"] = "becomes weaker"
    else:
        report["change_label"] = "remains similar"
    return report


def change_explanation(report: dict) -> str:
    """Explain in plain language what excluding the outliers did to r."""
    if report["n_outliers"] == 0:
        return (
            "No potential outliers were flagged by the IQR rule in the current "
            "selection, so the correlation is unchanged after filtering."
        )
    direction = (
        "weaker" if "weaker" in report["change_label"]
        else "stronger" if "stronger" in report["change_label"]
        else "similar"
    )
    return (
        f"After removing the {report['n_outliers']} potential outlier(s) flagged by "
        f"the IQR rule, the association **{report['change_label']}**: Pearson's r "
        f"moves from **{report['r_all']:.2f}** to **{report['r_excl']:.2f}**. The "
        f"underlying pattern is therefore {direction} to what the full dataset "
        "suggests — the extreme records "
        + ("did distort the headline number noticeably." if direction != "similar"
           else "were not driving the headline number.")
    )
