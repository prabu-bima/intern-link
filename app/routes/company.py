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
