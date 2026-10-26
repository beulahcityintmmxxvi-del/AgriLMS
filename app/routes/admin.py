# =============================================================
# Agri LMS — Admin Routes (Complete — No Duplicates)
# =============================================================
# File    : app/routes/admin.py
# =============================================================

import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, abort, jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.user import User
from app.models.course import Course
from app.models.module import Module
from app.models.material import Material
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission
from app.models.grade import Grade
from app.models.progress import Progress


# =============================================================
# BLUEPRINT AND DECORATOR
# =============================================================

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Restrict access to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash('Administrator privileges required.', 'error')
            return redirect(url_for('learner.dashboard'))
        return f(*args, **kwargs)
    return decorated


# =============================================================
# FILE UPLOAD HELPERS
# =============================================================

def _save_material_file(file_obj, original_filename):
    """Save an uploaded material file."""
    try:
        safe_name     = secure_filename(original_filename) or 'upload'
        unique_prefix = uuid.uuid4().hex[:8]
        stored_name   = f'{unique_prefix}_{safe_name}'
        extension     = safe_name.rsplit('.', 1)[-1].lower() \
                        if '.' in safe_name else ''
        upload_dir = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
            'materials'
        )
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, stored_name)
        file_obj.save(file_path)
        size_bytes = os.path.getsize(file_path)
        mime_type  = file_obj.content_type or None
        return stored_name, size_bytes, mime_type, extension
    except Exception:
        return None, None, None, None


def _save_thumbnail(file_obj, original_filename):
    """Save a course or video thumbnail."""
    try:
        safe_name     = secure_filename(original_filename) or 'thumb'
        unique_prefix = uuid.uuid4().hex[:8]
        stored_name   = f'{unique_prefix}_{safe_name}'
        upload_dir = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
            'thumbnails'
        )
        os.makedirs(upload_dir, exist_ok=True)
        file_obj.save(os.path.join(upload_dir, stored_name))
        return stored_name
    except Exception:
        return None


def _get_dashboard_data():
    """
    Collect all platform statistics needed for the dashboard
    and reports pages. Returns a dict of all metrics.
    """
    data = {}

    # ── User stats ────────────────────────────────────────────
    try:
        data['total_users']    = User.query.count()
        data['total_learners'] = User.query.filter_by(role='learner').count()
        data['total_admins']   = User.query.filter_by(role='admin').count()
        data['active_users']   = User.query.filter_by(is_active=True).count()
        thirty_ago = datetime.utcnow() - timedelta(days=30)
        seven_ago  = datetime.utcnow() - timedelta(days=7)
        data['new_users_30d']  = User.query.filter(
            User.date_registered >= thirty_ago).count()
        data['new_users_7d']   = User.query.filter(
            User.date_registered >= seven_ago).count()
    except Exception:
        data.update({
            'total_users': 0, 'total_learners': 0, 'total_admins': 0,
            'active_users': 0, 'new_users_30d': 0, 'new_users_7d': 0,
        })

    # ── Course stats ──────────────────────────────────────────
    try:
        data['total_courses']     = Course.query.count()
        data['published_courses'] = Course.query.filter_by(
            is_published=True, is_archived=False).count()
        data['draft_courses']     = Course.query.filter_by(
            is_published=False, is_archived=False).count()
        data['archived_courses']  = Course.query.filter_by(
            is_archived=True).count()
        data['total_modules']     = Module.query.count()
        data['total_materials']   = Material.query.count()
    except Exception:
        data.update({
            'total_courses': 0, 'published_courses': 0, 'draft_courses': 0,
            'archived_courses': 0, 'total_modules': 0, 'total_materials': 0,
        })

    # ── Enrollment stats ──────────────────────────────────────
    try:
        data['total_enrollments']     = Enrollment.query.count()
        data['active_enrollments']    = Enrollment.query.filter_by(
            status='active').count()
        data['completed_enrollments'] = Enrollment.query.filter_by(
            is_completed=True).count()
        data['certificates_issued']   = Enrollment.query.filter_by(
            certificate_issued=True).count()
        te = data['total_enrollments']
        ce = data['completed_enrollments']
        data['completion_rate'] = round((ce / te * 100), 1) if te > 0 else 0.0
    except Exception:
        data.update({
            'total_enrollments': 0, 'active_enrollments': 0,
            'completed_enrollments': 0, 'certificates_issued': 0,
            'completion_rate': 0.0,
        })

    # ── Submission stats ──────────────────────────────────────
    try:
        data['total_submissions']     = Submission.query.count()
        data['pending_grading']       = Submission.query.filter_by(
            is_graded=False).count()
        data['graded_submissions']    = Submission.query.filter_by(
            is_graded=True).count()
        data['total_assignments']     = Assignment.query.count()
        data['published_assignments'] = Assignment.query.filter_by(
            is_published=True).count()
    except Exception:
        data.update({
            'total_submissions': 0, 'pending_grading': 0,
            'graded_submissions': 0, 'total_assignments': 0,
            'published_assignments': 0,
        })

    # ── Top courses ───────────────────────────────────────────
    try:
        data['top_courses'] = db.session.query(
            Course,
            func.count(Enrollment.id).label('enrollment_count')
        ).join(
            Enrollment, Course.id == Enrollment.course_id, isouter=True
        ).filter(Course.is_archived == False).group_by(
            Course.id
        ).order_by(
            func.count(Enrollment.id).desc()
        ).limit(5).all()
    except Exception:
        data['top_courses'] = []

    # ── Monthly enrollment trend ──────────────────────────────
    try:
        monthly_labels      = []
        monthly_enrollments = []
        for i in range(5, -1, -1):
            now         = datetime.utcnow()
            month_date  = now.replace(day=1) - timedelta(days=i * 30)
            month_start = month_date.replace(
                day=1, hour=0, minute=0, second=0)
            if month_start.month < 12:
                month_end = month_start.replace(month=month_start.month + 1)
            else:
                month_end = month_start.replace(
                    year=month_start.year + 1, month=1)
            count = Enrollment.query.filter(
                Enrollment.date_enrolled >= month_start,
                Enrollment.date_enrolled <  month_end
            ).count()
            monthly_labels.append(month_start.strftime('%b %Y'))
            monthly_enrollments.append(count)
        data['monthly_labels']      = monthly_labels
        data['monthly_enrollments'] = monthly_enrollments
    except Exception:
        data['monthly_labels']      = ['Jan','Feb','Mar','Apr','May','Jun']
        data['monthly_enrollments'] = [0, 0, 0, 0, 0, 0]

    # ── Registration trend ────────────────────────────────────
    try:
        reg_labels = []
        reg_counts = []
        for i in range(6, -1, -1):
            day       = datetime.utcnow().date() - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end   = datetime.combine(day, datetime.max.time())
            count = User.query.filter(
                User.date_registered >= day_start,
                User.date_registered <= day_end
            ).count()
            reg_labels.append(day.strftime('%a'))
            reg_counts.append(count)
        data['reg_labels'] = reg_labels
        data['reg_counts'] = reg_counts
    except Exception:
        data['reg_labels'] = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        data['reg_counts'] = [0, 0, 0, 0, 0, 0, 0]

    # ── Submission status breakdown ───────────────────────────
    try:
        data['submission_status'] = {
            'pending':  data.get('pending_grading', 0),
            'graded':   data.get('graded_submissions', 0),
            'returned': Submission.query.filter_by(
                status='returned').count(),
        }
    except Exception:
        data['submission_status'] = {
            'pending': 0, 'graded': 0, 'returned': 0
        }

    # ── Recent users ──────────────────────────────────────────
    try:
        data['recent_users'] = User.query.order_by(
            User.date_registered.desc()).limit(8).all()
    except Exception:
        data['recent_users'] = []

    # ── Pending submissions ───────────────────────────────────
    try:
        data['pending_submissions'] = Submission.query.filter_by(
            is_graded=False
        ).order_by(Submission.date_submitted.desc()).limit(8).all()
    except Exception:
        data['pending_submissions'] = []

    return data


# =============================================================
# DASHBOARD
# =============================================================

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin overview dashboard with platform analytics."""
    data = _get_dashboard_data()
    data['title'] = 'Admin Dashboard'
    return render_template('admin/dashboard.html', **data)


# =============================================================
# COURSE MANAGEMENT
# =============================================================

@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """List all courses."""
    try:
        all_courses = Course.query.order_by(
            Course.date_created.desc()).all()
    except Exception:
        all_courses = []
    return render_template(
        'admin/courses.html',
        title='Manage Courses',
        courses=all_courses
    )


@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_course():
    """Create a new course."""
    if request.method == 'POST':
        title             = request.form.get('title', '').strip()
        short_description = request.form.get('short_description', '').strip()

        if not title or not short_description:
            flash('Title and short description are required.', 'error')
            return render_template(
                'admin/course_form.html',
                title='Create Course',
                form_data=request.form,
                action='create',
                course=None
            )

        try:
            dw = request.form.get('duration_weeks', '').strip()
            ps = request.form.get('passing_score', '50').strip()
            me = request.form.get('max_enrollments', '').strip()

            course = Course(
                created_by=current_user.id,
                title=title,
                short_description=short_description,
                full_description=request.form.get(
                    'full_description', '').strip() or None,
                category=request.form.get('category', '').strip() or None,
                level=request.form.get('level', 'beginner'),
                language=request.form.get('language', 'English'),
                duration_weeks=int(dw) if dw else None,
                tags=request.form.get('tags', '').strip() or None,
                prerequisites=request.form.get(
                    'prerequisites', '').strip() or None,
                learning_outcomes=request.form.get(
                    'learning_outcomes', '').strip() or None,
                passing_score=float(ps) if ps else 50.0,
                max_enrollments=int(me) if me else None,
                is_published=request.form.get('is_published') == 'on',
                is_featured=request.form.get('is_featured') == 'on',
                is_archived=False,
                enrollment_open=request.form.get(
                    'enrollment_open', 'on') == 'on',
                requires_approval=request.form.get(
                    'requires_approval') == 'on',
                certificate_available=request.form.get(
                    'certificate_available', 'on') == 'on',
                date_created=datetime.utcnow(),
            )

            course.slug = course.generate_slug()

            thumbnail = request.files.get('thumbnail')
            if thumbnail and thumbnail.filename:
                stored = _save_thumbnail(thumbnail, thumbnail.filename)
                if stored:
                    course.thumbnail = stored

            if course.is_published:
                course.date_published = datetime.utcnow()

            db.session.add(course)
            db.session.commit()
            flash(f'Course "{course.title}" created!', 'success')
            return redirect(url_for('admin.courses'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/course_form.html',
        title='Create Course',
        form_data={},
        action='create',
        course=None
    )


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit an existing course."""
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        try:
            was_published = course.is_published

            dw = request.form.get('duration_weeks', '').strip()
            ps = request.form.get('passing_score', '50').strip()
            me = request.form.get('max_enrollments', '').strip()

            course.title             = request.form.get('title', '').strip()
            course.short_description = request.form.get(
                'short_description', '').strip()
            course.full_description  = request.form.get(
                'full_description', '').strip() or None
            course.category          = request.form.get(
                'category', '').strip() or None
            course.level             = request.form.get('level', 'beginner')
            course.language          = request.form.get('language', 'English')
            course.tags              = request.form.get(
                'tags', '').strip() or None
            course.prerequisites     = request.form.get(
                'prerequisites', '').strip() or None
            course.learning_outcomes = request.form.get(
                'learning_outcomes', '').strip() or None
            course.is_featured       = request.form.get('is_featured') == 'on'
            course.enrollment_open   = request.form.get(
                'enrollment_open') == 'on'
            course.requires_approval = request.form.get(
                'requires_approval') == 'on'
            course.certificate_available = request.form.get(
                'certificate_available') == 'on'
            course.duration_weeks    = int(dw) if dw else None
            course.passing_score     = float(ps) if ps else 50.0
            course.max_enrollments   = int(me) if me else None

            is_pub = request.form.get('is_published') == 'on'
            course.is_published = is_pub
            if is_pub and not was_published:
                course.date_published = datetime.utcnow()

            thumbnail = request.files.get('thumbnail')
            if thumbnail and thumbnail.filename:
                stored = _save_thumbnail(thumbnail, thumbnail.filename)
                if stored:
                    course.thumbnail = stored

            db.session.commit()
            flash(f'Course "{course.title}" updated!', 'success')
            return redirect(url_for('admin.courses'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/course_form.html',
        title=f'Edit: {course.title}',
        course=course,
        form_data={},
        action='edit'
    )


@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete a course."""
    course = Course.query.get_or_404(course_id)
    title  = course.title
    try:
        db.session.delete(course)
        db.session.commit()
        flash(f'Course "{title}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/toggle-publish', methods=['POST'])
@login_required
@admin_required
def toggle_course_publish(course_id):
    """Toggle course published status."""
    course = Course.query.get_or_404(course_id)
    try:
        course.is_published = not course.is_published
        if course.is_published and not course.date_published:
            course.date_published = datetime.utcnow()
        db.session.commit()
        status = 'published' if course.is_published else 'set to draft'
        flash(f'"{course.title}" {status}.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error updating course.', 'error')
    return redirect(url_for('admin.courses'))


# =============================================================
# MODULE MANAGEMENT
# =============================================================

@admin_bp.route('/modules')
@login_required
@admin_required
def modules():
    """List modules filtered by course."""
    course_id = request.args.get('course_id', type=int)
    try:
        all_courses = Course.query.order_by(Course.title).all()
        if course_id:
            all_modules     = Module.query.filter_by(
                course_id=course_id
            ).order_by(Module.order_number).all()
            selected_course = Course.query.get(course_id)
        else:
            all_modules     = Module.query.order_by(
                Module.course_id, Module.order_number).all()
            selected_course = None
    except Exception:
        all_modules = []
        all_courses = []
        selected_course = None

    return render_template(
        'admin/modules.html',
        title='Manage Modules',
        modules=all_modules,
        courses=all_courses,
        selected_course=selected_course,
        course_id=course_id
    )


@admin_bp.route('/modules/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_module():
    """Create a new module."""
    course_id = request.args.get('course_id', type=int)
    courses   = Course.query.order_by(Course.title).all()

    if request.method == 'POST':
        try:
            cid    = int(request.form.get('course_id', 0))
            course = Course.query.get(cid)
            if not course:
                flash('Please select a valid course.', 'error')
                return render_template(
                    'admin/module_form.html',
                    title='Create Module',
                    courses=courses,
                    form_data=request.form,
                    action='create',
                    module=None,
                    selected_course_id=course_id
                )

            last = Module.query.filter_by(course_id=cid).order_by(
                Module.order_number.desc()).first()
            next_order = (last.order_number + 1) if last else 1
            manual_on  = request.form.get('order_number', '').strip()
            order_number = int(manual_on) if manual_on else next_order

            is_last = request.form.get('is_last_module') == 'on'
            if is_last:
                Module.query.filter_by(
                    course_id=cid, is_last_module=True
                ).update({'is_last_module': False})

            dm  = request.form.get('duration_minutes', '').strip()
            mod = Module(
                course_id=cid,
                title=request.form.get('title', '').strip(),
                description=request.form.get(
                    'description', '').strip() or None,
                learning_objectives=request.form.get(
                    'learning_objectives', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
                order_number=order_number,
                is_last_module=is_last,
                is_published=request.form.get('is_published') == 'on',
                is_free_preview=request.form.get('is_free_preview') == 'on',
                duration_minutes=int(dm) if dm else None,
                date_created=datetime.utcnow()
            )

            db.session.add(mod)
            course.total_modules = Module.query.filter_by(
                course_id=cid).count() + 1
            db.session.commit()
            flash(f'Module "{mod.title}" created!', 'success')
            return redirect(url_for('admin.modules', course_id=cid))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/module_form.html',
        title='Create Module',
        courses=courses,
        selected_course_id=course_id,
        form_data={},
        action='create',
        module=None
    )


@admin_bp.route('/modules/<int:module_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_module(module_id):
    """Edit an existing module."""
    module  = Module.query.get_or_404(module_id)
    courses = Course.query.order_by(Course.title).all()

    if request.method == 'POST':
        try:
            is_last = request.form.get('is_last_module') == 'on'
            if is_last and not module.is_last_module:
                Module.query.filter_by(
                    course_id=module.course_id, is_last_module=True
                ).update({'is_last_module': False})

            dm = request.form.get('duration_minutes', '').strip()
            on = request.form.get('order_number', '').strip()

            module.title               = request.form.get('title', '').strip()
            module.description         = request.form.get(
                'description', '').strip() or None
            module.learning_objectives = request.form.get(
                'learning_objectives', '').strip() or None
            module.notes               = request.form.get(
                'notes', '').strip() or None
            module.order_number        = int(on) if on else module.order_number
            module.is_last_module      = is_last
            module.is_published        = request.form.get(
                'is_published') == 'on'
            module.is_free_preview     = request.form.get(
                'is_free_preview') == 'on'
            module.duration_minutes    = int(dm) if dm else None

            db.session.commit()
            flash(f'Module "{module.title}" updated!', 'success')
            return redirect(
                url_for('admin.modules', course_id=module.course_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/module_form.html',
        title=f'Edit: {module.title}',
        module=module,
        courses=courses,
        selected_course_id=module.course_id,
        form_data={},
        action='edit'
    )


@admin_bp.route('/modules/<int:module_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_module(module_id):
    """Delete a module."""
    module    = Module.query.get_or_404(module_id)
    course_id = module.course_id
    title     = module.title
    try:
        db.session.delete(module)
        db.session.commit()
        flash(f'Module "{title}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('admin.modules', course_id=course_id))


# =============================================================
# MATERIAL MANAGEMENT
# =============================================================

@admin_bp.route('/materials')
@login_required
@admin_required
def materials():
    """List all materials."""
    module_id = request.args.get('module_id', type=int)
    course_id = request.args.get('course_id', type=int)

    try:
        query = Material.query
        if module_id:
            query = query.filter_by(module_id=module_id)
        elif course_id:
            query = query.join(Module).filter(Module.course_id == course_id)

        all_materials = query.order_by(
            Material.date_uploaded.desc()).all()
        courses = Course.query.order_by(Course.title).all()
        mods    = Module.query.order_by(
            Module.course_id, Module.order_number).all()

    except Exception:
        all_materials = []
        courses = []
        mods    = []

    return render_template(
        'admin/materials.html',
        title='Learning Materials',
        materials=all_materials,
        courses=courses,
        modules=mods,
        selected_module_id=module_id,
        selected_course_id=course_id
    )


@admin_bp.route('/materials/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_material():
    """Upload a new material."""
    mods      = Module.query.join(Course).order_by(
        Course.title, Module.order_number).all()
    courses   = Course.query.order_by(Course.title).all()
    module_id = request.args.get('module_id', type=int)

    if request.method == 'POST':
        try:
            mid = int(request.form.get('module_id', 0))
            mod = Module.query.get(mid)
            if not mod:
                flash('Please select a valid module.', 'error')
                return redirect(request.url)

            is_external = request.form.get('is_external') == 'on'
            ext_url     = request.form.get('external_url', '').strip()
            mat_title   = request.form.get('title', '').strip()
            allow_dl    = request.form.get('allow_download', 'on') == 'on'
            is_pub      = request.form.get('is_published') == 'on'
            on          = request.form.get('order_number', '').strip()
            vds         = request.form.get(
                'video_duration_seconds', '').strip()

            last_mat = Material.query.filter_by(
                module_id=mid
            ).order_by(Material.order_number.desc()).first()
            next_order   = (last_mat.order_number + 1) if last_mat else 1
            order_number = int(on) if on else next_order

            stored_file_name = None
            file_name        = None
            file_size_bytes  = None
            mime_type        = None
            file_extension   = None
            material_type    = request.form.get('material_type', 'other')

            uploaded = request.files.get('material_file')
            if uploaded and uploaded.filename and not is_external:
                stored_file_name, file_size_bytes, mime_type, file_extension = \
                    _save_material_file(uploaded, uploaded.filename)
                file_name = uploaded.filename
                if not stored_file_name:
                    flash('File upload failed.', 'error')
                    return redirect(request.url)
                if file_extension:
                    material_type = Material.detect_type_from_extension(
                        file_extension)
            elif is_external and ext_url:
                file_name = mat_title or ext_url

            if not file_name and not ext_url:
                flash('Upload a file or provide an external URL.', 'error')
                return redirect(request.url)

            material = Material(
                module_id=mid,
                title=mat_title or file_name,
                description=request.form.get(
                    'description', '').strip() or None,
                material_type=material_type,
                file_name=file_name,
                stored_file_name=stored_file_name or '',
                file_extension=file_extension,
                file_size_bytes=file_size_bytes,
                mime_type=mime_type,
                external_url=ext_url or None,
                is_external=is_external,
                order_number=order_number,
                allow_download=allow_dl,
                is_published=is_pub,
                video_duration_seconds=int(vds) if vds else None,
                date_uploaded=datetime.utcnow()
            )

            vthumb = request.files.get('video_thumbnail')
            if vthumb and vthumb.filename:
                ts = _save_thumbnail(vthumb, vthumb.filename)
                if ts:
                    material.video_thumbnail = ts

            db.session.add(material)
            db.session.commit()
            flash(f'Material "{material.title}" uploaded!', 'success')
            return redirect(url_for('admin.materials', module_id=mid))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/material_form.html',
        title='Upload Material',
        modules=mods,
        courses=courses,
        selected_module_id=module_id,
        form_data={},
        action='upload',
        material=None
    )


@admin_bp.route('/materials/<int:material_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_material(material_id):
    """Edit a material's metadata."""
    material = Material.query.get_or_404(material_id)
    mods     = Module.query.join(Course).order_by(
        Course.title, Module.order_number).all()
    courses  = Course.query.order_by(Course.title).all()

    if request.method == 'POST':
        try:
            material.title       = request.form.get('title', '').strip()
            material.description = request.form.get(
                'description', '').strip() or None
            material.order_number = int(
                request.form.get('order_number') or material.order_number)
            material.allow_download = request.form.get(
                'allow_download') == 'on'
            material.is_published   = request.form.get(
                'is_published') == 'on'
            vds = request.form.get('video_duration_seconds', '').strip()
            material.video_duration_seconds = int(vds) if vds else None
            ext_url = request.form.get('external_url', '').strip()
            if ext_url:
                material.external_url = ext_url
                material.is_external  = True
            db.session.commit()
            flash(f'Material "{material.title}" updated!', 'success')
            return redirect(
                url_for('admin.materials', module_id=material.module_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/material_form.html',
        title=f'Edit: {material.title}',
        material=material,
        modules=mods,
        courses=courses,
        selected_module_id=material.module_id,
        form_data={},
        action='edit'
    )


@admin_bp.route('/materials/<int:material_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_material(material_id):
    """Delete a material and its file."""
    material  = Material.query.get_or_404(material_id)
    module_id = material.module_id
    title     = material.title
    try:
        if material.stored_file_name and not material.is_external:
            fp = os.path.join(
                current_app.config.get(
                    'UPLOAD_FOLDER', 'app/static/uploads'),
                'materials', material.stored_file_name)
            if os.path.exists(fp):
                os.remove(fp)
        db.session.delete(material)
        db.session.commit()
        flash(f'Material "{title}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('admin.materials', module_id=module_id))


# =============================================================
# ASSIGNMENT MANAGEMENT
# =============================================================

@admin_bp.route('/assignments')
@login_required
@admin_required
def assignments():
    """List all assignments."""
    course_id = request.args.get('course_id', type=int)
    try:
        courses = Course.query.order_by(Course.title).all()
        query   = Assignment.query
        if course_id:
            query = query.filter_by(course_id=course_id)
        all_assignments = query.order_by(
            Assignment.date_created.desc()).all()
    except Exception:
        all_assignments = []
        courses = []

    return render_template(
        'admin/assignments.html',
        title='Manage Assignments',
        assignments=all_assignments,
        courses=courses,
        selected_course_id=course_id
    )


@admin_bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_assignment():
    """Create a new assignment."""
    courses   = Course.query.filter_by(
        is_published=True).order_by(Course.title).all()
    mods      = Module.query.order_by(
        Module.course_id, Module.order_number).all()
    course_id = request.args.get('course_id', type=int)

    if request.method == 'POST':
        try:
            cid = int(request.form.get('course_id', 0))
            if not Course.query.get(cid):
                flash('Please select a valid course.', 'error')
                return redirect(request.url)

            mid_raw  = request.form.get('module_id', '').strip()
            mid      = int(mid_raw) if mid_raw else None
            due_raw  = request.form.get('due_date', '').strip()
            due_date = datetime.strptime(
                due_raw, '%Y-%m-%dT%H:%M') if due_raw else None
            is_pub   = request.form.get('is_published') == 'on'

            asgn = Assignment(
                course_id=cid,
                module_id=mid,
                created_by=current_user.id,
                title=request.form.get('title', '').strip(),
                description=request.form.get('description', '').strip(),
                instructions=request.form.get(
                    'instructions', '').strip() or None,
                submission_type=request.form.get('submission_type', 'both'),
                total_marks=float(
                    request.form.get('total_marks') or 100),
                pass_mark=float(
                    request.form.get('pass_mark') or 50),
                weight=float(
                    request.form.get('weight') or 1.0),
                due_date=due_date,
                late_submission_allowed=request.form.get(
                    'late_submission_allowed', 'on') == 'on',
                late_penalty_percent=float(
                    request.form.get('late_penalty_percent') or 0),
                allowed_file_types=request.form.get(
                    'allowed_file_types',
                    'pdf,docx,doc,pptx,xlsx,png,jpg,jpeg,zip'
                ).strip(),
                max_file_size_mb=int(
                    request.form.get('max_file_size_mb') or 20),
                max_submissions=int(
                    request.form.get('max_submissions') or 1),
                reference_links=request.form.get(
                    'reference_links', '').strip() or None,
                is_published=is_pub,
                status='published' if is_pub else 'draft',
                order_number=int(
                    request.form.get('order_number') or 1),
                date_created=datetime.utcnow()
            )

            attachment = request.files.get('attachment')
            if attachment and attachment.filename:
                stored, _, _, _ = _save_material_file(
                    attachment, attachment.filename)
                if stored:
                    asgn.attachment_stored_filename = stored
                    asgn.attachment_filename = attachment.filename

            if is_pub:
                asgn.date_published = datetime.utcnow()

            db.session.add(asgn)
            db.session.commit()
            flash(f'Assignment "{asgn.title}" created!', 'success')
            return redirect(url_for('admin.assignments', course_id=cid))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/assignment_form.html',
        title='Create Assignment',
        courses=courses,
        modules=mods,
        selected_course_id=course_id,
        form_data={},
        action='create',
        assignment=None
    )


@admin_bp.route('/assignments/<int:assignment_id>/edit',
                methods=['GET', 'POST'])
@login_required
@admin_required
def edit_assignment(assignment_id):
    """Edit an assignment."""
    assignment = Assignment.query.get_or_404(assignment_id)
    courses    = Course.query.order_by(Course.title).all()
    mods       = Module.query.filter_by(
        course_id=assignment.course_id
    ).order_by(Module.order_number).all()

    if request.method == 'POST':
        try:
            due_raw  = request.form.get('due_date', '').strip()
            due_date = datetime.strptime(
                due_raw, '%Y-%m-%dT%H:%M') if due_raw else None
            was_pub  = assignment.is_published
            is_pub   = request.form.get('is_published') == 'on'

            assignment.title           = request.form.get('title', '').strip()
            assignment.description     = request.form.get(
                'description', '').strip()
            assignment.instructions    = request.form.get(
                'instructions', '').strip() or None
            assignment.submission_type = request.form.get(
                'submission_type', 'both')
            assignment.total_marks     = float(
                request.form.get('total_marks') or 100)
            assignment.pass_mark       = float(
                request.form.get('pass_mark') or 50)
            assignment.weight          = float(
                request.form.get('weight') or 1.0)
            assignment.due_date        = due_date
            assignment.late_submission_allowed = request.form.get(
                'late_submission_allowed') == 'on'
            assignment.late_penalty_percent = float(
                request.form.get('late_penalty_percent') or 0)
            assignment.allowed_file_types = request.form.get(
                'allowed_file_types', 'pdf,docx,doc,pptx,xlsx,png,jpg'
            ).strip()
            assignment.max_file_size_mb = int(
                request.form.get('max_file_size_mb') or 20)
            assignment.max_submissions  = int(
                request.form.get('max_submissions') or 1)
            assignment.reference_links  = request.form.get(
                'reference_links', '').strip() or None
            assignment.is_published = is_pub
            assignment.status = 'published' if is_pub else 'draft'
            if is_pub and not was_pub:
                assignment.date_published = datetime.utcnow()

            db.session.commit()
            flash(f'Assignment "{assignment.title}" updated!', 'success')
            return redirect(
                url_for('admin.assignments',
                        course_id=assignment.course_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template(
        'admin/assignment_form.html',
        title=f'Edit: {assignment.title}',
        assignment=assignment,
        courses=courses,
        modules=mods,
        selected_course_id=assignment.course_id,
        form_data={},
        action='edit'
    )


@admin_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_assignment(assignment_id):
    """Delete an assignment."""
    assignment = Assignment.query.get_or_404(assignment_id)
    course_id  = assignment.course_id
    title      = assignment.title
    try:
        db.session.delete(assignment)
        db.session.commit()
        flash(f'Assignment "{title}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('admin.assignments', course_id=course_id))


# =============================================================
# SUBMISSION GRADING
# =============================================================

@admin_bp.route('/submissions')
@login_required
@admin_required
def submissions():
    """Submission grading queue."""
    filter_by = request.args.get('filter', 'all')
    page      = request.args.get('page', 1, type=int)
    per_page  = 15

    try:
        query = Submission.query.order_by(
            Submission.date_submitted.desc())
        if filter_by == 'pending':
            query = query.filter_by(is_graded=False)
        elif filter_by == 'graded':
            query = query.filter_by(is_graded=True)

        pagination      = query.paginate(
            page=page, per_page=per_page, error_out=False)
        all_submissions = pagination.items
    except Exception:
        all_submissions = []
        pagination      = None

    return render_template(
        'admin/submissions.html',
        title='Submission Grading Queue',
        submissions=all_submissions,
        pagination=pagination,
        filter_by=filter_by
    )


@admin_bp.route('/submissions/<int:submission_id>/grade',
                methods=['GET', 'POST'])
@login_required
@admin_required
def grade_submission(submission_id):
    """Grade a learner's submission."""
    submission = Submission.query.get_or_404(submission_id)
    assignment = submission.assignment

    if request.method == 'POST':
        try:
            score_awarded  = float(request.form.get('score_awarded', 0))
            feedback       = request.form.get('feedback', '').strip()
            internal_notes = request.form.get('internal_notes', '').strip()
            max_score      = float(assignment.total_marks) \
                if assignment else 100.0
            score_awarded  = min(score_awarded, max_score)
            pass_mark_pct  = float(assignment.pass_mark or 50.0) \
                / max_score * 100 if assignment else 50.0

            existing_grade = Grade.query.filter_by(
                submission_id=submission_id).first()

            if existing_grade:
                existing_grade.revise(
                    reason=request.form.get('revision_reason', ''))
                existing_grade.score_awarded  = score_awarded
                existing_grade.max_score      = max_score
                existing_grade.feedback       = feedback or None
                existing_grade.internal_notes = internal_notes or None
                existing_grade.graded_by      = current_user.id
                existing_grade.compute_and_set_scores(pass_mark_pct)
                grade = existing_grade
            else:
                grade = Grade(
                    submission_id=submission_id,
                    graded_by=current_user.id,
                    score_awarded=score_awarded,
                    max_score=max_score,
                    late_penalty_applied=float(
                        assignment.late_penalty_percent or 0
                    ) if submission.is_late else 0.0,
                    feedback=feedback or None,
                    internal_notes=internal_notes or None,
                    date_graded=datetime.utcnow()
                )
                grade.compute_and_set_scores(pass_mark_pct)
                db.session.add(grade)

            final_pct = float(
                grade.adjusted_score_percent or grade.score_percent)
            submission.mark_graded(score_percent=final_pct)
            db.session.commit()

            _recalculate_enrollment_score(
                submission.user_id, assignment.course_id)

            flash(
                f'Graded! Score: {grade.get_score_display()} '
                f'({grade.get_percent_display()})',
                'success'
            )
            return redirect(url_for('admin.submissions'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error grading: {str(e)}', 'error')

    existing_grade = Grade.query.filter_by(
        submission_id=submission_id).first()

    return render_template(
        'admin/grade_submission.html',
        title=f'Grade: {assignment.title if assignment else "Submission"}',
        submission=submission,
        assignment=assignment,
        existing_grade=existing_grade
    )


def _recalculate_enrollment_score(user_id, course_id):
    """Recalculate a learner's final score after grading."""
    try:
        enrollment = Enrollment.query.filter_by(
            user_id=user_id, course_id=course_id).first()
        if not enrollment:
            return
        assignments = Assignment.query.filter_by(
            course_id=course_id, is_published=True).all()
        if not assignments:
            return
        total_w = total_s = 0.0
        for asgn in assignments:
            sub = Submission.query.filter_by(
                user_id=user_id,
                assignment_id=asgn.id,
                is_graded=True
            ).order_by(Submission.date_submitted.desc()).first()
            if sub and sub.score_percent is not None:
                w = float(asgn.weight or 1.0)
                total_s += float(sub.score_percent) * w
                total_w += w
        if total_w > 0:
            enrollment.final_score = round(total_s / total_w, 2)
            db.session.commit()
    except Exception:
        db.session.rollback()


# =============================================================
# USER MANAGEMENT
# =============================================================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management list."""
    search   = request.args.get('search', '').strip()
    role     = request.args.get('role', '').strip()
    page     = request.args.get('page', 1, type=int)
    per_page = 15

    try:
        query = User.query.order_by(User.date_registered.desc())
        if search:
            query = query.filter(
                db.or_(
                    User.full_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                ))
        if role:
            query = query.filter_by(role=role)
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False)
        all_users  = pagination.items
    except Exception:
        all_users  = []
        pagination = None

    return render_template(
        'admin/users.html',
        title='Manage Users',
        users=all_users,
        pagination=pagination,
        search=search,
        role=role
    )


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Activate or deactivate a user."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.users'))
    try:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User "{user.full_name}" {status}.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error updating user.', 'error')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/make-admin', methods=['POST'])
@login_required
@admin_required
def make_admin(user_id):
    """Promote a user to admin."""
    user = User.query.get_or_404(user_id)
    try:
        user.role = 'admin'
        db.session.commit()
        flash(f'"{user.full_name}" promoted to admin.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error updating role.', 'error')
    return redirect(url_for('admin.users'))


# =============================================================
# REPORTS
# =============================================================

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Platform reports and analytics."""
    data = _get_dashboard_data()
    data['title'] = 'Platform Reports'
    return render_template('admin/reports.html', **data)