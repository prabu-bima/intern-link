from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from flask_login import login_user, current_user

from app.extensions import db
from app.forms.auth import StudentRegistrationForm
from app.models.identity import UserAccount, StudentProfile

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register')
def register():
    """Selection page for registration (Student or Company)."""
    if current_user.is_authenticated:
        return redirect(url_for('guest.index'))
    return render_template('auth/register.html')

@bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('guest.index'))

    form = StudentRegistrationForm()
    
    if form.validate_on_submit():
        # Hash the password
        hashed_password = generate_password_hash(form.password.data)
        
        # Create UserAccount
        user = UserAccount(
            email=form.email.data,
            password_hash=hashed_password,
            role='student'
        )
        db.session.add(user)
        db.session.flush() # So we can get user.id for the profile
        
        # Create StudentProfile
        profile = StudentProfile(
            user_account_id=user.id,
            full_name=form.full_name.data,
            university_name=form.university_name.data,
            major=form.major.data
        )
        db.session.add(profile)
        db.session.commit()
        
        # Auto login
        login_user(user)
        flash('Pendaftaran berhasil! Selamat datang di InternLink.', 'success')
        return redirect(url_for('student.dashboard'))
        
    return render_template('auth/register_student.html', form=form)

@bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('guest.index'))

    from app.forms.auth import CompanyRegistrationForm
    from app.models.company import CompanyVerification
    from app.models.lookups import CompanyVerificationStatus

    form = CompanyRegistrationForm()
    
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        
        # Create UserAccount
        user = UserAccount(
            email=form.email.data,
            password_hash=hashed_password,
            role='company'
        )
        db.session.add(user)
        db.session.flush()
        
        # Create CompanyProfile
        from app.models.identity import CompanyProfile
        profile = CompanyProfile(
            user_account_id=user.id,
            company_name=form.company_name.data
        )
        db.session.add(profile)
        db.session.flush()
        
        # Create Verification Record (Status Pending)
        pending_status = CompanyVerificationStatus.query.filter_by(status_name='Pending').first()
        if pending_status:
            verification = CompanyVerification(
                company_profile_id=profile.id,
                verification_status_id=pending_status.id
            )
            db.session.add(verification)
        
        db.session.commit()
        
        login_user(user)
        flash('Pendaftaran berhasil! Akun Anda sedang dalam status "Pending Verification".', 'warning')
        return redirect(url_for('company.dashboard'))
        
    return render_template('auth/register_company.html', form=form)
