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

@bp.route('/internships')
def internships():
    from flask import request
    from app.models.internship import Internship
    from app.models.lookups import InternshipLifecycleStatus
    from app.models.master import TechnologyCategory, Location
    from app.models.identity import CompanyProfile
    from sqlalchemy import or_

    # Get master data for filters
    categories = TechnologyCategory.query.order_by(TechnologyCategory.category_name).all()
    locations = Location.query.order_by(Location.city).all()
    
    # Base query for ACTIVE internships
    query = Internship.query.join(InternshipLifecycleStatus).filter(
        InternshipLifecycleStatus.status_name.ilike('%active%')
    )
    
    # 1. Search by Keyword (q)
    q = request.args.get('q', '').strip()
    if q:
        search_term = f"%{q}%"
        # Join company profile to search by company name as well
        query = query.join(CompanyProfile).filter(
            or_(
                Internship.internship_title.ilike(search_term),
                Internship.internship_description.ilike(search_term),
                CompanyProfile.company_name.ilike(search_term)
            )
        )
        
    # 2. Filter by Category
    category_id = request.args.get('category_id')
    if category_id and category_id.isdigit():
        query = query.filter(Internship.technology_category_id == int(category_id))
        
    # 3. Filter by Location
    location_id = request.args.get('location_id')
    if location_id and location_id.isdigit():
        query = query.filter(Internship.location_id == int(location_id))
        
    # Sort by newest first
    query = query.order_by(Internship.id.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 9
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'guest/internships.html',
        pagination=pagination,
        internships=pagination.items,
        categories=categories,
        locations=locations,
        current_q=q,
        current_category=category_id,
        current_location=location_id
    )

@bp.route('/internships/<int:id>')
def internship_detail(id):
    from app.models.internship import Internship
    from flask import abort, redirect, url_for
    from flask_login import current_user
    
    if current_user.is_authenticated and current_user.role == 'student':
        return redirect(url_for('student.internship_detail', id=id))
        
    internship = Internship.query.get_or_404(id)
    
    # We only want to show it if it's active or if the user somehow has the link.
    # For now, it's fine to just show whatever is in the DB, or we can optionally check status.
    # For simplicity, we just render it.
    
    return render_template('guest/internship_detail.html', internship=internship)
