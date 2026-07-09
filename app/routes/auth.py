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
            role='student',
            display_name=form.full_name.data
        )
        db.session.add(user)
        db.session.flush() # So we can get user.id for the profile
        
        # Create StudentProfile
        from app.models.identity import StudentProfile
        profile = StudentProfile(
            user_account_id=user.id
        )
        db.session.add(profile)
        db.session.flush()

        # Create StudentEducationRecord for University and Major
        from app.models.student import StudentEducationRecord
        from datetime import date
        education = StudentEducationRecord(
            student_profile_id=profile.id,
            institution_name=form.university_name.data,
            field_of_study=form.major.data,
            degree_name='S1', # Default value since it's not in the form
            start_date=date.today() # Default value since it's not in the form
        )
        db.session.add(education)
        
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
            role='company',
            display_name=form.company_name.data
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

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('guest.index'))

    from app.forms.auth import LoginForm
    from werkzeug.security import check_password_hash
    from flask_login import login_user

    form = LoginForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            # Cek status akun jika direlasikan (Banned/Disabled)
            if user.status and user.status.status_name != 'Active':
                flash('Akun Anda saat ini dinonaktifkan. Silakan hubungi admin.', 'danger')
                return redirect(url_for('auth.login'))
                
            # Cek verifikasi perusahaan
            if user.role == 'company' and user.company_profile:
                if user.company_profile.verifications:
                    # Ambil record verifikasi terakhir
                    latest_verification = user.company_profile.verifications[-1]
                    if latest_verification.verification_status.status_name == 'Pending':
                        flash('Akun perusahaan Anda belum diverifikasi. Akses beberapa fitur mungkin dibatasi.', 'warning')
            
            login_user(user, remember=form.remember_me.data)
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user.role == 'student':
                    next_page = url_for('student.dashboard')
                elif user.role == 'company':
                    next_page = url_for('company.dashboard')
                elif user.role == 'admin':
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('guest.index')
                    
            return redirect(next_page)
            
        flash('Email atau kata sandi tidak valid.', 'danger')
        
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
    return redirect(url_for('guest.index'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('guest.index'))
        
    from app.forms.auth import ForgotPasswordForm
    from itsdangerous import URLSafeTimedSerializer
    from flask import current_app
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter_by(email=form.email.data).first()
        if user:
            # Generate token
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Simulate email sending (development)
            print(f"\n=== SIMULASI PENGIRIMAN EMAIL RESET PASSWORD ===")
            print(f"Kepada: {user.email}")
            print(f"Subjek: Atur Ulang Kata Sandi Anda")
            print(f"Tautan: {reset_url}")
            print(f"================================================\n")
            
            flash('Tautan untuk mengatur ulang kata sandi telah dikirim ke email Anda. (Cek konsol server untuk melihat tautan!)', 'info')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/forgot_password.html', form=form)

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('guest.index'))
        
    from app.forms.auth import ResetPasswordForm
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
    from flask import current_app
    from werkzeug.security import generate_password_hash
    
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # Token berlaku selama 1 jam (3600 detik)
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('Tautan reset kata sandi sudah kedaluwarsa. Silakan minta tautan baru.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('Tautan reset kata sandi tidak valid.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = UserAccount.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Kata sandi berhasil diatur ulang. Silakan masuk menggunakan kata sandi baru Anda.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/reset_password.html', form=form)
