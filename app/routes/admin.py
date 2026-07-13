from flask import Blueprint, render_template
from flask_login import current_user
from app.utils.decorators import admin_required
from app.extensions import db
from sqlalchemy import func

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/dashboard')
@admin_required
def dashboard():
    from app.models.identity import UserAccount
    from app.models.company import CompanyVerification
    from app.models.internship import Internship, InternshipApplication
    from app.models.lookups import (
        UserAccountStatus,
        CompanyVerificationStatus,
        InternshipLifecycleStatus,
        InternshipModerationStatus,
        ApplicationStatus,
    )

    # ── User Statistics ──────────────────────────────────────────
    total_students = UserAccount.query.filter_by(
        role='student', deleted_at=None
    ).count()

    active_status = UserAccountStatus.query.filter_by(status_code='active').first()
    active_students = UserAccount.query.filter_by(
        role='student',
        account_status_id=active_status.id if active_status else 0,
        deleted_at=None
    ).count()

    total_companies = UserAccount.query.filter_by(
        role='company', deleted_at=None
    ).count()

    # ── Company Statistics ────────────────────────────────────────
    verified_status   = CompanyVerificationStatus.query.filter_by(status_code='verified').first()
    pending_status    = CompanyVerificationStatus.query.filter_by(status_code='pending').first()
    rejected_status   = CompanyVerificationStatus.query.filter_by(status_code='rejected').first()

    # Latest verification record per company
    # Use a subquery: count distinct company_profile_ids for each status
    verified_companies = CompanyVerification.query.filter_by(
        verification_status_id=verified_status.id if verified_status else 0,
        deleted_at=None
    ).count()

    pending_companies = CompanyVerification.query.filter_by(
        verification_status_id=pending_status.id if pending_status else 0,
        deleted_at=None
    ).count()

    rejected_companies = CompanyVerification.query.filter_by(
        verification_status_id=rejected_status.id if rejected_status else 0,
        deleted_at=None
    ).count()

    # ── Internship Statistics ─────────────────────────────────────
    total_internships = Internship.query.filter(
        Internship.deleted_at.is_(None)
    ).count()

    active_lifecycle  = InternshipLifecycleStatus.query.filter_by(status_code='active').first()
    closed_lifecycle  = InternshipLifecycleStatus.query.filter_by(status_code='closed').first()
    pending_mod       = InternshipModerationStatus.query.filter_by(status_code='pending').first()

    active_internships = Internship.query.filter_by(
        lifecycle_status_id=active_lifecycle.id if active_lifecycle else 0
    ).filter(Internship.deleted_at.is_(None)).count()

    closed_internships = Internship.query.filter_by(
        lifecycle_status_id=closed_lifecycle.id if closed_lifecycle else 0
    ).filter(Internship.deleted_at.is_(None)).count()

    pending_moderation = Internship.query.filter_by(
        moderation_status_id=pending_mod.id if pending_mod else 0
    ).filter(Internship.deleted_at.is_(None)).count()

    # ── Application Statistics ────────────────────────────────────
    total_applications = InternshipApplication.query.filter(
        InternshipApplication.deleted_at.is_(None)
    ).count()

    # Per-status counts for funnel
    app_status_counts_raw = db.session.query(
        ApplicationStatus.status_code,
        ApplicationStatus.status_name,
        func.count(InternshipApplication.id).label('cnt')
    ).join(
        InternshipApplication,
        InternshipApplication.application_status_id == ApplicationStatus.id
    ).filter(
        InternshipApplication.deleted_at.is_(None)
    ).group_by(
        ApplicationStatus.status_code,
        ApplicationStatus.status_name
    ).all()

    app_status_counts = {row.status_code: {'name': row.status_name, 'count': row.cnt}
                         for row in app_status_counts_raw}

    # Ensure all funnel stages exist (fallback to 0)
    for code, name in [
        ('applied',     'Dikirim'),
        ('reviewing',   'Direview'),
        ('shortlisted', 'Shortlist'),
        ('interviewing','Wawancara'),
        ('accepted',    'Diterima'),
        ('rejected',    'Ditolak'),
    ]:
        app_status_counts.setdefault(code, {'name': name, 'count': 0})

    return render_template(
        'admin/dashboard.html',
        # User stats
        total_students=total_students,
        active_students=active_students,
        total_companies=total_companies,
        # Company stats
        verified_companies=verified_companies,
        pending_companies=pending_companies,
        rejected_companies=rejected_companies,
        # Internship stats
        total_internships=total_internships,
        active_internships=active_internships,
        closed_internships=closed_internships,
        pending_moderation=pending_moderation,
        # Application stats
        total_applications=total_applications,
        app_status_counts=app_status_counts,
    )


# ── Student Management ───────────────────────────────────────────

@bp.route('/students')
@admin_required
def students():
    from flask import request
    from app.models.identity import UserAccount, StudentProfile
    from app.models.lookups import UserAccountStatus
    from sqlalchemy.orm import joinedload

    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = UserAccount.query.options(
        joinedload(UserAccount.status),
        joinedload(UserAccount.student_profile).joinedload(StudentProfile.education_records)
    ).filter_by(role='student', deleted_at=None)

    if q:
        query = query.filter(
            db.or_(
                UserAccount.display_name.ilike(f'%{q}%'),
                UserAccount.email.ilike(f'%{q}%'),
            )
        )

    pagination = query.order_by(UserAccount.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        'admin/students.html',
        students=pagination.items,
        pagination=pagination,
        q=q,
    )


@bp.route('/students/<int:id>')
@admin_required
def student_detail(id):
    from app.models.identity import UserAccount, StudentProfile
    from app.models.internship import InternshipApplication
    from sqlalchemy.orm import joinedload

    student = UserAccount.query.filter_by(
        id=id, role='student', deleted_at=None
    ).first_or_404()

    applications = InternshipApplication.query.options(
        joinedload(InternshipApplication.internship),
        joinedload(InternshipApplication.application_status),
    ).filter_by(
        student_profile_id=student.student_profile.id if student.student_profile else 0,
        deleted_at=None
    ).order_by(InternshipApplication.submitted_at.desc()).all()

    return render_template(
        'admin/student_detail.html',
        student=student,
        applications=applications,
    )


@bp.route('/students/<int:id>/disable', methods=['POST'])
@admin_required
def disable_student(id):
    from flask import redirect, url_for, flash
    from app.models.identity import UserAccount
    from app.models.lookups import UserAccountStatus
    from app.models.system import AdminAuditLog
    from datetime import datetime

    student = UserAccount.query.filter_by(
        id=id, role='student', deleted_at=None
    ).first_or_404()

    disabled_status = UserAccountStatus.query.filter_by(status_code='disabled').first()
    if not disabled_status:
        flash('Status "disabled" tidak ditemukan di database.', 'danger')
        return redirect(url_for('admin.student_detail', id=id))

    student.account_status_id = disabled_status.id

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='disable_student',
        target_type='UserAccount',
        target_id=student.id,
        details_json={
            'student_email': student.email,
            'student_name': student.display_name,
        }
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Akun {student.display_name} berhasil dinonaktifkan.', 'success')
    return redirect(url_for('admin.student_detail', id=id))


@bp.route('/students/<int:id>/enable', methods=['POST'])
@admin_required
def enable_student(id):
    from flask import redirect, url_for, flash
    from app.models.identity import UserAccount
    from app.models.lookups import UserAccountStatus
    from app.models.system import AdminAuditLog

    student = UserAccount.query.filter_by(
        id=id, role='student', deleted_at=None
    ).first_or_404()

    active_status = UserAccountStatus.query.filter_by(status_code='active').first()
    if not active_status:
        flash('Status "active" tidak ditemukan di database.', 'danger')
        return redirect(url_for('admin.student_detail', id=id))

    student.account_status_id = active_status.id

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='enable_student',
        target_type='UserAccount',
        target_id=student.id,
        details_json={
            'student_email': student.email,
            'student_name': student.display_name,
        }
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Akun {student.display_name} berhasil diaktifkan kembali.', 'success')
    return redirect(url_for('admin.student_detail', id=id))


# ── Placeholder routes (diimplementasi di section berikutnya) ────

@bp.route('/companies')
@admin_required
def companies():
    return render_template('admin/companies.html')


@bp.route('/internships')
@admin_required
def internships():
    return render_template('admin/internships.html')


@bp.route('/categories')
@admin_required
def categories():
    return render_template('admin/categories.html')


@bp.route('/skills')
@admin_required
def skills():
    return render_template('admin/skills.html')


@bp.route('/tech-stacks')
@admin_required
def tech_stacks():
    return render_template('admin/tech_stacks.html')


@bp.route('/locations')
@admin_required
def locations():
    return render_template('admin/locations.html')
