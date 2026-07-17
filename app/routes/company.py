from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.decorators import company_required
from app.models.company import CompanyVerification
from app.models.internship import Internship, InternshipApplication
from app.models.lookups import InternshipLifecycleStatus, InternshipModerationStatus, ApplicationStatus
from app.models.system import Notification
from app.extensions import db
from sqlalchemy import func
from datetime import datetime

bp = Blueprint('company', __name__, url_prefix='/company')


@bp.context_processor
def inject_unread_notifications_count():
    if current_user.is_authenticated and current_user.role == 'company':
        count = Notification.query.filter_by(
            recipient_user_id=current_user.id,
            is_read=False,
            deleted_at=None
        ).count()
        return dict(unread_notifications_count=count)
    return dict(unread_notifications_count=0)

class VerificationStatusInfo:
    def __init__(self, status_code):
        self.status_code = status_code

class VerificationInfo:
    def __init__(self, status_code, admin_note):
        self.verification_status = VerificationStatusInfo(status_code)
        self.admin_note = admin_note

@bp.route('/dashboard')
@company_required
def dashboard():
    profile = current_user.company_profile
    if not profile:
        # Failsafe if company profile doesn't exist
        return "Company profile not found", 404

    from app.extensions import cache
    from sqlalchemy.orm import joinedload, selectinload
    from sqlalchemy import case
    from app.models.identity import StudentProfile

    # 2. Caching Status Lookups (IDs only to avoid session detachment errors)
    active_lifecycle_id = cache.get('status_lifecycle_active_id')
    if not active_lifecycle_id:
        active_lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='active').first()
        if active_lifecycle:
            active_lifecycle_id = active_lifecycle.id
            cache.set('status_lifecycle_active_id', active_lifecycle_id, timeout=86400)
            
    closed_lifecycle_id = cache.get('status_lifecycle_closed_id')
    if not closed_lifecycle_id:
        closed_lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='closed').first()
        if closed_lifecycle:
            closed_lifecycle_id = closed_lifecycle.id
            cache.set('status_lifecycle_closed_id', closed_lifecycle_id, timeout=86400)
            
    pending_moderation_id = cache.get('status_moderation_pending_id')
    if not pending_moderation_id:
        pending_moderation = InternshipModerationStatus.query.filter_by(status_code='pending').first()
        if pending_moderation:
            pending_moderation_id = pending_moderation.id
            cache.set('status_moderation_pending_id', pending_moderation_id, timeout=86400)

    # 3. Caching Dashboard Stats (60 seconds)
    stats_cache_key = f"company_dashboard_stats_{profile.id}"
    stats = cache.get(stats_cache_key)
    if not stats:
        # 3a. Company Verification Status
        verification_db = CompanyVerification.query.options(
            joinedload(CompanyVerification.verification_status)
        ).filter_by(
            company_profile_id=profile.id
        ).order_by(CompanyVerification.id.desc()).first()
        
        verification = None
        if verification_db:
            verification = VerificationInfo(
                verification_db.verification_status.status_code if verification_db.verification_status else None,
                verification_db.admin_note
            )

        # Job Statistics in a single combined query with conditional aggregation
        counts = db.session.query(
            func.count(Internship.id),
            func.sum(case((Internship.lifecycle_status_id == (active_lifecycle_id or 0), 1), else_=0)),
            func.sum(case((Internship.lifecycle_status_id == (closed_lifecycle_id or 0), 1), else_=0)),
            func.sum(case((Internship.moderation_status_id == (pending_moderation_id or 0), 1), else_=0))
        ).filter(
            Internship.company_profile_id == profile.id,
            Internship.deleted_at.is_(None)
        ).first()
        
        total_jobs, active_jobs, closed_jobs, pending_jobs = counts or (0, 0, 0, 0)
        total_jobs = int(total_jobs or 0)
        active_jobs = int(active_jobs or 0)
        closed_jobs = int(closed_jobs or 0)
        pending_jobs = int(pending_jobs or 0)

        # Applicant Statistics GROUP BY
        status_counts_query = db.session.query(
            ApplicationStatus.status_code, 
            ApplicationStatus.status_name, 
            func.count(InternshipApplication.id)
        ).select_from(InternshipApplication).join(Internship).join(ApplicationStatus, InternshipApplication.application_status_id == ApplicationStatus.id).filter(
            Internship.company_profile_id == profile.id,
            InternshipApplication.deleted_at.is_(None)
        ).group_by(ApplicationStatus.status_code, ApplicationStatus.status_name).all()

        applicant_stats = {code: {'name': name, 'count': count} for code, name, count in status_counts_query}
        # Ensure some defaults exist
        for code, default_name in [('applied', 'Dikirim'), ('reviewing', 'Direview'), ('interviewing', 'Wawancara'), ('accepted', 'Diterima'), ('rejected', 'Ditolak')]:
            if code not in applicant_stats:
                applicant_stats[code] = {'name': default_name, 'count': 0}

        total_applicants = sum(item['count'] for item in applicant_stats.values())

        # 4. Active Jobs list (limit 5) - use selectinload for applications collection
        active_jobs_list = Internship.query.options(
            joinedload(Internship.location),
            joinedload(Internship.technology_category),
            selectinload(Internship.applications)
        ).filter_by(
            company_profile_id=profile.id,
            lifecycle_status_id=active_lifecycle_id or 0
        ).filter(Internship.deleted_at.is_(None)).order_by(Internship.id.desc()).limit(5).all()

        # 5. Latest Applicants feed (limit 5) - eager load student_profile, user, and profile_photo to prevent N+1 queries
        latest_applicants = InternshipApplication.query.options(
            joinedload(InternshipApplication.student_profile).options(
                joinedload(StudentProfile.user),
                joinedload(StudentProfile.profile_photo)
            ),
            joinedload(InternshipApplication.internship),
            joinedload(InternshipApplication.application_status)
        ).join(Internship).filter(
            Internship.company_profile_id == profile.id
        ).filter(InternshipApplication.deleted_at.is_(None)).order_by(InternshipApplication.submitted_at.desc()).limit(5).all()

        stats = {
            'verification': verification,
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'closed_jobs': closed_jobs,
            'pending_jobs': pending_jobs,
            'total_applicants': total_applicants,
            'applicant_stats': applicant_stats,
            'active_jobs_list': active_jobs_list,
            'latest_applicants': latest_applicants
        }
        cache.set(stats_cache_key, stats, timeout=60)

    verification = stats['verification']
    total_jobs = stats['total_jobs']
    active_jobs = stats['active_jobs']
    closed_jobs = stats['closed_jobs']
    pending_jobs = stats['pending_jobs']
    total_applicants = stats['total_applicants']
    applicant_stats = stats['applicant_stats']
    active_jobs_list = stats['active_jobs_list']
    latest_applicants = stats['latest_applicants']

    return render_template(
        'company/dashboard.html',
        verification=verification,
        total_jobs=total_jobs,
        active_jobs_count=active_jobs,
        closed_jobs_count=closed_jobs,
        pending_jobs_count=pending_jobs,
        total_applicants=total_applicants,
        applicant_stats=applicant_stats,
        active_jobs_list=active_jobs_list,
        latest_applicants=latest_applicants
    )

from app.models.company import CompanySocialLink
from app.models.master import Location
from app.models.identity import FileAsset
from app.services.storage import upload_file, validate_file, get_bucket_for_purpose, delete_file
import os
import uuid
from werkzeug.utils import secure_filename

@bp.route('/profile')
@company_required
def profile():
    profile = current_user.company_profile
    locations = Location.query.all()
    verification = CompanyVerification.query.filter_by(
        company_profile_id=profile.id
    ).order_by(CompanyVerification.id.desc()).first()
    return render_template('company/profile.html', profile=profile, locations=locations, verification=verification)

@bp.route('/profile/info', methods=['POST'])
@company_required
def profile_info():
    profile = current_user.company_profile
    profile.company_name = request.form.get('company_name', profile.company_name)
    profile.company_description = request.form.get('company_description')
    profile.industry_category = request.form.get('industry_category')
    profile.company_size = request.form.get('company_size')
    
    founding_year = request.form.get('founding_year')
    if founding_year and founding_year.isdigit():
        profile.founding_year = int(founding_year)
        
    db.session.commit()
    flash('Informasi perusahaan berhasil diperbarui.', 'success')
    return redirect(url_for('company.profile'))

@bp.route('/profile/logo', methods=['POST'])
@company_required
def profile_logo():
    if 'company_logo' not in request.files:
        flash('Tidak ada file logo yang diunggah.', 'danger')
        return redirect(url_for('company.profile'))
        
    file = request.files['company_logo']
    is_valid, error_msg = validate_file(file, allowed_extensions=['jpg', 'jpeg', 'png', 'webp'], max_size_mb=2)
    
    if not is_valid:
        flash(error_msg, 'danger')
        return redirect(url_for('company.profile'))
        
    profile = current_user.company_profile
    bucket_name = get_bucket_for_purpose('company_logo')
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"company_{profile.id}_{uuid.uuid4().hex}.{ext}"
    
    try:
        object_key = upload_file(bucket_name, file, unique_filename, file.content_type)
        
        # Create new FileAsset
        new_asset = FileAsset(
            owner_user_id=current_user.id,
            file_purpose='company_logo',
            storage_bucket=bucket_name,
            object_key=object_key,
            file_name=secure_filename(file.filename),
            content_type=file.content_type,
            file_size_bytes=file.tell() if hasattr(file, 'tell') else 0
        )
        db.session.add(new_asset)
        db.session.flush()
        
        # Delete old logo if exists
        if profile.company_logo:
            try:
                delete_file(profile.company_logo.storage_bucket, profile.company_logo.object_key)
            except Exception as e:
                print(f"Failed to delete old logo: {e}")
                
        profile.company_logo_file_id = new_asset.id
        db.session.commit()
        flash('Logo perusahaan berhasil diperbarui.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal mengunggah logo: {str(e)}', 'danger')
        
    return redirect(url_for('company.profile'))

@bp.route('/profile/address', methods=['POST'])
@company_required
def profile_address():
    profile = current_user.company_profile
    profile.address_line = request.form.get('address_line')
    location_id = request.form.get('location_id')
    if location_id and location_id.isdigit():
        profile.location_id = int(location_id)
    db.session.commit()
    flash('Alamat perusahaan berhasil diperbarui.', 'success')
    return redirect(url_for('company.profile'))

@bp.route('/profile/website', methods=['POST'])
@company_required
def profile_website():
    profile = current_user.company_profile
    profile.website_url = request.form.get('website_url')
    db.session.commit()
    flash('Tautan website berhasil diperbarui.', 'success')
    return redirect(url_for('company.profile'))

@bp.route('/profile/social', methods=['POST'])
@company_required
def profile_social():
    profile = current_user.company_profile
    platform = request.form.get('platform')
    url = request.form.get('url')
    
    if platform and url:
        new_link = CompanySocialLink(
            company_profile_id=profile.id,
            platform=platform,
            url=url
        )
        db.session.add(new_link)
        db.session.commit()
        flash('Tautan media sosial berhasil ditambahkan.', 'success')
    else:
        flash('Platform dan URL harus diisi.', 'danger')
        
    return redirect(url_for('company.profile'))

@bp.route('/profile/social/<int:id>/delete', methods=['POST'])
@company_required
def profile_social_delete(id):
    link = CompanySocialLink.query.get_or_404(id)
    if link.company_profile_id != current_user.company_profile.id:
        flash('Anda tidak memiliki izin.', 'danger')
        return redirect(url_for('company.profile'))
        
    db.session.delete(link)
    db.session.commit()
    flash('Tautan media sosial berhasil dihapus.', 'success')
    return redirect(url_for('company.profile'))

from app.models.master import TechnologyCategory, Skill, TechStackItem
from app.models.internship import InternshipRequiredSkill, InternshipRequiredTechStackItem

@bp.route('/internships/create', methods=['GET'])
@company_required
def internship_create_form():
    # Only allow verified companies
    profile = current_user.company_profile
    verification = CompanyVerification.query.filter_by(
        company_profile_id=profile.id
    ).order_by(CompanyVerification.id.desc()).first()
    
    if not verification or verification.verification_status.status_code != 'verified':
        flash('Perusahaan Anda harus terverifikasi untuk dapat membuat lowongan.', 'warning')
        return redirect(url_for('company.dashboard'))
        
    locations = Location.query.all()
    categories = TechnologyCategory.query.all()
    skills = Skill.query.all()
    tech_stacks = TechStackItem.query.all()
    
    return render_template(
        'company/internship_form.html',
        locations=locations,
        categories=categories,
        skills=skills,
        tech_stacks=tech_stacks
    )

@bp.route('/internships/create', methods=['POST'])
@company_required
def internship_create():
    profile = current_user.company_profile
    
    # 1. Fetch form data
    title = request.form.get('internship_title')
    description = request.form.get('internship_description')
    internship_type = request.form.get('internship_type')
    duration_months = request.form.get('duration_months')
    location_id = request.form.get('location_id')
    category_id = request.form.get('technology_category_id')
    closing_at_str = request.form.get('closing_at')
    
    # Check required fields
    if not title or not description or not location_id or not category_id:
        flash('Pastikan kolom wajib (Judul, Deskripsi, Lokasi, Kategori) terisi.', 'danger')
        return redirect(url_for('company.internship_create_form'))
        
    # Parse closing_at
    closing_at = None
    if closing_at_str:
        from datetime import datetime
        try:
            closing_at = datetime.strptime(closing_at_str, '%Y-%m-%d')
        except ValueError:
            pass
            
    # Default statuses
    lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='active').first()
    moderation = InternshipModerationStatus.query.filter_by(status_code='approved').first() # Auto approve for now, or pending depending on policy
    
    new_internship = Internship(
        company_profile_id=profile.id,
        technology_category_id=int(category_id),
        location_id=int(location_id),
        internship_title=title,
        internship_description=description,
        internship_type=internship_type,
        duration_months=int(duration_months) if duration_months and duration_months.isdigit() else None,
        lifecycle_status_id=lifecycle.id if lifecycle else 2,
        moderation_status_id=moderation.id if moderation else 2,
        closing_at=closing_at
    )
    
    db.session.add(new_internship)
    db.session.flush() # to get ID
    
    # Handle Skills (Multi-select)
    selected_skills = request.form.getlist('skills') # List of IDs
    for skill_id in selected_skills:
        if skill_id.isdigit():
            req_skill = InternshipRequiredSkill(
                internship_id=new_internship.id,
                skill_id=int(skill_id),
                required_level='required'
            )
            db.session.add(req_skill)
            
    # Handle Tech Stacks (Multi-select)
    selected_techs = request.form.getlist('tech_stacks') # List of IDs
    for tech_id in selected_techs:
        if tech_id.isdigit():
            req_tech = InternshipRequiredTechStackItem(
                internship_id=new_internship.id,
                tech_stack_item_id=int(tech_id),
                required_level='required'
            )
            db.session.add(req_tech)
            
    db.session.commit()
    flash('Lowongan magang berhasil dipublikasikan!', 'success')
    return redirect(url_for('company.dashboard')) # Redirect to dashboard or a list page

@bp.route('/internships', methods=['GET'])
@login_required
def internships():
    from app.models.internship import Internship
    
    if current_user.role != 'company':
        flash('Akses ditolak. Anda bukan perusahaan.', 'error')
        return redirect(url_for('guest.index'))
        
    profile = current_user.company_profile
    if not profile:
        flash('Silakan lengkapi profil perusahaan Anda terlebih dahulu.', 'warning')
        return redirect(url_for('company.profile_form'))
        
    status_filter = request.args.get('status', 'all')
    
    from sqlalchemy.orm import joinedload
    query = Internship.query.options(
        joinedload(Internship.lifecycle_status),
        joinedload(Internship.location),
        joinedload(Internship.technology_category)
    ).filter_by(company_profile_id=profile.id).filter(Internship.deleted_at.is_(None))
    
    if status_filter == 'active':
        query = query.join(Internship.lifecycle_status).filter(InternshipLifecycleStatus.status_code == 'active')
    elif status_filter == 'closed':
        query = query.join(Internship.lifecycle_status).filter(InternshipLifecycleStatus.status_code == 'closed')
        
    query = query.order_by(Internship.id.desc())
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'company/internships.html',
        pagination=pagination,
        internships=pagination.items,
        current_status=status_filter
    )


@bp.route('/internships/<int:id>/edit', methods=['GET'])
@login_required
def internship_edit_form(id):
    from app.models.master import TechnologyCategory, Location, Skill, TechStackItem
    from app.models.internship import Internship
    
    if current_user.role != 'company':
        flash('Akses ditolak.', 'error')
        return redirect(url_for('guest.index'))
        
    internship = Internship.query.get_or_404(id)
    if internship.company_profile_id != current_user.company_profile.id:
        flash('Akses ditolak.', 'error')
        return redirect(url_for('company.dashboard'))
        
    categories = TechnologyCategory.query.all()
    locations = Location.query.all()
    skills = Skill.query.all()
    tech_stacks = TechStackItem.query.all()
    
    existing_skills = [s.skill_id for s in internship.required_skills]
    existing_tech_stacks = [t.tech_stack_item_id for t in internship.required_tech_stack_items]
    
    return render_template(
        'company/internship_form.html',
        categories=categories,
        locations=locations,
        skills=skills,
        tech_stacks=tech_stacks,
        internship=internship,
        existing_skills=existing_skills,
        existing_tech_stacks=existing_tech_stacks
    )


@bp.route('/internships/<int:id>/edit', methods=['POST'])
@login_required
def internship_edit(id):
    from app.models.internship import Internship, InternshipRequiredSkill, InternshipRequiredTechStackItem
    
    if current_user.role != 'company':
        return redirect(url_for('guest.index'))
        
    internship = Internship.query.get_or_404(id)
    if internship.company_profile_id != current_user.company_profile.id:
        return redirect(url_for('company.dashboard'))
        
    # Get form data
    category_id = request.form.get('technology_category_id')
    location_id = request.form.get('location_id')
    title = request.form.get('internship_title')
    description = request.form.get('internship_description')
    internship_type = request.form.get('internship_type')
    duration_months = request.form.get('duration_months')
    
    closing_at_str = request.form.get('closing_at')
    closing_at = None
    if closing_at_str:
        try:
            closing_at = datetime.strptime(closing_at_str, '%Y-%m-%d')
        except ValueError:
            pass
            
    # Update fields
    internship.technology_category_id = int(category_id)
    internship.location_id = int(location_id)
    internship.internship_title = title
    internship.internship_description = description
    internship.internship_type = internship_type
    internship.duration_months = int(duration_months) if duration_months and duration_months.isdigit() else None
    internship.closing_at = closing_at
    
    # Update Skills
    selected_skills = request.form.getlist('skills')
    
    # Remove old skills
    for rs in internship.required_skills:
        db.session.delete(rs)
        
    # Add new skills
    for skill_id in selected_skills:
        if skill_id.isdigit():
            req_skill = InternshipRequiredSkill(
                internship=internship,
                skill_id=int(skill_id)
            )
            db.session.add(req_skill)
            
    # Update Tech Stacks
    selected_tech_stacks = request.form.getlist('tech_stacks')
    
    # Remove old tech stacks
    for rt in internship.required_tech_stack_items:
        db.session.delete(rt)
        
    # Add new tech stacks
    for tech_id in selected_tech_stacks:
        if tech_id.isdigit():
            req_tech = InternshipRequiredTechStackItem(
                internship=internship,
                tech_stack_item_id=int(tech_id)
            )
            db.session.add(req_tech)
            
    db.session.commit()
    flash('Lowongan magang berhasil diperbarui!', 'success')
    return redirect(url_for('company.internships'))


@bp.route('/internships/<int:id>/close', methods=['POST'])
@login_required
def internship_close(id):
    from app.models.internship import Internship
    
    if current_user.role != 'company':
        return redirect(url_for('guest.index'))
        
    internship = Internship.query.get_or_404(id)
    if internship.company_profile_id != current_user.company_profile.id:
        return redirect(url_for('company.dashboard'))
        
    closed_status = InternshipLifecycleStatus.query.filter_by(status_code='closed').first()
    if closed_status:
        internship.lifecycle_status_id = closed_status.id
        db.session.commit()
        flash('Lowongan magang berhasil ditutup.', 'success')
    else:
        flash('Terjadi kesalahan pada sistem status.', 'error')
        
    return redirect(url_for('company.internships'))


@bp.route('/internships/<int:id>/delete', methods=['POST'])
@login_required
def internship_delete(id):
    from app.models.internship import Internship
    
    if current_user.role != 'company':
        return redirect(url_for('guest.index'))
        
    internship = Internship.query.get_or_404(id)
    if internship.company_profile_id != current_user.company_profile.id:
        return redirect(url_for('company.dashboard'))
        
    internship.deleted_at = datetime.utcnow()
    db.session.commit()
    
    flash('Lowongan magang berhasil dihapus.', 'success')
    return redirect(url_for('company.internships'))


@bp.route('/internships/<int:id>/applicants', methods=['GET'])
@login_required
def internship_applicants(id):
    from app.models.internship import Internship, InternshipApplication
    from app.models.lookups import ApplicationStatus
    
    if current_user.role != 'company':
        flash('Akses ditolak.', 'error')
        return redirect(url_for('guest.index'))
        
    internship = Internship.query.filter_by(id=id, company_profile_id=current_user.company_profile.id).first_or_404()
    
    # Filtering
    status = request.args.get('status', 'all')
    
    from app.models.identity import StudentProfile
    from sqlalchemy.orm import joinedload
    
    query = InternshipApplication.query.options(
        joinedload(InternshipApplication.student_profile).joinedload(StudentProfile.user),
        joinedload(InternshipApplication.student_profile).joinedload(StudentProfile.education_records),
        joinedload(InternshipApplication.application_status)
    ).filter_by(internship_id=internship.id)
    
    if status != 'all':
        query = query.join(ApplicationStatus).filter(ApplicationStatus.status_code == status)
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(InternshipApplication.submitted_at.desc()).paginate(page=page, per_page=10, error_out=False)
    applicants = pagination.items
    
    # Get all application statuses for filter bar
    application_statuses = ApplicationStatus.query.all()
    
    # Calculate counts for each status using a single GROUP BY query
    status_counts_query = db.session.query(
        InternshipApplication.application_status_id, 
        db.func.count(InternshipApplication.id)
    ).filter_by(internship_id=internship.id).group_by(InternshipApplication.application_status_id).all()
    
    status_counts_map = {status_id: count for status_id, count in status_counts_query}
    
    status_counts = {'all': sum(status_counts_map.values())}
    for stat in application_statuses:
        status_counts[stat.status_code] = status_counts_map.get(stat.id, 0)
    
    return render_template(
        'company/applicants.html',
        internship=internship,
        applicants=applicants,
        pagination=pagination,
        current_status=status,
        application_statuses=application_statuses,
        status_counts=status_counts
    )

@bp.route('/applicants/<int:application_id>', methods=['GET'])
@login_required
@company_required
def applicant_detail(application_id):
    from app.models.internship import InternshipApplication, Internship
    from app.models.identity import CompanyProfile
    from app.models.lookups import ApplicationStatus
    
    # Get current company profile
    profile = CompanyProfile.query.filter_by(user_account_id=current_user.id).first()
    
    # Get application and verify it belongs to this company
    application = InternshipApplication.query.join(Internship).filter(
        InternshipApplication.id == application_id,
        Internship.company_profile_id == profile.id,
        InternshipApplication.deleted_at.is_(None)
    ).first_or_404()
    
    # Get all possible application statuses
    application_statuses = ApplicationStatus.query.all()
    
    return render_template(
        'company/applicant_detail.html',
        application=application,
        application_statuses=application_statuses
    )

@bp.route('/applicants/<int:application_id>/status', methods=['POST'])
@login_required
@company_required
def update_applicant_status(application_id):
    from flask import request
    from app.models.internship import InternshipApplication, Internship
    from app.models.identity import CompanyProfile
    from app.models.lookups import ApplicationStatus, NotificationType
    from app.models.system import Notification
    import json
    
    # Get current company profile
    profile = CompanyProfile.query.filter_by(user_account_id=current_user.id).first()
    
    # Get application and verify it belongs to this company
    application = InternshipApplication.query.join(Internship).filter(
        InternshipApplication.id == application_id,
        Internship.company_profile_id == profile.id,
        InternshipApplication.deleted_at.is_(None)
    ).first_or_404()
    
    # Get new status
    new_status_code = request.form.get('status_code')
    if not new_status_code:
        flash('Status tidak valid.', 'error')
        return redirect(url_for('company.applicant_detail', application_id=application_id))
        
    new_status = ApplicationStatus.query.filter_by(status_code=new_status_code).first()
    if not new_status:
        flash('Status tidak valid.', 'error')
        return redirect(url_for('company.applicant_detail', application_id=application_id))
        
    # Update status
    old_status = application.application_status
    application.application_status_id = new_status.id
    
    # Create notification for student
    try:
        # We assume notification types like 'application_status_updated' or 'application_accepted' exist.
        # Fallback to a general one if specific doesn't exist.
        notification_type_code = f"application_{new_status_code}"
        notif_type = NotificationType.query.filter_by(type_code=notification_type_code).first()
        if not notif_type:
            # Fallback
            notif_type = NotificationType.query.filter_by(type_code='application').first()
            
        if notif_type:
            title = f"Status Lamaran: {new_status.status_name}"
            message = f"Status lamaran Anda untuk posisi {application.internship.internship_title} di {profile.company_name} telah diperbarui menjadi {new_status.status_name}."
            
            payload = {
                "title": title,
                "message": message,
                "internship_title": application.internship.internship_title,
                "company_name": profile.company_name,
                "old_status": old_status.status_name,
                "new_status": new_status.status_name,
                "application_id": application.id
            }
            notification = Notification(
                recipient_user_id=application.student_profile.user_account_id,
                notification_type_id=notif_type.id,
                payload_json=payload
            )
            db.session.add(notification)
    except Exception as e:
        # Ignore notification error if types aren't fully seeded yet
        print(f"Error creating notification: {e}")
        pass
        
    db.session.commit()
    
    flash(f'Status pelamar berhasil diubah menjadi {new_status.status_name}.', 'success')
    return redirect(url_for('company.applicant_detail', application_id=application_id))

@bp.route('/applicants/<int:application_id>/interview', methods=['GET', 'POST'])
@login_required
@company_required
def schedule_interview(application_id):
    from app.models.internship import InternshipApplication, ApplicationInterview
    from app.models.identity import CompanyProfile
    from app.models.lookups import ApplicationStatus, NotificationType
    from app.models.system import Notification
    import json
    from datetime import datetime
    
    # Get current company profile
    profile = CompanyProfile.query.filter_by(user_account_id=current_user.id).first()
    
    # Get application and verify ownership
    application = InternshipApplication.query.get_or_404(application_id)
    if application.internship.company_profile_id != profile.id:
        abort(403)
        
    if request.method == 'POST':
        scheduled_at_str = request.form.get('scheduled_at') # YYYY-MM-DDTHH:MM
        interview_format = request.form.get('interview_format')
        location_or_link = request.form.get('location_or_link')
        notes = request.form.get('notes')
        
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            flash('Format tanggal dan waktu tidak valid.', 'error')
            return redirect(request.url)
            
        location_or_link = location_or_link.strip() if location_or_link else None
        
        # Validation
        if interview_format == 'offline' and not location_or_link:
            flash('Alamat / Lokasi Wawancara wajib diisi untuk format Tatap Muka.', 'danger')
            return redirect(request.url)
            
        if interview_format == 'online' and location_or_link:
            from urllib.parse import urlparse
            parsed_url = urlparse(location_or_link)
            if not (parsed_url.scheme and parsed_url.netloc) or parsed_url.scheme not in ['http', 'https']:
                flash('Tautan rapat (Meeting Link) harus berupa URL yang valid (misal: https://meet.google.com/...).', 'danger')
                return redirect(request.url)
            
        from app.models.lookups import InterviewStatus
        interview_status_obj = InterviewStatus.query.filter_by(status_code='scheduled').first()
        
        interview = ApplicationInterview(
            internship_application_id=application.id,
            interview_status_id=interview_status_obj.id if interview_status_obj else 1,
            scheduled_at=scheduled_at,
            meeting_link=location_or_link,
            interview_notes=f"Format: {interview_format}\nNotes: {notes}"
        )
        db.session.add(interview)
        
        # Update application status to interview
        interview_status = ApplicationStatus.query.filter_by(status_code='interviewing').first()
        if interview_status:
            old_status = application.application_status
            application.application_status_id = interview_status.id
            
            # Send notification
            notif_type = NotificationType.query.filter_by(type_code='application').first()
            if notif_type:
                title = f"Undangan Wawancara: {application.internship.internship_title}"
                format_display = "Online" if interview_format == "online" else "Tatap Muka (Offline)"
                dt_display = scheduled_at.strftime('%d %B %Y, %H:%M')
                
                if interview_format == "online" and not location_or_link:
                    message = f"Perusahaan {profile.company_name} mengundang Anda untuk wawancara pada {dt_display} secara {format_display}. Tautan rapat akan dikirim kemudian."
                else:
                    message = f"Perusahaan {profile.company_name} mengundang Anda untuk wawancara pada {dt_display} secara {format_display}."
                
                payload = {
                    "title": title,
                    "message": message,
                    "internship_title": application.internship.internship_title,
                    "company_name": profile.company_name,
                    "old_status": old_status.status_name,
                    "new_status": interview_status.status_name,
                    "application_id": application.id
                }
                notification = Notification(
                    recipient_user_id=application.student_profile.user_account_id,
                    notification_type_id=notif_type.id,
                    payload_json=payload
                )
                db.session.add(notification)
                
        db.session.commit()
        flash('Jadwal wawancara berhasil dibuat dan undangan telah dikirim ke pelamar.', 'success')
        return redirect(url_for('company.applicant_detail', application_id=application.id))
        
    return render_template('company/interview_form.html', application=application)

@bp.route('/interviews/<int:interview_id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_interview(interview_id):
    from app.models.internship import ApplicationInterview
    from app.models.identity import CompanyProfile
    from app.models.lookups import NotificationType
    from app.models.system import Notification
    from datetime import datetime
    
    profile = CompanyProfile.query.filter_by(user_account_id=current_user.id).first()
    interview = ApplicationInterview.query.get_or_404(interview_id)
    
    # Verify ownership
    if interview.application.internship.company_profile_id != profile.id:
        abort(403)
        
    if request.method == 'POST':
        scheduled_at_str = request.form.get('scheduled_at') # YYYY-MM-DDTHH:MM
        interview_format = request.form.get('interview_format')
        location_or_link = request.form.get('location_or_link')
        notes = request.form.get('notes')
        
        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            flash('Format tanggal dan waktu tidak valid.', 'error')
            return redirect(request.url)
            
        location_or_link = location_or_link.strip() if location_or_link else None
        
        # Validation
        if interview_format == 'offline' and not location_or_link:
            flash('Alamat / Lokasi Wawancara wajib diisi untuk format Tatap Muka.', 'danger')
            return redirect(request.url)
            
        if interview_format == 'online' and location_or_link:
            from urllib.parse import urlparse
            parsed_url = urlparse(location_or_link)
            if not (parsed_url.scheme and parsed_url.netloc) or parsed_url.scheme not in ['http', 'https']:
                flash('Tautan rapat (Meeting Link) harus berupa URL yang valid (misal: https://meet.google.com/...).', 'danger')
                return redirect(request.url)
                
        # Check if meeting link is added or updated
        old_link = interview.meeting_link
        
        interview.scheduled_at = scheduled_at
        interview.meeting_link = location_or_link
        interview.interview_notes = f"Format: {interview_format}\nNotes: {notes}"
        
        # If meeting link changed
        if location_or_link and location_or_link != old_link:
            # Send notification to student
            try:
                notif_type = NotificationType.query.filter_by(type_code='application').first()
                if notif_type:
                    title = f"Pembaruan Wawancara: {interview.application.internship.internship_title}"
                    dt_display = scheduled_at.strftime('%d %B %Y, %H:%M')
                    message = f"Tautan rapat/lokasi untuk wawancara Anda pada {dt_display} telah ditambahkan atau diperbarui."
                    
                    payload = {
                        "title": title,
                        "message": message,
                        "internship_title": interview.application.internship.internship_title,
                        "company_name": profile.company_name,
                        "meeting_link": location_or_link,
                        "application_id": interview.application.id
                    }
                    notification = Notification(
                        recipient_user_id=interview.application.student_profile.user_account_id,
                        notification_type_id=notif_type.id,
                        payload_json=payload
                    )
                    db.session.add(notification)
            except Exception as e:
                print(f"Error creating notification: {e}")
                pass
                
        db.session.commit()
        flash('Jadwal wawancara berhasil diperbarui.', 'success')
        return redirect(url_for('company.interviews'))
        
    # Parse format and notes from interview_notes
    interview_format = 'online'
    notes = ''
    if interview.interview_notes:
        parts = interview.interview_notes.split('\n', 1)
        if len(parts) > 0 and parts[0].startswith('Format: '):
            interview_format = parts[0].replace('Format: ', '').strip()
        if len(parts) > 1 and parts[1].startswith('Notes: '):
            notes = parts[1].replace('Notes: ', '').strip()
        elif len(parts) > 1:
            notes = parts[1]
            
    scheduled_at_iso = interview.scheduled_at.isoformat()[:16]
            
    return render_template(
        'company/interview_form.html', 
        application=interview.application, 
        interview=interview,
        interview_format=interview_format,
        notes=notes,
        scheduled_at_iso=scheduled_at_iso
    )

@bp.route('/interviews', methods=['GET'])
@login_required
@company_required
def interviews():
    from app.models.identity import CompanyProfile
    from app.models.internship import ApplicationInterview, InternshipApplication, Internship
    from sqlalchemy import desc
    
    profile = CompanyProfile.query.filter_by(user_account_id=current_user.id).first()
    if not profile:
        abort(404)
        
    status_filter = request.args.get('status', 'all')
    
    from app.models.lookups import InterviewStatus
    
    query = ApplicationInterview.query.join(InternshipApplication).join(Internship).join(InterviewStatus).filter(
        Internship.company_profile_id == profile.id
    )
    
    if status_filter != 'all':
        query = query.filter(InterviewStatus.status_code == status_filter)
        
    # Default order by scheduled date
    interviews = query.order_by(desc(ApplicationInterview.scheduled_at)).all()
    
    return render_template('company/interviews.html', interviews=interviews, current_status=status_filter)

@bp.route('/interviews/<int:interview_id>/status', methods=['POST'])
@login_required
@company_required
def update_interview_status(interview_id):
    from app.models.internship import ApplicationInterview
    from app.models.identity import CompanyProfile
    
    profile = CompanyProfile.query.filter_by(user_account_id=current_user.id).first()
    interview = ApplicationInterview.query.get_or_404(interview_id)
    
    # Verify ownership
    if interview.application.internship.company_profile_id != profile.id:
        abort(403)
        
    new_status = request.form.get('status')
    
    from app.models.lookups import InterviewStatus
    from datetime import datetime
    valid_status_obj = InterviewStatus.query.filter_by(status_code=new_status).first()
    
    if valid_status_obj:
        interview.interview_status_id = valid_status_obj.id
        if new_status == 'completed':
            interview.interview_completed_at = datetime.utcnow()
        db.session.commit()
        flash('Status wawancara berhasil diperbarui.', 'success')
    else:
        flash('Status tidak valid.', 'error')
        
    return redirect(url_for('company.interviews'))

# ─────────────────────────────────────────────
# Company Notifications
# ─────────────────────────────────────────────

@bp.route('/notifications', methods=['GET'])
@company_required
def notifications():
    page = request.args.get('page', 1, type=int)

    query = Notification.query.filter_by(
        recipient_user_id=current_user.id,
        deleted_at=None
    ).order_by(Notification.event_at.desc())

    pagination = query.paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'company/notifications.html',
        notifications=pagination.items,
        pagination=pagination,
        now=datetime.utcnow()
    )


@bp.route('/notifications/<int:id>/read', methods=['POST'])
@company_required
def mark_notification_read(id):
    notif = Notification.query.filter_by(
        id=id,
        recipient_user_id=current_user.id,
        deleted_at=None
    ).first_or_404()

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.utcnow()
        db.session.commit()

    return redirect(url_for('company.notifications'))


@bp.route('/notifications/read-all', methods=['POST'])
@company_required
def mark_all_notifications_read():
    unread_notifs = Notification.query.filter_by(
        recipient_user_id=current_user.id,
        is_read=False,
        deleted_at=None
    ).all()

    now = datetime.utcnow()
    for notif in unread_notifs:
        notif.is_read = True
        notif.read_at = now

    db.session.commit()
    flash('Semua notifikasi telah ditandai sebagai dibaca.', 'success')
    return redirect(url_for('company.notifications'))
