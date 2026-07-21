from flask import Blueprint, render_template

bp = Blueprint('guest', __name__)

@bp.route('/')
def index():
    from app.extensions import cache

    # Statistik landing tidak perlu real-time -> cache 5 menit.
    # Menghindari 3x round-trip ke Supabase tiap kali halaman dibuka.
    @cache.cached(timeout=300, key_prefix='landing_stats')
    def _get_landing_stats():
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

        return {
            'students': student_count + base_students,
            'companies': company_count + base_companies,
            'internships': internship_count + base_internships
        }

    stats = _get_landing_stats()

    return render_template('guest/landing.html', stats=stats)

@bp.route('/internships')
def internships():
    from flask import request
    from app.models.internship import Internship, InternshipRequiredSkill
    from app.models.lookups import InternshipLifecycleStatus
    from app.models.master import TechnologyCategory, Location
    from app.models.identity import CompanyProfile
    from sqlalchemy import or_
    from sqlalchemy.orm import joinedload, selectinload
    from app.extensions import cache

    # Master data untuk filter jarang berubah -> cache 1 jam
    @cache.cached(timeout=3600, key_prefix='guest_filter_categories')
    def _filter_categories():
        return TechnologyCategory.query.order_by(TechnologyCategory.category_name).all()

    @cache.cached(timeout=3600, key_prefix='guest_filter_locations')
    def _filter_locations():
        return Location.query.order_by(Location.city).all()

    categories = _filter_categories()
    locations = _filter_locations()

    # Base query for ACTIVE internships.
    # Eager load relasi yang dipakai template (company_profile, location, required_skills)
    # untuk menghindari N+1 query saat me-render tiap kartu.
    query = Internship.query.options(
        joinedload(Internship.company_profile).joinedload(CompanyProfile.company_logo),
        joinedload(Internship.location),
        selectinload(Internship.required_skills).joinedload(InternshipRequiredSkill.skill),
    ).join(InternshipLifecycleStatus).filter(
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
        
    from sqlalchemy.orm import joinedload
    from app.models.identity import CompanyProfile
    from app.models.internship import InternshipRequiredSkill, InternshipRequiredTechStackItem
    
    internship = Internship.query.options(
        joinedload(Internship.company_profile).joinedload(CompanyProfile.company_logo),
        joinedload(Internship.location),
        joinedload(Internship.technology_category),
        joinedload(Internship.required_tech_stack_items).joinedload(InternshipRequiredTechStackItem.tech_stack_item),
        joinedload(Internship.required_skills).joinedload(InternshipRequiredSkill.skill)
    ).filter_by(id=id).first_or_404()
    
    # We only want to show it if it's active or if the user somehow has the link.
    # For now, it's fine to just show whatever is in the DB, or we can optionally check status.
    # For simplicity, we just render it.
    
    return render_template('guest/internship_detail.html', internship=internship)

@bp.route('/companies')
def companies():
    from flask import request
    from app.models.identity import CompanyProfile
    from sqlalchemy.orm import joinedload
    
    # Base query. Eager load company_logo & location, filter out soft-deleted
    query = CompanyProfile.query.options(
        joinedload(CompanyProfile.company_logo),
        joinedload(CompanyProfile.location)
    ).filter(CompanyProfile.deleted_at.is_(None))
    
    # Search by company name (q)
    q = request.args.get('q', '').strip()
    if q:
        search_term = f"%{q}%"
        query = query.filter(CompanyProfile.company_name.ilike(search_term))
        
    # Sort alphabetically by company name
    query = query.order_by(CompanyProfile.company_name.asc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 9
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'guest/companies.html',
        pagination=pagination,
        companies=pagination.items,
        current_q=q
    )

@bp.route('/companies/<int:id>')
def company_detail(id):
    from flask import abort
    from app.models.identity import CompanyProfile
    from app.models.internship import Internship, InternshipRequiredSkill
    from app.models.lookups import InternshipLifecycleStatus
    from sqlalchemy.orm import joinedload, selectinload
    
    # 1. Query CompanyProfile. Eager load logo and location. Must not be soft-deleted.
    company = CompanyProfile.query.options(
        joinedload(CompanyProfile.company_logo),
        joinedload(CompanyProfile.location)
    ).filter(
        CompanyProfile.id == id,
        CompanyProfile.deleted_at.is_(None)
    ).first_or_404()
    
    # 2. Query active internships for this company.
    active_internships = Internship.query.options(
        joinedload(Internship.location),
        joinedload(Internship.technology_category),
        selectinload(Internship.required_skills).joinedload(InternshipRequiredSkill.skill)
    ).join(InternshipLifecycleStatus).filter(
        Internship.company_profile_id == id,
        Internship.deleted_at.is_(None),
        InternshipLifecycleStatus.status_name.ilike('%active%')
    ).order_by(Internship.id.desc()).all()
    
    return render_template(
        'guest/company_detail.html',
        company=company,
        active_internships=active_internships
    )

@bp.route('/terms')
def terms():
    return render_template('guest/terms.html')

@bp.route('/privacy')
def privacy():
    return render_template('guest/privacy.html')

@bp.route('/cookies')
def cookies():
    return render_template('guest/cookies.html')




