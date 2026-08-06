# =============================================================
# Agri LMS — Learner Routes
# =============================================================
# File    : app/routes/learner.py
# Purpose : Handles learner dashboard, profile, and progress.
#           Full implementation coming in Phase 5.
# =============================================================

from flask import Blueprint, render_template
from flask_login import login_required

learner_bp = Blueprint('learner', __name__)


@learner_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the learner dashboard."""
    return render_template('learner/dashboard.html', title='My Dashboard')