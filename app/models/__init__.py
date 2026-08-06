# =============================================================
# Agri LMS — Models Package Initializer
# =============================================================
# File    : app/models/__init__.py
# Purpose : Imports and exposes all SQLAlchemy ORM models
#           from the models package so they can be imported
#           cleanly from anywhere in the application using:
#
#               from app.models import User, Course, Module
#
#           All models must be imported here so that
#           Flask-Migrate (Alembic) can detect them when
#           generating migration scripts.
#
#           Import order follows the dependency hierarchy:
#               1. User          — no dependencies
#               2. Course        — depends on User
#               3. Module        — depends on Course
#               4. Material      — depends on Module
#               5. Enrollment    — depends on User, Course
#               6. Assignment    — depends on Course, Module, User
#               7. Submission    — depends on Assignment, User
#               8. Grade         — depends on Submission, User
#               9. Progress      — depends on User, Module, Course
# =============================================================

from app.models.user import User
from app.models.course import Course
from app.models.module import Module
from app.models.material import Material, EXTENSION_TYPE_MAP, MATERIAL_TYPES
from app.models.enrollment import Enrollment, ENROLLMENT_STATUSES
from app.models.assignment import Assignment, ASSIGNMENT_TYPES, ASSIGNMENT_STATUSES
from app.models.submission import Submission, SUBMISSION_STATUSES
from app.models.grade import Grade
from app.models.progress import Progress

# Expose all models and constants for clean imports
__all__ = [
    # Models
    'User',
    'Course',
    'Module',
    'Material',
    'Enrollment',
    'Assignment',
    'Submission',
    'Grade',
    'Progress',

    # Constants
    'EXTENSION_TYPE_MAP',
    'MATERIAL_TYPES',
    'ENROLLMENT_STATUSES',
    'ASSIGNMENT_TYPES',
    'ASSIGNMENT_STATUSES',
    'SUBMISSION_STATUSES',
]