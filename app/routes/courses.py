# =============================================================
# Agri LMS — Course Routes
# =============================================================
# File    : app/routes/courses.py
# Purpose : Handles all course-related pages including:
#               - Course catalog with search and filtering
#               - Course detail page
#               - Course enrollment
#               - Course unenrollment
#
# Routes  :
#   GET  /courses/                      — Course catalog
#   GET  /courses/<id>                  — Course detail
#   POST /courses/<id>/enroll           — Enroll in a course
#   POST /courses/<id>/unenroll         — Unenroll from a course
# =============================================================

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    abort,
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models.course import Course
from app.models.module import Module
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.progress import Progress


# =============================================================
# BLUEPRINT
# =============================================================

courses_bp = Blueprint('courses', __name__)


# =============================================================
# COURSE CATALOG
# =============================================================

@courses_bp.route('/')
def catalog():
    """
    Render the public course catalog page.

    Supports filtering by:
        - Search query (title and description)
        - Category
        - Level (beginner, intermediate, advanced)

    Shows only published, non-archived courses.
    Authenticated learners see their enrollment status
    on each course card.

    Returns:
        Response: Rendered learner/courses.html template
    """

    # ── Query Parameters ──────────────────────────────────────
    search   = request.args.get('search',   '').strip()
    category = request.args.get('category', '').strip()
    level    = request.args.get('level',    '').strip()
    view     = request.args.get('view',     'catalog')

    # ── Base Query — published and not archived ───────────────
    try:
        query = Course.query.filter_by(
            is_published=True,
            is_archived=False
        )

        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Course.title.ilike(f'%{search}%'),
                    Course.short_description.ilike(f'%{search}%'),
                    Course.tags.ilike(f'%{search}%'),
                    Course.category.ilike(f'%{search}%')
                )
            )

        # Apply category filter
        if category:
            query = query.filter(
                Course.category.ilike(f'%{category}%')
            )

        # Apply level filter
        if level:
            query = query.filter_by(level=level)

        # Order by featured first, then newest
        courses = query.order_by(
            Course.is_featured.desc(),
            Course.date_created.desc()
        ).all()

    except Exception:
        courses = []

    # ── Build enrolled course ID set for logged-in learners ───
    enrolled_course_ids = set()
    if current_user.is_authenticated and current_user.is_learner():
        try:
            enrollments = Enrollment.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).all()
            enrolled_course_ids = {e.course_id for e in enrollments}
        except Exception:
            enrolled_course_ids = set()

    # ── Available Categories for Filter Dropdown ──────────────
    categories = [
        'Crop Production',
        'Livestock Management',
        'Soil Science',
        'Irrigation',
        'Pest & Disease Control',
        'Organic Farming',
        'Agroforestry',
        'Indigenous Practices',
        'Poultry Farming',
        'Fishery & Aquaculture',
        'Farm Business Management',
        'Agricultural Technology',
    ]

    return render_template(
        'learner/courses.html',
        title='Course Catalog',
        courses=courses,
        enrolled_course_ids=enrolled_course_ids,
        categories=categories,
        search=search,
        category=category,
        level=level,
        view=view,
        total_results=len(courses)
    )


# =============================================================
# COURSE DETAIL
# =============================================================

@courses_bp.route('/<int:course_id>')
def course_detail(course_id):
    """
    Render the course detail page.

    Shows full course information including:
        - Course description and learning outcomes
        - Module list with material counts
        - Assignment list
        - Enrollment status for authenticated learners
        - Enrollment button or Continue Learning button

    Publicly accessible — non-enrolled visitors can view
    the course details but cannot access module content.

    Args:
        course_id (int): Primary key of the course.

    Returns:
        Response: Rendered learner/course_detail.html template
        404: If course does not exist or is not published
    """

    # ── Fetch course ──────────────────────────────────────────
    course = Course.query.filter_by(
        id=course_id,
        is_archived=False
    ).first()

    # Return 404 if course not found
    if not course:
        abort(404)

    # Non-admin users cannot see unpublished courses
    if not course.is_published:
        if not (current_user.is_authenticated and current_user.is_admin()):
            abort(404)

    # ── Fetch published modules in order ──────────────────────
    try:
        if current_user.is_authenticated and current_user.is_admin():
            # Admins see all modules including drafts
            modules = Module.query.filter_by(
                course_id=course_id
            ).order_by(Module.order_number).all()
        else:
            # Learners and visitors see only published modules
            modules = Module.query.filter_by(
                course_id=course_id,
                is_published=True
            ).order_by(Module.order_number).all()

    except Exception:
        modules = []

    # ── Fetch published assignments ───────────────────────────
    try:
        assignments = Assignment.query.filter_by(
            course_id=course_id,
            is_published=True
        ).order_by(
            Assignment.order_number.asc().nullslast(),
            Assignment.date_created.asc()
        ).all()

    except Exception:
        assignments = []

    # ── Enrollment status for authenticated learner ───────────
    enrollment        = None
    is_enrolled       = False
    completed_modules = set()

    if current_user.is_authenticated and current_user.is_learner():
        try:
            enrollment = Enrollment.query.filter_by(
                user_id=current_user.id,
                course_id=course_id
            ).first()

            is_enrolled = enrollment is not None and enrollment.can_access_content()

            # Get set of completed module IDs for this learner
            if is_enrolled:
                progress_records = Progress.query.filter_by(
                    user_id=current_user.id,
                    course_id=course_id,
                    is_completed=True
                ).all()
                completed_modules = {p.module_id for p in progress_records}

        except Exception:
            enrollment        = None
            is_enrolled       = False
            completed_modules = set()

    # ── Find the last accessed module for resume ──────────────
    resume_module_id = None
    if enrollment and enrollment.last_accessed_module_id:
        resume_module_id = enrollment.last_accessed_module_id

    # ── Course statistics for display ─────────────────────────
    try:
        total_enrolled = course.get_total_enrollments()
        completion_rate = course.get_completion_rate()
    except Exception:
        total_enrolled  = 0
        completion_rate = 0.0

    return render_template(
        'learner/course_detail.html',
        title=course.title,
        course=course,
        modules=modules,
        assignments=assignments,
        enrollment=enrollment,
        is_enrolled=is_enrolled,
        completed_modules=completed_modules,
        resume_module_id=resume_module_id,
        total_enrolled=total_enrolled,
        completion_rate=completion_rate
    )


# =============================================================
# ENROLL IN COURSE
# =============================================================

@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    """
    Process a learner's enrollment request for a course.

    Validation:
        - User must be a learner (not admin)
        - Course must exist and be published
        - Course must be accepting enrollments
        - Learner must not already be enrolled
        - If requires_approval: status set to 'pending'
        - Otherwise: status set to 'active'

    Args:
        course_id (int): Primary key of the course to enroll in.

    Returns:
        Response: Redirect to course detail page.
    """

    # Admins cannot enroll as learners
    if current_user.is_admin():
        flash('Administrators cannot enroll in courses.', 'warning')
        return redirect(url_for('courses.course_detail',
                                course_id=course_id))

    # Fetch the course
    course = Course.query.filter_by(
        id=course_id,
        is_published=True,
        is_archived=False
    ).first()

    if not course:
        flash('Course not found or no longer available.', 'error')
        return redirect(url_for('courses.catalog'))

    # Check enrollment is available
    if not course.is_enrollment_available():
        flash(
            'Enrollment for this course is currently closed.',
            'warning'
        )
        return redirect(url_for('courses.course_detail',
                                course_id=course_id))

    # Check for existing enrollment
    existing = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()

    if existing:
        if existing.status == 'dropped':
            # Re-activate a dropped enrollment
            existing.activate()
            db.session.commit()
            flash(
                f'Welcome back! You have re-enrolled in '
                f'"{course.title}".',
                'success'
            )
        else:
            flash(
                'You are already enrolled in this course.',
                'info'
            )
        return redirect(url_for('courses.course_detail',
                                course_id=course_id))

    # Create new enrollment
    try:
        status = 'pending' if course.requires_approval else 'active'

        new_enrollment = Enrollment(
            user_id=current_user.id,
            course_id=course_id,
            status=status,
            is_active=(status == 'active'),
            progress_percent=0.00,
            modules_completed=0,
            is_completed=False,
            certificate_issued=False,
            date_enrolled=datetime.utcnow()
        )

        if status == 'active':
            new_enrollment.date_approved = datetime.utcnow()

        db.session.add(new_enrollment)
        db.session.commit()

        if status == 'pending':
            flash(
                f'Your enrollment request for "{course.title}" '
                f'has been submitted and is awaiting admin approval.',
                'info'
            )
        else:
            flash(
                f'You have successfully enrolled in "{course.title}". '
                f'Start learning by selecting a module below!',
                'success'
            )

    except Exception:
        db.session.rollback()
        flash(
            'An error occurred during enrollment. Please try again.',
            'error'
        )

    return redirect(url_for('courses.course_detail',
                            course_id=course_id))


# =============================================================
# UNENROLL FROM COURSE
# =============================================================

@courses_bp.route('/<int:course_id>/unenroll', methods=['POST'])
@login_required
def unenroll(course_id):
    """
    Process a learner's unenrollment request.

    Marks the enrollment as 'dropped' rather than deleting it
    to preserve progress and submission history.

    Args:
        course_id (int): Primary key of the course to leave.

    Returns:
        Response: Redirect to course catalog.
    """

    if current_user.is_admin():
        flash('Administrators are not enrolled in courses.', 'warning')
        return redirect(url_for('courses.catalog'))

    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()

    if not enrollment:
        flash('You are not enrolled in this course.', 'warning')
        return redirect(url_for('courses.catalog'))

    try:
        enrollment.drop(reason='Learner requested unenrollment.')
        db.session.commit()

        course = Course.query.get(course_id)
        course_title = course.title if course else 'the course'

        flash(
            f'You have unenrolled from "{course_title}". '
            f'Your progress has been saved.',
            'info'
        )

    except Exception:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')

    return redirect(url_for('courses.catalog'))

# =============================================================
# MODULE VIEW
# =============================================================

@courses_bp.route('/<int:course_id>/modules/<int:module_id>')
@login_required
def module_view(course_id, module_id):
    """
    Display a module's learning content.

    Shows all published materials for the module including:
        - Videos  — streamed via HTML5 player with optional download
        - PDFs    — rendered in iframe browser viewer with download option
        - Documents/Images/Other — download-only with info card

    Tracks learner access by creating or updating a Progress
    record when the learner opens the module page.

    Access control:
        - Learner must be enrolled and have active access
        - Admins can view any module regardless of enrollment
        - Free preview modules accessible without enrollment

    Args:
        course_id  (int): Primary key of the parent course.
        module_id  (int): Primary key of the module to view.

    Returns:
        Response: Rendered learner/module_view.html template
        403: If learner is not enrolled and module is not free preview
        404: If course or module does not exist
    """

    # ── Fetch course and module ───────────────────────────────
    course = Course.query.filter_by(
        id=course_id,
        is_archived=False
    ).first_or_404()

    module = Module.query.filter_by(
        id=module_id,
        course_id=course_id,
        is_published=True
    ).first_or_404()

    # ── Access control ────────────────────────────────────────
    if not current_user.is_admin():

        enrollment = Enrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()

        # Allow access if enrolled and active, or if free preview
        has_access = (
            module.is_free_preview or
            (enrollment and enrollment.can_access_content())
        )

        if not has_access:
            flash(
                'You must enroll in this course to access module content.',
                'warning'
            )
            return redirect(url_for(
                'courses.course_detail',
                course_id=course_id
            ))
    else:
        enrollment = None

    # ── Fetch published materials in order ────────────────────
    from app.models.material import Material

    materials = Material.query.filter_by(
        module_id=module_id,
        is_published=True
    ).order_by(Material.order_number).all()

    # ── Determine primary display material ────────────────────
    # Priority: first video > first PDF > first of any type
    primary_material = None

    videos    = [m for m in materials if m.is_video()]
    pdfs      = [m for m in materials if m.is_pdf()]
    documents = [m for m in materials if m.is_document()]
    images    = [m for m in materials if m.is_image()]
    others    = [m for m in materials
                 if not m.is_video() and not m.is_pdf()
                 and not m.is_document() and not m.is_image()]

    # Select which material to show first
    selected_material_id = request.args.get(
        'material', type=int
    )

    if selected_material_id:
        primary_material = next(
            (m for m in materials if m.id == selected_material_id),
            None
        )

    if not primary_material:
        if videos:
            primary_material = videos[0]
        elif pdfs:
            primary_material = pdfs[0]
        elif materials:
            primary_material = materials[0]

    # ── Get or create progress record ─────────────────────────
    progress = None
    if current_user.is_learner():
        try:
            progress, created = Progress.get_or_create(
                user_id=current_user.id,
                module_id=module_id,
                course_id=course_id
            )

            if not created:
                progress.record_access()

            db.session.commit()

            # Update last accessed module on enrollment
            if enrollment:
                enrollment.last_accessed_module_id = module_id
                db.session.commit()

        except Exception:
            db.session.rollback()
            progress = None

    # ── Get completed module IDs for this learner ─────────────
    completed_modules = set()
    if current_user.is_learner():
        try:
            completed_records = Progress.query.filter_by(
                user_id=current_user.id,
                course_id=course_id,
                is_completed=True
            ).all()
            completed_modules = {p.module_id for p in completed_records}
        except Exception:
            completed_modules = set()

    # ── Get all published modules for navigation ──────────────
    all_modules = Module.query.filter_by(
        course_id=course_id,
        is_published=True
    ).order_by(Module.order_number).all()

    # ── Previous and next module ──────────────────────────────
    prev_module = module.get_previous_module()
    next_module = module.get_next_module()

    return render_template(
        'learner/module_view.html',
        title=module.get_module_label(),
        course=course,
        module=module,
        materials=materials,
        videos=videos,
        pdfs=pdfs,
        documents=documents,
        images=images,
        others=others,
        primary_material=primary_material,
        progress=progress,
        completed_modules=completed_modules,
        all_modules=all_modules,
        prev_module=prev_module,
        next_module=next_module,
        enrollment=enrollment
    )


# =============================================================
# MARK MODULE COMPLETE
# =============================================================

@courses_bp.route(
    '/<int:course_id>/modules/<int:module_id>/complete',
    methods=['POST']
)
@login_required
def mark_module_complete(course_id, module_id):
    """
    Mark a module as completed by the learner.

    On completion:
        1. Progress record is updated — is_completed=True
        2. Enrollment.modules_completed is incremented
        3. Enrollment.progress_percent is recalculated
        4. If module.is_last_module is True:
               Enrollment is marked as completed
               Certificate is issued if eligible

    Args:
        course_id  (int): Primary key of the parent course.
        module_id  (int): Primary key of the module to complete.

    Returns:
        Response: Redirect to next module or course detail.
    """

    if current_user.is_admin():
        flash('Admins do not track module progress.', 'info')
        return redirect(url_for(
            'courses.module_view',
            course_id=course_id,
            module_id=module_id
        ))

    # ── Validate enrollment ───────────────────────────────────
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()

    if not enrollment or not enrollment.can_access_content():
        flash('You must be enrolled to track progress.', 'warning')
        return redirect(url_for(
            'courses.course_detail',
            course_id=course_id
        ))

    # ── Validate module exists ────────────────────────────────
    module = Module.query.filter_by(
        id=module_id,
        course_id=course_id,
        is_published=True
    ).first_or_404()

    # ── Get or create progress record ─────────────────────────
    try:
        progress, _ = Progress.get_or_create(
            user_id=current_user.id,
            module_id=module_id,
            course_id=course_id
        )

        # Only increment if not already completed
        if not progress.is_completed:
            progress.mark_complete()

            # Increment enrollment module counter
            enrollment.increment_modules_completed()

            # Recalculate overall progress percentage
            total_published = Module.query.filter_by(
                course_id=course_id,
                is_published=True
            ).count()

            enrollment.update_progress(total_published)

            # Check if this was the last module
            if module.is_last_module:
                # Calculate final score from graded submissions
                final_score = _calculate_final_score(
                    user_id=current_user.id,
                    course_id=course_id
                )

                passing_score = float(
                    enrollment.course.passing_score or 50.0
                ) if enrollment.course else 50.0

                enrollment.mark_completed(
                    final_score=final_score,
                    passing_score=passing_score
                )

                # Issue certificate if eligible
                if (enrollment.is_passed and
                        enrollment.course and
                        enrollment.course.certificate_available):
                    enrollment.issue_certificate()

                db.session.commit()

                if enrollment.is_passed:
                    flash(
                        '🎉 Congratulations! You have completed this course '
                        'and passed with a score of '
                        f'{final_score:.1f}%! '
                        + ('Your certificate is ready.' if enrollment.certificate_issued else ''),
                        'success'
                    )
                else:
                    flash(
                        'You have completed all modules in this course. '
                        'Review your assignment submissions to improve your score.',
                        'info'
                    )

                return redirect(url_for(
                    'courses.course_detail',
                    course_id=course_id
                ))

            db.session.commit()

            flash(
                f'✅ "{module.title}" marked as complete! '
                f'Keep going — you\'re making great progress.',
                'success'
            )

        else:
            flash(
                'You have already completed this module.',
                'info'
            )

    except Exception as e:
        db.session.rollback()
        flash(
            'An error occurred while saving your progress. '
            'Please try again.',
            'error'
        )

    # ── Redirect to next module or course detail ──────────────
    next_module = module.get_next_module()

    if next_module:
        return redirect(url_for(
            'courses.module_view',
            course_id=course_id,
            module_id=next_module.id
        ))

    return redirect(url_for(
        'courses.course_detail',
        course_id=course_id
    ))


# =============================================================
# SAVE LEARNER NOTES
# =============================================================

@courses_bp.route(
    '/<int:course_id>/modules/<int:module_id>/notes',
    methods=['POST']
)
@login_required
def save_module_notes(course_id, module_id):
    """
    Save the learner's personal study notes for a module.

    Notes are private to each learner and not visible to admins.

    Args:
        course_id  (int): Primary key of the parent course.
        module_id  (int): Primary key of the module.

    Returns:
        JSON: Success or error message.
    """
    from flask import jsonify

    if current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admins do not have notes.'})

    notes_content = request.form.get('notes', '').strip()

    try:
        progress, _ = Progress.get_or_create(
            user_id=current_user.id,
            module_id=module_id,
            course_id=course_id
        )
        progress.save_notes(notes_content)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Notes saved successfully.'
        })

    except Exception:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to save notes. Please try again.'
        })


# =============================================================
# UPDATE TIME SPENT
# =============================================================

@courses_bp.route(
    '/<int:course_id>/modules/<int:module_id>/time',
    methods=['POST']
)
@login_required
def update_time_spent(course_id, module_id):
    """
    Update the cumulative time a learner has spent on a module.

    Called via JavaScript when the learner leaves the module page.
    Receives minutes spent in the current session.

    Args:
        course_id  (int): Primary key of the parent course.
        module_id  (int): Primary key of the module.

    Returns:
        JSON: Success or error message.
    """
    from flask import jsonify

    if current_user.is_admin():
        return jsonify({'success': True})

    try:
        minutes = int(request.form.get('minutes', 0))
    except (ValueError, TypeError):
        minutes = 0

    if minutes > 0:
        try:
            progress, _ = Progress.get_or_create(
                user_id=current_user.id,
                module_id=module_id,
                course_id=course_id
            )
            progress.add_time_spent(minutes)
            db.session.commit()

        except Exception:
            db.session.rollback()

    from flask import jsonify
    return jsonify({'success': True})


# =============================================================
# PRIVATE HELPERS
# =============================================================

def _calculate_final_score(user_id, course_id):
    """
    Calculate the weighted average assignment score for
    a learner across all graded assignments in a course.

    Args:
        user_id   (int): The learner's primary key.
        course_id (int): The course's primary key.

    Returns:
        float: Weighted average score as a percentage.
                Returns None if no graded submissions exist.
    """
    from app.models.assignment import Assignment
    from app.models.submission import Submission

    try:
        # Get all published assignments for the course
        assignments = Assignment.query.filter_by(
            course_id=course_id,
            is_published=True
        ).all()

        if not assignments:
            return None

        total_weighted_score = 0.0
        total_weight         = 0.0

        for assignment in assignments:
            # Get most recent graded submission for this assignment
            submission = Submission.query.filter_by(
                user_id=user_id,
                assignment_id=assignment.id,
                is_graded=True
            ).order_by(
                Submission.date_submitted.desc()
            ).first()

            if submission and submission.score_percent is not None:
                weight = float(assignment.weight or 1.0)
                total_weighted_score += (
                    float(submission.score_percent) * weight
                )
                total_weight += weight

        if total_weight > 0:
            return round(total_weighted_score / total_weight, 2)

        return None

    except Exception:
        return None