# Student Performance & Study-Hours Analytics Dashboard

An interactive analytics dashboard, built with Python and Streamlit, that
investigates the relationship between students' reported study hours and their
academic assessment scores using anonymised student records.

> **Data notice:** the bundled dataset (`student_data.csv`) is **synthetic
> sample data** generated with a fixed random seed — it is not actual student
> results. No personally identifiable information is collected or stored; each
> record holds only an anonymous ID, a course name, self-reported study hours
> and an assessment score.

---

## Project overview

The dashboard answers a simple analytical question: *do students who report
more study hours tend to achieve higher assessment scores?* It does this with
six connected views, all computed live from the CSV dataset:

| # | Page | What it shows |
|---|------|----------------|
| 1 | **Overview** | Key metrics (student count, average score, average study hours, highest/lowest score), a score-distribution histogram, a study-hours vs score scatter plot and an auto-generated statistical summary. |
| 2 | **Student Records** | Searchable, sortable, filterable record table with add/edit/delete and CSV export. |
| 3 | **Performance Analysis** | Full descriptive statistics (mean, median, standard deviation, variance, min, max, Q1/Q2/Q3, IQR), a histogram and a box plot. |
| 4 | **Study Hours Analysis** | Scatter plot with trend line, Pearson correlation **before and after excluding IQR outliers**, and a plain-language interpretation — including an explicit note that correlation does not establish causation. |
| 5 | **Course Comparison** | Pandas GroupBy aggregation per course: counts, mean, median, standard deviation, average study hours, highest and lowest score, with comparison bar charts. |
| 6 | **Add Student Record** | Validated entry form; new records are graded automatically and persisted to CSV. |

All statistics and charts are recalculated from the current dataset whenever
records are added, edited, deleted or filtered — nothing is hardcoded.

## Objectives

- Demonstrate practical Python, NumPy, Pandas, Matplotlib/Seaborn, CSV
  handling and OOP in one coherent application.
- Practise the full data workflow: load → validate → filter → aggregate →
  visualise → interpret.
- Communicate statistics honestly: outliers are examined, not silently
  removed, and correlation is never presented as causation.

## Technologies used

- **Python 3** (developed and tested on Python 3.13, Windows 11)
- **Streamlit** — dashboard interface and navigation
- **NumPy** — array operations and statistical calculations
- **Pandas** — CSV I/O, DataFrames, filtering, sorting, GroupBy aggregation
- **Matplotlib + Seaborn** — data visualisation
- **CSV** — persistent storage (`student_data.csv`)
- **OOP** — the `StudentRecord` class with encapsulated, validated attributes

## Python concepts demonstrated

- **NumPy arrays:** storing scores/hours, `np.mean`, `np.median`, `np.std`,
  `np.var`, `np.percentile`, `np.corrcoef`, `np.polyfit`, boolean masking.
- **Pandas DataFrames:** reading/writing CSV, cleaning and coercing types,
  boolean filtering, sorting, `groupby().agg(...)` named aggregation,
  concatenating new rows.
- **Dictionaries:** records as dictionaries (`get_record()`), statistics
  returned as dictionaries, course profiles as dictionaries.
- **CSV file handling:** automatic sample-data creation, saving on every
  add/edit/delete, graceful handling of missing/invalid rows.
- **OOP:** `StudentRecord` with constructor, properties (encapsulation +
  validation), `calculate_grade()`, `get_record()`, `update_record()`.
- **Functions:** reusable, documented helpers for averages, grades, score
  statistics, outlier detection, correlation, course summaries and I/O.
- **Modular design:** interface, data, statistics, analysis and charts are
  kept in separate modules.

## Project structure

```
student-performance-dashboard/
├── app.py                      # Streamlit interface (all six pages)
├── student_data.csv            # the dataset (auto-created on first run)
├── requirements.txt
├── README.md
├── generate_student_data.py    # regenerates the sample CSV (seed = 42)
├── modules/
│   ├── __init__.py
│   ├── student_record.py       # StudentRecord class (OOP, grades)
│   ├── data_manager.py         # CSV I/O, sample data, validation, CRUD
│   ├── statistics.py           # NumPy stats, outliers, correlation, grades
│   ├── analysis.py             # Pandas aggregation + interpretation text
│   └── visualizations.py       # Matplotlib/Seaborn charts, shared style
├── assets/
│   └── custom.css              # dashboard styling (palette, cards, charts)
└── .streamlit/
    └── config.toml             # Streamlit theme
```

## Installation

Requires Python 3.10+ (tested on 3.13). From the project folder:

```bash
pip install -r requirements.txt
```

## How to run

```bash
streamlit run app.py
```

The browser opens at `http://localhost:8501`. If `student_data.csv` does not
exist, a reproducible synthetic dataset (125 records across four courses) is
created automatically. To regenerate it manually:

```bash
python generate_student_data.py
```

## Troubleshooting (Windows)

- **Port already in use.** If `8501` is taken, run
  `streamlit run app.py --server.port 8502`.
- **`OSError: [WinError 64]` / server stops accepting connections.** This is an
  upstream quirk between Python 3.13's default (IOCP) event loop and the web
  server when a connection is aborted mid-handshake. It is not caused by this
  app's code. If it appears, start the app with the selector event loop:

  ```bash
  python -c "import asyncio; asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()); from streamlit.web import cli as stcli; import sys; sys.argv=['streamlit','run','app.py']; stcli.main()"
  ```

## Statistical methods used

- **Descriptive statistics:** mean, median, standard deviation, variance,
  minimum, maximum, 25th/50th/75th percentiles and the interquartile range,
  all computed with NumPy (`modules/statistics.py`).
- **Outlier detection:** the 1.5 × IQR rule, applied independently to study
  hours and to scores. Flagged records are *highlighted, not removed* — the
  original dataset is always preserved.
- **Pearson correlation coefficient:** computed on the full data and again
  after excluding IQR-flagged outliers, so the page can state whether the
  association becomes weaker, stronger or stays similar once extreme records
  are set aside.
- **Simple linear regression:** a least-squares trend line via `np.polyfit`
  (descriptive only — it is a summary of the observed pattern, not a causal
  model).
- **Course aggregation:** Pandas GroupBy with per-course count, mean, median,
  standard deviation and averages.

## Grade calculation

| Score | Grade |
|-------|-------|
| 90–100 | O |
| 80–89  | A+ |
| 70–79  | A |
| 60–69  | B+ |
| 50–59  | B |
| 40–49  | C |
| Below 40 | F |

Grades are derived from the score on the fly (never stored), so editing a
score instantly updates the grade everywhere.

## Limitations of the analysis

- **Correlation is not causation.** A higher correlation between reported
  study hours and scores does not prove that studying more *causes* higher
  scores; unmeasured factors (aptitude, attendance, health, prior knowledge)
  may influence both.
- **Self-reported data.** Study hours are student estimates and may be
  inaccurate or rounded.
- **Synthetic dataset.** The bundled data is generated for demonstration and
  includes deliberate outliers so the IQR analysis is meaningful; real
  datasets will behave differently.
- **IQR sensitivity.** The 1.5 × IQR rule is a heuristic; different thresholds
  (e.g. 3 × IQR) flag different records, so "outlier" here means *potential*
  outlier.
- **Small scope.** With roughly a hundred records and no control variables,
  the analysis is descriptive rather than inferential — no significance
  testing or confidence intervals are attempted.
- **Simple linear model.** A straight trend line summarises the pattern but
  cannot capture curvature or interaction between courses.

All pages remain honest about these limits: the Study Hours page explicitly
states that correlation does not establish causation and never claims that
studying more necessarily raises scores.
