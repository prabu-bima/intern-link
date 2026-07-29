from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(role_name):
    """
    Decorator to require a specific role (or list of roles) for a view.
    If the user is not authenticated, let Flask-Login handle it.
    If the user does not have the required role, flash a message and redirect to home.
    Also checks if user account is still active — auto-logout if disabled/suspended.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.extensions import login_manager
            
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            
            # Check if account is still active (nonaktif/suspended → auto-logout)
            from app.models.lookups import UserAccountStatus
            if current_user.account_status_id is not None:
                user_status = UserAccountStatus.query.get(current_user.account_status_id)
                if user_status and user_status.status_code != 'active':
                    from flask_login import logout_user
                    logout_user()
                    flash('Akun Anda telah dinonaktifkan. Silakan hubungi admin.', 'error')
                    return redirect(url_for('auth.login'))
            
            roles = [role_name] if isinstance(role_name, str) else role_name
            if current_user.role not in roles:
                flash('Akses ditolak. Anda tidak memiliki izin untuk melihat halaman ini.', 'danger')
                return redirect(url_for('guest.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def student_required(f):
    return role_required('student')(f)

def company_required(f):
    return role_required('company')(f)

def admin_required(f):
    return role_required('admin')(f)
