# =============================================================
# Agri LMS — Grade Model
# =============================================================
# File    : app/models/grade.py
# Purpose : Defines the Grade database model representing an
#           admin's evaluation of a learner's submission.
#
#           A Grade record is created by an admin when they
#           review and score a learner's Submission. Each
#           Submission can have at most one Grade record —
#           enforced by the unique constraint on submission_id
#           and by the one-to-one relationship defined on
#           the Submission model.
#
#           The Grade stores:
#               - The raw score awarded (score_awarded)
#               - The maximum possible score (max_score)
#               - The calculated percentage (score_percent)
#               - Written feedback from the admin (feedback)
#               - A rubric breakdown (rubric_scores) for
#                 detailed criterion-by-criterion scoring
#               - Whether the submission passed (is_passed)
#               - Whether the learner has been notified
#
#           When a Grade is saved, the following happens
#           automatically through the post-save logic in
#           the route handler:
#               1. Submission.is_graded is set to True
#               2. Submission.score_percent is updated
#               3. Submission.status is set to 'graded'
#               4. Enrollment.final_score is recalculated
#                  by averaging all graded assignment scores
#                  for that learner in that course
#
# Relationships:
#   Grade >── Submission    (one grade belongs to one submission)
#   Grade >── User          (one grade awarded by one admin)
#
# Grading Lifecycle:
#   Admin opens submission in grading interface
#       → Admin reviews text content and/or downloads file
#       → Admin enters score_awarded and written feedback
#       → Admin optionally fills in rubric_scores breakdown
#       → Admin clicks Save Grade
#       → Grade record created
#       → Submission.mark_graded(score_percent) called
#       → Enrollment.final_score recalculated
#       → Learner sees grade and feedback on their page
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# GRADE MODEL
# =============================================================

class Grade(db.Model):
    """
    Represents the admin's evaluation of a single submission.

    One Grade record exists per Submission — enforced by the
    unique constraint on submission_id. If the admin needs
    to revise a grade, they update the existing Grade record
    rather than creating a new one.

    The score_percent field is calculated automatically
    from score_awarded and max_score when the grade is
    created or updated:
        score_percent = (score_awarded / max_score) * 100

    The is_passed field is determined by comparing
    score_percent against the assignment's pass_mark:
        is_passed = score_percent >= pass_mark_percent

    The feedback field supports free-form written comments
    from the admin to the learner, explaining what was
    done well, what needs improvement, and any suggestions
    for the learner's agricultural practice or further study.

    The rubric_scores field is an optional JSON-formatted
    text field that allows the admin to break down the
    score by individual assessment criteria — for example:
        {
            "Content Accuracy": 18,
            "Practical Application": 15,
            "Presentation": 8,
            "References": 9
        }
    """

    __tablename__ = 'grades'

    # ── Table-level constraints ───────────────────────────────
    __table_args__ = (
        # One grade per submission — enforces one-to-one
        db.UniqueConstraint(
            'submission_id',
            name='uq_grade_submission'
        ),
    )

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique grade identifier — auto-incremented primary key'
    )

    # ── Foreign Keys ──────────────────────────────────────────
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('submissions.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True,
        comment=(
            'Foreign key — ID of the submission being graded. '
            'UNIQUE: enforces one grade per submission. '
            'CASCADE: deleting a submission deletes its grade.'
        )
    )

    graded_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment=(
            'Foreign key — ID of the admin user who graded '
            'this submission. SET NULL if the admin is deleted.'
        )
    )

    # ── Score Fields ──────────────────────────────────────────
    score_awarded = db.Column(
        db.Numeric(6, 2),
        nullable=False,
        comment=(
            'The raw score awarded by the admin for this submission. '
            'Must be between 0 and max_score. '
            'e.g. If total_marks=100 and admin awards 75, '
            'score_awarded=75.00'
        )
    )

    max_score = db.Column(
        db.Numeric(6, 2),
        nullable=False,
        comment=(
            'The maximum possible score for this assignment — '
            'copied from Assignment.total_marks at grading time. '
            'Stored here so the grade remains accurate even if '
            'the assignment total_marks is later changed.'
        )
    )

    score_percent = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        comment=(
            'The final percentage score calculated as: '
            '(score_awarded / max_score) * 100. '
            'Calculated and stored at grading time. '
            'This is the value used for enrollment final_score averaging.'
        )
    )

    # ── Pass / Fail ───────────────────────────────────────────
    is_passed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Pass/fail flag for this individual assignment submission. '
            'True if score_percent >= assignment.pass_mark (as percentage). '
            'Calculated at grading time.'
        )
    )

    # ── Late Penalty ──────────────────────────────────────────
    late_penalty_applied = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        default=0.00,
        comment=(
            'Percentage penalty applied to this submission because '
            'it was submitted late. Copied from '
            'Assignment.late_penalty_percent when the submission '
            'is flagged as late. '
            'e.g. 10.00 means 10 percent was deducted. '
            '0.00 means no penalty was applied.'
        )
    )

    adjusted_score_percent = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        comment=(
            'The final score_percent after applying the late penalty. '
            'adjusted_score_percent = score_percent - late_penalty_applied. '
            'If no late penalty, this equals score_percent. '
            'This is the value that flows into enrollment final_score.'
        )
    )

    # ── Feedback ──────────────────────────────────────────────
    feedback = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Written feedback from the admin to the learner. '
            'Should explain what was done well, what needs '
            'improvement, and offer constructive suggestions. '
            'Displayed to the learner on their submission page '
            'after grading is complete.'
        )
    )

    # ── Rubric Breakdown ──────────────────────────────────────
    rubric_scores = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Optional JSON-formatted text storing a criterion-by-'
            'criterion breakdown of the score. '
            'Format: {"Criterion Name": score_value, ...} '
            'e.g. {"Content Accuracy": 18, "Practical Application": 15} '
            'Displayed as a breakdown table in the grading and '
            'learner feedback views.'
        )
    )

    # ── Internal Admin Notes ──────────────────────────────────
    internal_notes = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Internal grading notes visible only to admins — '
            'not shown to the learner. Used for recording '
            'grading rationale, moderation notes, or '
            'quality assurance comments.'
        )
    )

    # ── Grade Revision Tracking ───────────────────────────────
    is_revised = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Flag indicating whether this grade has been revised '
            'after the initial grading. True if the admin has '
            'updated the score or feedback at least once after '
            'the original grading.'
        )
    )

    revision_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        comment=(
            'Number of times this grade has been revised. '
            'Incremented each time the admin updates the grade '
            'after the initial submission.'
        )
    )

    revision_reason = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Admin explanation for why the grade was revised — '
            'e.g. marking error corrected, moderation applied, '
            'appeal granted. Visible to the learner.'
        )
    )

    # ── Notification Status ───────────────────────────────────
    learner_notified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Flag indicating whether the learner has been notified '
            'about this grade. Set to True after the platform '
            'displays or sends the grade notification to the learner.'
        )
    )

    # ── Timestamps ────────────────────────────────────────────
    date_graded = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when this grade was first created by the admin.'
    )

    date_revised = db.Column(
        db.DateTime,
        nullable=True,
        comment='UTC timestamp of the most recent grade revision.'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this grade record.'
    )

    # ==========================================================
    # SCORE CALCULATION METHODS
    # ==========================================================

    @staticmethod
    def calculate_score_percent(score_awarded, max_score):
        """
        Calculate the percentage score from raw score values.

        Args:
            score_awarded (float): The raw score the admin awarded.
            max_score (float): The maximum possible score.

        Returns:
            float: Percentage score rounded to 2 decimal places.
                   Returns 0.0 if max_score is zero or None.

        Example:
            calculate_score_percent(75, 100) → 75.0
            calculate_score_percent(18, 25)  → 72.0
        """
        if not max_score or float(max_score) <= 0:
            return 0.0
        percent = (float(score_awarded) / float(max_score)) * 100
        return round(percent, 2)

    @staticmethod
    def calculate_adjusted_score(score_percent, late_penalty_percent):
        """
        Apply a late submission penalty to a score percentage.

        Args:
            score_percent (float): The raw percentage score.
            late_penalty_percent (float): Percentage to deduct.

        Returns:
            float: Adjusted score after penalty, minimum 0.0.

        Example:
            calculate_adjusted_score(85.0, 10.0) → 75.0
            calculate_adjusted_score(5.0, 10.0)  → 0.0
        """
        if not late_penalty_percent or float(late_penalty_percent) <= 0:
            return round(float(score_percent), 2)
        adjusted = float(score_percent) - float(late_penalty_percent)
        return round(max(adjusted, 0.0), 2)

    def compute_and_set_scores(self, pass_mark_percent=50.0):
        """
        Calculate and set score_percent, adjusted_score_percent,
        and is_passed based on the current score_awarded,
        max_score, and late_penalty_applied values.

        Should be called after setting score_awarded, max_score,
        and late_penalty_applied before saving the grade.

        Args:
            pass_mark_percent (float): The minimum percentage
                required to pass this assignment. Defaults to 50.0.

        Example:
            grade.score_awarded = 75
            grade.max_score = 100
            grade.late_penalty_applied = 10
            grade.compute_and_set_scores(pass_mark_percent=50.0)
            # score_percent = 75.0
            # adjusted_score_percent = 65.0
            # is_passed = True
        """
        self.score_percent = self.calculate_score_percent(
            self.score_awarded,
            self.max_score
        )

        penalty = float(self.late_penalty_applied) if self.late_penalty_applied else 0.0
        self.adjusted_score_percent = self.calculate_adjusted_score(
            self.score_percent,
            penalty
        )

        self.is_passed = float(self.adjusted_score_percent) >= float(pass_mark_percent)

    # ==========================================================
    # REVISION METHODS
    # ==========================================================

    def revise(self, reason=None):
        """
        Record a grade revision by incrementing the revision
        counter, setting the is_revised flag, recording the
        revision timestamp, and storing the reason.

        Args:
            reason (str, optional): The reason for revising
                                    the grade.
        """
        self.is_revised = True
        self.revision_count += 1
        self.date_revised = datetime.utcnow()
        if reason:
            self.revision_reason = reason

    def mark_learner_notified(self):
        """
        Mark that the learner has been notified about
        this grade result.
        """
        self.learner_notified = True

    # ==========================================================
    # RUBRIC HELPERS
    # ==========================================================

    def get_rubric_scores_dict(self):
        """
        Parse the JSON-formatted rubric_scores text field
        into a Python dictionary.

        Returns:
            dict: Criterion-to-score mapping or empty dict.
        """
        if not self.rubric_scores:
            return {}
        try:
            import json
            return json.loads(self.rubric_scores)
        except (ValueError, TypeError):
            return {}

    def set_rubric_scores_from_dict(self, scores_dict):
        """
        Serialize a Python dictionary of rubric scores
        into JSON text for storage.

        Args:
            scores_dict (dict): Criterion-to-score mapping.
        """
        import json
        self.rubric_scores = json.dumps(scores_dict)

    def get_rubric_total(self):
        """
        Sum all criterion scores in the rubric breakdown.

        Returns:
            float: Sum of all rubric criterion scores.
        """
        rubric = self.get_rubric_scores_dict()
        if not rubric:
            return 0.0
        return sum(float(v) for v in rubric.values())

    # ==========================================================
    # DISPLAY HELPERS
    # ==========================================================

    def get_score_display(self):
        """
        Format the score as 'awarded / max' string.

        Returns:
            str: Formatted score string.
        """
        awarded = float(self.score_awarded) if self.score_awarded else 0.0
        maximum = float(self.max_score) if self.max_score else 0.0
        return f'{awarded:g} / {maximum:g}'

    def get_percent_display(self):
        """
        Format score_percent as a clean percentage string.

        Returns:
            str: Formatted percentage string.
        """
        if self.score_percent is None:
            return '0%'
        value = float(self.score_percent)
        if value == int(value):
            return f'{int(value)}%'
        return f'{value:.2f}%'

    def get_adjusted_percent_display(self):
        """
        Format adjusted_score_percent with penalty note.

        Returns:
            str: Formatted adjusted percentage string.
        """
        if self.adjusted_score_percent is None:
            return '0%'

        value = float(self.adjusted_score_percent)
        display = f'{int(value)}%' if value == int(value) else f'{value:.2f}%'

        penalty = float(self.late_penalty_applied) if self.late_penalty_applied else 0.0
        if penalty > 0:
            display += f' (after {penalty:g}% late penalty)'

        return display

    def get_grade_letter(self):
        """
        Convert adjusted_score_percent into a letter grade.

        Scale:
            A — 70% and above   (Distinction)
            B — 60% to 69%      (Merit)
            C — 50% to 59%      (Pass)
            D — 40% to 49%      (Below Pass)
            F — Below 40%       (Fail)

        Returns:
            str: Single letter grade.
        """
        if self.adjusted_score_percent is None:
            return 'F'

        score = float(self.adjusted_score_percent)

        if score >= 70:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'

    def get_grade_label(self):
        """
        Return a descriptive label for the letter grade.

        Returns:
            str: Full grade label.
        """
        labels = {
            'A': 'Distinction',
            'B': 'Merit',
            'C': 'Pass',
            'D': 'Below Pass',
            'F': 'Fail',
        }
        return labels.get(self.get_grade_letter(), 'Fail')

    def get_grade_badge_class(self):
        """
        Return a CSS class for the grade letter badge.

        Returns:
            str: CSS badge class string.
        """
        badge_classes = {
            'A': 'badge-success',
            'B': 'badge-primary',
            'C': 'badge-info',
            'D': 'badge-warning',
            'F': 'badge-danger',
        }
        return badge_classes.get(self.get_grade_letter(), 'badge-secondary')

    def get_date_graded_display(self):
        """
        Format date_graded into a readable string.

        Returns:
            str: Formatted grading date string.
        """
        return self.date_graded.strftime('%d %B %Y at %I:%M %p UTC')

    def get_turnaround_days(self):
        """
        Calculate days between submission and grading.

        Returns:
            int or None: Turnaround days or None.
        """
        if self.submission and self.submission.date_submitted:
            delta = self.date_graded - self.submission.date_submitted
            return max(delta.days, 0)
        return None

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self, include_internal_notes=False):
        """
        Serialize the Grade object to a plain dictionary.

        Args:
            include_internal_notes (bool): Include admin-only
                internal_notes field. Default False.

        Returns:
            dict: Grade data with all computed display fields.
        """
        data = {
            'id':                       self.id,
            'submission_id':            self.submission_id,
            'graded_by':                self.graded_by,
            'score_awarded':            float(self.score_awarded),
            'max_score':                float(self.max_score),
            'score_percent':            float(self.score_percent),
            'score_display':            self.get_score_display(),
            'percent_display':          self.get_percent_display(),
            'late_penalty_applied':     float(self.late_penalty_applied)
                                        if self.late_penalty_applied else 0.0,
            'adjusted_score_percent':   float(self.adjusted_score_percent)
                                        if self.adjusted_score_percent is not None
                                        else float(self.score_percent),
            'adjusted_percent_display': self.get_adjusted_percent_display(),
            'is_passed':                self.is_passed,
            'grade_letter':             self.get_grade_letter(),
            'grade_label':              self.get_grade_label(),
            'grade_badge_class':        self.get_grade_badge_class(),
            'feedback':                 self.feedback,
            'rubric_scores':            self.get_rubric_scores_dict(),
            'rubric_total':             self.get_rubric_total(),
            'is_revised':               self.is_revised,
            'revision_count':           self.revision_count,
            'revision_reason':          self.revision_reason,
            'learner_notified':         self.learner_notified,
            'turnaround_days':          self.get_turnaround_days(),
            'date_graded':              self.date_graded.strftime('%Y-%m-%d %H:%M:%S'),
            'date_graded_display':      self.get_date_graded_display(),
            'date_revised':             self.date_revised.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_revised else None,
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
        }

        if include_internal_notes:
            data['internal_notes'] = self.internal_notes

        return data

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Grade id={self.id} '
            f'submission_id={self.submission_id} '
            f'score={self.score_awarded}/{self.max_score} '
            f'({self.score_percent}%) '
            f'letter={self.get_grade_letter()} '
            f'passed={self.is_passed}>'
        )