# =============================================================
# Agri LMS — Flask Extensions
# =============================================================
# File    : app/extensions.py
# Purpose : Initializes all Flask extensions without binding
#           them to a specific app instance.
#           Extensions are bound to the app inside
#           create_app() using the init_app() pattern.
#           This prevents circular imports between
#           app/__init__.py and the model files.
# =============================================================

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# ── Database ORM ──────────────────────────────────────────────
db = SQLAlchemy()

# ── Database Migrations ───────────────────────────────────────
migrate = Migrate()

# ── User Session Management ───────────────────────────────────
login_manager = LoginManager()

# ── CSRF Protection ───────────────────────────────────────────
csrf = CSRFProtect()