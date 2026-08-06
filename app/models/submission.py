# =============================================================
# Agri LMS — Submission Model
# =============================================================
# File    : app/models/submission.py
# Purpose : Defines the Submission database model representing
#           a learner's response to an assignment.
#
#           A Submission is created when a learner submits
#           their work for an assignment. Depending on the
#           assignment's submission_type, a submission can
#           contain:
#               - A typed text response (text_content field)
#               - An uploaded file (file_name, stored_file_name)
#               - Both a typed response and an uploaded file
#
#           Each submission has a status that tracks its
#           lifecycle from the moment it is submitted through
#           to when it is graded and the learner is notified.
#
#           The Grade model is a separate linked record
#           created by the admin when grading a submission.
#           The Submission model itself holds a convenience
#           is_graded flag and a score_percent field that
#           are updated when a Grade record is saved, to
#           make querying and display faster without always
#           joining to the Grade table.
#
# Relationships:
#   Submission >── User         (many submissions by one learner)
#   Submission >── Assignment   (many submissions for one assignment)
#   Submission ──< Grade        (one submission has one grade)
#
# Submission Lifecycle:
#   Learner opens assignment page
#       → Learner types text and/or uploads file
#       → Learner clicks Submit
#       → Submission record created (status='submitted')
#       → Admin sees submission in grading queue
#       → Admin opens submission, reviews content
#       → Admin awards score and writes feedback
#       → Grade record created
#       → Submission updated (is_graded=True, status='graded')
#       → Learner sees grade and feedback on their submission page
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# SUBMISSION STATUS CONSTANTS
# =============================================================

SUBMISSION_STATUS_SUBMITTED = 'submitted'   # Awaiting admin review
SUBMISSION_STATUS_UNDER_REVIEW = 'under_review'  # Admin is reviewing
SUBMISSION_STATUS_GRADED    = 'graded'      # Grade has been assigned
SUBMISSION_STATUS_RETURNED  = 'returned'    # Returned for revision
SUBMISSION_STATUS_LATE      = 'late'        # Submitted after deadline

SUBMISSION_STATUSES = [
    SUBMISSION_STATUS_SUBMITTED,
    SUBMISSION_STATUS_UNDER_REVIEW,
    SUBMISSION_STATUS_GRADED,
    SUBMISSION_STATUS_RETURNED,
    SUBMISSION_STATUS_LATE,
]


# =============================================================
# SUBMISSION MODEL
# =============================================================

class Submission(db.Model):
    """
    Represents a single learner submission for an assignment.

    A learner may make multiple submissions for the same
    assignment if the assignment's max_submissions allows it.
    Each submission is a separate record with its own
    content, file, status, and grade.

    The text_content field stores the learner's typed
    response. It supports plain text and can store
    lengthy written answers.

    The file fields store metadata about the uploaded
    file. The actual file is saved on the server at
    static/uploads/submissions/.

    When an admin grades a submission, a Grade record is
    created and linked to this submission via the grade
    relationship. The is_graded and score_percent fields
    on the Submission are then updated as denormalized
    copies for fast querying.
    """

    __tablename__ = 'submissions'

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique submission identifier — auto-incremented primary key'
    )

    # ── Foreign Keys ──────────────────────────────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the learner who made this submission. '
            'CASCADE: deleting a user removes all their submissions.'
        )
    )

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey('assignments.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the assignment this submission responds to. '
            'CASCADE: deleting an assignment removes all its submissions.'
        )
    )

    # ── Submission Attempt Number ─────────────────────────────
    attempt_number = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        comment=(
            'Sequential attempt number for this learner on this assignment. '
            'First submission has attempt_number=1. '
            'Each resubmission increments this by one. '
            'Used to display "Attempt 1 of 3" to the learner.'
        )
    )

    # ── Text Content ──────────────────────────────────────────
    text_content = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'The learner typed text response to the assignment. '
            'May be NULL if the learner only uploaded a file. '
            'Stored as plain text — supports lengthy written answers.'
        )
    )

    # ── File Upload Fields ────────────────────────────────────
    file_name = db.Column(
        db.String(255),
        nullable=True,
        comment=(
            'Original filename of the uploaded submission file '
            'as provided by the learner — stored for display. '
            'May be NULL if the learner only submitted text.'
        )
    )

    stored_file_name = db.Column(
        db.String(255),
        nullable=True,
        comment=(
            'UUID-prefixed server-side filename for the submission file. '
            'File is stored at static/uploads/submissions/. '
            'Used to construct the download URL.'
        )
    )

    file_extension = db.Column(
        db.String(20),
        nullable=True,
        comment=(
            'Lowercase file extension of the uploaded file — '
            'e.g. pdf, docx, png. Used for icon display and '
            'validation in the admin grading view.'
        )
    )

    file_size_bytes = db.Column(
        db.BigInteger,
        nullable=True,
        comment='File size in bytes of the uploaded submission file.'
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True,
        comment=(
            'MIME type of the uploaded submission file — '
            'e.g. application/pdf, image/png, '
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    )

    # ── Submission Status ─────────────────────────────────────
    status = db.Column(
        db.String(20),
        nullable=False,
        default=SUBMISSION_STATUS_SUBMITTED,
        comment=(
            'Current status of this submission. '
            'submitted: received and awaiting admin review | '
            'under_review: admin is currently reviewing | '
            'graded: grade has been assigned by admin | '
            'returned: returned to learner for revision | '
            'late: submitted after the assignment due_date'
        )
    )

    # ── Late Submission Flag ──────────────────────────────────
    is_late = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Flag indicating this submission was made after '
            'the assignment due_date. Set automatically at '
            'submission time by comparing to assignment.due_date.'
        )
    )

    # ── Grading Convenience Fields ────────────────────────────
    # These are denormalized copies of Grade data for fast
    # querying without always joining to the grades table

    is_graded = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Quick flag indicating whether a Grade record exists '
            'for this submission. Updated when the admin saves a grade. '
            'Used for fast filtering in submission lists.'
        )
    )

    score_percent = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        comment=(
            'Denormalized copy of the final percentage score '
            'from the linked Grade record. '
            'Updated when the admin saves the grade. '
            'Allows fast score display without joining grades table.'
        )
    )

    # ── Learner Notes ─────────────────────────────────────────
    learner_notes = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Optional notes from the learner submitted alongside '
            'their work — e.g. explanations, clarifications, '
            'or context for the submission.'
        )
    )

    # ── Admin Flags ───────────────────────────────────────────
    is_flagged = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Admin flag — True means the admin has flagged this '
            'submission for special attention — e.g. suspected '
            'plagiarism, incomplete submission, or exceptional work.'
        )
    )

    flag_reason = db.Column(
        db.String(300),
        nullable=True,
        comment=(
            'Reason the admin flagged this submission. '
            'Only visible to admins — not shown to the learner.'
        )
    )

    # ── Timestamps ────────────────────────────────────────────
    date_submitted = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when the learner submitted this work.'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this submission record.'
    )

    # ── Relationships ─────────────────────────────────────────

    # One submission has at most one grade record
    # uselist=False enforces the one-to-one relationship
    grade = db.relationship(
        'Grade',
        backref='submission',
        uselist=False,
        lazy='joined',
        cascade='all, delete-orphan'
    )

    # ==========================================================
    # CONTENT TYPE DETECTION HELPERS
    # ==========================================================

    def has_text_content(self):
        """
        Check whether this submission contains a typed
        text response from the learner.

        Returns:
            bool: True if text_content is not empty.
        """
        return bool(self.text_content and self.text_content.strip())

    def has_file(self):
        """
        Check whether this submission contains an uploaded
        file from the learner.

        Returns:
            bool: True if a stored file exists for this submission.
        """
        return bool(self.stored_file_name)

    def has_both(self):
        """
        Check whether this submission contains both a typed
        text response and an uploaded file.

        Returns:
            bool: True if both text and file are present.
        """
        return self.has_text_content() and self.has_file()

    def is_empty(self):
        """
        Check whether this submission contains neither
        text content nor an uploaded file.
        An empty submission should not normally occur
        due to frontend and backend validation.

        Returns:
            bool: True if neither text nor file is present.
        """
        return not self.has_text_content() and not self.has_file()

    # ==========================================================
    # FILE HELPERS
    # ==========================================================

    def get_file_url(self):
        """
        Build the relative URL path for downloading or
        viewing the submitted file through Flask's
        static file serving route.

        Returns:
            str or None: Relative URL path to the submission file.
                         None if no file was uploaded.

        Example:
            'uploads/submissions/a3f1c2d4_assignment1_report.pdf'
        """
        if self.stored_file_name:
            return f'uploads/submissions/{self.stored_file_name}'
        return None

    def get_file_size_display(self):
        """
        Convert raw file_size_bytes into a human-readable
        string with the appropriate unit suffix.

        Returns:
            str: Formatted file size or 'Unknown size'.

        Examples:
            1024       → '1.0 KB'
            2097152    → '2.0 MB'
        """
        if not self.file_size_bytes:
            return 'Unknown size'

        size = self.file_size_bytes
        if size < 1024:
            return f'{size} B'
        elif size < 1024 ** 2:
            return f'{size / 1024:.1f} KB'
        elif size < 1024 ** 3:
            return f'{size / (1024 ** 2):.1f} MB'
        else:
            return f'{size / (1024 ** 3):.1f} GB'

    def get_file_icon(self):
        """
        Return an emoji icon string for the uploaded file
        based on its extension, for use in templates.

        Returns:
            str: Emoji icon representing the file type.
        """
        if not self.file_extension:
            return '📁'

        icons = {
            'pdf':  '📄',
            'doc':  '📝',
            'docx': '📝',
            'ppt':  '📊',
            'pptx': '📊',
            'xls':  '📈',
            'xlsx': '📈',
            'png':  '🖼️',
            'jpg':  '🖼️',
            'jpeg': '🖼️',
            'gif':  '🖼️',
            'zip':  '📦',
            'rar':  '📦',
            'txt':  '📋',
            'py':   '🐍',
        }
        return icons.get(self.file_extension.lower(), '📁')

    # ==========================================================
    # STATUS MANAGEMENT METHODS
    # ==========================================================

    def mark_under_review(self):
        """
        Mark this submission as currently being reviewed
        by an admin. Called when the admin opens the
        submission in the grading interface.
        """
        self.status = SUBMISSION_STATUS_UNDER_REVIEW

    def mark_graded(self, score_percent):
        """
        Mark this submission as graded and update the
        denormalized score fields.

        Called automatically when an admin saves a Grade
        record for this submission.

        Args:
            score_percent (float): The final percentage score
                                   awarded by the admin.
                                   Value between 0.0 and 100.0.
        """
        self.is_graded = True
        self.status = SUBMISSION_STATUS_GRADED
        self.score_percent = round(float(score_percent), 2)

    def mark_returned(self):
        """
        Mark this submission as returned to the learner
        for revision. The learner will see feedback
        and can resubmit if the assignment allows it.
        """
        self.status = SUBMISSION_STATUS_RETURNED
        self.is_graded = False

    def flag(self, reason=None):
        """
        Flag this submission for admin attention.

        Args:
            reason (str, optional): The reason for flagging.
                                    Stored in flag_reason field.
        """
        self.is_flagged = True
        if reason:
            self.flag_reason = reason

    def unflag(self):
        """
        Remove the admin flag from this submission
        and clear the flag reason.
        """
        self.is_flagged = False
        self.flag_reason = None

    # ==========================================================
    # LATE DETECTION
    # ==========================================================

    def check_and_set_late_status(self, due_date):
        """
        Check whether this submission was made after the
        assignment due_date and update the is_late flag
        and status accordingly.

        Should be called at the moment of submission
        creation, passing the assignment's due_date.

        Args:
            due_date (datetime or None): The assignment's
                due_date. If None, submission is never late.
        """
        if due_date and datetime.utcnow() > due_date:
            self.is_late = True
            self.status = SUBMISSION_STATUS_LATE

    # ==========================================================
    # DISPLAY HELPERS
    # ==========================================================

    def get_status_label(self):
        """
        Return a human-readable label for the current
        submission status.

        Returns:
            str: Descriptive status label.
        """
        labels = {
            SUBMISSION_STATUS_SUBMITTED:    'Submitted',
            SUBMISSION_STATUS_UNDER_REVIEW: 'Under Review',
            SUBMISSION_STATUS_GRADED:       'Graded',
            SUBMISSION_STATUS_RETURNED:     'Returned for Revision',
            SUBMISSION_STATUS_LATE:         'Late Submission',
        }
        return labels.get(self.status, 'Unknown')

    def get_status_badge_class(self):
        """
        Return a CSS class name for the submission status
        badge used in admin and learner templates.

        Returns:
            str: CSS badge class string.
        """
        badge_classes = {
            SUBMISSION_STATUS_SUBMITTED:    'badge-info',
            SUBMISSION_STATUS_UNDER_REVIEW: 'badge-warning',
            SUBMISSION_STATUS_GRADED:       'badge-success',
            SUBMISSION_STATUS_RETURNED:     'badge-danger',
            SUBMISSION_STATUS_LATE:         'badge-orange',
        }
        return badge_classes.get(self.status, 'badge-secondary')

    def get_score_display(self):
        """
        Format the score_percent value into a clean
        percentage string for display in templates.

        Returns:
            str: Formatted score string or 'Not graded yet'.

        Examples:
            85.5  → '85.50%'
            100.0 → '100%'
            None  → 'Not graded yet'
        """
        if self.score_percent is None:
            return 'Not graded yet'

        value = float(self.score_percent)
        if value == int(value):
            return f'{int(value)}%'
        return f'{value:.2f}%'

    def get_text_preview(self, max_length=200):
        """
        Generate a truncated preview of the text_content
        for display in submission list views where the
        full text is too long to show.

        Args:
            max_length (int): Maximum number of characters
                              to include in the preview.
                              Default is 200.

        Returns:
            str: Truncated text with ellipsis if needed,
                 or a placeholder if no text content exists.

        Example:
            Long text → 'The soil sample collected from...'
        """
        if not self.text_content:
            return 'No text submitted'

        text = self.text_content.strip()

        if len(text) <= max_length:
            return text

        return text[:max_length].rstrip() + '...'

    def get_submission_type_display(self):
        """
        Return a human-readable description of what type
        of content this submission contains.

        Returns:
            str: Descriptive content type string.

        Examples:
            'Text and File'
            'Text only'
            'File only'
            'Empty'
        """
        if self.has_both():
            return 'Text and File'
        elif self.has_text_content():
            return 'Text only'
        elif self.has_file():
            return 'File only'
        else:
            return 'Empty'

    def get_date_submitted_display(self):
        """
        Format the date_submitted timestamp into a
        human-readable string for display in templates.

        Returns:
            str: Formatted submission date string.

        Example:
            '15 January 2025 at 02:30 PM UTC'
        """
        return self.date_submitted.strftime('%d %B %Y at %I:%M %p UTC')

    def get_days_since_submission(self):
        """
        Calculate the number of days that have passed
        since this submission was made.

        Returns:
            int: Number of days since submission.
        """
        delta = datetime.utcnow() - self.date_submitted
        return delta.days

    # ==========================================================
    # STATIC UTILITY METHODS
    # ==========================================================

    @staticmethod
    def generate_stored_filename(original_filename):
        """
        Generate a unique server-side filename for an
        uploaded submission file by prepending a UUID4
        prefix to the sanitized original filename.

        This prevents filename collisions when multiple
        learners upload files with the same name, and
        eliminates directory traversal vulnerabilities.

        Args:
            original_filename (str): The original filename
                                     as provided by the learner.

        Returns:
            str: UUID-prefixed safe filename string.

        Example:
            'assignment report.pdf' → 'b4e2f1a8_assignment_report.pdf'
        """
        import uuid
        import re

        safe_name = re.sub(r'[^\w\-.]', '_', original_filename)
        unique_id = uuid.uuid4().hex[:8]
        return f'{unique_id}_{safe_name}'

    @staticmethod
    def get_next_attempt_number(assignment_id, user_id):
        """
        Calculate the next attempt number for a learner
        submitting to a specific assignment.

        Queries existing submissions for this learner and
        assignment, then returns the count + 1.

        Args:
            assignment_id (int): The assignment's primary key.
            user_id (int): The learner's primary key.

        Returns:
            int: The next sequential attempt number.
                 Returns 1 if this is the first submission.

        Example:
            If learner has 2 existing submissions → returns 3
        """
        count = Submission.query.filter_by(
            assignment_id=assignment_id,
            user_id=user_id
        ).count()
        return count + 1

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self, include_text=False):
        """
        Serialize the Submission object to a plain dictionary
        suitable for JSON responses and template rendering.

        Args:
            include_text (bool): If True, includes the full
                text_content in the response. Default is False
                to keep list views lightweight — the full text
                is only needed in the detail/grading view.

        Returns:
            dict: Submission data with all computed fields.
        """
        data = {
            'id':                       self.id,
            'user_id':                  self.user_id,
            'assignment_id':            self.assignment_id,
            'attempt_number':           self.attempt_number,
            'has_text_content':         self.has_text_content(),
            'has_file':                 self.has_file(),
            'has_both':                 self.has_both(),
            'submission_type_display':  self.get_submission_type_display(),
            'text_preview':             self.get_text_preview(),
            'file_name':                self.file_name,
            'stored_file_name':         self.stored_file_name,
            'file_extension':           self.file_extension,
            'file_size_bytes':          self.file_size_bytes,
            'file_size_display':        self.get_file_size_display(),
            'file_icon':                self.get_file_icon(),
            'file_url':                 self.get_file_url(),
            'mime_type':                self.mime_type,
            'status':                   self.status,
            'status_label':             self.get_status_label(),
            'status_badge_class':       self.get_status_badge_class(),
            'is_late':                  self.is_late,
            'is_graded':                self.is_graded,
            'score_percent':            float(self.score_percent)
                                        if self.score_percent is not None
                                        else None,
            'score_display':            self.get_score_display(),
            'learner_notes':            self.learner_notes,
            'is_flagged':               self.is_flagged,
            'flag_reason':              self.flag_reason,
            'days_since_submission':    self.get_days_since_submission(),
            'date_submitted':           self.date_submitted.strftime('%Y-%m-%d %H:%M:%S'),
            'date_submitted_display':   self.get_date_submitted_display(),
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
        }

        # Include full text only when explicitly requested
        # Used in the admin grading view and learner detail view
        if include_text:
            data['text_content'] = self.text_content

        # Include grade data if this submission has been graded
        if self.is_graded and self.grade:
            data['grade'] = self.grade.to_dict()
        else:
            data['grade'] = None

        return data

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Submission id={self.id} '
            f'user_id={self.user_id} '
            f'assignment_id={self.assignment_id} '
            f'attempt={self.attempt_number} '
            f'status={self.status!r} '
            f'graded={self.is_graded}>'
        )