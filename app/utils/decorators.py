# =============================================================
# Agri LMS — Custom Route Decorators
# =============================================================
# File    : app/utils/decorators.py
# Purpose : Reusable Flask route decorators for access
#           control, role checking, and request validation.
# =============================================================

from functools import wraps
from flask import redirect, url_for, flash, abort, request
from flask_login import current_user


# =============================================================
# ROLE-BASED ACCESS DECORATORS
# =============================================================

def admin_required(f):
    """
    Restrict a route to admin users only.

    Must be used AFTER @login_required to ensure the user
    is authenticated before the role check occurs.

    Usage:
        @app.route('/admin/dashboard')
        @login_required
        @admin_required
        def admin_dashboard():
            ...

    Returns:
        403 Forbidden if the user is not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash(
                'Access denied. Administrator privileges required.',
                'error'
            )
            return redirect(url_for('learner.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def learner_required(f):
    """
    Restrict a route to learner users only.
    Admins are redirected to the admin dashboard.

    Must be used AFTER @login_required.

    Usage:
        @app.route('/learner/dashboard')
        @login_required
        @learner_required
        def learner_dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def active_account_required(f):
    """
    Ensure the authenticated user's account is active.
    Deactivated accounts are shown an error and redirected.

    Must be used AFTER @login_required.

    Usage:
        @app.route('/learner/courses')
        @login_required
        @active_account_required
        def courses():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_active:
            flash(
                'Your account has been deactivated. '
                'Please contact support for assistance.',
                'error'
            )
            from flask_login import logout_user
            logout_user()
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================
# ENROLLMENT DECORATORS
# =============================================================

def enrollment_required(f):
    """
    Verify that the current learner is enrolled in the
    course specified by the course_id route parameter
    before allowing access to course content.

    Must be used AFTER @login_required.

    The decorated route MUST have a course_id parameter.

    Usage:
        @courses_bp.route('/<int:course_id>/content')
        @login_required
        @enrollment_required
        def course_content(course_id):
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))

        # Admins bypass enrollment checks
        if current_user.is_admin():
            return f(*args, **kwargs)

        course_id = kwargs.get('course_id')
        if not course_id:
            abort(400)

        from app.models.enrollment import Enrollment
        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()

        if not enrollment or not enrollment.can_access_content():
            flash(
                'You must be enrolled in this course '
                'to access its content.',
                'warning'
            )
            return redirect(url_for(
                'courses.course_detail',
                course_id=course_id
            ))

        return f(*args, **kwargs)
    return decorated_function