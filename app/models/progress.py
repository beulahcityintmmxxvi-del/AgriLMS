# =============================================================
# Agri LMS — Progress Model
# =============================================================
# File    : app/models/progress.py
# Purpose : Defines the Progress database model representing
#           a single learner's completion record for a single
#           module within a course they are enrolled in.
#
#           Progress is tracked at the module level — one
#           Progress record exists per learner per module.
#           When a learner opens a module and marks it as
#           complete, a Progress record is created or updated.
#
#           The collection of Progress records for a learner
#           across all modules in a course is used to:
#               1. Calculate enrollment.progress_percent
#               2. Determine which module to unlock next
#               3. Detect when the last module is complete
#                  and trigger course completion
#               4. Display a visual progress timeline
#                  to the learner on their dashboard
#
#           A learner can only mark a module complete if
#           they have completed all previous modules first —
#           enforced in the route handler logic, not the model.
#
# Relationships:
#   Progress >── User     (many progress records per learner)
#   Progress >── Module   (many progress records per module)
#
# Progress Lifecycle:
#   Learner clicks on a module
#       → Progress record created (is_completed=False)
#         if one does not already exist — tracking started
#       → Learner consumes module materials
#       → Learner clicks "Mark as Complete"
#       → Progress.mark_complete() called
#       → is_completed=True, date_completed recorded
#       → Enrollment.modules_completed incremented
#       → Enrollment.progress_percent recalculated
#       → If module.is_last_module=True:
#             Enrollment.mark_completed() triggered
#             Course completion flow begins
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# PROGRESS MODEL
# =============================================================

class Progress(db.Model):
    """
    Represents a single learner's interaction and completion
    record for a single module within an enrolled course.

    One Progress record exists per learner per module.
    This is enforced by the uq_progress_user_module
    unique constraint on (user_id, module_id).

    The model tracks:
        - Whether the learner has started the module
          (record exists)
        - Whether the learner has completed the module
          (is_completed=True)
        - When they first accessed the module
          (date_started)
        - When they marked it complete
          (date_completed)
        - How long they spent on the module
          (time_spent_minutes)
        - Their last access timestamp
          (last_accessed)
        - Optional self-assessment notes
          (learner_notes)
    """

    __tablename__ = 'progress'

    # ── Table-level constraints ───────────────────────────────
    __table_args__ = (
        # One progress record per learner per module
        db.UniqueConstraint(
            'user_id',
            'module_id',
            name='uq_progress_user_module'
        ),
    )

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique progress record identifier — auto-incremented primary key'
    )

    # ── Foreign Keys ──────────────────────────────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the learner this progress '
            'record belongs to. '
            'CASCADE: deleting a user removes all their progress records.'
        )
    )

    module_id = db.Column(
        db.Integer,
        db.ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the module this progress '
            'record tracks. '
            'CASCADE: deleting a module removes all its progress records.'
        )
    )

    # ── Convenience Foreign Key ───────────────────────────────
    # Stored for fast filtering of all progress records
    # for a learner within a specific course without
    # needing to join through the modules table
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the course this module belongs to. '
            'Stored as a convenience to allow fast filtering of '
            'all progress records for a learner in a course '
            'without joining through the modules table. '
            'CASCADE: deleting a course removes all related progress.'
        )
    )

    # ── Completion Status ─────────────────────────────────────
    is_completed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Module completion flag. '
            'False: learner has started but not yet completed this module. '
            'True: learner has explicitly marked this module as complete.'
        )
    )

    # ── Time Tracking ─────────────────────────────────────────
    date_started = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment=(
            'UTC timestamp of when the learner first opened '
            'this module — the moment the Progress record was created.'
        )
    )

    date_completed = db.Column(
        db.DateTime,
        nullable=True,
        comment=(
            'UTC timestamp of when the learner clicked '
            '"Mark as Complete" and is_completed was set to True.'
        )
    )

    last_accessed = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment=(
            'UTC timestamp of the most recent time the learner '
            'opened this module. Updated every time the learner '
            'visits the module view page.'
        )
    )

    time_spent_minutes = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        comment=(
            'Cumulative number of minutes the learner has spent '
            'on this module across all visits. '
            'Incremented each time the learner leaves the module '
            'page — tracked via JavaScript session timing '
            'and submitted with the page-leave event.'
        )
    )

    # ── Access Count ──────────────────────────────────────────
    access_count = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        comment=(
            'Number of times the learner has opened this module. '
            'Incremented on each visit to the module view page. '
            'Starts at 1 when the Progress record is created '
            'on the first visit.'
        )
    )

    # ── Learner Self-Assessment ───────────────────────────────
    learner_notes = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Optional personal notes the learner writes while '
            'studying this module. Private to the learner — '
            'not visible to admins. Displayed in the module '
            'view as a personal notepad.'
        )
    )

    learner_rating = db.Column(
        db.Integer,
        nullable=True,
        comment=(
            'Optional learner satisfaction rating for this module '
            'on a scale of 1 to 5. '
            '1=Very Poor, 2=Poor, 3=Fair, 4=Good, 5=Excellent. '
            'Used for admin analytics and course improvement.'
        )
    )

    learner_feedback = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Optional written feedback the learner submits '
            'about this module after completing it. '
            'Visible to admins for course improvement purposes.'
        )
    )

    # ==========================================================
    # COMPLETION METHODS
    # ==========================================================

    def mark_complete(self):
        """
        Mark this module as completed by the learner.

        Sets is_completed to True and records the
        completion timestamp.

        This method does NOT automatically update the
        parent Enrollment record — that is handled in
        the route handler to keep the model focused
        on its own data and avoid circular logic.

        After calling this method, the route handler
        should:
            1. Call enrollment.increment_modules_completed()
            2. Call enrollment.update_progress(total_modules)
            3. Check if module.is_last_module is True
            4. If so, call enrollment.mark_completed()
        """
        self.is_completed = True
        self.date_completed = datetime.utcnow()

    def mark_incomplete(self):
        """
        Revert this module's completion status back to
        incomplete. Used by admins to reset a learner's
        progress on a specific module if needed.

        Clears is_completed and date_completed.
        """
        self.is_completed = False
        self.date_completed = None

    # ==========================================================
    # ACCESS TRACKING METHODS
    # ==========================================================

    def record_access(self):
        """
        Record a new access event for this module.

        Increments the access_count and updates the
        last_accessed timestamp to the current UTC time.

        Should be called every time a learner opens
        the module view page.
        """
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def add_time_spent(self, minutes):
        """
        Add to the cumulative time the learner has spent
        on this module.

        Args:
            minutes (int): Number of minutes to add.
                           Should come from JavaScript
                           session timing submitted when
                           the learner leaves the page.
                           Negative values are ignored.
        """
        if minutes and minutes > 0:
            self.time_spent_minutes += int(minutes)

    # ==========================================================
    # LEARNER FEEDBACK METHODS
    # ==========================================================

    def save_rating_and_feedback(self, rating, feedback=None):
        """
        Save the learner's satisfaction rating and optional
        written feedback for this module.

        Args:
            rating (int): Satisfaction rating between 1 and 5.
                          Values outside this range are clamped.
            feedback (str, optional): Written feedback text.
        """
        # Clamp rating to valid range
        if rating is not None:
            self.learner_rating = max(1, min(5, int(rating)))

        if feedback and feedback.strip():
            self.learner_feedback = feedback.strip()

    def save_notes(self, notes):
        """
        Save or update the learner's personal study notes
        for this module.

        Args:
            notes (str): The learner's note content.
                         Pass an empty string to clear notes.
        """
        self.learner_notes = notes.strip() if notes else None

    # ==========================================================
    # TIME DISPLAY HELPERS
    # ==========================================================

    def get_time_spent_display(self):
        """
        Format the cumulative time_spent_minutes into a
        human-readable hours and minutes string.

        Returns:
            str: Formatted time string.

        Examples:
            0   → 'Less than a minute'
            45  → '45 min'
            90  → '1 hr 30 min'
            120 → '2 hr'
        """
        minutes = self.time_spent_minutes

        if minutes <= 0:
            return 'Less than a minute'
        elif minutes < 60:
            return f'{minutes} min'

        hours = minutes // 60
        remaining = minutes % 60

        if remaining == 0:
            return f'{hours} hr'
        return f'{hours} hr {remaining} min'

    def get_days_to_complete(self):
        """
        Calculate the number of days it took the learner
        to complete this module from first access to
        marking it complete.

        Returns:
            int or None: Days taken to complete.
                         None if the module is not yet complete.
        """
        if self.is_completed and self.date_completed:
            delta = self.date_completed - self.date_started
            return max(delta.days, 0)
        return None

    def get_days_since_start(self):
        """
        Calculate the number of days since the learner
        first opened this module.

        Returns:
            int: Days since first access.
        """
        delta = datetime.utcnow() - self.date_started
        return delta.days

    def get_last_accessed_display(self):
        """
        Format the last_accessed timestamp into a
        human-readable string for display in templates.

        Returns:
            str: Formatted last access date string.

        Example:
            '15 January 2025 at 02:30 PM UTC'
        """
        return self.last_accessed.strftime('%d %B %Y at %I:%M %p UTC')

    def get_date_completed_display(self):
        """
        Format the date_completed timestamp into a
        human-readable string for display.

        Returns:
            str: Formatted completion date or 'Not completed yet'.
        """
        if not self.date_completed:
            return 'Not completed yet'
        return self.date_completed.strftime('%d %B %Y at %I:%M %p UTC')

    # ==========================================================
    # RATING HELPERS
    # ==========================================================

    def get_rating_display(self):
        """
        Return a human-readable label for the learner's
        module satisfaction rating.

        Returns:
            str: Descriptive rating label.
        """
        labels = {
            1: 'Very Poor',
            2: 'Poor',
            3: 'Fair',
            4: 'Good',
            5: 'Excellent',
        }
        return labels.get(self.learner_rating, 'Not rated')

    def get_rating_stars(self):
        """
        Return a star string representation of the learner's
        rating for visual display in templates.

        Returns:
            str: Star characters representing the rating.

        Examples:
            rating=5 → '★★★★★'
            rating=3 → '★★★☆☆'
            None     → '☆☆☆☆☆'
        """
        if not self.learner_rating:
            return '☆☆☆☆☆'
        filled = '★' * self.learner_rating
        empty = '☆' * (5 - self.learner_rating)
        return filled + empty

    # ==========================================================
    # STATIC FACTORY METHOD
    # ==========================================================

    @staticmethod
    def get_or_create(user_id, module_id, course_id):
        """
        Retrieve the existing Progress record for a learner
        and module, or create a new one if it does not exist.

        This is the standard way to ensure a Progress record
        exists when a learner opens a module for the first
        time. On subsequent visits, the existing record is
        returned and record_access() is called on it.

        Args:
            user_id (int): The learner's primary key.
            module_id (int): The module's primary key.
            course_id (int): The course's primary key.

        Returns:
            tuple: (Progress, bool) where the bool is True
                   if the record was newly created,
                   False if it already existed.

        Usage in route handler:
            progress, created = Progress.get_or_create(
                user_id=current_user.id,
                module_id=module.id,
                course_id=module.course_id
            )
            if not created:
                progress.record_access()
            db.session.commit()
        """
        existing = Progress.query.filter_by(
            user_id=user_id,
            module_id=module_id
        ).first()

        if existing:
            return existing, False

        # Create a new progress record
        new_progress = Progress(
            user_id=user_id,
            module_id=module_id,
            course_id=course_id,
            is_completed=False,
            date_started=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=1,
            time_spent_minutes=0
        )
        db.session.add(new_progress)

        return new_progress, True

    @staticmethod
    def get_course_progress_for_user(user_id, course_id):
        """
        Retrieve all Progress records for a specific learner
        within a specific course, ordered by module sequence.

        Used to render the course progress timeline on the
        learner dashboard and course detail page.

        Args:
            user_id (int): The learner's primary key.
            course_id (int): The course's primary key.

        Returns:
            list[Progress]: Ordered list of progress records.
        """
        from app.models.module import Module
        return (
            Progress.query
            .join(Module, Progress.module_id == Module.id)
            .filter(
                Progress.user_id == user_id,
                Progress.course_id == course_id
            )
            .order_by(Module.order_number)
            .all()
        )

    @staticmethod
    def count_completed_for_user_in_course(user_id, course_id):
        """
        Count how many modules a learner has completed
        in a specific course.

        Used to verify the enrollment.modules_completed
        count and for recalculation if needed.

        Args:
            user_id (int): The learner's primary key.
            course_id (int): The course's primary key.

        Returns:
            int: Number of completed modules.
        """
        return Progress.query.filter_by(
            user_id=user_id,
            course_id=course_id,
            is_completed=True
        ).count()

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self):
        """
        Serialize the Progress object to a plain dictionary
        suitable for JSON responses and template rendering.

        Returns:
            dict: Progress data with all computed fields.
        """
        return {
            'id':                       self.id,
            'user_id':                  self.user_id,
            'module_id':                self.module_id,
            'course_id':                self.course_id,
            'is_completed':             self.is_completed,
            'date_started':             self.date_started.strftime('%Y-%m-%d %H:%M:%S'),
            'date_completed':           self.date_completed.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_completed else None,
            'date_completed_display':   self.get_date_completed_display(),
            'last_accessed':            self.last_accessed.strftime('%Y-%m-%d %H:%M:%S'),
            'last_accessed_display':    self.get_last_accessed_display(),
            'time_spent_minutes':       self.time_spent_minutes,
            'time_spent_display':       self.get_time_spent_display(),
            'access_count':             self.access_count,
            'days_to_complete':         self.get_days_to_complete(),
            'days_since_start':         self.get_days_since_start(),
            'learner_notes':            self.learner_notes,
            'learner_rating':           self.learner_rating,
            'rating_display':           self.get_rating_display(),
            'rating_stars':             self.get_rating_stars(),
            'learner_feedback':         self.learner_feedback,
        }

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Progress id={self.id} '
            f'user_id={self.user_id} '
            f'module_id={self.module_id} '
            f'completed={self.is_completed} '
            f'time={self.time_spent_minutes}min>'
        )