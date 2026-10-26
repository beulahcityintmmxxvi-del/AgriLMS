# =============================================================
# Agri LMS — Input Validators
# =============================================================
# File    : app/utils/validators.py
# Purpose : Reusable server-side input validation functions
#           for all platform forms. Each validator returns
#           a tuple of (is_valid: bool, errors: list[str]).
# =============================================================

import re
from datetime import datetime


# =============================================================
# REGISTRATION FORM VALIDATOR
# =============================================================

def validate_registration(form_data):
    """
    Validate all fields in the learner registration form.

    Args:
        form_data (dict): Form data from request.form.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    full_name    = form_data.get('full_name', '').strip()
    email        = form_data.get('email', '').strip().lower()
    password     = form_data.get('password', '')
    confirm      = form_data.get('confirm_password', '')
    phone        = form_data.get('phone_number', '').strip()

    # Full name
    if not full_name:
        errors.append('Full name is required.')
    elif len(full_name) < 2:
        errors.append('Full name must be at least 2 characters.')
    elif len(full_name) > 150:
        errors.append('Full name must not exceed 150 characters.')
    elif re.search(r'[<>"\'{}|\\^`]', full_name):
        errors.append('Full name contains invalid characters.')

    # Email
    if not email:
        errors.append('Email address is required.')
    elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        errors.append('Please enter a valid email address.')
    elif len(email) > 150:
        errors.append('Email address is too long (max 150 characters).')

    # Password
    if not password:
        errors.append('Password is required.')
    elif len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    elif len(password) > 128:
        errors.append('Password must not exceed 128 characters.')
    elif password.isdigit():
        errors.append('Password must contain at least one letter.')
    elif password.isalpha():
        errors.append('Password must contain at least one number.')

    # Confirm password
    if password and confirm and password != confirm:
        errors.append('Passwords do not match. Please try again.')
    elif not confirm and password:
        errors.append('Please confirm your password.')

    # Phone (optional)
    if phone:
        cleaned = re.sub(r'[\s\-\+\(\)]', '', phone)
        if not cleaned.isdigit():
            errors.append(
                'Phone number must contain only digits, spaces, or hyphens.')
        elif len(cleaned) < 10 or len(cleaned) > 15:
            errors.append(
                'Phone number must be between 10 and 15 digits.')

    return len(errors) == 0, errors


# =============================================================
# LOGIN FORM VALIDATOR
# =============================================================

def validate_login(form_data):
    """
    Validate the login form fields.

    Args:
        form_data (dict): Form data from request.form.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    email    = form_data.get('email', '').strip()
    password = form_data.get('password', '')

    if not email:
        errors.append('Email address is required.')
    elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        errors.append('Please enter a valid email address.')

    if not password:
        errors.append('Password is required.')

    return len(errors) == 0, errors


# =============================================================
# COURSE FORM VALIDATOR
# =============================================================

def validate_course_form(form_data):
    """
    Validate the course creation and editing form.

    Args:
        form_data (dict): Form data from request.form.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    title       = form_data.get('title', '').strip()
    short_desc  = form_data.get('short_description', '').strip()
    pass_score  = form_data.get('passing_score', '').strip()
    dur_weeks   = form_data.get('duration_weeks', '').strip()
    max_enroll  = form_data.get('max_enrollments', '').strip()

    if not title:
        errors.append('Course title is required.')
    elif len(title) > 300:
        errors.append('Course title must not exceed 300 characters.')

    if not short_desc:
        errors.append('Short description is required.')
    elif len(short_desc) > 500:
        errors.append('Short description must not exceed 500 characters.')

    if pass_score:
        try:
            ps = float(pass_score)
            if ps < 0 or ps > 100:
                errors.append('Passing score must be between 0 and 100.')
        except ValueError:
            errors.append('Passing score must be a valid number.')

    if dur_weeks:
        try:
            dw = int(dur_weeks)
            if dw < 1 or dw > 104:
                errors.append('Duration must be between 1 and 104 weeks.')
        except ValueError:
            errors.append('Duration must be a valid whole number of weeks.')

    if max_enroll:
        try:
            me = int(max_enroll)
            if me < 1:
                errors.append('Maximum enrollments must be at least 1.')
        except ValueError:
            errors.append('Maximum enrollments must be a valid number.')

    return len(errors) == 0, errors


# =============================================================
# MODULE FORM VALIDATOR
# =============================================================

def validate_module_form(form_data):
    """
    Validate the module creation and editing form.

    Args:
        form_data (dict): Form data from request.form.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    title      = form_data.get('title', '').strip()
    course_id  = form_data.get('course_id', '').strip()
    order_num  = form_data.get('order_number', '').strip()
    duration   = form_data.get('duration_minutes', '').strip()

    if not title:
        errors.append('Module title is required.')
    elif len(title) > 300:
        errors.append('Module title must not exceed 300 characters.')

    if not course_id:
        errors.append('Please select a parent course.')
    else:
        try:
            int(course_id)
        except ValueError:
            errors.append('Invalid course selection.')

    if order_num:
        try:
            on = int(order_num)
            if on < 1:
                errors.append('Order number must be at least 1.')
        except ValueError:
            errors.append('Order number must be a whole number.')

    if duration:
        try:
            dm = int(duration)
            if dm < 1:
                errors.append('Duration must be at least 1 minute.')
            elif dm > 600:
                errors.append(
                    'Duration must not exceed 600 minutes (10 hours).')
        except ValueError:
            errors.append('Duration must be a whole number of minutes.')

    return len(errors) == 0, errors


# =============================================================
# ASSIGNMENT FORM VALIDATOR
# =============================================================

def validate_assignment_form(form_data):
    """
    Validate the assignment creation and editing form.

    Args:
        form_data (dict): Form data from request.form.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    title       = form_data.get('title', '').strip()
    description = form_data.get('description', '').strip()
    course_id   = form_data.get('course_id', '').strip()
    total_marks = form_data.get('total_marks', '').strip()
    pass_mark   = form_data.get('pass_mark', '').strip()
    due_date    = form_data.get('due_date', '').strip()
    max_subs    = form_data.get('max_submissions', '').strip()

    if not title:
        errors.append('Assignment title is required.')
    elif len(title) > 300:
        errors.append('Assignment title must not exceed 300 characters.')

    if not description:
        errors.append('Assignment description is required.')

    if not course_id:
        errors.append('Please select a course for this assignment.')

    if total_marks:
        try:
            tm = float(total_marks)
            if tm <= 0:
                errors.append('Total marks must be greater than zero.')
            elif tm > 1000:
                errors.append('Total marks must not exceed 1000.')
        except ValueError:
            errors.append('Total marks must be a valid number.')

    if pass_mark and total_marks:
        try:
            pm = float(pass_mark)
            tm = float(total_marks)
            if pm < 0:
                errors.append('Pass mark cannot be negative.')
            elif pm > tm:
                errors.append('Pass mark cannot exceed total marks.')
        except ValueError:
            pass  # Already caught by total_marks validation

    if due_date:
        try:
            dt = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            if dt < datetime.utcnow():
                errors.append(
                    'Due date is in the past. '
                    'Consider setting a future date or leaving it blank.')
        except ValueError:
            errors.append(
                'Due date format is invalid. '
                'Please use the date picker.')

    if max_subs:
        try:
            ms = int(max_subs)
            if ms < 1:
                errors.append('Maximum submissions must be at least 1.')
            elif ms > 10:
                errors.append(
                    'Maximum submissions must not exceed 10.')
        except ValueError:
            errors.append('Maximum submissions must be a whole number.')

    return len(errors) == 0, errors


# =============================================================
# GRADE FORM VALIDATOR
# =============================================================

def validate_grade_form(form_data, total_marks):
    """
    Validate the grading form submission.

    Args:
        form_data (dict): Form data from request.form.
        total_marks (float): Maximum marks for the assignment.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    score_awarded = form_data.get('score_awarded', '').strip()

    if not score_awarded:
        errors.append('Please enter a score to award.')
    else:
        try:
            score = float(score_awarded)
            if score < 0:
                errors.append('Score cannot be negative.')
            elif total_marks and score > float(total_marks):
                errors.append(
                    f'Score ({score}) cannot exceed '
                    f'total marks ({total_marks}).')
        except ValueError:
            errors.append('Score must be a valid number.')

    return len(errors) == 0, errors


# =============================================================
# PROFILE UPDATE VALIDATOR
# =============================================================

def validate_profile_update(form_data):
    """
    Validate the learner profile update form.

    Args:
        form_data (dict): Form data from request.form.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    full_name = form_data.get('full_name', '').strip()
    phone     = form_data.get('phone_number', '').strip()
    bio       = form_data.get('bio', '').strip()

    if not full_name:
        errors.append('Full name is required.')
    elif len(full_name) < 2:
        errors.append('Full name must be at least 2 characters.')
    elif len(full_name) > 150:
        errors.append('Full name must not exceed 150 characters.')

    if phone:
        cleaned = re.sub(r'[\s\-\+\(\)]', '', phone)
        if not cleaned.isdigit():
            errors.append('Phone number must contain only digits.')
        elif len(cleaned) < 10 or len(cleaned) > 15:
            errors.append(
                'Phone number must be between 10 and 15 digits.')

    if bio and len(bio) > 500:
        errors.append('Bio must not exceed 500 characters.')

    return len(errors) == 0, errors