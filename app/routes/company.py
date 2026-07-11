from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
from app.utils.decorators import company_required
from app.models.company import CompanyVerification
from app.models.internship import Internship, InternshipApplication
from app.models.lookups import InternshipLifecycleStatus, InternshipModerationStatus, ApplicationStatus
from app.extensions import db
from sqlalchemy import func

bp = Blueprint('company', __name__, url_prefix='/company')

@bp.route('/dashboard')
@company_required
def dashboard():
    profile = current_user.company_profile
    if not profile:
        # Failsafe if company profile doesn't exist
        return "Company profile not found", 404

    # 1. Company Verification Status
    verification = CompanyVerification.query.filter_by(
        company_profile_id=profile.id
    ).order_by(CompanyVerification.id.desc()).first()

    # 2. Job Statistics
    # Total postings
    total_jobs = Internship.query.filter_by(company_profile_id=profile.id).filter(Internship.deleted_at.is_(None)).count()
    
    # Pre-fetch status codes to easily count
    active_lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='active').first()
    closed_lifecycle = InternshipLifecycleStatus.query.filter_by(status_code='closed').first()
    pending_moderation = InternshipModerationStatus.query.filter_by(status_code='pending').first()

    active_jobs = Internship.query.filter_by(
        company_profile_id=profile.id, 
        lifecycle_status_id=active_lifecycle.id if active_lifecycle else 0
    ).filter(Internship.deleted_at.is_(None)).count()

    closed_jobs = Internship.query.filter_by(
        company_profile_id=profile.id, 
        lifecycle_status_id=closed_lifecycle.id if closed_lifecycle else 0
    ).filter(Internship.deleted_at.is_(None)).count()

    pending_jobs = Internship.query.filter_by(
        company_profile_id=profile.id,
        moderation_status_id=pending_moderation.id if pending_moderation else 0
    ).filter(Internship.deleted_at.is_(None)).count()

    # 3. Applicant Statistics
    # Total applicants
    total_applicants = InternshipApplication.query.join(Internship).filter(
        Internship.company_profile_id == profile.id
    ).filter(InternshipApplication.deleted_at.is_(None)).count()
    
    # Applicants by status
    # query: SELECT status.status_code, status.status_name, COUNT(app.id) FROM application_status 
    # LEFT JOIN internship_application app ON ... 
    # We can just group by application_status_id.
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

    # 4. Active Jobs list (limit 5)
    active_jobs_list = Internship.query.filter_by(
        company_profile_id=profile.id,
        lifecycle_status_id=active_lifecycle.id if active_lifecycle else 0
    ).filter(Internship.deleted_at.is_(None)).order_by(Internship.id.desc()).limit(5).all()

    # 5. Latest Applicants feed (limit 5)
    latest_applicants = InternshipApplication.query.join(Internship).filter(
        Internship.company_profile_id == profile.id
    ).filter(InternshipApplication.deleted_at.is_(None)).order_by(InternshipApplication.submitted_at.desc()).limit(5).all()

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
