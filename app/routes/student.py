from flask import Blueprint, render_template
from flask_login import current_user
from app.utils.decorators import student_required
from app.models.internship import InternshipApplication, SavedInternship, Internship
from app.models.system import Notification
from app.models.lookups import ApplicationStatus, InternshipLifecycleStatus
from app.extensions import db

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/dashboard')
@student_required
def dashboard():
    # Make sure we have a student profile
    if not current_user.student_profile:
        # Failsafe if profile wasn't created
        profile_completeness = 0
        total_applications = 0
        upcoming_interviews = 0
        saved_internships_count = 0
        status_counts = {}
    else:
        # 1. Total Applications
        total_applications = InternshipApplication.query.filter_by(student_profile_id=current_user.student_profile.id).count()
        
        # 2. Upcoming Interviews
        interview_status = ApplicationStatus.query.filter_by(status_name='Interview').first()
        upcoming_interviews = 0
        if interview_status:
            upcoming_interviews = InternshipApplication.query.filter_by(
                student_profile_id=current_user.student_profile.id,
                application_status_id=interview_status.id
            ).count()
            
        # 3. Saved Internships
        saved_internships_count = SavedInternship.query.filter_by(student_profile_id=current_user.student_profile.id).count()
        
        # 4. Profile Completeness Calculation
        profile = current_user.student_profile
        completeness = 20 # Base for having an account
        if profile.bio: completeness += 20
        if profile.phone_number: completeness += 10
        if profile.date_of_birth: completeness += 10
        if profile.education_records: completeness += 20
        if profile.skills or profile.tech_stack_items: completeness += 20
        profile_completeness = min(100, completeness)
        
        # 5. Application Status Pipeline
        status_counts = {
            'submitted': 0,
            'under_review': 0,
            'interview': 0,
            'accepted': 0,
            'rejected': 0
        }
        applications = InternshipApplication.query.filter_by(student_profile_id=current_user.student_profile.id).all()
        for app in applications:
            status_name = app.application_status.status_name.lower().replace(' ', '_')
            if status_name in status_counts:
                status_counts[status_name] += 1
                
    # 6. Latest Internships
    active_lifecycle = InternshipLifecycleStatus.query.filter(InternshipLifecycleStatus.status_name.ilike('%active%')).first()
    latest_internships = []
    if active_lifecycle:
        latest_internships = Internship.query.filter_by(lifecycle_status_id=active_lifecycle.id)\
            .order_by(Internship.id.desc()).limit(5).all()
            
    # 7. Notifications
    notifications = Notification.query.filter_by(recipient_user_id=current_user.id, is_read=False)\
        .order_by(Notification.event_at.desc()).limit(5).all()
        
    return render_template(
        'student/dashboard.html',
        total_applications=total_applications,
        upcoming_interviews=upcoming_interviews,
        saved_internships_count=saved_internships_count,
        profile_completeness=profile_completeness,
        status_counts=status_counts,
        latest_internships=latest_internships,
        notifications=notifications
    )
