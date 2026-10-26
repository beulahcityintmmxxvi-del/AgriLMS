# =============================================================
# Agri LMS — Authentication Routes
# =============================================================
# File    : app/routes/auth.py
# Purpose : Handles all user authentication including:
#               - Learner registration with validation
#               - Login with email and password
#               - Secure logout with session clearing
#               - Role-based post-login redirection
#               - Duplicate email prevention
#               - Password hashing via Werkzeug
#               - CSRF protection via Flask-WTF
#               - Flask-Login session management
#
# Routes  :
#   GET  /auth/register  — Show registration form
#   POST /auth/register  — Process registration
#   GET  /auth/login     — Show login form
#   POST /auth/login     — Process login
#   GET  /auth/logout    — Log out and clear session
# =============================================================

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from app.extensions import db
from app.models.user import User

# =============================================================
# BLUEPRINT
# =============================================================

auth_bp = Blueprint('auth', __name__)


# =============================================================
# HELPER FUNCTIONS
# =============================================================

def _redirect_authenticated_user():
    """
    Redirect an already-authenticated user to their
    appropriate dashboard based on their role.

    Returns:
        Response: Redirect to admin or learner dashboard.
    """
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('learner.dashboard'))


def _validate_registration_form(form_data):
    """
    Validate all registration form fields server-side.

    Performs validation that cannot be done by HTML5 alone:
        - Required field checks
        - Email format validation
        - Password length and match validation
        - Phone number format check (optional)

    Args:
        form_data (dict): The request.form dictionary.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    full_name    = form_data.get('full_name', '').strip()
    email        = form_data.get('email', '').strip().lower()
    password     = form_data.get('password', '')
    confirm_pass = form_data.get('confirm_password', '')
    phone        = form_data.get('phone_number', '').strip()

    # ── Required fields ──────────────────────────────────────
    if not full_name:
        errors.append('Full name is required.')
    elif len(full_name) < 2:
        errors.append('Full name must be at least 2 characters.')
    elif len(full_name) > 150:
        errors.append('Full name must not exceed 150 characters.')

    if not email:
        errors.append('Email address is required.')
    elif '@' not in email or '.' not in email.split('@')[-1]:
        errors.append('Please enter a valid email address.')
    elif len(email) > 150:
        errors.append('Email address is too long.')

    # ── Password validation ───────────────────────────────────
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

    if not confirm_pass:
        errors.append('Please confirm your password.')
    elif password and confirm_pass and password != confirm_pass:
        errors.append('Passwords do not match. Please try again.')

    # ── Optional phone validation ─────────────────────────────
    if phone:
        cleaned_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        if not cleaned_phone.isdigit():
            errors.append('Phone number must contain only digits, spaces, or hyphens.')
        elif len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
            errors.append('Phone number must be between 10 and 15 digits.')

    return len(errors) == 0, errors


def _validate_login_form(form_data):
    """
    Validate login form fields server-side.

    Args:
        form_data (dict): The request.form dictionary.

    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []

    email    = form_data.get('email', '').strip()
    password = form_data.get('password', '')

    if not email:
        errors.append('Email address is required.')
    if not password:
        errors.append('Password is required.')

    return len(errors) == 0, errors


# =============================================================
# REGISTRATION
# =============================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle learner registration.

    GET  — Display the registration form.
    POST — Validate form data, create User record,
           log the user in, and redirect to dashboard.

    Validation steps:
        1. Redirect if already authenticated
        2. Server-side field validation
        3. Duplicate email check against database
        4. User creation with hashed password
        5. Auto-login after successful registration
        6. Redirect to learner dashboard

    Returns:
        GET  — Rendered register.html template
        POST — Redirect on success | Re-render with errors
    """

    # Already logged in — redirect to appropriate dashboard
    if current_user.is_authenticated:
        return _redirect_authenticated_user()

    # ── GET — Display empty registration form ─────────────────
    if request.method == 'GET':
        return render_template(
            'auth/register.html',
            title='Create Your Account'
        )

    # ── POST — Process registration form ──────────────────────
    form_data = request.form

    # Step 1 — Server-side validation
    is_valid, errors = _validate_registration_form(form_data)

    if not is_valid:
        for error in errors:
            flash(error, 'error')
        return render_template(
            'auth/register.html',
            title='Create Your Account',
            form_data=form_data
        )

    # Step 2 — Extract cleaned form data
    full_name    = form_data.get('full_name', '').strip()
    email        = form_data.get('email', '').strip().lower()
    password     = form_data.get('password', '')
    phone_number = form_data.get('phone_number', '').strip() or None
    state        = form_data.get('state', '').strip() or None
    country      = form_data.get('country', 'Nigeria').strip()

    # Step 3 — Check for duplicate email
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash(
            'An account with this email address already exists. '
            'Please log in or use a different email.',
            'error'
        )
        return render_template(
            'auth/register.html',
            title='Create Your Account',
            form_data=form_data
        )

    # Step 4 — Create the new user
    try:
        new_user = User(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            state=state,
            country=country,
            role='learner',
            is_active=True,
            date_registered=datetime.utcnow()
        )

        # Hash the password — never store plaintext
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.flush()  # Get the new user's ID before commit

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(
            'An error occurred while creating your account. '
            'Please try again.',
            'error'
        )
        return render_template(
            'auth/register.html',
            title='Create Your Account',
            form_data=form_data
        )

    # Step 5 — Auto-login the new user
    login_user(new_user, remember=False)

    # Update last login timestamp
    new_user.last_login = datetime.utcnow()
    db.session.commit()

    # Step 6 — Success message and redirect
    flash(
        f'Welcome to Agri LMS, {new_user.full_name.split()[0]}! '
        f'Your account has been created successfully. '
        f'Start by browsing our available courses.',
        'success'
    )

    return redirect(url_for('learner.dashboard'))


# =============================================================
# LOGIN
# =============================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    GET  — Display the login form.
    POST — Validate credentials, create session,
           and redirect to appropriate dashboard.

    Security measures:
        - Constant-time password comparison via Werkzeug
        - Account active status check before login
        - Generic error messages to prevent email enumeration
        - Remember-me session persistence
        - next URL validation to prevent open redirect

    Returns:
        GET  — Rendered login.html template
        POST — Redirect on success | Re-render with errors
    """

    # Already logged in — redirect to appropriate dashboard
    if current_user.is_authenticated:
        return _redirect_authenticated_user()

    # Capture the 'next' URL from query string for post-login redirect
    next_page = request.args.get('next', '')

    # ── GET — Display empty login form ────────────────────────
    if request.method == 'GET':
        return render_template(
            'auth/login.html',
            title='Log In to Your Account',
            next_page=next_page
        )

    # ── POST — Process login form ─────────────────────────────
    form_data = request.form

    # Step 1 — Basic field validation
    is_valid, errors = _validate_login_form(form_data)

    if not is_valid:
        for error in errors:
            flash(error, 'error')
        return render_template(
            'auth/login.html',
            title='Log In to Your Account',
            form_data=form_data,
            next_page=next_page
        )

    # Step 2 — Extract form data
    email       = form_data.get('email', '').strip().lower()
    password    = form_data.get('password', '')
    remember_me = form_data.get('remember_me') == 'on'

    # Step 3 — Look up user by email
    user = User.query.filter_by(email=email).first()

    # Step 4 — Verify credentials
    # Use a generic message to prevent email enumeration attacks
    if not user or not user.check_password(password):
        flash(
            'Invalid email address or password. '
            'Please check your credentials and try again.',
            'error'
        )
        return render_template(
            'auth/login.html',
            title='Log In to Your Account',
            form_data=form_data,
            next_page=next_page
        )

    # Step 5 — Check account is active
    if not user.is_active:
        flash(
            'Your account has been deactivated. '
            'Please contact support for assistance.',
            'error'
        )
        return render_template(
            'auth/login.html',
            title='Log In to Your Account',
            form_data=form_data,
            next_page=next_page
        )

    # Step 6 — Create authenticated session
    login_user(user, remember=remember_me)

    # Step 7 — Update last login timestamp
    try:
        user.last_login = datetime.utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Step 8 — Flash welcome message
    flash(
        f'Welcome back, {user.full_name.split()[0]}! '
        f'You have logged in successfully.',
        'success'
    )

    # Step 9 — Redirect to next page or role-appropriate dashboard
    # Validate next_page to prevent open redirect vulnerability
    if next_page and next_page.startswith('/') and not next_page.startswith('//'):
        return redirect(next_page)

    return _redirect_authenticated_user()


# =============================================================
# LOGOUT
# =============================================================

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user and clear their session.

    Clears the Flask-Login session, flashes a goodbye message,
    and redirects to the platform landing page.

    The @login_required decorator ensures only authenticated
    users can access this route. Unauthenticated GET requests
    are automatically redirected to the login page.

    Returns:
        Response: Redirect to landing page after logout.
    """

    # Capture name before logout clears current_user
    user_name = current_user.full_name.split()[0] \
        if current_user.full_name else 'Learner'

    # Clear the Flask-Login session
    logout_user()

    # Clear any remaining session data
    session.clear()

    flash(
        f'You have been logged out successfully. '
        f'See you again soon, {user_name}!',
        'info'
    )

    return redirect(url_for('main.index'))