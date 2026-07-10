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

@bp.route('/profile', methods=['GET'])
@student_required
def profile():
    from app.forms.student import PersonalInformationForm
    
    # Initialize the form with current data
    personal_form = PersonalInformationForm(
        full_name=current_user.display_name,
        email=current_user.email,
        phone_number=current_user.student_profile.phone_number if current_user.student_profile else '',
        date_of_birth=current_user.student_profile.date_of_birth if current_user.student_profile else None,
        gender=current_user.student_profile.gender if current_user.student_profile else '',
        bio=current_user.student_profile.bio if current_user.student_profile else ''
    )
    
    return render_template(
        'student/profile.html',
        personal_form=personal_form
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
