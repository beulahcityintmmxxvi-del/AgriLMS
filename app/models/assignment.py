# =============================================================
# Agri LMS — Assignment Model
# =============================================================
# File    : app/models/assignment.py
# Purpose : Defines the Assignment database model representing
#           tasks, exercises, and assessments created by admins
#           for learners to complete within a course.
#
#           Assignments are created by admins and attached to
#           a specific course. They can optionally be linked
#           to a specific module, or they can be course-level
#           assignments that span the entire course.
#
#           Learners submit their work through the Submission
#           model — either by typing a text response directly
#           into the platform or by uploading a file.
#
#           Admins then review each submission and assign a
#           grade with optional written feedback through the
#           Grade model.
#
#           Assignment types supported:
#               text_submission  — Learner types their answer
#                                  directly in a text editor
#               file_upload      — Learner uploads a file
#                                  (PDF, Word, image, etc.)
#               both             — Learner can submit text,
#                                  a file, or both together
#
# Relationships:
#   Assignment >── Course       (many assignments per course)
#   Assignment >── Module       (optionally linked to a module)
#   Assignment >── User         (created by an admin)
#   Assignment ──< Submission   (one assignment has many submissions)
#
# Assignment Lifecycle:
#   Admin creates assignment (is_published=False)
#       → Admin publishes assignment (is_published=True)
#       → Learners see assignment in their course dashboard
#       → Learners submit before due_date
#       → Admin reviews and grades each submission
#       → Learner sees grade and feedback
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# ASSIGNMENT TYPE CONSTANTS
# =============================================================

ASSIGNMENT_TYPE_TEXT   = 'text_submission'
ASSIGNMENT_TYPE_FILE   = 'file_upload'
ASSIGNMENT_TYPE_BOTH   = 'both'

ASSIGNMENT_TYPES = [
    ASSIGNMENT_TYPE_TEXT,
    ASSIGNMENT_TYPE_FILE,
    ASSIGNMENT_TYPE_BOTH,
]

# =============================================================
# ASSIGNMENT STATUS CONSTANTS
# =============================================================

ASSIGNMENT_STATUS_DRAFT     = 'draft'
ASSIGNMENT_STATUS_PUBLISHED = 'published'
ASSIGNMENT_STATUS_CLOSED    = 'closed'
ASSIGNMENT_STATUS_ARCHIVED  = 'archived'

ASSIGNMENT_STATUSES = [
    ASSIGNMENT_STATUS_DRAFT,
    ASSIGNMENT_STATUS_PUBLISHED,
    ASSIGNMENT_STATUS_CLOSED,
    ASSIGNMENT_STATUS_ARCHIVED,
]


# =============================================================
# ASSIGNMENT MODEL
# =============================================================

class Assignment(db.Model):
    """
    Represents a single assignment or assessment task
    within a course on the platform.

    Assignments are created and managed by admins.
    Each assignment belongs to a course and optionally
    to a specific module within that course.

    The submission_type field determines how learners
    can respond:
        text_submission — A rich text area is presented
                          for the learner to type their answer
        file_upload     — A file upload input is presented
        both            — Both a text area and file upload
                          are available simultaneously

    Grading is done per submission by the admin through
    the Grade model, which stores the score and feedback.

    The total_marks field defines the maximum possible
    score for this assignment. The admin awards a score
    between 0 and total_marks when grading a submission.
    The final_score stored on the Grade model is then
    converted to a percentage for averaging.
    """

    __tablename__ = 'assignments'

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique assignment identifier — auto-incremented primary key'
    )

    # ── Foreign Keys ──────────────────────────────────────────
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the course this assignment belongs to. '
            'CASCADE: deleting a course deletes all its assignments.'
        )
    )

    module_id = db.Column(
        db.Integer,
        db.ForeignKey('modules.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment=(
            'Foreign key — optional ID of the module this assignment '
            'is associated with. NULL means it is a course-level '
            'assignment not tied to any specific module. '
            'SET NULL: deleting a module does not delete the assignment.'
        )
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment=(
            'Foreign key — ID of the admin user who created '
            'this assignment. SET NULL if the admin is deleted.'
        )
    )

    # ── Assignment Identity ───────────────────────────────────
    title = db.Column(
        db.String(300),
        nullable=False,
        comment=(
            'Title of the assignment displayed to learners — '
            'e.g. "Assignment 1: Soil Testing Report", '
            '"Module 2 Quiz: Crop Rotation Principles"'
        )
    )

    description = db.Column(
        db.Text,
        nullable=False,
        comment=(
            'Full description of the assignment including '
            'background context, what is being assessed, '
            'and any relevant information the learner needs '
            'before starting.'
        )
    )

    instructions = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Step-by-step instructions for completing and '
            'submitting this assignment. Displayed prominently '
            'on the assignment submission page.'
        )
    )

    # ── Submission Type ───────────────────────────────────────
    submission_type = db.Column(
        db.String(20),
        nullable=False,
        default=ASSIGNMENT_TYPE_BOTH,
        comment=(
            'Determines how learners submit their work. '
            'text_submission: typed answer only | '
            'file_upload: file upload only | '
            'both: text answer and/or file upload accepted'
        )
    )

    # ── Grading Configuration ─────────────────────────────────
    total_marks = db.Column(
        db.Numeric(6, 2),
        nullable=False,
        default=100.00,
        comment=(
            'Maximum possible marks for this assignment. '
            'The admin awards a score between 0 and total_marks '
            'when grading. The percentage is then calculated as '
            '(score_awarded / total_marks) * 100.'
        )
    )

    pass_mark = db.Column(
        db.Numeric(6, 2),
        nullable=True,
        default=50.00,
        comment=(
            'Minimum marks required to pass this specific assignment. '
            'Used for individual assignment pass/fail reporting. '
            'Does not affect the overall course pass/fail — '
            'that uses the averaged final_score.'
        )
    )

    weight = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        default=1.00,
        comment=(
            'Relative weight of this assignment when calculating '
            'the course final_score. '
            'e.g. weight=2.0 means this assignment counts double '
            'compared to assignments with weight=1.0. '
            'Default is 1.0 — equal weight for all assignments.'
        )
    )

    # ── Deadline Settings ─────────────────────────────────────
    due_date = db.Column(
        db.DateTime,
        nullable=True,
        comment=(
            'UTC deadline for submitting this assignment. '
            'NULL means no deadline — submissions accepted anytime. '
            'After this date, late_submission_allowed determines '
            'whether the learner can still submit.'
        )
    )

    late_submission_allowed = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment=(
            'Whether submissions are accepted after the due_date. '
            'True: late submissions accepted and flagged as late. '
            'False: submission form is locked after due_date passes.'
        )
    )

    late_penalty_percent = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        default=0.00,
        comment=(
            'Percentage deducted from the score for late submissions. '
            'e.g. 10.00 means a 10% penalty is applied to late work. '
            '0.00 means no penalty even if submitted late.'
        )
    )

    # ── File Upload Settings ──────────────────────────────────
    allowed_file_types = db.Column(
        db.String(500),
        nullable=True,
        default='pdf,docx,doc,pptx,xlsx,png,jpg,jpeg,zip',
        comment=(
            'Comma-separated list of allowed file extensions '
            'for submissions when submission_type is file_upload or both. '
            'e.g. "pdf,docx,png,jpg"'
        )
    )

    max_file_size_mb = db.Column(
        db.Integer,
        nullable=True,
        default=20,
        comment=(
            'Maximum allowed file size in megabytes for '
            'file submissions. Default is 20MB.'
        )
    )

    max_submissions = db.Column(
        db.Integer,
        nullable=True,
        default=1,
        comment=(
            'Maximum number of submission attempts allowed '
            'per learner for this assignment. '
            'NULL or 0 means unlimited resubmissions. '
            'Default is 1 — one submission per learner.'
        )
    )

    # ── Additional Resources ──────────────────────────────────
    attachment_filename = db.Column(
        db.String(255),
        nullable=True,
        comment=(
            'Filename of an optional file the admin attaches '
            'to this assignment — e.g. a template, rubric, or '
            'reference document. Stored in static/uploads/materials/. '
            'Learners can download this before submitting.'
        )
    )

    attachment_stored_filename = db.Column(
        db.String(255),
        nullable=True,
        comment=(
            'Server-side UUID-prefixed filename for the '
            'admin attachment file.'
        )
    )

    reference_links = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Newline-separated list of external reference URLs '
            'relevant to this assignment — e.g. research articles, '
            'government agriculture resources, videos.'
        )
    )

    # ── Status and Visibility ─────────────────────────────────
    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Publication flag. '
            'False: draft — visible only to admins. '
            'True: visible to all enrolled learners in the course.'
        )
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default=ASSIGNMENT_STATUS_DRAFT,
        comment=(
            'Detailed status of the assignment. '
            'draft: being prepared by admin | '
            'published: active and accepting submissions | '
            'closed: no longer accepting submissions | '
            'archived: hidden from learner view'
        )
    )

    # ── Display Order ─────────────────────────────────────────
    order_number = db.Column(
        db.Integer,
        nullable=True,
        default=1,
        comment=(
            'Display order of this assignment within the course. '
            'Lower numbers appear first in the assignment list.'
        )
    )

    # ── Timestamps ────────────────────────────────────────────
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when this assignment was created by the admin.'
    )

    date_published = db.Column(
        db.DateTime,
        nullable=True,
        comment='UTC timestamp of when this assignment was first published.'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this assignment.'
    )

    # ── Relationships ─────────────────────────────────────────

    # One assignment has many learner submissions
    submissions = db.relationship(
        'Submission',
        backref='assignment',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Submission.date_submitted.desc()'
    )

    # Optional module relationship for module-level assignments
    module = db.relationship(
        'Module',
        foreign_keys=[module_id],
        lazy='joined',
        backref=db.backref(
            'assignments',
            lazy='dynamic'
        )
    )

    # ==========================================================
    # STATUS MANAGEMENT METHODS
    # ==========================================================

    def publish(self):
        """
        Publish this assignment, making it visible to all
        enrolled learners in the course.

        Sets is_published to True, status to 'published',
        and records the publication timestamp.
        """
        self.is_published = True
        self.status = ASSIGNMENT_STATUS_PUBLISHED
        if not self.date_published:
            self.date_published = datetime.utcnow()

    def close(self):
        """
        Close this assignment so it no longer accepts
        new submissions. Existing submissions are retained.
        Learners can still view the assignment but cannot submit.
        """
        self.status = ASSIGNMENT_STATUS_CLOSED

    def archive(self):
        """
        Archive this assignment, hiding it from learner view
        while preserving all submissions and grades.
        """
        self.status = ASSIGNMENT_STATUS_ARCHIVED
        self.is_published = False

    def reopen(self):
        """
        Reopen a closed assignment to accept new submissions.
        Restores status to published.
        """
        self.status = ASSIGNMENT_STATUS_PUBLISHED
        self.is_published = True

    # ==========================================================
    # DEADLINE HELPERS
    # ==========================================================

    def is_past_due(self):
        """
        Check whether the assignment deadline has passed.

        Returns:
            bool: True if due_date is set and has passed.
                  False if no due_date is set (no deadline).
        """
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date

    def is_accepting_submissions(self):
        """
        Determine whether the assignment is currently
        accepting new submissions from learners.

        Conditions for accepting:
            - Status must be 'published'
            - If past due, late_submission_allowed must be True

        Returns:
            bool: True if new submissions are accepted.
        """
        if self.status != ASSIGNMENT_STATUS_PUBLISHED:
            return False
        if self.is_past_due() and not self.late_submission_allowed:
            return False
        return True

    def get_days_until_due(self):
        """
        Calculate the number of days remaining until
        the assignment deadline.

        Returns:
            int or None: Positive = days remaining.
                         Negative = days overdue.
                         None = no deadline set.
        """
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days

    def get_due_date_display(self):
        """
        Format the due_date into a human-readable string
        for display in templates.

        Returns:
            str: Formatted due date string or 'No deadline'.
        """
        if not self.due_date:
            return 'No deadline'
        return self.due_date.strftime('%d %B %Y at %I:%M %p UTC')

    def get_time_remaining_display(self):
        """
        Generate a human-readable time remaining string
        for display on the assignment page.

        Returns:
            str: Descriptive time remaining or overdue string.

        Examples:
            '5 days remaining'
            '2 hours remaining'
            'Overdue by 3 days'
            'No deadline'
        """
        if not self.due_date:
            return 'No deadline'

        now = datetime.utcnow()
        delta = self.due_date - now

        if delta.total_seconds() <= 0:
            # Assignment is overdue
            overdue_delta = now - self.due_date
            days_overdue = overdue_delta.days
            if days_overdue == 0:
                hours_overdue = int(overdue_delta.total_seconds() // 3600)
                return f'Overdue by {hours_overdue} hour{"s" if hours_overdue != 1 else ""}'
            return f'Overdue by {days_overdue} day{"s" if days_overdue != 1 else ""}'

        total_seconds = int(delta.total_seconds())
        days = delta.days
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        if days > 1:
            return f'{days} days remaining'
        elif days == 1:
            return f'1 day {hours} hr remaining'
        elif hours > 0:
            return f'{hours} hour{"s" if hours != 1 else ""} remaining'
        elif minutes > 0:
            return f'{minutes} minute{"s" if minutes != 1 else ""} remaining'
        else:
            return 'Due very soon'

    # ==========================================================
    # SUBMISSION HELPERS
    # ==========================================================

    def get_total_submissions(self):
        """
        Count the total number of submissions received
        for this assignment across all learners.

        Returns:
            int: Total submission count.
        """
        return self.submissions.count()

    def get_graded_submissions_count(self):
        """
        Count how many submissions have been graded
        by an admin.

        Returns:
            int: Number of graded submissions.
        """
        from app.models.submission import Submission
        return self.submissions.filter_by(
            is_graded=True
        ).count()

    def get_pending_submissions_count(self):
        """
        Count how many submissions are awaiting grading.

        Returns:
            int: Number of ungraded submissions.
        """
        from app.models.submission import Submission
        return self.submissions.filter_by(
            is_graded=False
        ).count()

    def get_submission_by_user(self, user_id):
        """
        Retrieve the most recent submission made by a
        specific learner for this assignment.

        Args:
            user_id (int): The primary key of the learner.

        Returns:
            Submission or None: The learner's submission
                                if it exists.
        """
        from app.models.submission import Submission
        return self.submissions.filter_by(
            user_id=user_id
        ).order_by(
            Submission.date_submitted.desc()
        ).first()

    def get_submission_count_by_user(self, user_id):
        """
        Count how many times a specific learner has
        submitted work for this assignment.

        Args:
            user_id (int): The primary key of the learner.

        Returns:
            int: Number of submissions by this learner.
        """
        return self.submissions.filter_by(
            user_id=user_id
        ).count()

    def has_submitted(self, user_id):
        """
        Check whether a specific learner has submitted
        at least once for this assignment.

        Args:
            user_id (int): The primary key of the learner.

        Returns:
            bool: True if at least one submission exists.
        """
        return self.get_submission_count_by_user(user_id) > 0

    def can_learner_submit(self, user_id):
        """
        Determine whether a specific learner is currently
        allowed to make a new submission for this assignment.

        Checks:
            1. Assignment must be accepting submissions
            2. Learner must not have exceeded max_submissions

        Args:
            user_id (int): The primary key of the learner.

        Returns:
            bool: True if the learner can submit.
        """
        if not self.is_accepting_submissions():
            return False

        # Check submission limit
        if self.max_submissions and self.max_submissions > 0:
            count = self.get_submission_count_by_user(user_id)
            if count >= self.max_submissions:
                return False

        return True

    # ==========================================================
    # GRADING HELPERS
    # ==========================================================

    def get_average_score(self):
        """
        Calculate the average score across all graded
        submissions for this assignment.

        Returns:
            float or None: Average score as a percentage.
                           None if no graded submissions exist.
        """
        from app.models.submission import Submission
        from app.models.grade import Grade
        from sqlalchemy import func

        result = db.session.query(
            func.avg(Grade.score_awarded)
        ).join(
            Submission,
            Grade.submission_id == Submission.id
        ).filter(
            Submission.assignment_id == self.id
        ).scalar()

        if result is None:
            return None

        # Convert to percentage
        if self.total_marks and float(self.total_marks) > 0:
            return round((float(result) / float(self.total_marks)) * 100, 2)
        return round(float(result), 2)

    def get_highest_score(self):
        """
        Find the highest score awarded for any submission
        to this assignment.

        Returns:
            float or None: Highest score as raw marks awarded.
                           None if no graded submissions.
        """
        from app.models.submission import Submission
        from app.models.grade import Grade
        from sqlalchemy import func

        result = db.session.query(
            func.max(Grade.score_awarded)
        ).join(
            Submission,
            Grade.submission_id == Submission.id
        ).filter(
            Submission.assignment_id == self.id
        ).scalar()

        return float(result) if result is not None else None

    # ==========================================================
    # FORMATTING HELPERS
    # ==========================================================

    def get_allowed_file_types_list(self):
        """
        Parse the comma-separated allowed_file_types string
        into a clean Python list.

        Returns:
            list[str]: List of allowed file extension strings.

        Example:
            'pdf,docx,png' → ['pdf', 'docx', 'png']
        """
        if not self.allowed_file_types:
            return []
        return [
            ext.strip().lower()
            for ext in self.allowed_file_types.split(',')
            if ext.strip()
        ]

    def get_reference_links_list(self):
        """
        Parse the newline-separated reference_links text
        into a clean Python list.

        Returns:
            list[str]: List of reference URL strings.
        """
        if not self.reference_links:
            return []
        return [
            link.strip()
            for link in self.reference_links.splitlines()
            if link.strip()
        ]

    def get_submission_type_label(self):
        """
        Return a human-readable label for the submission type.

        Returns:
            str: Descriptive submission type label.
        """
        labels = {
            ASSIGNMENT_TYPE_TEXT: 'Text Submission',
            ASSIGNMENT_TYPE_FILE: 'File Upload',
            ASSIGNMENT_TYPE_BOTH: 'Text or File Upload',
        }
        return labels.get(self.submission_type, 'Submission')

    def get_status_badge_class(self):
        """
        Return a CSS class name for the assignment status
        badge used in admin and learner templates.

        Returns:
            str: CSS badge class string.
        """
        badge_classes = {
            ASSIGNMENT_STATUS_DRAFT:     'badge-secondary',
            ASSIGNMENT_STATUS_PUBLISHED: 'badge-success',
            ASSIGNMENT_STATUS_CLOSED:    'badge-warning',
            ASSIGNMENT_STATUS_ARCHIVED:  'badge-dark',
        }
        return badge_classes.get(self.status, 'badge-secondary')

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self, user_id=None):
        """
        Serialize the Assignment object to a plain dictionary.

        Args:
            user_id (int, optional): If provided, includes
                learner-specific fields such as has_submitted
                and can_submit for the given user.

        Returns:
            dict: Assignment data with all computed fields.
        """
        data = {
            'id':                       self.id,
            'course_id':                self.course_id,
            'module_id':                self.module_id,
            'created_by':               self.created_by,
            'title':                    self.title,
            'description':              self.description,
            'instructions':             self.instructions,
            'submission_type':          self.submission_type,
            'submission_type_label':    self.get_submission_type_label(),
            'total_marks':              float(self.total_marks),
            'pass_mark':                float(self.pass_mark)
                                        if self.pass_mark else None,
            'weight':                   float(self.weight)
                                        if self.weight else 1.0,
            'due_date':                 self.due_date.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.due_date else None,
            'due_date_display':         self.get_due_date_display(),
            'time_remaining':           self.get_time_remaining_display(),
            'is_past_due':              self.is_past_due(),
            'late_submission_allowed':  self.late_submission_allowed,
            'late_penalty_percent':     float(self.late_penalty_percent)
                                        if self.late_penalty_percent else 0.0,
            'allowed_file_types':       self.get_allowed_file_types_list(),
            'max_file_size_mb':         self.max_file_size_mb,
            'max_submissions':          self.max_submissions,
            'attachment_filename':      self.attachment_filename,
            'reference_links':          self.get_reference_links_list(),
            'is_published':             self.is_published,
            'status':                   self.status,
            'status_badge_class':       self.get_status_badge_class(),
            'order_number':             self.order_number,
            'is_accepting_submissions': self.is_accepting_submissions(),
            'total_submissions':        self.get_total_submissions(),
            'graded_submissions':       self.get_graded_submissions_count(),
            'pending_submissions':      self.get_pending_submissions_count(),
            'average_score':            self.get_average_score(),
            'highest_score':            self.get_highest_score(),
            'date_created':             self.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            'date_published':           self.date_published.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_published else None,
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
        }

        # Include learner-specific fields if user_id is provided
        if user_id is not None:
            data['has_submitted']  = self.has_submitted(user_id)
            data['can_submit']     = self.can_learner_submit(user_id)
            data['submission_count'] = self.get_submission_count_by_user(user_id)

        return data

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Assignment id={self.id} '
            f'course_id={self.course_id} '
            f'title={self.title!r} '
            f'status={self.status!r}>'
        )