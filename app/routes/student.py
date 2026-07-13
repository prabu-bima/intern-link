from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from app.utils.decorators import student_required
from app.models.internship import InternshipApplication, SavedInternship, Internship, ApplicationInterview
from app.models.system import Notification
from app.models.lookups import ApplicationStatus, InternshipLifecycleStatus, NotificationType
from app.models.student import StudentCvVersion
from app.models.master import TechnologyCategory, Location
from app.extensions import db
from datetime import datetime

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

@bp.route('/profile', methods=['GET'])
@student_required
def profile():
    from app.forms.student import PersonalInformationForm, GithubProfileForm, LinkedinProfileForm
    
    profile = current_user.student_profile
    
    # Initialize the form with current data
    personal_form = PersonalInformationForm(
        full_name=current_user.display_name,
        email=current_user.email,
        phone_number=profile.phone_number if profile else '',
        date_of_birth=profile.date_of_birth if profile else None,
        gender=profile.gender if profile else '',
        bio=profile.bio if profile else ''
    )
    
    github_form = GithubProfileForm(
        github_username=profile.github_profile.github_username if profile and profile.github_profile else '',
        github_url=profile.github_profile.github_url if profile and profile.github_profile else ''
    )
    
    linkedin_form = LinkedinProfileForm(
        linkedin_url=profile.linkedin_profile.linkedin_url if profile and profile.linkedin_profile else ''
    )
    
    return render_template(
        'student/profile.html',
        personal_form=personal_form,
        github_form=github_form,
        linkedin_form=linkedin_form
    )

@bp.route('/profile/personal', methods=['POST'])
@student_required
def update_personal_info():
    from flask import redirect, url_for, flash, request
    from app.forms.student import PersonalInformationForm
    from app.models.identity import UserAccount
    
    form = PersonalInformationForm(request.form)
    if form.validate_on_submit():
        # Check if email is being changed and if it's already taken
        if form.email.data != current_user.email:
            existing_user = UserAccount.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email address is already in use by another account.', 'error')
                return redirect(url_for('student.profile'))
                
        # Update UserAccount
        current_user.display_name = form.full_name.data
        current_user.email = form.email.data
        
        # Update StudentProfile
        if current_user.student_profile:
            current_user.student_profile.phone_number = form.phone_number.data
            current_user.student_profile.date_of_birth = form.date_of_birth.data
            current_user.student_profile.gender = form.gender.data
            current_user.student_profile.bio = form.bio.data
            
        db.session.commit()
        flash('Personal information updated successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('student.profile'))

@bp.route('/profile/photo', methods=['POST'])
@student_required
def upload_profile_photo():
    from flask import request, jsonify, current_app
    from werkzeug.utils import secure_filename
    from app.services.storage import upload_file, delete_file, get_bucket_for_purpose, validate_file
    from app.models.identity import FileAsset
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['photo']
    
    is_valid, error_msg = validate_file(file, allowed_extensions=['jpg', 'jpeg', 'png'], max_size_mb=2)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
        
    filename = secure_filename(file.filename)
    bucket_name = get_bucket_for_purpose('profile_photo')
    
    # Get file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    try:
        # Upload to Supabase
        object_key = upload_file(
            bucket_name=bucket_name,
            file_stream=file,
            file_name=filename,
            content_type=file.content_type
        )
        
        profile = current_user.student_profile
        if not profile:
            return jsonify({'error': 'Student profile not found.'}), 404
        
        # If user already has a photo, delete the old one from storage and db
        if profile.profile_photo:
            old_photo = profile.profile_photo
            profile.profile_photo_file_id = None
            db.session.flush() # Clear foreign key reference before deleting
            
            delete_file(bucket_name, old_photo.object_key)
            db.session.delete(old_photo)
            
        # Create new FileAsset
        new_photo = FileAsset(
            owner_user_id=current_user.id,
            file_purpose='profile_photo',
            storage_bucket=bucket_name,
            object_key=object_key,
            file_name=filename,
            content_type=file.content_type,
            file_size_bytes=size
        )
        db.session.add(new_photo)
        db.session.flush() # To get the ID
        
        profile.profile_photo_file_id = new_photo.id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile photo updated successfully',
            'url': new_photo.url
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading profile photo: {e}")
        return jsonify({'error': 'Failed to upload photo due to a server error.'}), 500

@bp.route('/profile/photo/delete', methods=['POST'])
@student_required
def delete_profile_photo():
    from flask import jsonify, current_app
    from app.services.storage import delete_file, get_bucket_for_purpose
    
    profile = current_user.student_profile
    if not profile or not profile.profile_photo:
        return jsonify({'error': 'No profile photo found.'}), 404
        
    try:
        old_photo = profile.profile_photo
        bucket_name = get_bucket_for_purpose('profile_photo')
        
        # Clear foreign key reference
        profile.profile_photo_file_id = None
        db.session.flush()
        
        delete_file(bucket_name, old_photo.object_key)
        db.session.delete(old_photo)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile photo deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting profile photo: {e}")
        return jsonify({'error': 'Failed to delete photo due to a server error.'}), 500

@bp.route('/profile/education', methods=['GET'])
@student_required
def get_educations():
    from flask import jsonify, request
    from app.models.student import StudentEducationRecord
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    edu_id = request.args.get('id', type=int)
    if edu_id:
        record = StudentEducationRecord.query.filter_by(id=edu_id, student_profile_id=profile.id).first()
        if not record:
            return jsonify({'error': 'Education record not found.'}), 404
        return jsonify({
            'id': record.id,
            'institution_name': record.institution_name,
            'field_of_study': record.field_of_study,
            'degree_name': record.degree_name,
            'start_date': record.start_date.isoformat() if record.start_date else '',
            'end_date': record.end_date.isoformat() if record.end_date else '',
            'grade': record.grade
        })
        
    records = StudentEducationRecord.query.filter_by(student_profile_id=profile.id).order_by(StudentEducationRecord.start_date.desc()).all()
    return jsonify([{
        'id': r.id,
        'institution_name': r.institution_name,
        'field_of_study': r.field_of_study,
        'degree_name': r.degree_name,
        'start_date': r.start_date.isoformat() if r.start_date else '',
        'end_date': r.end_date.isoformat() if r.end_date else '',
        'grade': r.grade
    } for r in records])

@bp.route('/profile/education', methods=['POST'])
@student_required
def add_education():
    from flask import request, jsonify
    from app.forms.student import EducationForm
    from app.models.student import StudentEducationRecord
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    form = EducationForm(request.form)
    if form.validate_on_submit():
        new_record = StudentEducationRecord(
            student_profile_id=profile.id,
            institution_name=form.institution_name.data,
            field_of_study=form.field_of_study.data,
            degree_name=form.degree_name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            grade=form.grade.data
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Education record added successfully.'})
    
    return jsonify({'error': 'Validation failed.', 'errors': form.errors}), 400

@bp.route('/profile/education/<int:id>', methods=['POST'])
@student_required
def edit_education(id):
    from flask import request, jsonify
    from app.forms.student import EducationForm
    from app.models.student import StudentEducationRecord
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentEducationRecord.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Education record not found.'}), 404
        
    form = EducationForm(request.form)
    if form.validate_on_submit():
        record.institution_name = form.institution_name.data
        record.field_of_study = form.field_of_study.data
        record.degree_name = form.degree_name.data
        record.start_date = form.start_date.data
        record.end_date = form.end_date.data
        record.grade = form.grade.data
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Education record updated successfully.'})
        
    return jsonify({'error': 'Validation failed.', 'errors': form.errors}), 400

@bp.route('/profile/education/<int:id>/delete', methods=['POST'])
@student_required
def delete_education(id):
    from flask import jsonify
    from app.models.student import StudentEducationRecord
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentEducationRecord.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Education record not found.'}), 404
        
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Education record deleted successfully.'})

@bp.route('/profile/skills/options', methods=['GET'])
@student_required
def get_skills_options():
    from flask import jsonify
    from app.models.master import Skill
    
    skills = Skill.query.order_by(Skill.skill_name.asc()).all()
    return jsonify([{
        'id': s.id,
        'skill_name': s.skill_name
    } for s in skills])

@bp.route('/profile/skills', methods=['GET'])
@student_required
def get_student_skills():
    from flask import jsonify
    from app.models.student import StudentSkill
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    records = StudentSkill.query.filter_by(student_profile_id=profile.id).all()
    return jsonify([{
        'id': r.id,
        'skill_id': r.skill_id,
        'skill_name': r.skill.skill_name if r.skill else '',
        'proficiency_level': r.proficiency_level
    } for r in records])

@bp.route('/profile/skills', methods=['POST'])
@student_required
def add_student_skill():
    from flask import request, jsonify
    from app.forms.student import StudentSkillForm
    from app.models.student import StudentSkill
    from app.models.master import Skill
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    form = StudentSkillForm(request.form)
    # Populate choices for validation
    form.skill_id.choices = [(s.id, s.skill_name) for s in Skill.query.all()]
    
    if form.validate_on_submit():
        # Check if already exists
        existing = StudentSkill.query.filter_by(student_profile_id=profile.id, skill_id=form.skill_id.data).first()
        if existing:
            return jsonify({'error': 'Keahlian ini sudah ditambahkan sebelumnya.'}), 400
            
        new_record = StudentSkill(
            student_profile_id=profile.id,
            skill_id=form.skill_id.data,
            proficiency_level=form.proficiency_level.data
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Skill added successfully.'})
    
    return jsonify({'error': 'Validation failed.', 'errors': form.errors}), 400

@bp.route('/profile/skills/<int:id>/delete', methods=['POST'])
@student_required
def delete_student_skill(id):
    from flask import jsonify
    from app.models.student import StudentSkill
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentSkill.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Skill record not found.'}), 404
        
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Skill deleted successfully.'})

@bp.route('/profile/tech-stack/options', methods=['GET'])
@student_required
def get_tech_stack_options():
    from flask import jsonify
    from app.models.master import TechStackItem
    
    items = TechStackItem.query.order_by(TechStackItem.tech_stack_name.asc()).all()
    return jsonify([{
        'id': i.id,
        'tech_stack_name': i.tech_stack_name
    } for i in items])

@bp.route('/profile/tech-stack', methods=['GET'])
@student_required
def get_student_tech_stack():
    from flask import jsonify
    from app.models.student import StudentTechStackItem
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    records = StudentTechStackItem.query.filter_by(student_profile_id=profile.id).all()
    return jsonify([{
        'id': r.id,
        'tech_stack_item_id': r.tech_stack_item_id,
        'tech_stack_name': r.tech_stack_item.tech_stack_name if r.tech_stack_item else '',
        'proficiency_level': r.proficiency_level
    } for r in records])

@bp.route('/profile/tech-stack', methods=['POST'])
@student_required
def add_student_tech_stack():
    from flask import request, jsonify
    from app.forms.student import StudentTechStackItemForm
    from app.models.student import StudentTechStackItem
    from app.models.master import TechStackItem
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    form = StudentTechStackItemForm(request.form)
    # Populate choices for validation
    form.tech_stack_item_id.choices = [(i.id, i.tech_stack_name) for i in TechStackItem.query.all()]
    
    if form.validate_on_submit():
        # Check if already exists
        existing = StudentTechStackItem.query.filter_by(student_profile_id=profile.id, tech_stack_item_id=form.tech_stack_item_id.data).first()
        if existing:
            return jsonify({'error': 'Tech stack ini sudah ditambahkan sebelumnya.'}), 400
            
        new_record = StudentTechStackItem(
            student_profile_id=profile.id,
            tech_stack_item_id=form.tech_stack_item_id.data,
            proficiency_level=form.proficiency_level.data
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tech stack added successfully.'})
    
    return jsonify({'error': 'Validation failed.', 'errors': form.errors}), 400

@bp.route('/profile/tech-stack/<int:id>/delete', methods=['POST'])
@student_required
def delete_student_tech_stack(id):
    from flask import jsonify
    from app.models.student import StudentTechStackItem
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentTechStackItem.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Tech stack record not found.'}), 404
        
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Tech stack deleted successfully.'})

@bp.route('/profile/experience', methods=['GET'])
@student_required
def get_experience():
    from flask import request, jsonify
    from app.models.student import StudentExperience
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    exp_id = request.args.get('id', type=int)
    if exp_id:
        record = StudentExperience.query.filter_by(id=exp_id, student_profile_id=profile.id).first()
        if not record:
            return jsonify({'error': 'Experience not found.'}), 404
        return jsonify({
            'id': record.id,
            'title': record.title,
            'organization_name': record.organization_name,
            'description': record.description,
            'start_date': record.start_date.strftime('%Y-%m-%d') if record.start_date else '',
            'end_date': record.end_date.strftime('%Y-%m-%d') if record.end_date else ''
        })
        
    records = StudentExperience.query.filter_by(student_profile_id=profile.id).order_by(StudentExperience.start_date.desc()).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'organization_name': r.organization_name,
        'description': r.description,
        'start_date': r.start_date.strftime('%Y-%m-%d') if r.start_date else '',
        'end_date': r.end_date.strftime('%Y-%m-%d') if r.end_date else ''
    } for r in records])

@bp.route('/profile/experience', methods=['POST'])
@bp.route('/profile/experience/<int:id>', methods=['POST'])
@student_required
def save_experience(id=None):
    from flask import request, jsonify
    from app.forms.student import ExperienceForm
    from app.models.student import StudentExperience
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    form = ExperienceForm(request.form)
    if form.validate_on_submit():
        if id:
            record = StudentExperience.query.filter_by(id=id, student_profile_id=profile.id).first()
            if not record:
                return jsonify({'error': 'Experience not found.'}), 404
        else:
            record = StudentExperience(student_profile_id=profile.id)
            db.session.add(record)
            
        record.organization_name = form.organization_name.data
        record.title = form.title.data
        record.start_date = form.start_date.data
        record.end_date = form.end_date.data if form.end_date.data else None
        record.description = form.description.data
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Experience saved successfully.'})
        
    return jsonify({'error': 'Validation failed', 'errors': form.errors}), 400

@bp.route('/profile/experience/<int:id>/delete', methods=['POST'])
@student_required
def delete_experience(id):
    from flask import jsonify
    from app.models.student import StudentExperience
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentExperience.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Experience not found.'}), 404
        
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Experience deleted successfully.'})

@bp.route('/profile/organization', methods=['GET'])
@student_required
def get_organizations():
    from flask import request, jsonify
    from app.models.student import StudentOrganization
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    org_id = request.args.get('id', type=int)
    if org_id:
        record = StudentOrganization.query.filter_by(id=org_id, student_profile_id=profile.id).first()
        if not record:
            return jsonify({'error': 'Organization not found.'}), 404
        return jsonify({
            'id': record.id,
            'organization_name': record.organization_name,
            'role_title': record.role_title,
            'description': record.description,
            'start_date': record.start_date.strftime('%Y-%m-%d') if record.start_date else '',
            'end_date': record.end_date.strftime('%Y-%m-%d') if record.end_date else ''
        })
        
    records = StudentOrganization.query.filter_by(student_profile_id=profile.id).order_by(StudentOrganization.start_date.desc()).all()
    return jsonify([{
        'id': r.id,
        'organization_name': r.organization_name,
        'role_title': r.role_title,
        'description': r.description,
        'start_date': r.start_date.strftime('%Y-%m-%d') if r.start_date else '',
        'end_date': r.end_date.strftime('%Y-%m-%d') if r.end_date else ''
    } for r in records])

@bp.route('/profile/organization', methods=['POST'])
@bp.route('/profile/organization/<int:id>', methods=['POST'])
@student_required
def save_organization(id=None):
    from flask import request, jsonify
    from app.forms.student import OrganizationForm
    from app.models.student import StudentOrganization
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    form = OrganizationForm(request.form)
    if form.validate_on_submit():
        if id:
            record = StudentOrganization.query.filter_by(id=id, student_profile_id=profile.id).first()
            if not record:
                return jsonify({'error': 'Organization not found.'}), 404
        else:
            record = StudentOrganization(student_profile_id=profile.id)
            db.session.add(record)
            
        record.organization_name = form.organization_name.data
        record.role_title = form.role_title.data
        record.start_date = form.start_date.data
        record.end_date = form.end_date.data if form.end_date.data else None
        record.description = form.description.data
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Organization saved successfully.'})
        
    return jsonify({'error': 'Validation failed', 'errors': form.errors}), 400

@bp.route('/profile/organization/<int:id>/delete', methods=['POST'])
@student_required
def delete_organization(id):
    from flask import jsonify
    from app.models.student import StudentOrganization
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentOrganization.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Organization not found.'}), 404
        
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Organization deleted successfully.'})


@bp.route('/profile/certificates', methods=['GET'])
@student_required
def get_certificates():
    from flask import request, jsonify
    from app.models.student import StudentCertificate

    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404

    cert_id = request.args.get('id', type=int)
    if cert_id:
        record = StudentCertificate.query.filter_by(id=cert_id, student_profile_id=profile.id).first()
        if not record:
            return jsonify({'error': 'Certificate not found.'}), 404
        return jsonify({
            'id': record.id,
            'certificate_title': record.certificate_title,
            'issuer': record.issuer,
            'issue_date': record.issue_date.strftime('%Y-%m-%d') if record.issue_date else '',
            'credential_url': record.credential_url,
            'has_file': record.certificate_file_id is not None,
            'file_url': record.certificate_file.url if record.certificate_file else None
        })

    records = StudentCertificate.query.filter_by(student_profile_id=profile.id).order_by(StudentCertificate.issue_date.desc()).all()
    return jsonify([{
        'id': r.id,
        'certificate_title': r.certificate_title,
        'issuer': r.issuer,
        'issue_date': r.issue_date.strftime('%Y-%m-%d') if r.issue_date else '',
        'credential_url': r.credential_url,
        'has_file': r.certificate_file_id is not None,
        'file_url': r.certificate_file.url if r.certificate_file else None
    } for r in records])


@bp.route('/profile/certificates', methods=['POST'])
@bp.route('/profile/certificates/<int:id>', methods=['POST'])
@student_required
def save_certificate(id=None):
    from flask import request, jsonify, current_app
    from werkzeug.utils import secure_filename
    from app.models.student import StudentCertificate
    from app.models.identity import FileAsset
    from app.services.storage import upload_file, delete_file, get_bucket_for_purpose, validate_file
    from datetime import date

    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404

    # --- Manual validation (no WTForms FileField needed) ---
    certificate_title = request.form.get('certificate_title', '').strip()
    issuer = request.form.get('issuer', '').strip()
    issue_date_str = request.form.get('issue_date', '').strip()
    credential_url = request.form.get('credential_url', '').strip()

    errors = {}
    if not certificate_title:
        errors['certificate_title'] = ['Nama sertifikat wajib diisi.']
    elif len(certificate_title) > 200:
        errors['certificate_title'] = ['Maksimal 200 karakter.']

    if not issuer:
        errors['issuer'] = ['Lembaga penerbit wajib diisi.']
    elif len(issuer) > 200:
        errors['issuer'] = ['Maksimal 200 karakter.']

    issue_date = None
    if not issue_date_str:
        errors['issue_date'] = ['Tanggal diterbitkan wajib diisi.']
    else:
        try:
            issue_date = date.fromisoformat(issue_date_str)
        except ValueError:
            errors['issue_date'] = ['Format tanggal tidak valid (YYYY-MM-DD).']

    if credential_url and len(credential_url) > 500:
        errors['credential_url'] = ['URL maksimal 500 karakter.']

    # Must provide either file or credential URL
    uploaded_file = request.files.get('certificate_file')
    has_file = uploaded_file and uploaded_file.filename
    # If editing, maybe it already has a file
    record_exists = False
    existing_file = False
    if id:
        record_exists_check = StudentCertificate.query.filter_by(id=id, student_profile_id=profile.id).first()
        if record_exists_check:
            record_exists = True
            existing_file = record_exists_check.certificate_file_id is not None

    if not credential_url and not has_file and not existing_file:
        errors['certificate_file'] = ['Anda harus mengunggah file sertifikat atau memberikan URL kredensial.']

    if errors:
        return jsonify({'error': 'Validation failed', 'errors': errors}), 400

    # --- Resolve record ---
    if id:
        record = StudentCertificate.query.filter_by(id=id, student_profile_id=profile.id).first()
        if not record:
            return jsonify({'error': 'Certificate not found.'}), 404
    else:
        record = StudentCertificate(student_profile_id=profile.id)
        db.session.add(record)

    record.certificate_title = certificate_title
    record.issuer = issuer
    record.issue_date = issue_date
    record.credential_url = credential_url if credential_url else None

    # --- Handle optional file upload ---
    uploaded_file = request.files.get('certificate_file')
    if uploaded_file and uploaded_file.filename:
        is_valid, error_msg = validate_file(
            uploaded_file,
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'],
            max_size_mb=5
        )
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        filename = secure_filename(uploaded_file.filename)
        bucket_name = get_bucket_for_purpose('certificate')

        uploaded_file.seek(0, 2)
        size = uploaded_file.tell()
        uploaded_file.seek(0)

        try:
            object_key = upload_file(
                bucket_name=bucket_name,
                file_stream=uploaded_file,
                file_name=filename,
                content_type=uploaded_file.content_type
            )

            # Delete old file if replacing
            if record.certificate_file_id:
                old_file = record.certificate_file
                old_bucket = old_file.storage_bucket
                old_key = old_file.object_key
                record.certificate_file_id = None
                db.session.flush()
                delete_file(old_bucket, old_key)
                db.session.delete(old_file)

            new_file = FileAsset(
                owner_user_id=current_user.id,
                file_purpose='certificate',
                storage_bucket=bucket_name,
                object_key=object_key,
                file_name=filename,
                content_type=uploaded_file.content_type,
                file_size_bytes=size
            )
            db.session.add(new_file)
            db.session.flush()
            record.certificate_file_id = new_file.id

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading certificate file: {e}")
            return jsonify({'error': 'Gagal mengunggah file sertifikat.'}), 500

    db.session.commit()
    return jsonify({'success': True, 'message': 'Sertifikat berhasil disimpan.'})


@bp.route('/profile/certificates/<int:id>/delete', methods=['POST'])
@student_required
def delete_certificate(id):
    from flask import jsonify, current_app
    from app.models.student import StudentCertificate
    from app.services.storage import delete_file

    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404

    record = StudentCertificate.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Certificate not found.'}), 404

    try:
        # Delete associated file from storage if exists
        if record.certificate_file_id:
            old_file = record.certificate_file
            record.certificate_file_id = None
            db.session.flush()
            delete_file(old_file.storage_bucket, old_file.object_key)
            db.session.delete(old_file)

        db.session.delete(record)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Sertifikat berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting certificate: {e}")
        return jsonify({'error': 'Gagal menghapus sertifikat.'}), 500

@bp.route('/profile/certificates/fetch-metadata', methods=['POST'])
@student_required
def fetch_certificate_metadata():
    from flask import request, jsonify
    import urllib.request
    import html.parser
    import re
    from urllib.parse import urlparse

    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL tidak valid.'}), 400

    try:
        # Validate URL format basic
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({'error': 'URL tidak valid.'}), 400

        # Build request with standard user-agent to prevent blocks
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='ignore')

        title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        desc_match = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)

        title = title_match.group(1) if title_match else ''
        description = desc_match.group(1) if desc_match else ''
        
        # Try to infer issuer from the domain or description
        issuer = parsed.netloc.replace('www.', '').split('.')[0].capitalize()
        if 'hackerrank' in parsed.netloc.lower():
            issuer = 'HackerRank'
        elif 'coursera' in parsed.netloc.lower():
            issuer = 'Coursera'
        elif 'udemy' in parsed.netloc.lower():
            issuer = 'Udemy'
        elif 'dicoding' in parsed.netloc.lower():
            issuer = 'Dicoding'

        # Special handling for HackerRank title like "Prabu Bima is now a verified Software Engineer"
        # and description like "Click here to see my certificate for React (Basic) on HackerRank"
        if issuer == 'HackerRank' and description:
            cert_name_match = re.search(r'certificate for\s+(.+?)\s+on', description, re.IGNORECASE)
            if cert_name_match:
                title = cert_name_match.group(1).strip()
            
        return jsonify({
            'success': True,
            'title': title,
            'issuer': issuer
        })

    except Exception as e:
        return jsonify({'error': f'Gagal menarik data dari URL: {str(e)}'}), 500

@bp.route('/profile/portfolio', methods=['GET'])
@student_required
def get_portfolios():
    from flask import request, jsonify
    from app.models.student import StudentPortfolio

    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404

    portfolio_id = request.args.get('id', type=int)
    if portfolio_id:
        record = StudentPortfolio.query.filter_by(id=portfolio_id, student_profile_id=profile.id).first()
        if not record:
            return jsonify({'error': 'Portfolio not found.'}), 404
        return jsonify({
            'id': record.id,
            'portfolio_title': record.portfolio_title,
            'portfolio_url': record.portfolio_url,
            'description': record.description
        })

    records = StudentPortfolio.query.filter_by(student_profile_id=profile.id).order_by(StudentPortfolio.id.desc()).all()
    return jsonify([{
        'id': r.id,
        'portfolio_title': r.portfolio_title,
        'portfolio_url': r.portfolio_url,
        'description': r.description
    } for r in records])

@bp.route('/profile/portfolio', methods=['POST'])
@bp.route('/profile/portfolio/<int:id>', methods=['POST'])
@student_required
def save_portfolio(id=None):
    from flask import request, jsonify
    from app.forms.student import PortfolioForm
    from app.models.student import StudentPortfolio
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    form = PortfolioForm(request.form)
    if form.validate_on_submit():
        if id:
            record = StudentPortfolio.query.filter_by(id=id, student_profile_id=profile.id).first()
            if not record:
                return jsonify({'error': 'Portfolio not found.'}), 404
        else:
            record = StudentPortfolio(student_profile_id=profile.id)
            db.session.add(record)
            
        record.portfolio_title = form.portfolio_title.data
        record.portfolio_url = form.portfolio_url.data
        record.description = form.description.data
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Portofolio berhasil disimpan.'})
        
    return jsonify({'error': 'Validation failed', 'errors': form.errors}), 400

@bp.route('/profile/portfolio/<int:id>/delete', methods=['POST'])
@student_required
def delete_portfolio(id):
    from flask import jsonify
    from app.models.student import StudentPortfolio
    
    profile = current_user.student_profile
    if not profile:
        return jsonify({'error': 'Student profile not found.'}), 404
        
    record = StudentPortfolio.query.filter_by(id=id, student_profile_id=profile.id).first()
    if not record:
        return jsonify({'error': 'Portfolio not found.'}), 404
        
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Portofolio berhasil dihapus.'})

@bp.route('/profile/github', methods=['POST'])
@student_required
def save_github_profile():
    from flask import request, jsonify, flash, redirect, url_for
    from app.forms.student import GithubProfileForm
    from app.models.student import StudentGithubProfile
    
    profile = current_user.student_profile
    if not profile:
        flash('Silakan lengkapi profil personal terlebih dahulu.', 'error')
        return redirect(url_for('student.profile') + '#personal')
        
    form = GithubProfileForm(request.form)
    if form.validate_on_submit():
        record = profile.github_profile
        if not record:
            record = StudentGithubProfile(student_profile_id=profile.id)
            db.session.add(record)
            
        record.github_username = form.github_username.data
        record.github_url = form.github_url.data
        
        db.session.commit()
        flash('Profil GitHub berhasil disimpan.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error pada {getattr(form, field).label.text}: {error}', 'error')
                
    return redirect(url_for('student.profile') + '#personal')

# --- CV MANAGEMENT ---

@bp.route('/cv', methods=['GET'])
@student_required
def cv_management():
    from flask import render_template
    from app.forms.student import StudentCvUploadForm
    from app.models.student import StudentCvVersion
    
    profile = current_user.student_profile
    if not profile:
        flash('Silakan lengkapi profil Anda terlebih dahulu.', 'warning')
        return redirect(url_for('student.profile'))
        
    cv_form = StudentCvUploadForm()
    
    # Get all non-deleted CV versions ordered by version_no desc
    cv_versions = StudentCvVersion.query.filter_by(
        student_profile_id=profile.id, 
        deleted_at=None
    ).order_by(StudentCvVersion.version_no.desc()).all()
    
    current_cv = next((cv for cv in cv_versions if cv.is_current), None)
    
    return render_template('student/cv.html', 
                           cv_form=cv_form, 
                           cv_versions=cv_versions,
                           current_cv=current_cv)

@bp.route('/cv/upload', methods=['POST'])
@student_required
def upload_cv():
    from flask import request, current_app, redirect, url_for, flash
    from werkzeug.utils import secure_filename
    from app.services.storage import upload_file, get_bucket_for_purpose, validate_file
    from app.models.identity import FileAsset
    from app.models.student import StudentCvVersion
    from app.forms.student import StudentCvUploadForm
    
    form = StudentCvUploadForm()
    
    if form.validate_on_submit():
        file = form.cv_file.data
        
        is_valid, error_msg = validate_file(file, allowed_extensions=['pdf'], max_size_mb=5)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('student.cv_management'))
            
        filename = secure_filename(file.filename)
        bucket_name = get_bucket_for_purpose('student_cv')
        
        # Get file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        profile = current_user.student_profile
        
        try:
            # Upload to Supabase
            object_key = upload_file(
                bucket_name=bucket_name,
                file_stream=file,
                file_name=filename,
                content_type=file.content_type
            )
            
            # Create FileAsset
            new_file_asset = FileAsset(
                owner_user_id=current_user.id,
                file_purpose='student_cv',
                storage_bucket=bucket_name,
                object_key=object_key,
                file_name=filename,
                content_type=file.content_type,
                file_size_bytes=size
            )
            db.session.add(new_file_asset)
            db.session.flush() # Get the new file asset ID
            
            # Determine new version number
            latest_cv = StudentCvVersion.query.filter_by(student_profile_id=profile.id).order_by(StudentCvVersion.version_no.desc()).first()
            new_version_no = (latest_cv.version_no + 1) if latest_cv else 1
            
            # Set all existing CVs to is_current=False
            StudentCvVersion.query.filter_by(student_profile_id=profile.id, is_current=True).update({'is_current': False})
            
            # Create new StudentCvVersion
            new_cv_version = StudentCvVersion(
                student_profile_id=profile.id,
                file_asset_id=new_file_asset.id,
                version_no=new_version_no,
                is_current=True
            )
            db.session.add(new_cv_version)
            
            db.session.commit()
            flash('CV berhasil diunggah dan diatur sebagai CV utama.', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading student CV: {e}")
            flash('Gagal mengunggah CV karena kesalahan server.', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
                
    return redirect(url_for('student.cv_management'))

@bp.route('/cv/<int:id>/delete', methods=['POST'])
@student_required
def delete_cv(id):
    from flask import current_app, redirect, url_for, flash
    from datetime import datetime
    from app.models.student import StudentCvVersion
    
    cv_version = StudentCvVersion.query.get_or_404(id)
    
    # Security check: Ensure it belongs to the current user
    if cv_version.student_profile_id != current_user.student_profile.id:
        flash('Anda tidak memiliki akses ke CV ini.', 'error')
        return redirect(url_for('student.cv_management'))
        
    try:
        cv_version.deleted_at = datetime.utcnow()
        
        if cv_version.is_current:
            cv_version.is_current = False
            # We decided in the plan to leave them with NO current CV (Option B)
            
        db.session.commit()
        flash('CV berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting student CV: {e}")
        flash('Terjadi kesalahan saat menghapus CV.', 'error')
        
    return redirect(url_for('student.cv_management'))
@bp.route('/profile/linkedin', methods=['POST'])
@student_required
def save_linkedin_profile():
    from flask import request, jsonify, flash, redirect, url_for
    from app.forms.student import LinkedinProfileForm
    from app.models.student import StudentLinkedinProfile
    
    profile = current_user.student_profile
    if not profile:
        flash('Silakan lengkapi profil personal terlebih dahulu.', 'error')
        return redirect(url_for('student.profile') + '#personal')
        
    form = LinkedinProfileForm(request.form)
    if form.validate_on_submit():
        record = profile.linkedin_profile
        if not record:
            record = StudentLinkedinProfile(student_profile_id=profile.id)
            db.session.add(record)
            
        record.linkedin_url = form.linkedin_url.data
        
        db.session.commit()
        flash('Profil LinkedIn berhasil disimpan.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error pada {getattr(form, field).label.text}: {error}', 'error')
                
    return redirect(url_for('student.profile') + '#personal')

@bp.route('/internships', methods=['GET'])
@student_required
def internships():
    q = request.args.get('q', '').strip()
    cat_id = request.args.get('cat', type=int)
    loc_id = request.args.get('loc', type=int)
    
    # 1. Base Query: Only show active/published internships
    active_status = InternshipLifecycleStatus.query.filter(InternshipLifecycleStatus.status_name.ilike('%active%')).first()
    if not active_status:
        active_status = InternshipLifecycleStatus.query.filter(InternshipLifecycleStatus.status_name.ilike('%open%')).first()
        
    query = Internship.query
    if active_status:
        query = query.filter(Internship.lifecycle_status_id == active_status.id)
    query = query.filter(Internship.deleted_at.is_(None))
    
    # 2. Search & Filter
    if q:
        search_filter = db.or_(
            Internship.internship_title.ilike(f'%{q}%'),
            Internship.internship_description.ilike(f'%{q}%')
        )
        query = query.filter(search_filter)
        
    if cat_id:
        query = query.filter(Internship.technology_category_id == cat_id)
        
    if loc_id:
        query = query.filter(Internship.location_id == loc_id)
        
    # Order by newest
    query = query.order_by(Internship.id.desc())
    internships_list = query.all()
    
    # 3. Get Saved Internships for the current user
    saved_internships = SavedInternship.query.filter_by(
        student_profile_id=current_user.student_profile.id
    ).filter(SavedInternship.deleted_at.is_(None)).all()
    saved_internship_ids = [s.internship_id for s in saved_internships]
    
    # 4. Filter Options for Dropdowns
    categories = TechnologyCategory.query.all()
    locations = Location.query.all()
    
    return render_template(
        'student/internships.html',
        internships=internships_list,
        saved_internship_ids=saved_internship_ids,
        categories=categories,
        locations=locations,
        q=q,
        cat_id=cat_id,
        loc_id=loc_id
    )

@bp.route('/internships/<int:id>/save', methods=['POST'])
@student_required
def toggle_save_internship(id):
    from datetime import datetime
    
    # Verify internship exists
    internship = Internship.query.get_or_404(id)
    profile_id = current_user.student_profile.id
    
    # Check if already saved
    saved = SavedInternship.query.filter_by(
        student_profile_id=profile_id,
        internship_id=id
    ).first()
    
    is_saved = False
    if saved:
        if saved.deleted_at:
            # Restore soft-deleted record
            saved.deleted_at = None
            is_saved = True
            msg = 'Lowongan magang berhasil disimpan'
        else:
            # Soft delete to unsave
            saved.deleted_at = datetime.utcnow()
            is_saved = False
            msg = 'Lowongan magang dihapus dari daftar simpan'
    else:
        # Create new save record
        new_save = SavedInternship(
            student_profile_id=profile_id,
            internship_id=id
        )
        db.session.add(new_save)
        is_saved = True
        msg = 'Lowongan magang berhasil disimpan'
        
    db.session.commit()
    
    if request.headers.get('Accept') == 'application/json' or request.is_json:
        return jsonify({
            'status': 'success',
            'is_saved': is_saved,
            'message': msg
        })
        
    flash(msg, 'success')
    return redirect(request.referrer or url_for('student.internships'))

@bp.route('/saved', methods=['GET'])
@student_required
def saved_internships():
    page = request.args.get('page', 1, type=int)
    profile_id = current_user.student_profile.id
    
    query = SavedInternship.query.filter_by(
        student_profile_id=profile_id
    ).filter(SavedInternship.deleted_at.is_(None)).order_by(SavedInternship.id.desc())
    
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    
    return render_template(
        'student/saved_internships.html',
        saved_items=pagination.items,
        pagination=pagination
    )

@bp.route('/internships/<int:id>', methods=['GET'])
@student_required
def internship_detail(id):
    internship = Internship.query.get_or_404(id)
    profile_id = current_user.student_profile.id
    
    # Check if saved
    saved = SavedInternship.query.filter_by(
        student_profile_id=profile_id,
        internship_id=id
    ).filter(SavedInternship.deleted_at.is_(None)).first()
    is_saved = True if saved else False
    
    # Check if applied
    application = InternshipApplication.query.filter_by(
        student_profile_id=profile_id,
        internship_id=id
    ).first()
    is_applied = True if application else False
    
    return render_template(
        'student/internship_detail.html',
        internship=internship,
        is_saved=is_saved,
        is_applied=is_applied
    )

@bp.route('/internships/<int:id>/ai-match', methods=['GET'])
@student_required
def internship_ai_match(id):
    from app.services.ai_skill_match import run_skill_match
    
    profile_id = current_user.student_profile.id
    
    # Call the robust service
    match_run = run_skill_match(profile_id, id)
    
    if not match_run:
        return jsonify({'status': 'error', 'message': 'Gagal melakukan analisis'})
        
    # Render the partial
    html = render_template('student/_ai_match_partial.html', match_run=match_run)
    
    return jsonify({
        'status': 'success',
        'html': html
    })

@bp.route('/internships/<int:id>/apply', methods=['POST'])
@student_required
def apply_internship(id):
    internship = Internship.query.get_or_404(id)
    profile_id = current_user.student_profile.id
    
    # 1. Check if student has a current CV
    current_cv = StudentCvVersion.query.filter_by(
        student_profile_id=profile_id,
        is_current=True,
        deleted_at=None
    ).first()
    
    if not current_cv:
        flash('Anda harus mengunggah CV aktif sebelum melamar magang.', 'error')
        return redirect(url_for('student.internship_detail', id=id))
        
    # 2. Check if already applied
    existing_app = InternshipApplication.query.filter_by(
        student_profile_id=profile_id,
        internship_id=id,
        deleted_at=None
    ).first()
    
    if existing_app:
        flash('Anda sudah pernah melamar posisi ini.', 'warning')
        return redirect(url_for('student.internship_detail', id=id))
        
    # 3. Create Application
    status_applied = ApplicationStatus.query.filter_by(status_code='applied').first()
    if not status_applied:
        # Fallback if not seeded
        status_applied = ApplicationStatus(status_code='applied', status_name='Applied')
        db.session.add(status_applied)
        db.session.flush()
        
    application = InternshipApplication(
        student_profile_id=profile_id,
        internship_id=id,
        application_status_id=status_applied.id,
        submitted_cv_id=current_cv.file_asset_id
    )
    db.session.add(application)
    
    # 4. Notifications
    notif_type = NotificationType.query.filter_by(type_code='application').first()
    if not notif_type:
        notif_type = NotificationType(type_code='application', type_name='Application')
        db.session.add(notif_type)
        db.session.flush()
        
    # Notification for Student
    student_payload = {
        "title": "Lamaran Terkirim",
        "message": f"Lamaran Anda untuk posisi {internship.internship_title} telah berhasil dikirim.",
        "internship_id": id
    }
    notif_student = Notification(
        recipient_user_id=current_user.id,
        notification_type_id=notif_type.id,
        payload_json=student_payload
    )
    db.session.add(notif_student)
    
    # Notification for Company (if company has user_account_id)
    if internship.company_profile.user_account_id:
        company_payload = {
            "title": "Pelamar Baru",
            "message": f"Terdapat pelamar baru untuk posisi {internship.internship_title}.",
            "internship_id": id,
            "student_profile_id": profile_id
        }
        notif_company = Notification(
            recipient_user_id=internship.company_profile.user_account_id,
            notification_type_id=notif_type.id,
            payload_json=company_payload
        )
        db.session.add(notif_company)
        
    db.session.commit()
    
    flash('Berhasil mengirim lamaran magang!', 'success')
    return redirect(url_for('student.internship_detail', id=id))

@bp.route('/applications', methods=['GET'])
@student_required
def applications():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    
    query = InternshipApplication.query.filter_by(
        student_profile_id=current_user.student_profile.id,
        deleted_at=None
    )
    
    if status_filter:
        status_lookup = ApplicationStatus.query.filter_by(status_code=status_filter).first()
        if status_lookup:
            query = query.filter_by(application_status_id=status_lookup.id)
            
    # Order by most recently submitted
    query = query.order_by(InternshipApplication.submitted_at.desc())
    
    pagination = query.paginate(page=page, per_page=10, error_out=False)
    applications = pagination.items
    
    # Get all possible statuses for the filter dropdown in correct order
    statuses = ApplicationStatus.query.order_by(ApplicationStatus.id).all()
    
    return render_template(
        'student/applications.html',
        applications=applications,
        pagination=pagination,
        statuses=statuses,
        current_status=status_filter
    )

@bp.route('/applications/<int:id>', methods=['GET'])
@student_required
def application_detail(id):
    application = InternshipApplication.query.filter_by(
        id=id,
        student_profile_id=current_user.student_profile.id,
        deleted_at=None
    ).first_or_404()
    
    # Check if there's an interview
    interview = ApplicationInterview.query.filter_by(
        internship_application_id=application.id,
        deleted_at=None
    ).first()
    
    return render_template(
        'student/application_detail.html',
        application=application,
        interview=interview
    )

@bp.route('/applications/<int:id>/cancel', methods=['POST'])
@student_required
def cancel_application(id):
    application = InternshipApplication.query.filter_by(
        id=id,
        student_profile_id=current_user.student_profile.id,
        deleted_at=None
    ).first_or_404()
    
    # Validate status allows cancellation
    cancellable_statuses = ['applied', 'reviewing', 'shortlisted']
    if application.application_status.status_code not in cancellable_statuses:
        flash('Lamaran ini tidak dapat dibatalkan pada tahap ini.', 'error')
        return redirect(url_for('student.application_detail', id=id))
        
    # Update status to withdrawn
    withdrawn_status = ApplicationStatus.query.filter_by(status_code='withdrawn').first()
    application.application_status_id = withdrawn_status.id
    application.canceled_at = datetime.utcnow()
    
    # Send notification to company
    if application.internship.company_profile.user_account_id:
        notif_type = NotificationType.query.filter_by(type_code='application').first()
        company_payload = {
            "title": "Pelamar Membatalkan Lamaran",
            "message": f"Pelamar untuk posisi {application.internship.internship_title} telah membatalkan lamarannya.",
            "internship_id": application.internship.id,
            "student_profile_id": current_user.student_profile.id
        }
        notif_company = Notification(
            recipient_user_id=application.internship.company_profile.user_account_id,
            notification_type_id=notif_type.id,
            payload_json=company_payload
        )
        db.session.add(notif_company)
        
    db.session.commit()
    flash('Lamaran berhasil dibatalkan.', 'success')
    return redirect(url_for('student.application_detail', id=id))

@bp.context_processor
def inject_unread_notifications_count():
    if current_user.is_authenticated and current_user.role == 'student':
        count = Notification.query.filter_by(
            recipient_user_id=current_user.id,
            is_read=False,
            deleted_at=None
        ).count()
        return dict(unread_notifications_count=count)
    return dict(unread_notifications_count=0)

@bp.route('/notifications', methods=['GET'])
@student_required
def notifications():
    page = request.args.get('page', 1, type=int)
    
    query = Notification.query.filter_by(
        recipient_user_id=current_user.id,
        deleted_at=None
    ).order_by(Notification.event_at.desc())
    
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    
    return render_template(
        'student/notifications.html',
        notifications=pagination.items,
        pagination=pagination,
        now=datetime.utcnow()
    )

@bp.route('/notifications/<int:id>/read', methods=['POST'])
@student_required
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
        
    return redirect(url_for('student.notifications'))

@bp.route('/notifications/read-all', methods=['POST'])
@student_required
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
    return redirect(url_for('student.notifications'))

