# =============================================================
# Agri LMS — Course Model
# =============================================================
# File    : app/models/course.py
# Purpose : Defines the Course database model representing
#           every agricultural learning course available
#           on the platform.
#
#           A Course is the top-level learning unit.
#           It contains Modules, which contain Materials.
#           Learners enroll in Courses and progress through
#           each Module sequentially.
#
# Relationships:
#   Course ──< Module       (one course has many modules)
#   Course ──< Enrollment   (one course has many enrollments)
#   Course ──< Assignment   (one course has many assignments)
#   Course >── User         (many courses created by one admin)
#
# Hierarchy:
#   Course
#     └── Module 1
#           └── Material (video, PDF, document)
#     └── Module 2
#           └── Material
#     └── Module N  ← marked as last module
#           └── Material
#     └── Assignment 1
#     └── Assignment N
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# COURSE MODEL
# =============================================================

class Course(db.Model):
    """
    Represents a single agricultural learning course
    on the platform.

    A course is created and managed exclusively by admins.
    Learners discover courses in the catalog, enroll,
    and then work through the course modules in order.

    A course is considered complete when a learner has
    marked progress on all modules up to and including
    the module flagged as is_last_module=True.
    """

    __tablename__ = 'courses'

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique course identifier — auto-incremented primary key'
    )

    # ── Foreign Key — Admin who created the course ────────────
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='Foreign key — ID of the admin user who created this course'
    )

    # ── Course Identity ───────────────────────────────────────
    title = db.Column(
        db.String(300),
        nullable=False,
        comment='Full title of the course displayed to learners'
    )

    slug = db.Column(
        db.String(350),
        nullable=True,
        unique=True,
        index=True,
        comment='URL-friendly version of the title used in course URLs'
    )

    short_description = db.Column(
        db.String(500),
        nullable=False,
        comment='Brief summary shown on course catalog cards — max 500 characters'
    )

    full_description = db.Column(
        db.Text,
        nullable=True,
        comment='Detailed course description shown on the course detail page'
    )

    # ── Classification ────────────────────────────────────────
    category = db.Column(
        db.String(150),
        nullable=True,
        index=True,
        comment=(
            'Course category for filtering and navigation — '
            'e.g. Crop Production, Livestock Management, '
            'Soil Science, Pest Control, Irrigation, '
            'Indigenous Practices, Organic Farming'
        )
    )

    level = db.Column(
        db.String(50),
        nullable=True,
        default='beginner',
        comment='Difficulty level — beginner | intermediate | advanced'
    )

    language = db.Column(
        db.String(50),
        nullable=True,
        default='English',
        comment='Primary language of instruction for this course'
    )

    tags = db.Column(
        db.Text,
        nullable=True,
        comment='Comma-separated tags for search — e.g. maize, irrigation, soil'
    )

    # ── Media ─────────────────────────────────────────────────
    thumbnail = db.Column(
        db.String(255),
        nullable=True,
        default='default_course.png',
        comment='Filename of the course thumbnail stored in static/uploads/thumbnails/'
    )

    # ── Course Structure Metadata ─────────────────────────────
    duration_weeks = db.Column(
        db.Integer,
        nullable=True,
        comment='Estimated duration of the course in weeks'
    )

    total_modules = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        comment='Total number of modules in this course — updated automatically'
    )

    # ── Enrollment Settings ───────────────────────────────────
    max_enrollments = db.Column(
        db.Integer,
        nullable=True,
        comment='Maximum number of learners allowed to enroll — NULL means unlimited'
    )

    enrollment_open = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='Whether new enrollments are currently being accepted'
    )

    requires_approval = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Whether admin approval is required before enrollment is activated'
    )

    # ── Completion Settings ───────────────────────────────────
    passing_score = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        default=50.00,
        comment='Minimum average assignment score required to pass the course (percentage)'
    )

    certificate_available = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='Whether a completion certificate is issued upon course completion'
    )

    # ── Publishing Status ─────────────────────────────────────
    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Publication status — '
            'False: draft visible only to admins | '
            'True: visible to all learners in the catalog'
        )
    )

    is_featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Featured flag — True means displayed prominently on the landing page'
    )

    is_archived = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Archived flag — True means the course is hidden from the catalog'
    )

    # ── Prerequisites ─────────────────────────────────────────
    prerequisites = db.Column(
        db.Text,
        nullable=True,
        comment='Free-text description of knowledge or courses required before enrolling'
    )

    # ── What Learners Will Learn ──────────────────────────────
    learning_outcomes = db.Column(
        db.Text,
        nullable=True,
        comment='Comma or newline separated list of learning outcomes for this course'
    )

    # ── Timestamps ────────────────────────────────────────────
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when the course was first created'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this course'
    )

    date_published = db.Column(
        db.DateTime,
        nullable=True,
        comment='UTC timestamp of when the course was first published to learners'
    )

    # ── Relationships ─────────────────────────────────────────

    # One course has many modules — ordered by module order_number
    modules = db.relationship(
        'Module',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Module.order_number'
    )

    # One course has many enrollments
    enrollments = db.relationship(
        'Enrollment',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # One course has many assignments
    assignments = db.relationship(
        'Assignment',
        backref='course',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Assignment.date_created'
    )

    # ==========================================================
    # COMPUTED PROPERTIES
    # ==========================================================

    def get_total_enrollments(self):
        """
        Count the total number of learners enrolled
        in this course.

        Returns:
            int: Total enrollment count.
        """
        return self.enrollments.count()

    def get_active_enrollments(self):
        """
        Count the number of currently active enrollments.

        Returns:
            int: Active enrollment count.
        """
        return self.enrollments.filter_by(
            is_active=True
        ).count()

    def get_completed_enrollments(self):
        """
        Count the number of learners who have completed
        this course.

        Returns:
            int: Completed enrollment count.
        """
        return self.enrollments.filter_by(
            is_completed=True
        ).count()

    def get_published_modules(self):
        """
        Retrieve all published modules for this course
        ordered by their sequence number.

        Returns:
            list[Module]: Ordered list of published modules.
        """
        from app.models.module import Module
        return self.modules.filter_by(
            is_published=True
        ).order_by(Module.order_number).all()

    def get_all_modules(self):
        """
        Retrieve all modules for this course including
        unpublished drafts. Used by admin views.

        Returns:
            list[Module]: All modules ordered by sequence.
        """
        from app.models.module import Module
        return self.modules.order_by(
            Module.order_number
        ).all()

    def get_last_module(self):
        """
        Retrieve the module flagged as the final module
        in this course.

        Returns:
            Module or None: The last module if set.
        """
        from app.models.module import Module
        return self.modules.filter_by(
            is_last_module=True
        ).first()

    def get_total_modules_count(self):
        """
        Count all modules belonging to this course.

        Returns:
            int: Total module count.
        """
        return self.modules.count()

    def get_published_modules_count(self):
        """
        Count only published modules belonging to
        this course.

        Returns:
            int: Published module count.
        """
        return self.modules.filter_by(
            is_published=True
        ).count()

    def is_enrollment_available(self):
        """
        Determine whether a new learner can enroll
        in this course right now.

        Checks:
            - Course must be published
            - Enrollment must be open
            - Must not be archived
            - If max_enrollments is set, must not be full

        Returns:
            bool: True if enrollment is possible.
        """
        if not self.is_published:
            return False
        if not self.enrollment_open:
            return False
        if self.is_archived:
            return False
        if self.max_enrollments is not None:
            if self.get_total_enrollments() >= self.max_enrollments:
                return False
        return True

    def get_completion_rate(self):
        """
        Calculate the course completion rate as a percentage.

        Returns:
            float: Percentage of enrolled learners who completed
                   the course. Returns 0.0 if no enrollments.
        """
        total = self.get_total_enrollments()
        if total == 0:
            return 0.0
        completed = self.get_completed_enrollments()
        return round((completed / total) * 100, 2)

    def generate_slug(self):
        """
        Generate a URL-friendly slug from the course title.
        Replaces spaces with hyphens and lowercases all characters.
        Strips any characters that are not alphanumeric or hyphens.

        Example:
            'Introduction to Crop Science' → 'introduction-to-crop-science'

        Returns:
            str: URL-safe slug string.
        """
        import re
        slug = self.title.lower().strip()
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'[^\w-]', '', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug

    def get_tags_list(self):
        """
        Parse the comma-separated tags string into a
        clean Python list.

        Returns:
            list[str]: List of individual tag strings.
                       Returns empty list if no tags set.

        Example:
            'maize, irrigation, soil' → ['maize', 'irrigation', 'soil']
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def get_learning_outcomes_list(self):
        """
        Parse the learning outcomes text into a list.
        Splits on newline characters for structured display.

        Returns:
            list[str]: List of individual learning outcome strings.
        """
        if not self.learning_outcomes:
            return []
        return [
            outcome.strip()
            for outcome in self.learning_outcomes.splitlines()
            if outcome.strip()
        ]

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self):
        """
        Serialize the Course object to a plain dictionary
        suitable for JSON responses and template rendering.

        Returns:
            dict: Course data with computed statistics included.
        """
        return {
            'id':                       self.id,
            'created_by':               self.created_by,
            'title':                    self.title,
            'slug':                     self.slug,
            'short_description':        self.short_description,
            'full_description':         self.full_description,
            'category':                 self.category,
            'level':                    self.level,
            'language':                 self.language,
            'tags':                     self.get_tags_list(),
            'thumbnail':                self.thumbnail,
            'duration_weeks':           self.duration_weeks,
            'total_modules':            self.get_total_modules_count(),
            'published_modules':        self.get_published_modules_count(),
            'max_enrollments':          self.max_enrollments,
            'enrollment_open':          self.enrollment_open,
            'requires_approval':        self.requires_approval,
            'passing_score':            float(self.passing_score)
                                        if self.passing_score else 50.0,
            'certificate_available':    self.certificate_available,
            'is_published':             self.is_published,
            'is_featured':              self.is_featured,
            'is_archived':              self.is_archived,
            'prerequisites':            self.prerequisites,
            'learning_outcomes':        self.get_learning_outcomes_list(),
            'total_enrollments':        self.get_total_enrollments(),
            'active_enrollments':       self.get_active_enrollments(),
            'completed_enrollments':    self.get_completed_enrollments(),
            'completion_rate':          self.get_completion_rate(),
            'enrollment_available':     self.is_enrollment_available(),
            'date_created':             self.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
            'date_published':           self.date_published.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_published else None,
        }

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Course id={self.id} '
            f'title={self.title!r} '
            f'published={self.is_published}>'
        )