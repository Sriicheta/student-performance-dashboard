"""
student_record.py
=================

Defines the :class:`StudentRecord` class — a single anonymised student and
their assessment result.

The class demonstrates object-oriented programming (constructor, properties,
encapsulation and methods). Every value passes through a property setter, so
a ``StudentRecord`` object can never hold an invalid score or a negative
study-hours value.

No personally identifiable information is stored: only an anonymous ID, the
course name, self-reported study hours and the assessment score.
"""

# (minimum score, grade) pairs, checked from the highest floor downwards.
GRADE_FLOORS = (
    (90, "O"),
    (80, "A+"),
    (70, "A"),
    (60, "B+"),
    (50, "B"),
    (40, "C"),
)


class StudentRecord:
    """One anonymised student record.

    Attributes (read through properties):
        student_id: anonymous ID such as ``"STU001"`` (stored uppercase)
        course:     course name
        study_hours: reported study hours per week (>= 0)
        score:      assessment score between 0 and 100
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(self, student_id, course, study_hours, score):
        """Create a record; validation happens inside the property setters."""
        self.student_id = student_id
        self.course = course
        self.study_hours = study_hours
        self.score = score

    # ------------------------------------------------------------------
    # Small validation helpers used by the setters
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_text(value, field_name):
        """Strip whitespace and reject empty text."""
        text = str(value).strip()
        if not text:
            raise ValueError(f"{field_name} cannot be empty.")
        return text

    @staticmethod
    def _clean_number(value, field_name, minimum=None, maximum=None):
        """Convert to float and enforce an optional inclusive range."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a number.") from None
        if minimum is not None and number < minimum:
            raise ValueError(f"{field_name} cannot be below {minimum}.")
        if maximum is not None and number > maximum:
            raise ValueError(f"{field_name} cannot be above {maximum}.")
        return number

    # ------------------------------------------------------------------
    # Properties (encapsulation)
    # ------------------------------------------------------------------
    @property
    def student_id(self):
        """Anonymous student ID, e.g. ``"STU001"``."""
        return self._student_id

    @student_id.setter
    def student_id(self, value):
        cleaned = self._clean_text(value, "Student ID").upper()
        if " " in cleaned:
            raise ValueError("Student ID cannot contain spaces.")
        self._student_id = cleaned

    @property
    def course(self):
        """Course name."""
        return self._course

    @course.setter
    def course(self, value):
        self._course = self._clean_text(value, "Course")

    @property
    def study_hours(self):
        """Reported study hours per week (>= 0)."""
        return self._study_hours

    @study_hours.setter
    def study_hours(self, value):
        self._study_hours = self._clean_number(value, "Study hours", minimum=0)

    @property
    def score(self):
        """Assessment score (0-100)."""
        return self._score

    @score.setter
    def score(self, value):
        self._score = self._clean_number(value, "Score", minimum=0, maximum=100)

    # ------------------------------------------------------------------
    # Methods required by the project brief
    # ------------------------------------------------------------------
    def calculate_grade(self, score=None):
        """Return the letter grade for this record (or a supplied score).

        Grading system:
            90-100 -> O | 80-89 -> A+ | 70-79 -> A | 60-69 -> B+ |
            50-59  -> B | 40-49 -> C | below 40 -> F
        """
        from .statistics import grade_for_score  # local import avoids a cycle

        return grade_for_score(self._score if score is None else score)

    def get_record(self, include_grade=True):
        """Return the record as a plain dictionary (a CSV-ready row)."""
        record = {
            "student_id": self._student_id,
            "course": self._course,
            "study_hours": round(self._study_hours, 1),
            "score": int(round(self._score)),
        }
        if include_grade:
            record["grade"] = self.calculate_grade()
        return record

    def update_record(self, course=None, study_hours=None, score=None):
        """Update any of the editable fields (None = leave unchanged).

        Validation is handled automatically by the property setters, so an
        invalid value raises ``ValueError`` without touching the record.
        """
        if course is not None:
            self.course = course
        if study_hours is not None:
            self.study_hours = study_hours
        if score is not None:
            self.score = score

    # ------------------------------------------------------------------
    # Debugging helper
    # ------------------------------------------------------------------
    def __repr__(self):
        return (
            f"StudentRecord(student_id={self._student_id!r}, "
            f"course={self._course!r}, study_hours={self._study_hours}, "
            f"score={self._score})"
        )
