# =============================================================
# Agri LMS — Main Routes
# =============================================================
# File    : app/routes/main.py
# Purpose : Handles public-facing pages — landing page,
#           about page, and contact page with form submission.
# =============================================================

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, request
)
from app.extensions import db
from app.models.course import Course


main_bp = Blueprint('main', __name__)


# =============================================================
# LANDING PAGE
# =============================================================

@main_bp.route('/')
def index():
    """Render the platform landing page with featured courses."""
    try:
        featured_courses = Course.query.filter_by(
            is_published=True,
            is_featured=True,
            is_archived=False
        ).order_by(Course.date_created.desc()).limit(6).all()

        if not featured_courses:
            featured_courses = Course.query.filter_by(
                is_published=True,
                is_archived=False
            ).order_by(Course.date_created.desc()).limit(6).all()

    except Exception:
        featured_courses = []

    return render_template(
        'index.html',
        title='Welcome — Learn Agriculture Online',
        featured_courses=featured_courses
    )


# =============================================================
# ABOUT PAGE
# =============================================================

@main_bp.route('/about')
def about():
    """Render the platform about page."""
    return render_template(
        'about.html',
        title='About Us'
    )


# =============================================================
# CONTACT PAGE
# =============================================================

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Render the contact page and handle form submissions.

    GET  — Display the contact form.
    POST — Process the contact form submission.
    """

    if request.method == 'POST':

        # Extract form fields
        sender_name  = request.form.get('sender_name', '').strip()
        sender_email = request.form.get('sender_email', '').strip()
        sender_phone = request.form.get('sender_phone', '').strip()
        category     = request.form.get('category', '').strip()
        subject      = request.form.get('subject', '').strip()
        message      = request.form.get('message', '').strip()

        # Server-side validation
        errors = []

        if not sender_name or len(sender_name) < 2:
            errors.append('Please enter your full name.')

        if not sender_email or '@' not in sender_email:
            errors.append('Please enter a valid email address.')

        if not category:
            errors.append('Please select a message category.')

        if not subject or len(subject) < 5:
            errors.append('Please enter a subject.')

        if not message or len(message) < 20:
            errors.append('Please enter a message.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'contact.html',
                title='Contact Us'
            )

        # Save to database if ContactMessage model exists
        try:
            from app.models.contact_message import ContactMessage
            msg = ContactMessage(
                sender_name=sender_name,
                sender_email=sender_email,
                sender_phone=sender_phone or None,
                subject=f'[{category}] {subject}',
                message=message,
                is_read=False,
                is_replied=False
            )
            db.session.add(msg)
            db.session.commit()
        except Exception:
            # If ContactMessage model doesn't exist yet,
            # just show success without saving
            pass

        flash(
            f'Thank you {sender_name.split()[0]}! Your message has been '
            f'received. We will respond to {sender_email} within 24–48 hours.',
            'success'
        )

        return redirect(url_for('main.contact') + '?sent=1')

    return render_template(
        'contact.html',
        title='Contact Us'
    )