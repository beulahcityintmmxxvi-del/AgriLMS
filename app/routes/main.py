# =============================================================
# Agri LMS — Main Routes
# =============================================================
# File    : app/routes/main.py
# Purpose : Handles the top-level public-facing routes of the
#           platform — the landing page, about page,
#           and contact page.
#
#           These routes do not require authentication.
#           They are the first pages a visitor sees.
# =============================================================

from flask import Blueprint, render_template

# Create the main blueprint — no URL prefix
# Routes defined here are at the root: /, /about, /contact
main_bp = Blueprint('main', __name__)


# =============================================================
# LANDING PAGE
# =============================================================

@main_bp.route('/')
def index():
    """
    Render the platform landing page.

    The landing page is the first page visitors see.
    It introduces the platform, lists featured courses,
    and provides calls-to-action to register or log in.

    Returns:
        Response: Rendered index.html template.
    """
    return render_template(
        'index.html',
        title='Welcome to Agri Learning Platform'
    )


# =============================================================
# ABOUT PAGE
# =============================================================

@main_bp.route('/about')
def about():
    """
    Render the platform about page.

    Returns:
        Response: Rendered about.html template.
    """
    return render_template(
        'about.html',
        title='About Us'
    )


# =============================================================
# CONTACT PAGE
# =============================================================

@main_bp.route('/contact')
def contact():
    """
    Render the platform contact page.

    Returns:
        Response: Rendered contact.html template.
    """
    return render_template(
        'contact.html',
        title='Contact Us'
    )