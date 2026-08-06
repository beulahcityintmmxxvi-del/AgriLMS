# =============================================================
# Agri LMS — Enrollment Model
# =============================================================
# File    : app/models/enrollment.py
# Purpose : Defines the Enrollment database model representing
#           the formal relationship between a learner and a
#           course they have joined.
#
#           An Enrollment is created when a learner clicks
#           "Enroll" on a course. It tracks the full lifecycle
#           of a learner's journey through a course — from
#           enrollment date through to completion, including
#           their overall progress percentage, final score,
#           and certificate eligibility.
#
#           This model is the central linking table between
#           the User and Course models, and it is the primary
#           source of truth for:
#               - Whether a learner has access to a course
#               - How far through the course a learner is
#               - Whether a learner has completed the course
#               - Whether a learner passed and earned a certificate
#
# Relationships:
#   Enrollment >── User     (many enrollments belong to one user)
#   Enrollment >── Course   (many enrollments belong to one course)
#
# Enrollment Lifecycle:
#   Learner clicks Enroll
#       → Enrollment created (status='pending' if approval needed
#                             status='active' if open enrollment)
#       → Learner accesses modules
#       → progress_percent updates as modules are completed
#       → final_score calculated from assignment grades
#       → is_completed set True when last module is done
#       → is_passed set True if final_score >= course passing_score
#       → certificate_issued set True if eligible
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# ENROLLMENT STATUS CONSTANTS
# =============================================================

ENROLLMENT_STATUS_PENDING   = 'pending'     # Awaiting admin approval
ENROLLMENT_STATUS_ACTIVE    = 'active'      # Approved and learning
ENROLLMENT_STATUS_COMPLETED = 'completed'   # Finished all modules
ENROLLMENT_STATUS_SUSPENDED = 'suspended'   # Temporarily blocked
ENROLLMENT_STATUS_DROPPED   = 'dropped'     # Learner withdrew

ENROLLMENT_STATUSES = [
    ENROLLMENT_STATUS_PENDING,
    ENROLLMENT_STATUS_ACTIVE,
    ENROLLMENT_STATUS_COMPLETED,
    ENROLLMENT_STATUS_SUSPENDED,
    ENROLLMENT_STATUS_DROPPED,
]


# =============================================================
# ENROLLMENT MODEL
# =============================================================

class Enrollment(db.Model):
    """
    Represents a single learner's enrollment in a single course.

    Each Enrollment record is unique per learner per course —
    enforced by the uq_enrollment_user_course constraint.
    A learner cannot enroll in the same course twice.

    The enrollment tracks:
        - Access status (active, pending, suspended, dropped)
        - Progress through the course (progress_percent)
        - Completion status (is_completed)
        - Pass/fail status (is_passed)
        - Final score (final_score from graded assignments)
        - Certificate eligibility (certificate_issued)
    """

    __tablename__ = 'enrollments'

    # ── Table-level constraints ───────────────────────────────
    __table_args__ = (
        # One learner can only enroll in a course once
        db.UniqueConstraint(
            'user_id',
            'course_id',
            name='uq_enrollment_user_course'
        ),
    )

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique enrollment identifier — auto-incremented primary key'
    )

    # ── Foreign Keys ──────────────────────────────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the learner who enrolled. '
            'CASCADE: deleting a user removes all their enrollments.'
        )
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the course the learner enrolled in. '
            'CASCADE: deleting a course removes all its enrollments.'
        )
    )

    # ── Enrollment Status ─────────────────────────────────────
    status = db.Column(
        db.String(20),
        nullable=False,
        default=ENROLLMENT_STATUS_ACTIVE,
        comment=(
            'Current status of this enrollment. '
            'pending: awaiting admin approval | '
            'active: learner has full course access | '
            'completed: all modules finished | '
            'suspended: access temporarily blocked | '
            'dropped: learner withdrew from the course'
        )
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment=(
            'Quick access flag derived from status. '
            'True when status is active or completed. '
            'False when pending, suspended, or dropped. '
            'Used for fast filtering without string comparison.'
        )
    )

    # ── Progress Tracking ─────────────────────────────────────
    progress_percent = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=0.00,
        comment=(
            'Overall course progress as a percentage (0.00 to 100.00). '
            'Calculated as: (completed modules / total published modules) * 100. '
            'Updated automatically each time a learner completes a module.'
        )
    )

    modules_completed = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        comment=(
            'Running count of how many modules this learner '
            'has marked as complete in this course.'
        )
    )

    last_accessed_module_id = db.Column(
        db.Integer,
        db.ForeignKey('modules.id', ondelete='SET NULL'),
        nullable=True,
        comment=(
            'Foreign key — ID of the last module the learner '
            'opened or was viewing. Used to resume learning '
            'from where they left off.'
        )
    )

    # ── Completion ────────────────────────────────────────────
    is_completed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Course completion flag. '
            'Set to True automatically when the learner completes '
            'the module where is_last_module=True. '
            'Once True, the system calculates final_score '
            'and determines is_passed.'
        )
    )

    date_completed = db.Column(
        db.DateTime,
        nullable=True,
        comment=(
            'UTC timestamp of when the learner completed '
            'the final module and is_completed was set to True.'
        )
    )

    # ── Scoring and Grading ───────────────────────────────────
    final_score = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        comment=(
            'Final averaged score across all graded assignments '
            'for this course enrollment. Expressed as a percentage. '
            'Calculated when the course is completed or on demand.'
        )
    )

    is_passed = db.Column(
        db.Boolean,
        nullable=True,
        comment=(
            'Pass/fail flag. '
            'Set to True if final_score >= course.passing_score. '
            'Null until the course is completed and scored.'
        )
    )

    # ── Certificate ───────────────────────────────────────────
    certificate_issued = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Certificate issuance flag. '
            'True when: is_completed=True AND is_passed=True '
            'AND course.certificate_available=True. '
            'Enables the certificate download link for the learner.'
        )
    )

    certificate_issued_date = db.Column(
        db.DateTime,
        nullable=True,
        comment='UTC timestamp of when the certificate was issued to the learner.'
    )

    # ── Admin Notes ───────────────────────────────────────────
    admin_notes = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Internal admin-only notes about this enrollment — '
            'e.g. special accommodations, approval reasons, '
            'suspension reasons. Not visible to the learner.'
        )
    )

    # ── Timestamps ────────────────────────────────────────────
    date_enrolled = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when the learner submitted the enrollment request.'
    )

    date_approved = db.Column(
        db.DateTime,
        nullable=True,
        comment=(
            'UTC timestamp of when an admin approved this enrollment. '
            'Null for courses that do not require approval.'
        )
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this enrollment record.'
    )

    # ── Relationships ─────────────────────────────────────────

    # The last module the learner accessed — for resume functionality
    last_accessed_module = db.relationship(
        'Module',
        foreign_keys=[last_accessed_module_id],
        lazy='joined'
    )

    # ==========================================================
    # STATUS MANAGEMENT METHODS
    # ==========================================================

    def activate(self):
        """
        Activate this enrollment, granting the learner
        full access to the course content.

        Sets status to 'active', is_active to True,
        and records the approval timestamp.

        Typical use: Admin approves a pending enrollment.
        """
        self.status = ENROLLMENT_STATUS_ACTIVE
        self.is_active = True
        self.date_approved = datetime.utcnow()

    def suspend(self, reason=None):
        """
        Suspend this enrollment, temporarily blocking
        the learner from accessing the course.

        Args:
            reason (str, optional): Reason for suspension
                                    stored in admin_notes.
        """
        self.status = ENROLLMENT_STATUS_SUSPENDED
        self.is_active = False
        if reason:
            self.admin_notes = (
                f'[SUSPENDED {datetime.utcnow().strftime("%Y-%m-%d")}]: '
                f'{reason}\n'
                + (self.admin_notes or '')
            )

    def drop(self, reason=None):
        """
        Mark this enrollment as dropped, indicating the
        learner has voluntarily withdrawn from the course.

        Args:
            reason (str, optional): Reason for dropping
                                    stored in admin_notes.
        """
        self.status = ENROLLMENT_STATUS_DROPPED
        self.is_active = False
        if reason:
            self.admin_notes = (
                f'[DROPPED {datetime.utcnow().strftime("%Y-%m-%d")}]: '
                f'{reason}\n'
                + (self.admin_notes or '')
            )

    def mark_completed(self, final_score=None, passing_score=50.0):
        """
        Mark this enrollment as completed.

        Sets is_completed to True, records the completion
        timestamp, calculates pass/fail status, and
        determines certificate eligibility.

        Args:
            final_score (float, optional): The learner's
                averaged assignment score as a percentage.
            passing_score (float): The minimum score required
                to pass. Defaults to 50.0 if not provided.

        Typical use: Called automatically when a learner
        completes the module flagged as is_last_module=True.
        """
        self.is_completed = True
        self.status = ENROLLMENT_STATUS_COMPLETED
        self.date_completed = datetime.utcnow()

        if final_score is not None:
            self.final_score = round(final_score, 2)
            self.is_passed = float(final_score) >= float(passing_score)
        else:
            # No graded assignments — completion counts as pass
            self.is_passed = True

    def issue_certificate(self):
        """
        Issue a completion certificate to this learner
        if they are eligible.

        Eligibility requires:
            - is_completed must be True
            - is_passed must be True
            - Certificate not already issued

        Returns:
            bool: True if the certificate was issued,
                  False if the learner is not eligible
                  or certificate was already issued.
        """
        if self.is_completed and self.is_passed and not self.certificate_issued:
            self.certificate_issued = True
            self.certificate_issued_date = datetime.utcnow()
            return True
        return False

    # ==========================================================
    # PROGRESS METHODS
    # ==========================================================

    def update_progress(self, total_published_modules):
        """
        Recalculate and update the progress_percent field
        based on the current modules_completed count and
        the total number of published modules in the course.

        This method should be called every time a learner
        completes a new module.

        Args:
            total_published_modules (int): Total number of
                published modules in the course.

        Example:
            If 3 of 5 modules are complete:
            update_progress(5) → progress_percent = 60.00
        """
        if total_published_modules <= 0:
            self.progress_percent = 0.00
            return

        percent = (self.modules_completed / total_published_modules) * 100
        self.progress_percent = round(min(percent, 100.00), 2)

    def increment_modules_completed(self):
        """
        Increment the modules_completed counter by one.
        Should be called when a learner marks a module complete.
        """
        self.modules_completed += 1

    def get_progress_display(self):
        """
        Format the progress_percent as a clean percentage
        string for display in templates and dashboards.

        Returns:
            str: Formatted percentage string.

        Examples:
            0.00  → '0%'
            66.67 → '66.67%'
            100.0 → '100%'
        """
        if not self.progress_percent:
            return '0%'
        value = float(self.progress_percent)
        if value == int(value):
            return f'{int(value)}%'
        return f'{value:.2f}%'

    def get_days_since_enrollment(self):
        """
        Calculate the number of days that have passed
        since the learner enrolled in this course.

        Returns:
            int: Number of days since enrollment.
        """
        delta = datetime.utcnow() - self.date_enrolled
        return delta.days

    def get_days_to_complete(self):
        """
        Calculate how many days it took for the learner
        to complete the course.

        Returns:
            int or None: Days from enrollment to completion.
                         None if course is not yet completed.
        """
        if self.is_completed and self.date_completed:
            delta = self.date_completed - self.date_enrolled
            return delta.days
        return None

    # ==========================================================
    # STATUS CHECK HELPERS
    # ==========================================================

    def is_pending(self):
        """
        Check whether this enrollment is awaiting
        admin approval.

        Returns:
            bool: True if status is 'pending'.
        """
        return self.status == ENROLLMENT_STATUS_PENDING

    def is_suspended(self):
        """
        Check whether this enrollment is currently
        suspended by an admin.

        Returns:
            bool: True if status is 'suspended'.
        """
        return self.status == ENROLLMENT_STATUS_SUSPENDED

    def is_dropped(self):
        """
        Check whether the learner has dropped
        this course.

        Returns:
            bool: True if status is 'dropped'.
        """
        return self.status == ENROLLMENT_STATUS_DROPPED

    def can_access_content(self):
        """
        Determine whether this learner currently has
        permission to access the course content.

        Access is granted only when the enrollment
        status is active or completed.

        Returns:
            bool: True if the learner can view course content.
        """
        return self.status in (
            ENROLLMENT_STATUS_ACTIVE,
            ENROLLMENT_STATUS_COMPLETED
        )

    def get_status_badge_class(self):
        """
        Return a CSS class name corresponding to the
        current enrollment status for badge styling
        in templates.

        Returns:
            str: CSS class string for the status badge.
        """
        badge_classes = {
            ENROLLMENT_STATUS_PENDING:   'badge-warning',
            ENROLLMENT_STATUS_ACTIVE:    'badge-success',
            ENROLLMENT_STATUS_COMPLETED: 'badge-primary',
            ENROLLMENT_STATUS_SUSPENDED: 'badge-danger',
            ENROLLMENT_STATUS_DROPPED:   'badge-secondary',
        }
        return badge_classes.get(self.status, 'badge-secondary')

    def get_status_label(self):
        """
        Return a human-readable label for the current
        enrollment status.

        Returns:
            str: Capitalized status label.
        """
        labels = {
            ENROLLMENT_STATUS_PENDING:   'Pending Approval',
            ENROLLMENT_STATUS_ACTIVE:    'Active',
            ENROLLMENT_STATUS_COMPLETED: 'Completed',
            ENROLLMENT_STATUS_SUSPENDED: 'Suspended',
            ENROLLMENT_STATUS_DROPPED:   'Dropped',
        }
        return labels.get(self.status, 'Unknown')

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self):
        """
        Serialize the Enrollment object to a plain dictionary
        suitable for JSON responses and template rendering.

        Returns:
            dict: Enrollment data with all computed fields.
        """
        return {
            'id':                       self.id,
            'user_id':                  self.user_id,
            'course_id':                self.course_id,
            'status':                   self.status,
            'status_label':             self.get_status_label(),
            'status_badge_class':       self.get_status_badge_class(),
            'is_active':                self.is_active,
            'progress_percent':         float(self.progress_percent)
                                        if self.progress_percent else 0.0,
            'progress_display':         self.get_progress_display(),
            'modules_completed':        self.modules_completed,
            'last_accessed_module_id':  self.last_accessed_module_id,
            'is_completed':             self.is_completed,
            'date_completed':           self.date_completed.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_completed else None,
            'final_score':              float(self.final_score)
                                        if self.final_score else None,
            'is_passed':                self.is_passed,
            'certificate_issued':       self.certificate_issued,
            'certificate_issued_date':  self.certificate_issued_date.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.certificate_issued_date else None,
            'can_access_content':       self.can_access_content(),
            'days_since_enrollment':    self.get_days_since_enrollment(),
            'days_to_complete':         self.get_days_to_complete(),
            'admin_notes':              self.admin_notes,
            'date_enrolled':            self.date_enrolled.strftime('%Y-%m-%d %H:%M:%S'),
            'date_approved':            self.date_approved.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_approved else None,
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
        }

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Enrollment id={self.id} '
            f'user_id={self.user_id} '
            f'course_id={self.course_id} '
            f'status={self.status!r} '
            f'progress={self.progress_percent}%>'
        )