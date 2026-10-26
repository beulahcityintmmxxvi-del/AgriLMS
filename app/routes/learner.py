# =============================================================
# Agri LMS — Learner Routes
# =============================================================
# File    : app/routes/learner.py
# Purpose : Handles all learner-facing pages including:
#               - Dashboard
#               - My courses
#               - Progress tracking
#               - Profile management
#               - Assignment listing and submission
#               - Submission history and feedback
# =============================================================

import os
import uuid
import re
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    send_from_directory,
    abort,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.progress import Progress
from app.models.grade import Grade


# =============================================================
# BLUEPRINT
# =============================================================

learner_bp = Blueprint('learner', __name__)


# =============================================================
# HELPER — ADMIN REDIRECT GUARD
# =============================================================

def _learner_only():
    """
    Redirect admin users away from learner pages.

    Returns:
        Response or None
    """
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    return None


# =============================================================
# HELPER — FILE UPLOAD
# =============================================================

def _allowed_submission_file(filename):
    """
    Check whether an uploaded filename has an allowed extension
    for assignment submissions.

    Args:
        filename (str): The original filename from the upload.

    Returns:
        bool: True if the extension is permitted.
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get(
        'ALLOWED_SUBMISSION_EXTENSIONS',
        {'pdf', 'docx', 'doc', 'pptx', 'xlsx',
         'png', 'jpg', 'jpeg', 'zip', 'rar', 'txt'}
    )


def _save_submission_file(file_obj, original_filename):
    """
    Save an uploaded submission file to the submissions
    upload directory with a UUID-prefixed safe filename.

    Args:
        file_obj: Werkzeug FileStorage object from request.files.
        original_filename (str): Original filename as uploaded.

    Returns:
        tuple: (stored_filename, file_size_bytes, mime_type, extension)
               Returns (None, None, None, None) on failure.
    """
    try:
        # Sanitize original filename
        safe_name = secure_filename(original_filename)
        if not safe_name:
            safe_name = 'upload'

        # Generate unique stored filename
        unique_prefix = uuid.uuid4().hex[:8]
        stored_name   = f'{unique_prefix}_{safe_name}'

        # Build upload path
        upload_dir = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
            'submissions'
        )
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, stored_name)
        file_obj.save(file_path)

        # Get file metadata
        file_size = os.path.getsize(file_path)
        extension = safe_name.rsplit('.', 1)[-1].lower() \
            if '.' in safe_name else ''
        mime_type = file_obj.content_type or None

        return stored_name, file_size, mime_type, extension

    except Exception:
        return None, None, None, None


# =============================================================
# DASHBOARD
# =============================================================

@learner_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Render the learner dashboard with platform statistics,
    enrolled courses, upcoming assignments, and charts.
    """
    guard = _learner_only()
    if guard:
        return guard

    user_id = current_user.id

    # ── Enrollment Statistics ─────────────────────────────────
    try:
        all_enrollments   = Enrollment.query.filter_by(
            user_id=user_id
        ).all()
        total_enrolled    = len(all_enrollments)
        active_courses    = sum(
            1 for e in all_enrollments if e.status == 'active'
        )
        completed_courses = sum(
            1 for e in all_enrollments if e.is_completed
        )
        in_progress       = sum(
            1 for e in all_enrollments
            if e.status == 'active' and not e.is_completed
        )
        overall_progress  = round(
            sum(float(e.progress_percent or 0)
                for e in all_enrollments
                if e.status in ('active', 'completed')) /
            max(total_enrolled, 1), 1
        ) if total_enrolled > 0 else 0.0

    except Exception:
        all_enrollments = []
        total_enrolled  = active_courses = completed_courses = 0
        in_progress     = 0
        overall_progress = 0.0

    # ── Assignment Statistics ─────────────────────────────────
    try:
        enrolled_course_ids = [e.course_id for e in all_enrollments]
        total_assignments   = 0

        if enrolled_course_ids:
            total_assignments = Assignment.query.filter(
                Assignment.course_id.in_(enrolled_course_ids),
                Assignment.is_published == True
            ).count()

        all_submissions = Submission.query.filter_by(
            user_id=user_id
        ).all()

        total_submitted = len(all_submissions)
        pending_grades  = sum(
            1 for s in all_submissions if not s.is_graded
        )
        graded_count    = sum(
            1 for s in all_submissions if s.is_graded
        )
        graded_scores   = [
            float(s.score_percent)
            for s in all_submissions
            if s.is_graded and s.score_percent is not None
        ]
        average_grade   = round(
            sum(graded_scores) / len(graded_scores), 1
        ) if graded_scores else None

    except Exception:
        total_assignments = total_submitted = 0
        pending_grades    = graded_count    = 0
        average_grade     = None

    # ── Recent Enrollments ────────────────────────────────────
    try:
        recent_enrollments = Enrollment.query.filter_by(
            user_id=user_id
        ).order_by(
            Enrollment.date_enrolled.desc()
        ).limit(4).all()
    except Exception:
        recent_enrollments = []

    # ── Upcoming Assignments ──────────────────────────────────
    try:
        upcoming_assignments = []
        if enrolled_course_ids:
            now       = datetime.utcnow()
            due_limit = now + timedelta(days=14)
            upcoming_assignments = Assignment.query.filter(
                Assignment.course_id.in_(enrolled_course_ids),
                Assignment.is_published == True,
                Assignment.due_date != None,
                Assignment.due_date >= now,
                Assignment.due_date <= due_limit
            ).order_by(Assignment.due_date.asc()).limit(5).all()
    except Exception:
        upcoming_assignments = []

    # ── Recent Submissions ────────────────────────────────────
    try:
        recent_submissions = Submission.query.filter_by(
            user_id=user_id
        ).order_by(
            Submission.date_submitted.desc()
        ).limit(5).all()
    except Exception:
        recent_submissions = []

    # ── Weekly Activity Data ──────────────────────────────────
    try:
        weekly_labels   = []
        weekly_activity = []
        for i in range(6, -1, -1):
            day       = datetime.utcnow().date() - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end   = datetime.combine(day, datetime.max.time())
            count     = Progress.query.filter(
                Progress.user_id == user_id,
                Progress.is_completed == True,
                Progress.date_completed >= day_start,
                Progress.date_completed <= day_end
            ).count()
            weekly_labels.append(day.strftime('%a'))
            weekly_activity.append(count)
    except Exception:
        weekly_labels   = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        weekly_activity = [0, 0, 0, 0, 0, 0, 0]

    # ── Course Progress Data ──────────────────────────────────
    try:
        course_progress_data = {
            'completed':   completed_courses,
            'in_progress': in_progress,
            'not_started': max(
                0, total_enrolled - completed_courses - in_progress
            ),
        }
    except Exception:
        course_progress_data = {
            'completed': 0, 'in_progress': 0, 'not_started': 0
        }

    # ── Certificates ──────────────────────────────────────────
    try:
        certificates_earned = Enrollment.query.filter_by(
            user_id=user_id,
            certificate_issued=True
        ).count()
    except Exception:
        certificates_earned = 0

    return render_template(
        'learner/dashboard.html',
        title='My Dashboard',
        total_enrolled=total_enrolled,
        active_courses=active_courses,
        completed_courses=completed_courses,
        in_progress=in_progress,
        overall_progress=overall_progress,
        total_assignments=total_assignments,
        total_submitted=total_submitted,
        pending_grades=pending_grades,
        graded_count=graded_count,
        average_grade=average_grade,
        certificates_earned=certificates_earned,
        recent_enrollments=recent_enrollments,
        upcoming_assignments=upcoming_assignments,
        recent_submissions=recent_submissions,
        weekly_labels=weekly_labels,
        weekly_activity=weekly_activity,
        course_progress_data=course_progress_data,
    )


# =============================================================
# MY COURSES
# =============================================================

@learner_bp.route('/my-courses')
@login_required
def my_courses():
    """Display all enrolled courses."""
    guard = _learner_only()
    if guard:
        return guard

    try:
        enrollments = Enrollment.query.filter_by(
            user_id=current_user.id
        ).order_by(Enrollment.date_enrolled.desc()).all()
    except Exception:
        enrollments = []

    return render_template(
        'learner/courses.html',
        title='My Courses',
        enrollments=enrollments,
        view='my_courses',
        courses=[e.course for e in enrollments if e.course],
        enrolled_course_ids={e.course_id for e in enrollments},
        categories=[],
        search='',
        category='',
        level='',
        total_results=len(enrollments)
    )


# =============================================================
# PROGRESS
# =============================================================

@learner_bp.route('/progress')
@login_required
def progress():
    """Display learner progress across all enrolled courses."""
    guard = _learner_only()
    if guard:
        return guard

    try:
        enrollments = Enrollment.query.filter_by(
            user_id=current_user.id
        ).order_by(Enrollment.date_enrolled.desc()).all()
    except Exception:
        enrollments = []

    return render_template(
        'learner/progress.html',
        title='My Progress',
        enrollments=enrollments
    )


# =============================================================
# ASSIGNMENTS LIST
# =============================================================

@learner_bp.route('/assignments')
@login_required
def assignments():
    """
    Display all assignments for the learner's enrolled courses.

    Groups assignments by:
        - Pending (not submitted or returned)
        - Submitted (awaiting grading)
        - Graded (feedback available)

    Returns:
        Response: Rendered learner/assignments.html template
    """
    guard = _learner_only()
    if guard:
        return guard

    try:
        # Get enrolled course IDs
        enrollments = Enrollment.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()

        enrolled_course_ids = [e.course_id for e in enrollments]

        if enrolled_course_ids:
            all_assignments = Assignment.query.filter(
                Assignment.course_id.in_(enrolled_course_ids),
                Assignment.is_published == True
            ).order_by(
                Assignment.due_date.asc().nullslast(),
                Assignment.date_created.asc()
            ).all()
        else:
            all_assignments = []

        # Build submissions map — most recent per assignment
        submissions_map = {}
        if all_assignments:
            assignment_ids = [a.id for a in all_assignments]
            subs = Submission.query.filter(
                Submission.user_id == current_user.id,
                Submission.assignment_id.in_(assignment_ids)
            ).order_by(
                Submission.date_submitted.desc()
            ).all()

            # Keep most recent submission per assignment
            for sub in subs:
                if sub.assignment_id not in submissions_map:
                    submissions_map[sub.assignment_id] = sub

        # Group assignments
        pending_assignments  = []
        submitted_assignments = []
        graded_assignments   = []

        for assignment in all_assignments:
            sub = submissions_map.get(assignment.id)
            if sub:
                if sub.is_graded:
                    graded_assignments.append(assignment)
                else:
                    submitted_assignments.append(assignment)
            else:
                pending_assignments.append(assignment)

    except Exception:
        all_assignments       = []
        submissions_map       = {}
        pending_assignments   = []
        submitted_assignments = []
        graded_assignments    = []

    return render_template(
        'learner/assignments.html',
        title='My Assignments',
        all_assignments=all_assignments,
        submissions_map=submissions_map,
        pending_assignments=pending_assignments,
        submitted_assignments=submitted_assignments,
        graded_assignments=graded_assignments,
        total_count=len(all_assignments)
    )


# =============================================================
# SUBMIT ASSIGNMENT
# =============================================================

@learner_bp.route(
    '/assignments/<int:assignment_id>/submit',
    methods=['GET', 'POST']
)
@login_required
def submit_assignment(assignment_id):
    """
    Display the assignment submission form and process submissions.

    GET  — Show assignment details and submission form.
    POST — Process the submission (text and/or file upload).

    Validates:
        - Learner must be enrolled in the assignment's course
        - Assignment must be published and accepting submissions
        - Submission limit must not be exceeded
        - File type must be allowed if file is uploaded
        - At least one of text or file must be provided

    Args:
        assignment_id (int): Primary key of the assignment.

    Returns:
        GET  — Rendered learner/submit_assignment.html
        POST — Redirect to assignments list on success
    """
    guard = _learner_only()
    if guard:
        return guard

    # ── Fetch assignment ──────────────────────────────────────
    assignment = Assignment.query.filter_by(
        id=assignment_id,
        is_published=True
    ).first_or_404()

    # ── Verify enrollment ─────────────────────────────────────
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=assignment.course_id,
        is_active=True
    ).first()

    if not enrollment or not enrollment.can_access_content():
        flash(
            'You must be enrolled in this course to submit assignments.',
            'error'
        )
        return redirect(url_for('learner.assignments'))

    # ── Fetch submission history ───────────────────────────────
    submission_history = Submission.query.filter_by(
        user_id=current_user.id,
        assignment_id=assignment_id
    ).order_by(Submission.date_submitted.desc()).all()

    # Most recent submission
    latest_submission = submission_history[0] if submission_history else None

    # ── Check if learner can submit ───────────────────────────
    can_submit = assignment.can_learner_submit(current_user.id)

    # ── GET — Show submission form ────────────────────────────
    if request.method == 'GET':
        return render_template(
            'learner/submit_assignment.html',
            title=f'Submit: {assignment.title}',
            assignment=assignment,
            submission_history=submission_history,
            latest_submission=latest_submission,
            can_submit=can_submit,
            enrollment=enrollment
        )

    # ── POST — Process submission ─────────────────────────────

    # Verify submission is still accepted
    if not can_submit:
        if not assignment.is_accepting_submissions():
            flash(
                'This assignment is no longer accepting submissions.',
                'error'
            )
        else:
            flash(
                f'You have reached the maximum number of submissions '
                f'({assignment.max_submissions}) for this assignment.',
                'error'
            )
        return redirect(url_for(
            'learner.submit_assignment',
            assignment_id=assignment_id
        ))

    # ── Extract form data ─────────────────────────────────────
    text_content  = request.form.get('text_content', '').strip()
    learner_notes = request.form.get('learner_notes', '').strip()
    uploaded_file = request.files.get('submission_file')

    # ── Validate — at least text or file required ─────────────
    has_text = bool(text_content)
    has_file = bool(
        uploaded_file and uploaded_file.filename
    )

    if not has_text and not has_file:
        flash(
            'Please provide a text answer, upload a file, '
            'or both before submitting.',
            'error'
        )
        return render_template(
            'learner/submit_assignment.html',
            title=f'Submit: {assignment.title}',
            assignment=assignment,
            submission_history=submission_history,
            latest_submission=latest_submission,
            can_submit=can_submit,
            enrollment=enrollment
        )

    # ── Validate submission type rules ────────────────────────
    from app.models.assignment import (
        ASSIGNMENT_TYPE_TEXT,
        ASSIGNMENT_TYPE_FILE,
        ASSIGNMENT_TYPE_BOTH
    )

    if assignment.submission_type == ASSIGNMENT_TYPE_TEXT and has_file:
        flash(
            'This assignment only accepts typed text submissions. '
            'Please remove the file and submit your text answer.',
            'error'
        )
        return redirect(url_for(
            'learner.submit_assignment',
            assignment_id=assignment_id
        ))

    if assignment.submission_type == ASSIGNMENT_TYPE_FILE and has_text and not has_file:
        flash(
            'This assignment requires a file upload. '
            'Please upload your work as a file.',
            'error'
        )
        return redirect(url_for(
            'learner.submit_assignment',
            assignment_id=assignment_id
        ))

    # ── Process file upload ───────────────────────────────────
    stored_file_name = None
    original_file_name = None
    file_size_bytes  = None
    mime_type        = None
    file_extension   = None

    if has_file:
        original_file_name = uploaded_file.filename

        # Validate file extension
        if not _allowed_submission_file(original_file_name):
            allowed = ', '.join(
                assignment.get_allowed_file_types_list() or
                ['pdf', 'docx', 'png', 'jpg']
            )
            flash(
                f'File type not allowed. '
                f'Allowed formats: {allowed}',
                'error'
            )
            return redirect(url_for(
                'learner.submit_assignment',
                assignment_id=assignment_id
            ))

        # Validate file size
        max_mb = assignment.max_file_size_mb or 20
        uploaded_file.seek(0, 2)  # Seek to end
        file_bytes = uploaded_file.tell()
        uploaded_file.seek(0)     # Reset

        if file_bytes > max_mb * 1024 * 1024:
            flash(
                f'File is too large. Maximum allowed size is {max_mb} MB.',
                'error'
            )
            return redirect(url_for(
                'learner.submit_assignment',
                assignment_id=assignment_id
            ))

        # Save the file
        stored_file_name, file_size_bytes, mime_type, file_extension = \
            _save_submission_file(uploaded_file, original_file_name)

        if not stored_file_name:
            flash(
                'File upload failed. Please try again.',
                'error'
            )
            return redirect(url_for(
                'learner.submit_assignment',
                assignment_id=assignment_id
            ))

    # ── Determine attempt number ──────────────────────────────
    attempt_number = Submission.get_next_attempt_number(
        assignment_id=assignment_id,
        user_id=current_user.id
    )

    # ── Create submission record ──────────────────────────────
    try:
        new_submission = Submission(
            user_id=current_user.id,
            assignment_id=assignment_id,
            attempt_number=attempt_number,
            text_content=text_content if has_text else None,
            file_name=original_file_name,
            stored_file_name=stored_file_name,
            file_extension=file_extension,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            learner_notes=learner_notes if learner_notes else None,
            is_graded=False,
            date_submitted=datetime.utcnow()
        )

        # Check and set late status
        new_submission.check_and_set_late_status(
            assignment.due_date
        )

        db.session.add(new_submission)
        db.session.commit()

        if new_submission.is_late:
            flash(
                f'Your submission has been received, but it was submitted '
                f'after the deadline. A late penalty may apply.',
                'warning'
            )
        else:
            flash(
                f'✅ Your submission for "{assignment.title}" '
                f'has been received successfully! '
                f'The instructor will review and grade it soon.',
                'success'
            )

    except Exception:
        db.session.rollback()

        # Clean up uploaded file on database error
        if stored_file_name:
            try:
                upload_dir = os.path.join(
                    current_app.config.get(
                        'UPLOAD_FOLDER', 'app/static/uploads'
                    ),
                    'submissions'
                )
                file_path = os.path.join(upload_dir, stored_file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        flash(
            'An error occurred while saving your submission. '
            'Please try again.',
            'error'
        )
        return redirect(url_for(
            'learner.submit_assignment',
            assignment_id=assignment_id
        ))

    return redirect(url_for('learner.assignments'))


# =============================================================
# VIEW SUBMISSION DETAIL
# =============================================================

@learner_bp.route('/submissions/<int:submission_id>')
@login_required
def view_submission(submission_id):
    """
    Display the full detail of a single submission including
    the submitted content, file download link, and grade feedback.

    Args:
        submission_id (int): Primary key of the submission.

    Returns:
        Response: Rendered learner/submit_assignment.html
        403: If the submission belongs to a different user
    """
    guard = _learner_only()
    if guard:
        return guard

    submission = Submission.query.filter_by(
        id=submission_id,
        user_id=current_user.id
    ).first_or_404()

    assignment = submission.assignment
    if not assignment:
        abort(404)

    # Fetch all submissions for this assignment
    submission_history = Submission.query.filter_by(
        user_id=current_user.id,
        assignment_id=assignment.id
    ).order_by(Submission.date_submitted.desc()).all()

    return render_template(
        'learner/submit_assignment.html',
        title=f'Submission: {assignment.title}',
        assignment=assignment,
        submission_history=submission_history,
        latest_submission=submission,
        can_submit=assignment.can_learner_submit(current_user.id),
        viewing_submission=submission,
        enrollment=None
    )


# =============================================================
# PROFILE
# =============================================================

@learner_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Display and handle profile updates."""
    guard = _learner_only()
    if guard:
        return guard

    if request.method == 'POST':
        try:
            current_user.full_name = request.form.get(
                'full_name', current_user.full_name
            ).strip()
            current_user.phone_number = request.form.get(
                'phone_number', ''
            ).strip() or None
            current_user.state = request.form.get(
                'state', ''
            ).strip() or None
            current_user.country = request.form.get(
                'country', 'Nigeria'
            ).strip()
            current_user.bio = request.form.get(
                'bio', ''
            ).strip() or None
            current_user.farming_background = request.form.get(
                'farming_background', ''
            ).strip() or None

            db.session.commit()
            flash('Profile updated successfully.', 'success')

        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')

        return redirect(url_for('learner.profile'))

    return render_template(
        'learner/profile.html',
        title='My Profile'
    )