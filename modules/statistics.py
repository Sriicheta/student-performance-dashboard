"""
statistics.py
=============

NumPy-based statistical helpers:

- descriptive statistics (mean, median, spread, percentiles, IQR)
- grade calculation
- outlier detection with the IQR rule
- Pearson correlation, computed before and after excluding outliers

All numeric work is done on NumPy arrays rather than relying on Pandas
built-in functions, as required by the project brief.
"""

from __future__ import annotations

import numpy as np

# Grade floors, checked from the highest downwards.
GRADE_FLOORS = (
    (90, "O"),
    (80, "A+"),
    (70, "A"),
    (60, "B+"),
    (50, "B"),
    (40, "C"),
)

# Display order used wherever grades are listed.
GRADE_ORDER = ["O", "A+", "A", "B+", "B", "C", "F"]


# ---------------------------------------------------------------------------
# Basic reusable functions
# ---------------------------------------------------------------------------
def calculate_average(values) -> float:
    """Average of a collection of numbers as a NumPy array operation."""
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return float("nan")
    return float(np.mean(array))


def grade_for_score(score) -> str:
    """Return the letter grade for a numeric score.

    Non-numeric input returns an empty string so damaged rows stay quiet.
    """
    try:
        value = float(score)
    except (TypeError, ValueError):
        return ""
    for floor, grade in GRADE_FLOORS:
        if value >= floor:
            return grade
    return "F"


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------
def calculate_score_statistics(values) -> dict:
    """Full descriptive statistics for an array of assessment scores.

    Returns a dictionary with count, mean, median, standard deviation,
    variance, min, max, the 25th/50th/75th percentiles and the IQR.
    """
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        empty = float("nan")
        return {
            "count": 0, "mean": empty, "median": empty, "std_dev": empty,
            "variance": empty, "min": empty, "max": empty,
            "q1": empty, "q2": empty, "q3": empty, "iqr": empty,
        }

    q1, q2, q3 = np.percentile(array, [25, 50, 75])
    ddof = 1 if array.size > 1 else 0  # sample variance when possible
    return {
        "count": int(array.size),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "std_dev": float(np.std(array, ddof=ddof)),
        "variance": float(np.var(array, ddof=ddof)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "q1": float(q1),
        "q2": float(q2),
        "q3": float(q3),
        "iqr": float(q3 - q1),
    }


# ---------------------------------------------------------------------------
# Outliers
# ---------------------------------------------------------------------------
def find_outliers_iqr(values):
    """Flag potential outliers using the 1.5 x IQR rule.

    Returns ``(mask, lower, upper)`` where ``mask`` is a boolean NumPy array
    that is True for potential outliers.
    """
    array = np.asarray(values, dtype=float)
    q1, q3 = np.percentile(array, [25, 75])
    iqr = q3 - q1
    lower = float(q1 - 1.5 * iqr)
    upper = float(q3 + 1.5 * iqr)
    mask = (array < lower) | (array > upper)
    return mask, lower, upper


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------
def pearson_correlation(x, y) -> float:
    """Pearson correlation coefficient between two equal-length arrays."""
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if x_array.size < 2 or np.std(x_array) == 0 or np.std(y_array) == 0:
        return float("nan")
    return float(np.corrcoef(x_array, y_array)[0, 1])


def correlation_before_and_after_outliers(study_hours, scores) -> dict:
    """Compare the study-hours/score correlation with and without IQR outliers.

    Outliers are flagged on *either* variable (unusual study hours or an
    unusual score). The original data is never modified — the cleaned
    correlation is computed on a separate filtered copy.
    """
    hours = np.asarray(study_hours, dtype=float)
    scores_array = np.asarray(scores, dtype=float)

    mask_h, lower_h, upper_h = find_outliers_iqr(hours)
    mask_s, lower_s, upper_s = find_outliers_iqr(scores_array)
    outlier_mask = mask_h | mask_s

    r_all = pearson_correlation(hours, scores_array)

    keep = ~outlier_mask
    if keep.sum() >= 3 and outlier_mask.sum() > 0:
        r_excl = pearson_correlation(hours[keep], scores_array[keep])
    else:
        r_excl = r_all  # too few points left to recompute meaningfully

    return {
        "r_all": r_all,
        "r_excl": r_excl,
        "n_outliers": int(outlier_mask.sum()),
        "outlier_mask": outlier_mask,
        "bounds": {
            "study_hours": (lower_h, upper_h),
            "score": (lower_s, upper_s),
        },
    }


def strength_label(r: float) -> str:
    """Plain-language label for the strength/direction of a correlation."""
    if r != r:  # NaN check
        return "not available"
    magnitude = abs(r)
    if magnitude < 0.1:
        return "virtually no"
    if magnitude < 0.3:
        return "weak positive" if r > 0 else "weak negative"
    if magnitude < 0.5:
        return "moderate positive" if r > 0 else "moderate negative"
    if magnitude < 0.7:
        return "moderately strong positive" if r > 0 else "moderately strong negative"
    return "strong positive" if r > 0 else "strong negative"
