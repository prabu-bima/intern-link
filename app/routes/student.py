from flask import Blueprint, render_template
from app.utils.decorators import student_required

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/dashboard')
@student_required
def dashboard():
    return '''
    <h1>Student Dashboard Placeholder</h1>
    <a href="/auth/logout">Logout</a>
    '''
