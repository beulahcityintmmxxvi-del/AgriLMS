# =============================================================
# Agri LMS — Utils Package
# =============================================================
# File    : app/utils/__init__.py
# Purpose : Exposes utility functions and classes for
#           clean imports throughout the application.
#
# Usage:
#   from app.utils import format_file_size, sanitize_string
#   from app.utils.decorators import admin_required
#   from app.utils.validators import validate_registration
# =============================================================

from app.utils.helpers import (
    Pagination,
    format_file_size,
    format_naira,
    format_date,
    format_datetime,
    time_since,
    truncate_words,
    truncate_chars,
    slugify,
    parse_comma_list,
    parse_newline_list,
    calculate_percentage,
    get_grade_letter,
    get_grade_label,
    ensure_upload_dirs,
    get_upload_path,
    file_exists,
    delete_upload_file,
)

from app.utils.security import (
    sanitize_string,
    sanitize_email,
    sanitize_filename,
    sanitize_integer,
    sanitize_float,
    is_safe_file_extension,
    is_safe_file_size,
    get_file_size_bytes,
    generate_secure_filename,
    is_safe_redirect_url,
    get_safe_next_url,
    log_security_event,
    log_failed_login,
    log_access_denied,
)

from app.utils.validators import (
    validate_registration,
    validate_login,
    validate_course_form,
    validate_module_form,
    validate_assignment_form,
    validate_grade_form,
    validate_profile_update,
)

from app.utils.decorators import (
    admin_required,
    learner_required,
    active_account_required,
    enrollment_required,
)

__all__ = [
    # Helpers
    'Pagination',
    'format_file_size', 'format_naira', 'format_date',
    'format_datetime', 'time_since', 'truncate_words',
    'truncate_chars', 'slugify', 'parse_comma_list',
    'parse_newline_list', 'calculate_percentage',
    'get_grade_letter', 'get_grade_label',
    'ensure_upload_dirs', 'get_upload_path',
    'file_exists', 'delete_upload_file',

    # Security
    'sanitize_string', 'sanitize_email', 'sanitize_filename',
    'sanitize_integer', 'sanitize_float',
    'is_safe_file_extension', 'is_safe_file_size',
    'get_file_size_bytes', 'generate_secure_filename',
    'is_safe_redirect_url', 'get_safe_next_url',
    'log_security_event', 'log_failed_login', 'log_access_denied',

    # Validators
    'validate_registration', 'validate_login',
    'validate_course_form', 'validate_module_form',
    'validate_assignment_form', 'validate_grade_form',
    'validate_profile_update',

    # Decorators
    'admin_required', 'learner_required',
    'active_account_required', 'enrollment_required',
]