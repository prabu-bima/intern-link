from flask import Blueprint, render_template
from app.utils.decorators import company_required

bp = Blueprint('company', __name__, url_prefix='/company')

@bp.route('/dashboard')
@company_required
def dashboard():
    return '''
    <h1>Company Dashboard Placeholder</h1>
    <a href="/auth/logout">Logout</a>
    '''
