# =============================================================
# Agri LMS — Module Model
# =============================================================
# File    : app/models/module.py
# Purpose : Defines the Module database model representing
#           individual learning units within a Course.
#
#           A Module is the second level of the learning
#           hierarchy. Each course contains one or more
#           modules arranged in a strict sequential order.
#           Learners must complete each module before
#           unlocking the next one.
#
#           The admin specifies which module is the final
#           module in a course using the is_last_module flag.
#           This flag is what the system uses to determine
#           when a learner has completed an entire course.
#
# Relationships:
#   Module >── Course       (many modules belong to one course)
#   Module ──< Material     (one module has many materials)
#   Module ──< Progress     (one module has many progress records)
#
# Learning Hierarchy:
#   Course
#     └── Module 1  (order_number=1)
#           └── Material (video)
#           └── Material (PDF)
#     └── Module 2  (order_number=2)
#           └── Material (video)
#     └── Module N  (order_number=N, is_last_module=True)
#           └── Material
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# MODULE MODEL
# =============================================================

class Module(db.Model):
    """
    Represents a single learning module within a Course.

    Modules are the core content delivery unit of the platform.
    Each module has an order number that determines its position
    in the course sequence. Learners progress through modules
    one at a time in ascending order_number sequence.

    The admin sets is_last_module=True on exactly one module
    per course to indicate where the course ends. The system
    uses this flag — not a count — to determine completion,
    giving the admin full flexibility to add or remove modules
    without reconfiguring the course structure.

    Each module contains one or more Materials (videos, PDFs,
    documents) that the learner consumes before marking the
    module as complete and moving to the next.
    """

    __tablename__ = 'modules'

    # ── Table-level constraints ───────────────────────────────
    __table_args__ = (
        # Enforce unique ordering within each course
        # No two modules in the same course can share an order number
        db.UniqueConstraint(
            'course_id',
            'order_number',
            name='uq_module_course_order'
        ),
    )

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique module identifier — auto-incremented primary key'
    )

    # ── Foreign Key — Parent Course ───────────────────────────
    course_id = db.Column(
        db.Integer,
        db.ForeignKey('courses.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the course this module belongs to. '
            'CASCADE: deleting a course deletes all its modules.'
        )
    )

    # ── Module Identity ───────────────────────────────────────
    title = db.Column(
        db.String(300),
        nullable=False,
        comment='Title of the module displayed to learners — e.g. Module 1: Introduction to Soil Types'
    )

    description = db.Column(
        db.Text,
        nullable=True,
        comment='Overview of what this module covers — shown before the learner starts'
    )

    learning_objectives = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Newline-separated list of specific things the learner '
            'will be able to do after completing this module'
        )
    )

    # ── Sequencing ────────────────────────────────────────────
    order_number = db.Column(
        db.Integer,
        nullable=False,
        comment=(
            'Position of this module in the course sequence. '
            'Module 1 has order_number=1, Module 2 has order_number=2, etc. '
            'Learners progress through modules in ascending order. '
            'Must be unique within a course — enforced by uq_module_course_order.'
        )
    )

    # ── Last Module Flag ──────────────────────────────────────
    is_last_module = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Designates this module as the final module of the course. '
            'Set by the admin when creating or editing the module. '
            'When a learner completes a module where is_last_module=True, '
            'the system automatically marks their course enrollment as complete. '
            'Only one module per course should have this set to True.'
        )
    )

    # ── Estimated Duration ────────────────────────────────────
    duration_minutes = db.Column(
        db.Integer,
        nullable=True,
        comment='Estimated time in minutes a learner needs to complete this module'
    )

    # ── Content Notes ─────────────────────────────────────────
    notes = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Supplementary notes, key takeaways, or additional reading '
            'written by the admin — displayed alongside the materials'
        )
    )

    instructor_notes = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Internal admin-only notes about this module — '
            'not visible to learners'
        )
    )

    # ── Publishing Status ─────────────────────────────────────
    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Publication flag — '
            'False: module is a draft, visible only to admins | '
            'True: module is visible to enrolled learners'
        )
    )

    # ── Free Preview ──────────────────────────────────────────
    is_free_preview = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Preview flag — '
            'True: this module is accessible to non-enrolled users '
            'as a sample before they enroll in the course'
        )
    )

    # ── Timestamps ────────────────────────────────────────────
    date_created = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when this module was created by the admin'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this module'
    )

    # ── Relationships ─────────────────────────────────────────

    # One module contains many materials
    # Ordered by the material's own order_number for display
    materials = db.relationship(
        'Material',
        backref='module',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='Material.order_number'
    )

    # One module has many learner progress records
    # One record per learner per module
    progress_records = db.relationship(
        'Progress',
        backref='module',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # ==========================================================
    # MATERIAL HELPERS
    # ==========================================================

    def get_all_materials(self):
        """
        Retrieve all materials in this module including
        unpublished drafts. Used by admin views.

        Returns:
            list[Material]: All materials ordered by order_number.
        """
        from app.models.material import Material
        return self.materials.order_by(
            Material.order_number
        ).all()

    def get_published_materials(self):
        """
        Retrieve only published materials in this module.
        Used by learner views.

        Returns:
            list[Material]: Published materials ordered by order_number.
        """
        from app.models.material import Material
        return self.materials.filter_by(
            is_published=True
        ).order_by(Material.order_number).all()

    def get_materials_by_type(self, material_type):
        """
        Retrieve all published materials of a specific type
        in this module.

        Args:
            material_type (str): The type to filter by.
                                 Options: 'video' | 'pdf' |
                                 'document' | 'image' | 'other'

        Returns:
            list[Material]: Filtered and ordered materials.
        """
        from app.models.material import Material
        return self.materials.filter_by(
            material_type=material_type,
            is_published=True
        ).order_by(Material.order_number).all()

    def get_video_count(self):
        """
        Count the number of video materials in this module.

        Returns:
            int: Number of video materials.
        """
        return self.materials.filter_by(
            material_type='video',
            is_published=True
        ).count()

    def get_pdf_count(self):
        """
        Count the number of PDF materials in this module.

        Returns:
            int: Number of PDF materials.
        """
        return self.materials.filter_by(
            material_type='pdf',
            is_published=True
        ).count()

    def get_total_materials_count(self):
        """
        Count all materials in this module regardless of type
        or publishing status. Used in admin views.

        Returns:
            int: Total material count.
        """
        return self.materials.count()

    def get_published_materials_count(self):
        """
        Count only published materials in this module.

        Returns:
            int: Published material count.
        """
        return self.materials.filter_by(
            is_published=True
        ).count()

    # ==========================================================
    # SEQUENCING HELPERS
    # ==========================================================

    def get_next_module(self):
        """
        Retrieve the next module in the course sequence.
        Returns None if this is already the last module.

        Returns:
            Module or None: The next module in sequence.
        """
        return Module.query.filter(
            Module.course_id == self.course_id,
            Module.order_number > self.order_number,
            Module.is_published == True
        ).order_by(Module.order_number).first()

    def get_previous_module(self):
        """
        Retrieve the previous module in the course sequence.
        Returns None if this is the first module.

        Returns:
            Module or None: The previous module in sequence.
        """
        return Module.query.filter(
            Module.course_id == self.course_id,
            Module.order_number < self.order_number,
            Module.is_published == True
        ).order_by(Module.order_number.desc()).first()

    def is_first_module(self):
        """
        Determine whether this is the first module in its course
        by checking if no module with a lower order_number exists.

        Returns:
            bool: True if this is the first module.
        """
        return Module.query.filter(
            Module.course_id == self.course_id,
            Module.order_number < self.order_number
        ).count() == 0

    # ==========================================================
    # PROGRESS HELPERS
    # ==========================================================

    def get_completion_count(self):
        """
        Count how many learners have completed this module.

        Returns:
            int: Number of learners who completed this module.
        """
        from app.models.progress import Progress
        return self.progress_records.filter_by(
            is_completed=True
        ).count()

    def is_completed_by(self, user_id):
        """
        Check whether a specific learner has completed
        this module.

        Args:
            user_id (int): The primary key of the learner.

        Returns:
            bool: True if the learner has completed this module.
        """
        from app.models.progress import Progress
        record = self.progress_records.filter_by(
            user_id=user_id,
            is_completed=True
        ).first()
        return record is not None

    def get_progress_for_user(self, user_id):
        """
        Retrieve the Progress record for a specific learner
        on this module.

        Args:
            user_id (int): The primary key of the learner.

        Returns:
            Progress or None: The progress record if it exists.
        """
        from app.models.progress import Progress
        return self.progress_records.filter_by(
            user_id=user_id
        ).first()

    # ==========================================================
    # CONTENT HELPERS
    # ==========================================================

    def get_learning_objectives_list(self):
        """
        Parse the newline-separated learning objectives text
        into a clean Python list for template rendering.

        Returns:
            list[str]: List of individual objective strings.
                       Returns empty list if none are set.

        Example:
            'Identify soil types\\nTest soil pH\\nApply amendments'
            → ['Identify soil types', 'Test soil pH', 'Apply amendments']
        """
        if not self.learning_objectives:
            return []
        return [
            obj.strip()
            for obj in self.learning_objectives.splitlines()
            if obj.strip()
        ]

    def get_duration_display(self):
        """
        Format the duration_minutes value into a
        human-readable hours and minutes string.

        Returns:
            str: Formatted duration string.

        Examples:
            45  → '45 min'
            90  → '1 hr 30 min'
            120 → '2 hr'
        """
        if not self.duration_minutes:
            return 'N/A'

        minutes = self.duration_minutes

        if minutes < 60:
            return f'{minutes} min'

        hours = minutes // 60
        remaining_minutes = minutes % 60

        if remaining_minutes == 0:
            return f'{hours} hr'

        return f'{hours} hr {remaining_minutes} min'

    def get_module_label(self):
        """
        Generate a formatted module label combining the
        order number and title for display in navigation
        and breadcrumbs.

        Returns:
            str: Formatted label string.

        Example:
            order_number=3, title='Soil pH Testing'
            → 'Module 3: Soil pH Testing'
        """
        return f'Module {self.order_number}: {self.title}'

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self, include_materials=False):
        """
        Serialize the Module object to a plain dictionary.

        Args:
            include_materials (bool): If True, includes a
                serialized list of all published materials.
                Default is False for performance.

        Returns:
            dict: Module data with optional materials included.
        """
        data = {
            'id':                       self.id,
            'course_id':                self.course_id,
            'title':                    self.title,
            'description':              self.description,
            'learning_objectives':      self.get_learning_objectives_list(),
            'order_number':             self.order_number,
            'is_last_module':           self.is_last_module,
            'duration_minutes':         self.duration_minutes,
            'duration_display':         self.get_duration_display(),
            'module_label':             self.get_module_label(),
            'notes':                    self.notes,
            'is_published':             self.is_published,
            'is_free_preview':          self.is_free_preview,
            'is_first_module':          self.is_first_module(),
            'total_materials':          self.get_total_materials_count(),
            'published_materials':      self.get_published_materials_count(),
            'video_count':              self.get_video_count(),
            'pdf_count':                self.get_pdf_count(),
            'completion_count':         self.get_completion_count(),
            'date_created':             self.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
        }

        # Optionally include serialized materials
        if include_materials:
            data['materials'] = [
                material.to_dict()
                for material in self.get_published_materials()
            ]

        return data

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Module id={self.id} '
            f'course_id={self.course_id} '
            f'order={self.order_number} '
            f'title={self.title!r} '
            f'last={self.is_last_module}>'
        )