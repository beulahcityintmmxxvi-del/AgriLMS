# =============================================================
# Agri LMS — Application Configuration
# =============================================================
# File    : config.py
# Purpose : Environment-aware configuration for development,
#           testing, and production deployments.
# =============================================================

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    # ── Identity ──────────────────────────────────────────────
    APP_NAME    = os.environ.get('APP_NAME', 'Agri Learning Platform')
    SECRET_KEY  = os.environ.get('SECRET_KEY', 'change-this-in-production')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@agrilms.com')

    # ── Database ──────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'postgresql://postgres:password@localhost:5432/agri_lms_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle':  300,
        'pool_pre_ping': True,
        'pool_size':     10,
        'max_overflow':  20,
    }

    # ── Session Security ──────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7200      # 2 hours

    # ── CSRF ─────────────────────────────────────────────────
    WTF_CSRF_ENABLED    = True
    WTF_CSRF_TIME_LIMIT = 7200

    # ── File Uploads ──────────────────────────────────────────
    _max_mb = int(os.environ.get('MAX_UPLOAD_MB', 100))
    MAX_CONTENT_LENGTH = _max_mb * 1024 * 1024
    UPLOAD_FOLDER      = os.environ.get(
        'UPLOAD_FOLDER', 'app/static/uploads')

    ALLOWED_MATERIAL_EXTENSIONS = {
        'mp4', 'webm', 'mkv', 'avi', 'mov',
        'pdf',
        'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls',
        'png', 'jpg', 'jpeg', 'gif', 'webp',
        'zip', 'rar', 'txt',
    }

    ALLOWED_SUBMISSION_EXTENSIONS = {
        'pdf', 'docx', 'doc', 'pptx', 'xlsx',
        'png', 'jpg', 'jpeg', 'zip', 'rar', 'txt',
        'py', 'ipynb', 'csv',
    }

    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ── Pagination ────────────────────────────────────────────
    ITEMS_PER_PAGE = 10


class DevelopmentConfig(Config):
    """Development — debug on, verbose errors."""
    DEBUG        = True
    TESTING      = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing — isolated database, CSRF off."""
    DEBUG        = True
    TESTING      = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://postgres:password@localhost:5432/agri_lms_test_db'
    )


class ProductionConfig(Config):
    """Production — strict security settings."""
    DEBUG                = False
    TESTING              = False
    SESSION_COOKIE_SECURE = True     # Requires HTTPS
    SQLALCHEMY_ECHO      = False

    # Enforce strong secret key in production
    @classmethod
    def init_app(cls, app):
        if cls.SECRET_KEY == 'change-this-in-production':
            raise ValueError(
                'SECRET_KEY must be set to a strong random value '
                'in production. Set the SECRET_KEY environment variable.'
            )


# ── Config selector ───────────────────────────────────────────
config = {
    'development': DevelopmentConfig,
    'testing':     TestingConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}