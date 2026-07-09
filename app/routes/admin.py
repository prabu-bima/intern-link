from flask import Blueprint
from app.utils.decorators import admin_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@admin_required
def dashboard():
    return '''
    <h1>Admin Dashboard Placeholder</h1>
    <a href="/auth/logout">Logout</a>
    '''
