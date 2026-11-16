"""
data_manager.py
===============

Everything related to storing and changing the dataset:

- loading and saving ``student_data.csv`` (CSV file handling)
- generating the reproducible synthetic sample dataset
- validating form input
- add / update / delete helpers used by the dashboard

The CSV holds one row per student with the columns:
``student_id, course, study_hours, score``
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .student_record import StudentRecord

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "student_data.csv"

CSV_COLUMNS = ["student_id", "course", "study_hours", "score"]

COURSES = [
    "Computer Science",
    "Electronics",
    "Mechanical Engineering",
    "Electrical Engineering",
]

# Recipe used to build the synthetic sample dataset. "base_score" shifts a
# course slightly up or down so the Course Comparison page has differences
# to show; the real spread comes from the random components.
COURSE_PROFILES = {
    "Computer Science": {"count": 30, "mean_hours": 13.0, "base_score": 62},
    "Electronics": {"count": 30, "mean_hours": 11.5, "base_score": 58},
    "Mechanical Engineering": {"count": 30, "mean_hours": 10.0, "base_score": 55},
    "Electrical Engineering": {"count": 30, "mean_hours": 12.0, "base_score": 60},
}


# ---------------------------------------------------------------------------
# Sample dataset (synthetic, reproducible)
# ---------------------------------------------------------------------------
def create_sample_dataset(path: Path = DATA_FILE, seed: int = 42) -> pd.DataFrame:
    """Generate the synthetic sample dataset and save it to CSV.

    A fixed random seed keeps the dataset identical between runs. The
    study-hours/score relationship is deliberately noisy (an ability term
    and random noise are added on top of a modest hours effect) so the
    correlation is realistic rather than artificially perfect. A few
    deliberate outliers are included so the IQR analysis has work to do.
    """
    rng = np.random.default_rng(seed)
    rows = []
    number = 0

    for course, profile in COURSE_PROFILES.items():
        for _ in range(profile["count"]):
            # Half-hour steps keep the reported hours readable.
            hours = round(float(np.clip(rng.normal(profile["mean_hours"], 4.2), 2.0, 26.0)) * 2) / 2
            ability = rng.normal(0, 7.0)   # student aptitude, independent of hours
            noise = rng.normal(0, 5.0)     # everyday variation
            raw = profile["base_score"] + 1.8 * (hours - 12.0) + ability + noise
            score = int(round(float(np.clip(raw, 0, 100))))
            number += 1
            rows.append(
                {
                    "student_id": f"STU{number:03d}",
                    "course": course,
                    "study_hours": hours,
                    "score": score,
                }
            )

    # A handful of plausible outliers: unusual hour/score combinations.
    planned_outliers = [
        ("Computer Science", 24.5, 34),          # studies a lot, scores poorly
        ("Electronics", 3.0, 89),                # studies little, scores highly
        ("Mechanical Engineering", 25.0, 45),    # very heavy study, weak result
        ("Electrical Engineering", 4.0, 92),     # minimal study, strong result
        ("Computer Science", 2.5, 18),           # disengaged student
    ]
    for course, hours, score in planned_outliers:
        number += 1
        rows.append(
            {
                "student_id": f"STU{number:03d}",
                "course": course,
                "study_hours": hours,
                "score": score,
            }
        )

    df = pd.DataFrame(rows, columns=CSV_COLUMNS)
    df.to_csv(path, index=False, encoding="utf-8")
    return df


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------
def load_records(path: Path = DATA_FILE) -> pd.DataFrame:
    """Load student records from CSV, creating sample data if the file is missing.

    Rows with missing or invalid values are dropped gracefully so a damaged
    file can never crash the dashboard.
    """
    if not path.exists():
        create_sample_dataset(path)

    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, UnicodeDecodeError, OSError):
        df = pd.DataFrame(columns=CSV_COLUMNS)

    # Normalise column names and keep only the expected columns.
    df.columns = [str(column).strip().lower() for column in df.columns]
    if not set(CSV_COLUMNS).issubset(df.columns):
        df = pd.DataFrame(columns=CSV_COLUMNS)
    df = df[CSV_COLUMNS].copy()

    # Clean types: text fields to stripped strings, numbers coerced, bad rows dropped.
    df["student_id"] = df["student_id"].astype(str).str.strip()
    df["course"] = df["course"].astype(str).str.strip()
    df["study_hours"] = pd.to_numeric(df["study_hours"], errors="coerce")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")

    df = df.dropna(subset=["study_hours", "score"])
    df = df[(df["study_hours"] >= 0) & df["score"].between(0, 100)]
    df = df[(df["student_id"] != "") & (df["student_id"] != "nan")]

    df["score"] = df["score"].round().astype(int)
    df = df.sort_values("student_id").reset_index(drop=True)
    return df


def save_records(df: pd.DataFrame, path: Path = DATA_FILE) -> None:
    """Write the current dataset back to CSV (index column excluded)."""
    df.to_csv(path, index=False, encoding="utf-8")


def records_as_objects(df: pd.DataFrame) -> list[StudentRecord]:
    """Convert every DataFrame row into a StudentRecord object."""
    return [
        StudentRecord(row["student_id"], row["course"], row["study_hours"], row["score"])
        for _, row in df.iterrows()
    ]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_inputs(df, student_id, course, study_hours, score, original_id=None) -> list[str]:
    """Validate form input and return a list of error messages (empty = valid).

    ``original_id`` is passed when editing an existing record so the record's
    own ID does not trigger the uniqueness check.
    """
    errors = []

    sid = str(student_id or "").strip().upper()
    if not sid:
        errors.append("Student ID is required.")
    elif " " in sid:
        errors.append("Student ID cannot contain spaces.")
    elif original_id is None and sid in set(df["student_id"].str.upper()):
        errors.append(f"Student ID '{sid}' already exists — IDs must be unique.")

    if not str(course or "").strip():
        errors.append("Course is required.")

    try:
        hours = float(study_hours)
        if hours < 0:
            errors.append("Study hours cannot be negative.")
        elif hours > 80:
            errors.append("Study hours above 80 per week look implausible.")
    except (TypeError, ValueError):
        errors.append("Study hours must be a number.")

    try:
        value = float(score)
        if not 0 <= value <= 100:
            errors.append("Assessment score must be between 0 and 100.")
    except (TypeError, ValueError):
        errors.append("Assessment score must be a number between 0 and 100.")

    return errors


# ---------------------------------------------------------------------------
# Add / update / delete (each returns a new DataFrame; caller saves it)
# ---------------------------------------------------------------------------
def add_record(df: pd.DataFrame, record: StudentRecord) -> pd.DataFrame:
    """Append a StudentRecord object to the dataset."""
    new_row = pd.DataFrame([record.get_record(include_grade=False)])[CSV_COLUMNS]
    return pd.concat([df, new_row], ignore_index=True)


def apply_update(df: pd.DataFrame, student_id: str, record: StudentRecord) -> pd.DataFrame:
    """Write an updated StudentRecord back into the dataset (ID unchanged)."""
    df = df.copy()
    mask = df["student_id"] == student_id
    values = record.get_record(include_grade=False)
    for column in ("course", "study_hours", "score"):
        df.loc[mask, column] = values[column]
    return df


def delete_record(df: pd.DataFrame, student_id: str) -> pd.DataFrame:
    """Remove the record with the given student ID."""
    remaining = df[df["student_id"] != student_id]
    return remaining.reset_index(drop=True)
