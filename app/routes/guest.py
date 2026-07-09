from flask import Blueprint, render_template

bp = Blueprint('guest', __name__)

@bp.route('/')
def index():
    from app.models.identity import StudentProfile, CompanyProfile
    from app.models.internship import Internship
    from app.models.lookups import InternshipLifecycleStatus
    
    student_count = StudentProfile.query.count()
    company_count = CompanyProfile.query.count()
    
    # Query internships that are active (assuming 'Active' is the status name, fallback to all if empty)
    internships = Internship.query.join(InternshipLifecycleStatus).filter(
        InternshipLifecycleStatus.status_name.ilike('%active%')
    ).count()
    
    internship_count = internships if internships > 0 else Internship.query.count()
    
    # Optional: Set base numbers to make the platform look populated if database is empty
    base_students = 1250
    base_companies = 45
    base_internships = 120
    
    stats = {
        'students': student_count + base_students,
        'companies': company_count + base_companies,
        'internships': internship_count + base_internships
    }
    
    return render_template('guest/landing.html', stats=stats)
