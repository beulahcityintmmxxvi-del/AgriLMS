# =============================================================
# Agri LMS — Application Factory
# =============================================================
# File    : app/__init__.py
# Purpose : Flask application factory function.
#           Creates and fully configures the Flask application
#           instance including:
#               - Extension initialization
#               - Blueprint registration
#               - Error handler registration
#               - Jinja2 template utilities
#               - Logging configuration
#               - Database table verification
#
# Pattern : Application Factory — allows multiple instances
#           to be created with different configurations
#           (development, testing, production) without
#           conflicts. All extensions use init_app().
#
# Usage   :
#   from app import create_app
#   app = create_app('development')
#   app.run()
# =============================================================

import os
import logging
from datetime import datetime
from flask import Flask, render_template

from config import config
from app.extensions import db, migrate, login_manager, csrf


# =============================================================
# APPLICATION FACTORY
# =============================================================

def create_app(config_name=None):
    """
    Create and configure a Flask application instance.

    This is the central factory function for the Agri LMS.
    It is called once at startup from run.py and once during
    testing to create isolated test instances.

    Args:
        config_name (str): Configuration profile to load.
            'development' — debug on, verbose errors
            'testing'     — isolated DB, CSRF off
            'production'  — strict security, no debug
            None          — reads FLASK_ENV from environment,
                            falls back to 'development'

    Returns:
        Flask: Fully configured Flask application instance
               ready to handle requests.
    """

    # ── Resolve configuration name ────────────────────────────
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Fallback to development if an unrecognized name is given
    if config_name not in config:
        config_name = 'development'

    # ── Create Flask instance ─────────────────────────────────
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    # ── Load configuration ────────────────────────────────────
    app.config.from_object(config[config_name])

    # ── Configure logging ─────────────────────────────────────
    _configure_logging(app)

    # ── Initialize Flask extensions ───────────────────────────
    _initialize_extensions(app)

    # ── Configure Flask-Login ─────────────────────────────────
    _configure_login_manager(app)

    # ── Register all blueprints ───────────────────────────────
    _register_blueprints(app)

    # ── Register error handlers ───────────────────────────────
    _register_error_handlers(app)

    # ── Register Jinja2 utilities ─────────────────────────────
    _register_template_utilities(app)

    # ── Ensure upload directories exist ───────────────────────
    _ensure_upload_directories(app)

    # ── Verify database tables exist ──────────────────────────
    with app.app_context():
        # Import all models so Flask-Migrate can detect them
        # This import must happen inside app context
        _import_all_models()
        app.logger.info(
            f'Agri LMS started successfully '
            f'[config={config_name}]'
        )

    return app


# =============================================================
# PRIVATE SETUP FUNCTIONS
# =============================================================

def _configure_logging(app):
    """
    Configure application-level logging.

    Development — DEBUG level, console output with timestamps.
    Production  — INFO level, structured format for log files.

    Args:
        app (Flask): The Flask application instance.
    """
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    app.logger.setLevel(log_level)


def _initialize_extensions(app):
    """
    Bind all Flask extensions to the application instance
    using the init_app() pattern.

    Extensions are defined in app/extensions.py without
    an app instance so they can be imported by models
    without causing circular imports.

    Args:
        app (Flask): The Flask application instance.
    """
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.logger.debug('All extensions initialized.')


def _configure_login_manager(app):
    """
    Configure Flask-Login behavior for the application.

    Sets the login view route, message, message category,
    and session protection level.

    Args:
        app (Flask): The Flask application instance.
    """
    from app.models.user import User

    # Route name to redirect unauthenticated users to
    login_manager.login_view = 'auth.login'

    # Flash message shown when redirect happens
    login_manager.login_message = (
        'Please log in to access this page.'
    )

    # Bootstrap alert category for the flash message
    login_manager.login_message_category = 'warning'

    # 'strong' — regenerates session on user-agent change
    # 'basic'  — only checks the session exists
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user object from the database by their ID.

        Called automatically by Flask-Login on every request
        where a user session cookie exists. Returns None if
        the user ID is invalid or the user no longer exists
        in the database — this safely logs out stale sessions.

        Args:
            user_id (str): String form of the user's integer PK.

        Returns:
            User or None: The User object if found, else None.
        """
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    app.logger.debug('Flask-Login configured.')


def _register_blueprints(app):
    """
    Import and register all Flask blueprints.

    Each blueprint handles one feature area of the platform.
    Blueprints are registered with URL prefixes so all their
    routes are namespaced correctly.

    URL structure:
        /           — Main routes (landing, about, contact)
        /auth/      — Authentication (login, register, logout)
        /learner/   — Learner dashboard and profile
        /courses/   — Course catalog and module viewer
        /admin/     — Admin dashboard and management tools

    Args:
        app (Flask): The Flask application instance.
    """
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.learner import learner_bp
    from app.routes.courses import courses_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(learner_bp, url_prefix='/learner')
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(admin_bp,   url_prefix='/admin')

    app.logger.debug('All blueprints registered.')


def _register_error_handlers(app):
    """
    Register custom HTTP error handlers for common
    error codes.

    Each handler renders a dedicated error template
    that matches the platform's visual design rather
    than showing Flask's default plain-text error pages.

    Args:
        app (Flask): The Flask application instance.
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        return render_template(
            'errors/400.html',
            error=error,
            title='Bad Request'
        ), 400

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden — unauthorized access attempt."""
        return render_template(
            'errors/403.html',
            error=error,
            title='Access Forbidden'
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found — missing page or resource."""
        return render_template(
            'errors/404.html',
            error=error,
            title='Page Not Found'
        ), 404

    @app.errorhandler(413)
    def file_too_large(error):
        """Handle 413 Payload Too Large — file upload exceeds limit."""
        return render_template(
            'errors/413.html',
            error=error,
            title='File Too Large'
        ), 413

    @app.errorhandler(500)
    def internal_error(error):
        """
        Handle 500 Internal Server Error.
        Rolls back the database session to prevent
        corrupted transactions from persisting.
        """
        db.session.rollback()
        return render_template(
            'errors/500.html',
            error=error,
            title='Server Error'
        ), 500

    app.logger.debug('Error handlers registered.')


def _register_template_utilities(app):
    """
    Register Jinja2 context processors, custom template
    filters, and global template functions.

    Context processors inject variables into every template
    automatically — no need to pass them from each route.

    Custom filters allow clean formatting of data types
    directly inside Jinja2 template expressions.

    Args:
        app (Flask): The Flask application instance.
    """

    # ── Context Processor — Global Template Variables ─────────
    @app.context_processor
    def inject_globals():
        """
        Inject global variables available in every template.

        These variables do not need to be passed from
        individual route functions — they are available
        in every render_template() call automatically.

        Returns:
            dict: Key-value pairs injected into template context.
        """
        return {
            'app_name':        app.config.get('APP_NAME', 'Agri Learning Platform'),
            'current_year':    datetime.utcnow().year,
            'current_time':    datetime.utcnow(),
        }

    # ── Custom Filter — Currency Formatting ───────────────────
    @app.template_filter('naira')
    def naira_filter(value):
        """
        Format a numeric value as Nigerian Naira currency.

        Usage in template:
            {{ course.price | naira }}
            → ₦15,000.00

        Args:
            value: Numeric value to format.

        Returns:
            str: Formatted Naira string.
        """
        try:
            return f'₦{float(value):,.2f}'
        except (ValueError, TypeError):
            return '₦0.00'

    # ── Custom Filter — Date Formatting ───────────────────────
    @app.template_filter('dateformat')
    def dateformat_filter(value, fmt='%d %b %Y'):
        """
        Format a datetime object into a readable string.

        Usage in template:
            {{ enrollment.date_enrolled | dateformat }}
            → 15 Jan 2025

            {{ enrollment.date_enrolled | dateformat('%d/%m/%Y') }}
            → 15/01/2025

        Args:
            value (datetime): The datetime to format.
            fmt (str): strftime format string.

        Returns:
            str: Formatted date string or 'N/A'.
        """
        if not value:
            return 'N/A'
        try:
            return value.strftime(fmt)
        except AttributeError:
            return 'N/A'

    # ── Custom Filter — Text Truncation ───────────────────────
    @app.template_filter('truncate_words')
    def truncate_words_filter(text, num_words=20):
        """
        Truncate text to a maximum number of words,
        appending an ellipsis if truncation occurs.

        Usage in template:
            {{ course.description | truncate_words(15) }}

        Args:
            text (str): The text to truncate.
            num_words (int): Maximum number of words.

        Returns:
            str: Truncated text with ellipsis if needed.
        """
        if not text:
            return ''
        words = str(text).split()
        if len(words) <= num_words:
            return text
        return ' '.join(words[:num_words]) + '...'

    # ── Custom Filter — File Size Display ─────────────────────
    @app.template_filter('filesize')
    def filesize_filter(size_bytes):
        """
        Convert raw bytes into a human-readable file size.

        Usage in template:
            {{ material.file_size_bytes | filesize }}
            → 2.5 MB

        Args:
            size_bytes (int): File size in bytes.

        Returns:
            str: Human-readable file size string.
        """
        if not size_bytes:
            return 'Unknown'
        try:
            size = int(size_bytes)
            if size < 1024:
                return f'{size} B'
            elif size < 1024 ** 2:
                return f'{size / 1024:.1f} KB'
            elif size < 1024 ** 3:
                return f'{size / (1024 ** 2):.1f} MB'
            else:
                return f'{size / (1024 ** 3):.1f} GB'
        except (ValueError, TypeError):
            return 'Unknown'

    # ── Custom Filter — Percentage Display ────────────────────
    @app.template_filter('percent')
    def percent_filter(value):
        """
        Format a numeric value as a clean percentage string.

        Usage in template:
            {{ enrollment.progress_percent | percent }}
            → 66%

        Args:
            value: Numeric value to format.

        Returns:
            str: Formatted percentage string.
        """
        try:
            v = float(value)
            if v == int(v):
                return f'{int(v)}%'
            return f'{v:.1f}%'
        except (ValueError, TypeError):
            return '0%'

    # ── Custom Filter — Grade Letter Color ────────────────────
    @app.template_filter('grade_color')
    def grade_color_filter(letter):
        """
        Return a CSS color class for a grade letter.

        Usage in template:
            <span class="{{ grade.grade_letter | grade_color }}">
                {{ grade.grade_letter }}
            </span>

        Args:
            letter (str): Grade letter — A, B, C, D, or F.

        Returns:
            str: CSS class string.
        """
        colors = {
            'A': 'text-success',
            'B': 'text-primary',
            'C': 'text-info',
            'D': 'text-warning',
            'F': 'text-danger',
        }
        return colors.get(str(letter).upper(), 'text-secondary')

    app.logger.debug('Template utilities registered.')


def _ensure_upload_directories(app):
    """
    Create all required upload directories if they
    do not already exist.

    Upload directories are excluded from Git via .gitignore
    but must exist on the server for file saving to work.
    This function ensures they are always present when
    the application starts.

    Args:
        app (Flask): The Flask application instance.
    """
    base = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')

    directories = [
        base,
        os.path.join(base, 'materials'),
        os.path.join(base, 'submissions'),
        os.path.join(base, 'thumbnails'),
        os.path.join(base, 'profiles'),
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    app.logger.debug('Upload directories verified.')


def _import_all_models():
    """
    Import all SQLAlchemy models to ensure Flask-Migrate
    (Alembic) can detect all tables for migration generation.

    This function is called inside the app context so
    the db instance is fully bound before models are imported.

    All models must be imported here — models that are never
    imported will be invisible to flask db migrate and will
    not appear in the generated migration script.
    """
    from app.models import (       # noqa: F401
        User,
        Course,
        Module,
        Material,
        Enrollment,
        Assignment,
        Submission,
        Grade,
        Progress,
    )