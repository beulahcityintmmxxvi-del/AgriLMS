# =============================================================
# Agri LMS — Authentication Routes
# =============================================================
# File    : app/routes/auth.py
# Purpose : Handles user registration, login, and logout.
#           Full implementation coming in Phase 4.
# =============================================================

from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    """Render the login page."""
    return render_template('auth/login.html', title='Login')


@auth_bp.route('/register')
def register():
    """Render the registration page."""
    return render_template('auth/register.html', title='Register')