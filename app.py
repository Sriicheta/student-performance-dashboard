"""
app.py
======

Student Performance & Study-Hours Analytics Dashboard
----------------------------------------------------

A Streamlit application that investigates the relationship between students'
reported study hours and their assessment scores, using anonymised records
stored in ``student_data.csv``.

Run it with::

    streamlit run app.py

This file contains only the user interface. Data handling lives in
``modules/data_manager.py``, statistics in ``modules/statistics.py``, higher
level analysis in ``modules/analysis.py`` and charts in
``modules/visualizations.py``.

The dataset shown by default is synthetic sample data, not real student
results. No personally identifiable information is collected.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from modules import analysis, statistics
from modules import data_manager as dm
from modules.student_record import StudentRecord
from modules import visualizations as viz

# ---------------------------------------------------------------------------
# Basic setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Student Performance Analytics",
    page_icon=":material/school:",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_ROOT = Path(__file__).resolve().parent
CSS_FILE = APP_ROOT / "assets" / "custom.css"
if CSS_FILE.exists():
    st.markdown(
        f"<style>{CSS_FILE.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# Sort choices for the records table: label -> (column, ascending)
SORT_OPTIONS = {
    "Student ID (A-Z)": ("student_id", True),
    "Score (high to low)": ("score", False),
    "Score (low to high)": ("score", True),
    "Study hours (high to low)": ("study_hours", False),
    "Study hours (low to high)": ("study_hours", True),
}


# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------
def get_data() -> pd.DataFrame:
    """Return the working copy of the dataset (loaded once per session)."""
    if "data" not in st.session_state:
        st.session_state["data"] = dm.load_records()
    return st.session_state["data"]


def save_data(df: pd.DataFrame, message: str) -> None:
    """Replace the working dataset, persist it to CSV and queue a message."""
    df = df.reset_index(drop=True)
    st.session_state["data"] = df
    dm.save_records(df)
    st.session_state["flash"] = ("success", message)


def show_flash() -> None:
    """Display and clear a one-shot status message from a previous run."""
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        (st.success if kind == "success" else st.error)(message)


def page_header(title: str, caption: str) -> None:
    """Consistent page title + one-line description."""
    st.markdown(
        f"<p class='page-title'>{title}</p><p class='page-caption'>{caption}</p>",
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    """Small uppercase section label, used above charts and tables."""
    st.markdown(f"<p class='section-label'>{text}</p>", unsafe_allow_html=True)


def course_filter(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Reusable course multi-select; returns the filtered DataFrame."""
    courses = sorted(df["course"].dropna().unique().tolist())
    selected = st.multiselect(
        "Filter by course", courses, default=courses, key=key,
        help="Leave a course unticked to exclude it from every number below.",
    )
    return df[df["course"].isin(selected)].reset_index(drop=True)


def chart_or_empty(view: pd.DataFrame, column: str) -> bool:
    """Guard used before charting: True when there is nothing to plot."""
    return view[column].dropna().empty


# ===========================================================================
# PAGE 1 — Overview
# ===========================================================================
def page_overview() -> None:
    df = get_data()
    page_header(
        "Overview",
        "A quick picture of the cohort — every number updates as records change.",
    )
    if df.empty:
        st.warning("The dataset is empty. Add records from the sidebar to begin.")
        return

    view = course_filter(df, "overview_filter")
    if view.empty:
        st.info("No records match the selected courses.")
        return

    metrics = analysis.overall_metrics(view)

    # --- key metrics -------------------------------------------------------
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Students", f"{metrics['n']}")
    m2.metric("Avg score", f"{metrics['avg_score']:.1f}")
    m3.metric("Avg hrs / week", f"{metrics['avg_hours']:.1f}")
    m4.metric("Highest", f"{metrics['highest']:.0f}")
    m5.metric("Lowest", f"{metrics['lowest']:.0f}")

    # --- charts ------------------------------------------------------------
    left, right = st.columns(2, gap="medium")
    with left:
        section_label("Score distribution")
        if not chart_or_empty(view, "score"):
            st.pyplot(
                viz.score_histogram(view["score"]),
                width="stretch",
            )
    with right:
        section_label("Study hours vs scores")
        if not chart_or_empty(view, "study_hours"):
            st.pyplot(
                viz.scatter_hours_scores(view["study_hours"], view["score"]),
                width="stretch",
            )
    # --- auto-generated summary --------------------------------------------
    section_label("Statistical summary")
    with st.container(border=True):
        st.markdown(analysis.overview_paragraph(metrics))
        st.caption(
            "Note: the bundled dataset is synthetic sample data for demonstration, "
            "not actual student results."
        )


# ===========================================================================
# PAGE 2 — Student Records
# ===========================================================================
def page_records() -> None:
    df = get_data()
    page_header(
        "Student Records",
        "Search, sort, edit and export the anonymised records.",
    )
    if df.empty:
        st.warning("The dataset is empty. Add a record first.")
        return

    # --- search / filter / sort --------------------------------------------
    top = st.columns([1, 1, 2])
    search = top[0].text_input("Search by student ID", placeholder="e.g. STU042")
    courses = ["All courses"] + sorted(df["course"].dropna().unique().tolist())
    course_choice = top[1].selectbox("Course", courses)
    sort_label = top[2].selectbox("Sort by", list(SORT_OPTIONS), index=1)

    view = df.copy()
    if search.strip():
        view = view[view["student_id"].str.contains(search.strip(), case=False)]
    if course_choice != "All courses":
        view = view[view["course"] == course_choice]

    column, ascending = SORT_OPTIONS[sort_label]
    view = view.sort_values(column, ascending=ascending).reset_index(drop=True)

    if view.empty:
        st.info("No records match the current search or filter.")
        return

    # Grade is always derived from the score, never stored.
    view = view.copy()
    view["grade"] = view["score"].map(statistics.grade_for_score)
    view = view[["student_id", "course", "study_hours", "score", "grade"]]

    st.dataframe(
        view,
        width="stretch",
        hide_index=True,
        column_config={
            "student_id": st.column_config.TextColumn("Student ID", width="small"),
            "course": st.column_config.TextColumn("Course"),
            "study_hours": st.column_config.NumberColumn("Study hrs / week", format="%.1f"),
            "score": st.column_config.NumberColumn("Score", format="%d"),
            "grade": st.column_config.TextColumn("Grade", width="small"),
        },
    )
    st.download_button(
        "Export records as CSV",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="student_records_export.csv",
        mime="text/csv",
    )

    # --- edit ---------------------------------------------------------------
    all_ids = df["student_id"].tolist()
    course_options = sorted(set(dm.COURSES) | set(df["course"].dropna().unique().tolist()))

    with st.expander("Edit a record"):
        # The ID selector sits outside the form so choosing a different
        # student immediately re-prefills the fields below.
        selected_id = st.selectbox("Student ID", all_ids, key="edit_id")
        row = df[df["student_id"] == selected_id].iloc[0]
        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            course = c1.selectbox(
                "Course", course_options,
                index=course_options.index(row["course"]) if row["course"] in course_options else 0,
            )
            hours = c2.number_input(
                "Study hours per week", min_value=0.0, max_value=80.0,
                value=float(row["study_hours"]), step=0.5,
            )
            score = st.number_input(
                "Assessment score", min_value=0, max_value=100,
                value=int(row["score"]), step=1,
            )
            if st.form_submit_button("Save changes", type="primary"):
                errors = dm.validate_inputs(df, selected_id, course, hours, score,
                                            original_id=selected_id)
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    record = StudentRecord(selected_id, row["course"],
                                           row["study_hours"], row["score"])
                    record.update_record(course=course,
                                         study_hours=float(hours), score=int(score))
                    save_data(dm.apply_update(df, selected_id, record),
                              f"Record {selected_id} updated.")
                    st.rerun()

    # --- delete --------------------------------------------------------------
    with st.expander("Delete a record"):
        del_id = st.selectbox("Student ID", all_ids, key="delete_id")
        confirm = st.checkbox("I understand this permanently removes the record")
        if st.button("Delete record", type="primary", disabled=not confirm):
            save_data(dm.delete_record(df, del_id), f"Record {del_id} deleted.")
            st.rerun()


# ===========================================================================
# PAGE 3 — Performance Analysis
# ===========================================================================
def page_performance() -> None:
    df = get_data()
    page_header(
        "Performance Analysis",
        "Descriptive statistics for assessment scores, computed with NumPy.",
    )
    if df.empty:
        st.warning("The dataset is empty. Add records to analyse performance.")
        return

    view = course_filter(df, "performance_filter")
    if view.empty:
        st.info("No records match the selected courses.")
        return

    stats = statistics.calculate_score_statistics(view["score"])

    # --- headline numbers ----------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mean score", f"{stats['mean']:.1f}")
    m2.metric("Median score", f"{stats['median']:.1f}")
    m3.metric("Std deviation", f"{stats['std_dev']:.1f}")
    m4.metric("IQR", f"{stats['iqr']:.1f}")

    # --- charts ---------------------------------------------------------------
    left, right = st.columns(2, gap="medium")
    with left:
        section_label("Distribution")
        st.pyplot(viz.score_histogram(view["score"]), width="stretch")
    with right:
        section_label("Box plot")
        st.pyplot(viz.score_boxplot(view["score"]), width="stretch")

    # --- full statistics table -------------------------------------------------
    section_label("Summary statistics")
    stat_rows = [
        ("Number of students", f"{stats['count']}"),
        ("Mean score", f"{stats['mean']:.2f}"),
        ("Median score", f"{stats['median']:.2f}"),
        ("Standard deviation", f"{stats['std_dev']:.2f}"),
        ("Variance", f"{stats['variance']:.2f}"),
        ("Minimum score", f"{stats['min']:.0f}"),
        ("Maximum score", f"{stats['max']:.0f}"),
        ("25th percentile (Q1)", f"{stats['q1']:.2f}"),
        ("50th percentile (Q2)", f"{stats['q2']:.2f}"),
        ("75th percentile (Q3)", f"{stats['q3']:.2f}"),
        ("Interquartile range (IQR)", f"{stats['iqr']:.2f}"),
    ]
    table = pd.DataFrame(stat_rows, columns=["Statistic", "Value"])
    st.dataframe(table, width="stretch", hide_index=True)

    # Outlier note for the current selection.
    score_mask, low, high = statistics.find_outliers_iqr(view["score"])
    st.caption(
        f"IQR rule on scores: values below {low:.1f} or above {high:.1f} are flagged "
        f"as potential outliers — {int(score_mask.sum())} of {stats['count']} records "
        "in the current selection."
    )


# ===========================================================================
# PAGE 4 — Study Hours Analysis
# ===========================================================================
def page_study_hours() -> None:
    df = get_data()
    page_header(
        "Study Hours Analysis",
        "Do students who report more study hours tend to score higher?",
    )
    if df.empty:
        st.warning("The dataset is empty. Add records to analyse study hours.")
        return

    view = course_filter(df, "hours_filter")
    if view.empty or chart_or_empty(view, "study_hours"):
        st.info("No records match the selected courses.")
        return

    hours = view["study_hours"].to_numpy(dtype=float)
    scores = view["score"].to_numpy(dtype=float)

    report = analysis.correlation_report(view)
    slope, intercept = analysis.regression_line(hours, scores)

    # --- chart + headline numbers ---------------------------------------------
    left, right = st.columns([3, 2], gap="medium")
    with left:
        section_label("Scatter plot")
        st.pyplot(
            viz.scatter_hours_scores(
                hours, scores,
                outlier_mask=report["outlier_mask"],
                trend=(slope, intercept),
            ),
            width="stretch",
        )
    with right:
        section_label("Correlation")
        r1, r2 = st.columns(2)
        r1.metric("Pearson r (all)", f"{report['r_all']:.2f}")
        r2.metric("r excl. outliers", f"{report['r_excl']:.2f}")
        st.metric("Potential outliers (IQR)", f"{report['n_outliers']}")
        st.caption(
            "Outliers are flagged with the 1.5 x IQR rule on study hours, on scores, "
            "or both. The original dataset is never modified — the second value is "
            "computed on a separate filtered copy."
        )

    # --- outlier details ---------------------------------------------------------
    with st.expander("Identified potential outliers"):
        if report["n_outliers"] == 0:
            st.caption("No records fall outside the IQR bounds in this selection.")
        else:
            low_h, high_h = report["bounds"]["study_hours"]
            low_s, high_s = report["bounds"]["score"]

            def outlier_reason(row: pd.Series) -> str:
                reasons = []
                if row["study_hours"] > high_h:
                    reasons.append("very high study hours")
                elif row["study_hours"] < low_h:
                    reasons.append("very low study hours")
                if row["score"] > high_s:
                    reasons.append("unusually high score")
                elif row["score"] < low_s:
                    reasons.append("unusually low score")
                return "; ".join(reasons)

            outliers = view.loc[report["outlier_mask"]].copy()
            outliers["flagged for"] = outliers.apply(outlier_reason, axis=1)
            st.dataframe(
                outliers[["student_id", "course", "study_hours", "score", "flagged for"]],
                width="stretch", hide_index=True,
            )
            st.caption(
                f"Study-hours bounds: {low_h:.1f} to {high_h:.1f} hrs/week. "
                f"Score bounds: {low_s:.1f} to {high_s:.1f}."
            )

    # --- interpretation ------------------------------------------------------------
    section_label("Interpretation")
    with st.container(border=True):
        st.markdown(
            f"Across {len(view)} students, reported study hours show a "
            f"**{report['label_all']}** linear relationship with assessment scores "
            f"(r = **{report['r_all']:.2f}**). {analysis.change_explanation(report)} "
            f"The fitted trend line rises by about **{slope:.1f} score points per "
            "extra reported study hour**, on average, within this data."
        )
        st.markdown(
            "In everyday terms: students reporting more study hours *tend* to score "
            "higher in this dataset, but the spread around the trend is wide — many "
            "students do better or worse than their hours alone would suggest."
        )
        st.markdown(
            "**Important:** correlation does not establish causation. This analysis "
            "cannot claim that studying more *causes* higher scores. Self-reported "
            "hours may be inaccurate, and factors such as aptitude, attendance, "
            "health or prior knowledge could influence both variables."
        )


# ===========================================================================
# PAGE 5 — Course Comparison
# ===========================================================================
def page_courses() -> None:
    df = get_data()
    page_header(
        "Course Comparison",
        "Course-wise aggregation computed with Pandas GroupBy.",
    )
    if df.empty:
        st.warning("The dataset is empty. Add records to compare courses.")
        return

    courses = sorted(df["course"].dropna().unique().tolist())
    selected = st.multiselect(
        "Courses to compare", courses, default=courses,
        help="Pick two or more courses to focus the comparison.",
    )
    view = df[df["course"].isin(selected)]
    if view.empty:
        st.info("Select at least one course to compare.")
        return

    summary = analysis.course_summary(view)

    # --- bar charts -------------------------------------------------------------
    left, right = st.columns(2, gap="medium")
    with left:
        section_label("Average assessment score")
        st.pyplot(
            viz.course_bar_chart(summary["avg_score"], "Average score"),
            width="stretch",
        )
    with right:
        section_label("Average reported study hours")
        st.pyplot(
            viz.course_bar_chart(summary["avg_study_hours"],
                                 "Average study hrs / week", color=viz.SAGE),
            width="stretch",
        )

    # --- summary table -----------------------------------------------------------
    section_label("Course-wise summary")
    display = summary.reset_index().rename(
        columns={
            "course": "Course",
            "students": "Students",
            "avg_score": "Avg score",
            "median_score": "Median",
            "std_score": "Std dev",
            "avg_study_hours": "Avg study hrs/wk",
            "highest_score": "Highest",
            "lowest_score": "Lowest",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)


# ===========================================================================
# PAGE 6 — Add Student Record
# ===========================================================================
def page_add() -> None:
    df = get_data()
    page_header(
        "Add Student Record",
        "New records are validated, graded and saved to student_data.csv.",
    )

    course_options = sorted(set(dm.COURSES) | set(df["course"].dropna().unique().tolist()))

    with st.form("add_form"):
        st.markdown("##### New student record")
        c1, c2 = st.columns(2)
        student_id = c1.text_input("Student ID", placeholder="e.g. STU126")
        course = c2.selectbox("Course", course_options)
        c3, c4 = st.columns(2)
        hours = c3.number_input(
            "Study hours per week", min_value=0.0, max_value=80.0,
            value=10.0, step=0.5,
        )
        score = c4.number_input(
            "Assessment score", min_value=0, max_value=100, value=70, step=1,
        )
        st.caption(
            "Only an anonymous ID is stored — no names or contact details. "
            "The grade is calculated automatically from the score."
        )
        submitted = st.form_submit_button("Add record", type="primary")

    if submitted:
        errors = dm.validate_inputs(df, student_id, course, hours, score)
        if errors:
            for error in errors:
                st.error(error)
        else:
            record = StudentRecord(student_id, course, float(hours), int(score))
            save_data(
                dm.add_record(df, record),
                f"Record {record.student_id} added — grade {record.calculate_grade()}. "
                f"The dataset now holds {len(df) + 1} records and has been saved to CSV.",
            )
            st.rerun()

    st.caption(f"Current dataset: **{len(df)} records** in {df['course'].nunique()} course(s).")


# ===========================================================================
# Navigation
# ===========================================================================
show_flash()

pg = st.navigation(
    [
        st.Page(page_overview, title="Overview", icon=":material/home:", default=True),
        st.Page(page_records, title="Student Records", icon=":material/table_rows:"),
        st.Page(page_performance, title="Performance Analysis", icon=":material/query_stats:"),
        st.Page(page_study_hours, title="Study Hours Analysis", icon=":material/schedule:"),
        st.Page(page_courses, title="Course Comparison", icon=":material/library_books:"),
        st.Page(page_add, title="Add Student Record", icon=":material/person_add:"),
    ]
)
pg.run()

# Sidebar footer: dataset status shown under the navigation menu.
st.sidebar.divider()
st.sidebar.markdown(
    f"<p class='section-label'>Dataset</p>"
    f"<p style='font-size:0.82rem;color:#6e7276;line-height:1.5;'>"
    f"{len(get_data())} records &middot; student_data.csv<br>"
    "Synthetic sample data, not real student results.</p>",
    unsafe_allow_html=True,
)
