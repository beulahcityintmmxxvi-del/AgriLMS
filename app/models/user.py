# =============================================================
# Agri LMS — User Model
# =============================================================
# File    : app/models/user.py
# Purpose : Defines the User database model representing all
#           platform users — both learners and administrators.
#           Implements Flask-Login's UserMixin for session
#           management and Werkzeug for password hashing.
#
# Relationships:
#   User ──< Enrollment       (one user enrolls in many courses)
#   User ──< Submission       (one user submits many assignments)
#   User ──< Progress         (one user has many progress records)
#   User ──< Course           (one admin creates many courses)
#   User ──< Assignment       (one admin creates many assignments)
#   User ──< Grade            (one admin grades many submissions)
# =============================================================

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# =============================================================
# USER MODEL
# =============================================================

class User(UserMixin, db.Model):
    """
    Represents every registered user on the platform.

    Two roles are supported:
        'learner' — A student who enrolls in and studies courses.
        'admin'   — A platform administrator who manages all
                    content, courses, assignments, and grades.

    Flask-Login integration is provided through UserMixin,
    which supplies the default implementations of:
        is_authenticated, is_active, is_anonymous, get_id()
    """

    __tablename__ = 'users'

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique user identifier — auto-incremented primary key'
    )

    # ── Personal Information ──────────────────────────────────
    full_name = db.Column(
        db.String(150),
        nullable=False,
        comment='Full legal name of the user'
    )

    email = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True,
        comment='Unique email address — used as login identifier'
    )

    phone_number = db.Column(
        db.String(20),
        nullable=True,
        comment='Optional contact phone number'
    )

    # ── Location ──────────────────────────────────────────────
    state = db.Column(
        db.String(100),
        nullable=True,
        comment='State or province of residence'
    )

    country = db.Column(
        db.String(100),
        nullable=True,
        default='Nigeria',
        comment='Country of residence'
    )

    # ── Profile ───────────────────────────────────────────────
    profile_photo = db.Column(
        db.String(255),
        nullable=True,
        default='default_profile.png',
        comment='Filename of uploaded profile photo stored in static/uploads/profiles/'
    )

    bio = db.Column(
        db.Text,
        nullable=True,
        comment='Short biography or personal description of the user'
    )

    farming_background = db.Column(
        db.Text,
        nullable=True,
        comment='Brief description of the user farming experience or agricultural background'
    )

    # ── Authentication ────────────────────────────────────────
    password_hash = db.Column(
        db.String(256),
        nullable=False,
        comment='Werkzeug-hashed password — plaintext is never stored'
    )

    # ── Role-Based Access Control ─────────────────────────────
    role = db.Column(
        db.String(20),
        nullable=False,
        default='learner',
        comment='User role — learner: standard student | admin: platform administrator'
    )

    # ── Account Status ────────────────────────────────────────
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='Account active flag — False means the account is suspended'
    )

    email_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Whether the user has verified their email address'
    )

    # ── Timestamps ────────────────────────────────────────────
    date_registered = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when the account was created'
    )

    last_login = db.Column(
        db.DateTime,
        nullable=True,
        comment='UTC timestamp of the most recent successful login'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the last profile update'
    )

    # ── Relationships ─────────────────────────────────────────
    # Courses created by this user (admin only)
    courses_created = db.relationship(
        'Course',
        backref='created_by_user',
        lazy='dynamic',
        foreign_keys='Course.created_by',
        cascade='all, delete-orphan'
    )

    # Assignments created by this user (admin only)
    assignments_created = db.relationship(
        'Assignment',
        backref='created_by_user',
        lazy='dynamic',
        foreign_keys='Assignment.created_by',
        cascade='all, delete-orphan'
    )

    # Course enrollments for this user (learner only)
    enrollments = db.relationship(
        'Enrollment',
        backref='learner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Assignment submissions by this user (learner only)
    submissions = db.relationship(
        'Submission',
        backref='learner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Module progress records for this user (learner only)
    progress_records = db.relationship(
        'Progress',
        backref='learner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Grades awarded by this user (admin only)
    grades_awarded = db.relationship(
        'Grade',
        backref='graded_by_user',
        lazy='dynamic',
        foreign_keys='Grade.graded_by',
        cascade='all, delete-orphan'
    )

    # ==========================================================
    # PASSWORD METHODS
    # ==========================================================

    def set_password(self, password):
        """
        Hash and store the provided plaintext password.
        Uses Werkzeug's pbkdf2:sha256 hashing algorithm.

        Args:
            password (str): Plaintext password from registration
                            or password change form.

        Example:
            user.set_password('MySecurePassword123')
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify a plaintext password against the stored hash.

        Args:
            password (str): Plaintext password from login form.

        Returns:
            bool: True if the password matches, False otherwise.

        Example:
            if user.check_password('MySecurePassword123'):
                login_user(user)
        """
        return check_password_hash(self.password_hash, password)

    # ==========================================================
    # ROLE HELPER METHODS
    # ==========================================================

    def is_admin(self):
        """
        Check whether this user has the administrator role.

        Returns:
            bool: True if role is 'admin', False otherwise.
        """
        return self.role == 'admin'

    def is_learner(self):
        """
        Check whether this user has the learner role.

        Returns:
            bool: True if role is 'learner', False otherwise.
        """
        return self.role == 'learner'

    # ==========================================================
    # FLASK-LOGIN REQUIRED OVERRIDE
    # ==========================================================

    def get_id(self):
        """
        Return the user's primary key as a string.
        Required by Flask-Login for session management.

        Returns:
            str: String representation of the user's integer ID.
        """
        return str(self.id)

    # ==========================================================
    # ENROLLMENT HELPERS
    # ==========================================================

    def is_enrolled_in(self, course_id):
        """
        Check whether this learner is enrolled in a given course.

        Args:
            course_id (int): The primary key of the course to check.

        Returns:
            bool: True if an active enrollment exists.
        """
        from app.models.enrollment import Enrollment
        return self.enrollments.filter_by(
            course_id=course_id,
            is_active=True
        ).first() is not None

    def get_enrollment(self, course_id):
        """
        Retrieve the Enrollment object for a specific course.

        Args:
            course_id (int): The primary key of the course.

        Returns:
            Enrollment or None: The enrollment record if found.
        """
        from app.models.enrollment import Enrollment
        return self.enrollments.filter_by(
            course_id=course_id
        ).first()

    def total_enrollments(self):
        """
        Count the total number of courses this learner
        has enrolled in.

        Returns:
            int: Total enrollment count.
        """
        return self.enrollments.count()

    def completed_courses(self):
        """
        Count the number of courses this learner has completed.

        Returns:
            int: Number of completed enrollments.
        """
        from app.models.enrollment import Enrollment
        return self.enrollments.filter_by(
            is_completed=True
        ).count()

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self):
        """
        Serialize the User object to a plain dictionary.
        The password hash is deliberately excluded for security.

        Returns:
            dict: User data safe for JSON responses or template use.
        """
        return {
            'id':                 self.id,
            'full_name':          self.full_name,
            'email':              self.email,
            'phone_number':       self.phone_number,
            'state':              self.state,
            'country':            self.country,
            'profile_photo':      self.profile_photo,
            'bio':                self.bio,
            'farming_background': self.farming_background,
            'role':               self.role,
            'is_active':          self.is_active,
            'email_verified':     self.email_verified,
            'date_registered':    self.date_registered.strftime('%Y-%m-%d %H:%M:%S'),
            'last_login':         self.last_login.strftime('%Y-%m-%d %H:%M:%S')
                                  if self.last_login else None,
        }

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<User id={self.id} '
            f'email={self.email!r} '
            f'role={self.role!r}>'
        )