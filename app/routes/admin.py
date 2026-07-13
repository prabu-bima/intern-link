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

    disabled_status = UserAccountStatus.query.filter_by(status_code='inactive').first()
    if not disabled_status:
        flash('Status "inactive" tidak ditemukan di database.', 'danger')
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


# ── Company Management ───────────────────────────────────────────

@bp.route('/companies')
@admin_required
def companies():
    from flask import request
    from app.models.identity import UserAccount, CompanyProfile
    from app.models.company import CompanyVerification
    from app.models.lookups import CompanyVerificationStatus
    from sqlalchemy.orm import joinedload

    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    query = UserAccount.query.options(
        joinedload(UserAccount.status),
        joinedload(UserAccount.company_profile).joinedload(CompanyProfile.verifications)
    ).filter_by(role='company', deleted_at=None)

    if q:
        query = query.join(CompanyProfile, CompanyProfile.user_account_id == UserAccount.id).filter(
            db.or_(
                UserAccount.display_name.ilike(f'%{q}%'),
                UserAccount.email.ilike(f'%{q}%'),
                CompanyProfile.company_name.ilike(f'%{q}%'),
            )
        )

    # Filter by latest verification status
    if status_filter != 'all':
        ver_status = CompanyVerificationStatus.query.filter_by(status_code=status_filter).first()
        if ver_status:
            # Subquery: company_profile_ids whose latest verification has this status
            from sqlalchemy import select
            latest_ver = db.session.query(
                CompanyVerification.company_profile_id,
                db.func.max(CompanyVerification.id).label('max_id')
            ).group_by(CompanyVerification.company_profile_id).subquery()

            matching_ids = db.session.query(CompanyProfile.user_account_id).join(
                latest_ver, latest_ver.c.company_profile_id == CompanyProfile.id
            ).join(
                CompanyVerification, CompanyVerification.id == latest_ver.c.max_id
            ).filter(
                CompanyVerification.verification_status_id == ver_status.id
            ).subquery()

            query = query.filter(UserAccount.id.in_(
                db.session.query(matching_ids)
            ))

    verification_statuses = CompanyVerificationStatus.query.all()
    pagination = query.order_by(UserAccount.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        'admin/companies.html',
        companies=pagination.items,
        pagination=pagination,
        q=q,
        status_filter=status_filter,
        verification_statuses=verification_statuses,
    )


@bp.route('/companies/<int:id>')
@admin_required
def company_detail(id):
    from app.models.identity import UserAccount, CompanyProfile
    from app.models.company import CompanyVerification
    from app.models.internship import Internship
    from sqlalchemy.orm import joinedload

    company = UserAccount.query.filter_by(
        id=id, role='company', deleted_at=None
    ).first_or_404()

    verifications = CompanyVerification.query.options(
        joinedload(CompanyVerification.verification_status),
        joinedload(CompanyVerification.admin_user),
    ).filter_by(
        company_profile_id=company.company_profile.id if company.company_profile else 0
    ).order_by(CompanyVerification.id.desc()).all()

    internships = Internship.query.filter_by(
        company_profile_id=company.company_profile.id if company.company_profile else 0,
        deleted_at=None
    ).order_by(Internship.id.desc()).limit(10).all()

    latest_verification = verifications[0] if verifications else None

    return render_template(
        'admin/company_detail.html',
        company=company,
        verifications=verifications,
        internships=internships,
        latest_verification=latest_verification,
    )


@bp.route('/companies/<int:id>/verify', methods=['POST'])
@admin_required
def verify_company(id):
    from flask import request, redirect, url_for, flash
    from app.models.identity import UserAccount
    from app.models.company import CompanyVerification
    from app.models.lookups import CompanyVerificationStatus
    from app.models.system import AdminAuditLog
    from datetime import datetime

    company = UserAccount.query.filter_by(
        id=id, role='company', deleted_at=None
    ).first_or_404()

    verified_status = CompanyVerificationStatus.query.filter_by(status_code='verified').first()
    if not verified_status:
        flash('Status "verified" tidak ditemukan di database.', 'danger')
        return redirect(url_for('admin.company_detail', id=id))

    admin_note = request.form.get('admin_note', '').strip()

    verification = CompanyVerification(
        company_profile_id=company.company_profile.id,
        verification_status_id=verified_status.id,
        admin_user_id=current_user.id,
        admin_note=admin_note or None,
        verified_at=datetime.utcnow(),
    )
    db.session.add(verification)

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='verify_company',
        target_type='CompanyProfile',
        target_id=company.company_profile.id,
        details_json={
            'company_name': company.company_profile.company_name,
            'admin_note': admin_note,
        }
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Perusahaan {company.company_profile.company_name} berhasil diverifikasi.', 'success')
    return redirect(url_for('admin.company_detail', id=id))


@bp.route('/companies/<int:id>/reject', methods=['POST'])
@admin_required
def reject_company(id):
    from flask import request, redirect, url_for, flash
    from app.models.identity import UserAccount
    from app.models.company import CompanyVerification
    from app.models.lookups import CompanyVerificationStatus
    from app.models.system import AdminAuditLog

    company = UserAccount.query.filter_by(
        id=id, role='company', deleted_at=None
    ).first_or_404()

    rejected_status = CompanyVerificationStatus.query.filter_by(status_code='rejected').first()
    if not rejected_status:
        flash('Status "rejected" tidak ditemukan di database.', 'danger')
        return redirect(url_for('admin.company_detail', id=id))

    admin_note = request.form.get('admin_note', '').strip()

    verification = CompanyVerification(
        company_profile_id=company.company_profile.id,
        verification_status_id=rejected_status.id,
        admin_user_id=current_user.id,
        admin_note=admin_note or None,
    )
    db.session.add(verification)

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='reject_company',
        target_type='CompanyProfile',
        target_id=company.company_profile.id,
        details_json={
            'company_name': company.company_profile.company_name,
            'admin_note': admin_note,
        }
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Perusahaan {company.company_profile.company_name} telah ditolak.', 'warning')
    return redirect(url_for('admin.company_detail', id=id))


@bp.route('/companies/<int:id>/disable', methods=['POST'])
@admin_required
def disable_company(id):
    from flask import redirect, url_for, flash
    from app.models.identity import UserAccount
    from app.models.lookups import UserAccountStatus, InternshipLifecycleStatus
    from app.models.internship import Internship
    from app.models.system import AdminAuditLog
    from datetime import datetime

    company = UserAccount.query.filter_by(
        id=id, role='company', deleted_at=None
    ).first_or_404()

    disabled_status = UserAccountStatus.query.filter_by(status_code='inactive').first()
    if not disabled_status:
        flash('Status "inactive" tidak ditemukan di database.', 'danger')
        return redirect(url_for('admin.company_detail', id=id))

    company.account_status_id = disabled_status.id

    # Soft-hide all active internship postings
    if company.company_profile:
        active_lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='active').first()
        closed_lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='closed').first()
        if active_lifecycle and closed_lifecycle:
            Internship.query.filter_by(
                company_profile_id=company.company_profile.id,
                lifecycle_status_id=active_lifecycle.id,
                deleted_at=None
            ).update({'lifecycle_status_id': closed_lifecycle.id})

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='disable_company',
        target_type='UserAccount',
        target_id=company.id,
        details_json={
            'company_name': company.company_profile.company_name if company.company_profile else company.display_name,
            'email': company.email,
        }
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Akun perusahaan {company.display_name} berhasil dinonaktifkan dan semua lowongan aktif telah ditutup.', 'success')
    return redirect(url_for('admin.company_detail', id=id))


@bp.route('/companies/<int:id>/enable', methods=['POST'])
@admin_required
def enable_company(id):
    from flask import redirect, url_for, flash
    from app.models.identity import UserAccount
    from app.models.lookups import UserAccountStatus
    from app.models.system import AdminAuditLog

    company = UserAccount.query.filter_by(
        id=id, role='company', deleted_at=None
    ).first_or_404()

    active_status = UserAccountStatus.query.filter_by(status_code='active').first()
    if not active_status:
        flash('Status "active" tidak ditemukan di database.', 'danger')
        return redirect(url_for('admin.company_detail', id=id))

    company.account_status_id = active_status.id

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='enable_company',
        target_type='UserAccount',
        target_id=company.id,
        details_json={
            'company_name': company.company_profile.company_name if company.company_profile else company.display_name,
            'email': company.email,
        }
    )
    db.session.add(audit)
    db.session.commit()

    flash(f'Akun perusahaan {company.display_name} berhasil diaktifkan kembali.', 'success')
    return redirect(url_for('admin.company_detail', id=id))


# ── Internship Management ────────────────────────────────────────

@bp.route('/internships')
@admin_required
def internships():
    from flask import request
    from app.models.internship import Internship
    from app.models.identity import CompanyProfile
    from app.models.lookups import InternshipLifecycleStatus, InternshipModerationStatus
    from sqlalchemy.orm import joinedload
    
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    mod_filter = request.args.get('mod', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Internship.query.options(
        joinedload(Internship.company_profile),
        joinedload(Internship.lifecycle_status),
        joinedload(Internship.moderation_status)
    ).filter(Internship.deleted_at.is_(None))
    
    if q:
        query = query.join(CompanyProfile).filter(
            db.or_(
                Internship.internship_title.ilike(f'%{q}%'),
                CompanyProfile.company_name.ilike(f'%{q}%')
            )
        )
        
    if status_filter != 'all':
        status_obj = InternshipLifecycleStatus.query.filter_by(status_code=status_filter).first()
        if status_obj:
            query = query.filter(Internship.lifecycle_status_id == status_obj.id)
            
    if mod_filter != 'all':
        mod_obj = InternshipModerationStatus.query.filter_by(status_code=mod_filter).first()
        if mod_obj:
            query = query.filter(Internship.moderation_status_id == mod_obj.id)
            
    pagination = query.order_by(Internship.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    lifecycle_statuses = InternshipLifecycleStatus.query.all()
    mod_statuses = InternshipModerationStatus.query.all()
    
    return render_template(
        'admin/internships.html',
        internships=pagination.items,
        pagination=pagination,
        q=q,
        current_status=status_filter,
        current_mod=mod_filter,
        lifecycle_statuses=lifecycle_statuses,
        mod_statuses=mod_statuses
    )


@bp.route('/internships/<int:id>')
@admin_required
def internship_detail(id):
    from app.models.internship import Internship, InternshipApplication, InternshipModerationEvent
    from sqlalchemy.orm import joinedload
    
    internship = Internship.query.options(
        joinedload(Internship.company_profile),
        joinedload(Internship.technology_category),
        joinedload(Internship.location),
        joinedload(Internship.lifecycle_status),
        joinedload(Internship.moderation_status),
        joinedload(Internship.required_skills),
        joinedload(Internship.required_tech_stack_items)
    ).filter_by(id=id, deleted_at=None).first_or_404()
    
    # Get applicants count
    applicants_count = InternshipApplication.query.filter_by(
        internship_id=internship.id, deleted_at=None
    ).count()
    
    # Get moderation events
    moderation_events = InternshipModerationEvent.query.options(
        joinedload(InternshipModerationEvent.admin_user),
        joinedload(InternshipModerationEvent.moderation_status)
    ).filter_by(
        internship_id=internship.id, deleted_at=None
    ).order_by(InternshipModerationEvent.id.desc()).all()
    
    return render_template(
        'admin/internship_detail.html',
        internship=internship,
        applicants_count=applicants_count,
        moderation_events=moderation_events
    )


@bp.route('/internships/<int:id>/moderate', methods=['POST'])
@admin_required
def moderate_internship(id):
    from flask import request, redirect, url_for, flash
    from app.models.internship import Internship, InternshipModerationEvent
    from app.models.lookups import InternshipModerationStatus
    from app.models.system import AdminAuditLog
    
    internship = Internship.query.filter_by(id=id, deleted_at=None).first_or_404()
    
    action = request.form.get('action') # 'approved', 'flagged', 'hidden'
    note = request.form.get('note', '').strip()
    
    mod_status = InternshipModerationStatus.query.filter_by(status_code=action).first()
    if not mod_status:
        flash('Status moderasi tidak valid.', 'danger')
        return redirect(url_for('admin.internship_detail', id=id))
        
    internship.moderation_status_id = mod_status.id
    
    mod_event = InternshipModerationEvent(
        internship_id=internship.id,
        admin_user_id=current_user.id,
        moderation_status_id=mod_status.id,
        action_note=note
    )
    db.session.add(mod_event)
    
    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code=f'moderate_internship_{action}',
        target_type='Internship',
        target_id=internship.id,
        details_json={
            'internship_title': internship.internship_title,
            'company_name': internship.company_profile.company_name if internship.company_profile else 'Unknown',
            'note': note
        }
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'Status moderasi berhasil diubah menjadi {mod_status.status_name}.', 'success')
    return redirect(url_for('admin.internship_detail', id=id))


@bp.route('/internships/<int:id>/delete', methods=['POST'])
@admin_required
def delete_internship(id):
    from flask import redirect, url_for, flash
    from app.models.internship import Internship
    from app.models.system import AdminAuditLog
    from datetime import datetime
    
    internship = Internship.query.filter_by(id=id, deleted_at=None).first_or_404()
    
    internship.deleted_at = datetime.utcnow()
    
    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        action_code='delete_internship',
        target_type='Internship',
        target_id=internship.id,
        details_json={
            'internship_title': internship.internship_title,
            'company_name': internship.company_profile.company_name if internship.company_profile else 'Unknown'
        }
    )
    db.session.add(audit)
    db.session.commit()
    
    flash('Lowongan magang berhasil dihapus.', 'success')
    return redirect(url_for('admin.internships'))

@bp.route('/categories')
@admin_required
def categories():
    from flask import redirect, url_for
    return redirect(url_for('admin.master_data', tab='categories'))


@bp.route('/skills')
@admin_required
def skills():
    from flask import redirect, url_for
    return redirect(url_for('admin.master_data', tab='skills'))


@bp.route('/tech-stacks')
@admin_required
def tech_stacks():
    from flask import redirect, url_for
    return redirect(url_for('admin.master_data', tab='tech-stack'))


@bp.route('/locations')
@admin_required
def locations():
    from flask import redirect, url_for
    return redirect(url_for('admin.master_data', tab='locations'))


# ── Master Data Management ───────────────────────────────────────

@bp.route('/master-data')
@admin_required
def master_data():
    from flask import request
    from app.models.master import TechnologyCategory, Skill, TechStackItem, Location

    tab = request.args.get('tab', 'categories')

    categories = TechnologyCategory.query.order_by(TechnologyCategory.category_name).all()
    skills = Skill.query.order_by(Skill.skill_name).all()
    tech_stacks = TechStackItem.query.order_by(TechStackItem.tech_stack_name).all()
    locations = Location.query.order_by(Location.city).all()

    return render_template(
        'admin/master_data.html',
        tab=tab,
        categories=categories,
        skills=skills,
        tech_stacks=tech_stacks,
        locations=locations,
    )


# — Technology Categories —

@bp.route('/master-data/categories', methods=['POST'])
@admin_required
def add_category():
    from flask import request, jsonify
    from app.models.master import TechnologyCategory

    name = request.form.get('category_name', '').strip()
    code = request.form.get('category_code', '').strip().lower()
    desc = request.form.get('description', '').strip()

    if not name or not code:
        return jsonify({'error': 'Nama dan kode kategori wajib diisi.'}), 400

    if TechnologyCategory.query.filter_by(category_code=code).first():
        return jsonify({'error': f'Kode "{code}" sudah digunakan.'}), 400

    item = TechnologyCategory(category_code=code, category_name=name, description=desc or None)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id, 'category_name': item.category_name, 'category_code': item.category_code, 'description': item.description})


@bp.route('/master-data/categories/<int:id>', methods=['POST'])
@admin_required
def edit_category(id):
    from flask import request, jsonify
    from app.models.master import TechnologyCategory

    item = TechnologyCategory.query.get_or_404(id)
    name = request.form.get('category_name', '').strip()
    desc = request.form.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Nama kategori wajib diisi.'}), 400

    item.category_name = name
    item.description = desc or None
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/master-data/categories/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    from flask import jsonify
    from app.models.master import TechnologyCategory

    item = TechnologyCategory.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Tidak dapat menghapus kategori yang masih digunakan oleh lowongan.'}), 400


# — Skills —

@bp.route('/master-data/skills', methods=['POST'])
@admin_required
def add_skill():
    from flask import request, jsonify
    from app.models.master import Skill

    name = request.form.get('skill_name', '').strip()
    code = request.form.get('skill_code', '').strip().lower()
    desc = request.form.get('description', '').strip()

    if not name or not code:
        return jsonify({'error': 'Nama dan kode keahlian wajib diisi.'}), 400

    if Skill.query.filter_by(skill_code=code).first():
        return jsonify({'error': f'Kode "{code}" sudah digunakan.'}), 400

    item = Skill(skill_code=code, skill_name=name, description=desc or None)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id, 'skill_name': item.skill_name, 'skill_code': item.skill_code, 'description': item.description})


@bp.route('/master-data/skills/<int:id>', methods=['POST'])
@admin_required
def edit_skill(id):
    from flask import request, jsonify
    from app.models.master import Skill

    item = Skill.query.get_or_404(id)
    name = request.form.get('skill_name', '').strip()
    desc = request.form.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Nama keahlian wajib diisi.'}), 400

    item.skill_name = name
    item.description = desc or None
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/master-data/skills/<int:id>/delete', methods=['POST'])
@admin_required
def delete_skill(id):
    from flask import jsonify
    from app.models.master import Skill

    item = Skill.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Tidak dapat menghapus keahlian yang masih digunakan.'}), 400


# — Tech Stack —

@bp.route('/master-data/tech-stack', methods=['POST'])
@admin_required
def add_tech_stack():
    from flask import request, jsonify
    from app.models.master import TechStackItem

    name = request.form.get('tech_stack_name', '').strip()
    code = request.form.get('tech_stack_code', '').strip().lower()
    desc = request.form.get('description', '').strip()

    if not name or not code:
        return jsonify({'error': 'Nama dan kode tech stack wajib diisi.'}), 400

    if TechStackItem.query.filter_by(tech_stack_code=code).first():
        return jsonify({'error': f'Kode "{code}" sudah digunakan.'}), 400

    item = TechStackItem(tech_stack_code=code, tech_stack_name=name, description=desc or None)
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id, 'tech_stack_name': item.tech_stack_name, 'tech_stack_code': item.tech_stack_code, 'description': item.description})


@bp.route('/master-data/tech-stack/<int:id>', methods=['POST'])
@admin_required
def edit_tech_stack(id):
    from flask import request, jsonify
    from app.models.master import TechStackItem

    item = TechStackItem.query.get_or_404(id)
    name = request.form.get('tech_stack_name', '').strip()
    desc = request.form.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Nama tech stack wajib diisi.'}), 400

    item.tech_stack_name = name
    item.description = desc or None
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/master-data/tech-stack/<int:id>/delete', methods=['POST'])
@admin_required
def delete_tech_stack(id):
    from flask import jsonify
    from app.models.master import TechStackItem

    item = TechStackItem.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Tidak dapat menghapus tech stack yang masih digunakan.'}), 400


# — Locations —

@bp.route('/master-data/locations', methods=['POST'])
@admin_required
def add_location():
    from flask import request, jsonify
    from app.models.master import Location

    code = request.form.get('location_code', '').strip().lower()
    city = request.form.get('city', '').strip()
    region = request.form.get('region', '').strip()
    country = request.form.get('country', 'Indonesia').strip()

    if not code or not city:
        return jsonify({'error': 'Kode dan nama kota wajib diisi.'}), 400

    if Location.query.filter_by(location_code=code).first():
        return jsonify({'error': f'Kode "{code}" sudah digunakan.'}), 400

    item = Location(location_code=code, city=city, region=region or None, country=country or 'Indonesia')
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id, 'city': item.city, 'region': item.region, 'country': item.country, 'location_code': item.location_code})


@bp.route('/master-data/locations/<int:id>', methods=['POST'])
@admin_required
def edit_location(id):
    from flask import request, jsonify
    from app.models.master import Location

    item = Location.query.get_or_404(id)
    city = request.form.get('city', '').strip()
    region = request.form.get('region', '').strip()
    country = request.form.get('country', '').strip()

    if not city:
        return jsonify({'error': 'Nama kota wajib diisi.'}), 400

    item.city = city
    item.region = region or None
    item.country = country or 'Indonesia'
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/master-data/locations/<int:id>/delete', methods=['POST'])
@admin_required
def delete_location(id):
    from flask import jsonify
    from app.models.master import Location

    item = Location.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Tidak dapat menghapus lokasi yang masih digunakan.'}), 400
