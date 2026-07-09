import os
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.identity import UserAccount, CompanyProfile
from app.models.master import Location, TechnologyCategory, TechStackItem, Skill
from app.models.lookups import InternshipLifecycleStatus, InternshipModerationStatus, UserAccountStatus
from app.models.internship import Internship, InternshipRequiredSkill, InternshipRequiredTechStackItem

app = create_app()

with app.app_context():
    # Ensure UserAccountStatus for Active exists
    status = UserAccountStatus.query.filter_by(status_name='Active').first()
    if not status:
        status = UserAccountStatus(status_name='Active')
        db.session.add(status)
        db.session.commit()

    # Create dummy user if not exists
    user = UserAccount.query.filter_by(email='dummycompany@example.com').first()
    if not user:
        user = UserAccount(
            role='company',
            email='dummycompany@example.com',
            password_hash='scrypt:32768:8:1$dummy',
            display_name='Dummy Tech',
            account_status_id=status.id
        )
        db.session.add(user)
        db.session.commit()
    
    # Get Location and Tech Category
    location = Location.query.first()
    if not location:
        location = Location(location_code='JKT', city='Jakarta', country='Indonesia')
        db.session.add(location)
        db.session.commit()
        
    tech_category = TechnologyCategory.query.first()
    if not tech_category:
        tech_category = TechnologyCategory(category_code='FE', category_name='Frontend Development')
        db.session.add(tech_category)
        db.session.commit()

    # Create Company Profile
    company = CompanyProfile.query.filter_by(user_account_id=user.id).first()
    if not company:
        company = CompanyProfile(
            user_account_id=user.id,
            company_name='Nusantara Tech',
            company_description='Nusantara Tech adalah perusahaan rintisan terdepan di Indonesia yang berfokus pada solusi SaaS (Software as a Service) untuk UMKM. Kami membangun ekosistem digital terintegrasi yang memudahkan pengusaha lokal mengembangkan bisnisnya.',
            address_line='Gedung Tech Tower Lt. 12, Sudirman',
            location_id=location.id,
            website_url='https://nusantara-tech.example.com'
        )
        db.session.add(company)
        db.session.commit()

    # Get statuses
    lifecycle = InternshipLifecycleStatus.query.filter(InternshipLifecycleStatus.status_name.ilike('%active%')).first()
    if not lifecycle:
        lifecycle = InternshipLifecycleStatus(status_code='ACTIVE', status_name='Active')
        db.session.add(lifecycle)
        
    moderation = InternshipModerationStatus.query.filter_by(status_name='Approved').first()
    if not moderation:
        moderation = InternshipModerationStatus(status_code='APPROVED', status_name='Approved')
        db.session.add(moderation)
    
    db.session.commit()

    # Delete existing dummy internship if exists
    existing = Internship.query.filter_by(internship_title='Frontend Developer Intern - React').first()
    if existing:
        InternshipRequiredSkill.query.filter_by(internship_id=existing.id).delete()
        InternshipRequiredTechStackItem.query.filter_by(internship_id=existing.id).delete()
        db.session.delete(existing)
        db.session.commit()

    # Create Internship
    internship = Internship(
        company_profile_id=company.id,
        technology_category_id=tech_category.id,
        location_id=location.id,
        internship_title='Frontend Developer Intern - React',
        internship_description='''
        <p>Kami sedang mencari kandidat <strong>Frontend Developer Intern</strong> yang bersemangat untuk bergabung dengan tim produk kami. Anda akan bekerja langsung dengan tim UI/UX dan Backend untuk mengembangkan antarmuka aplikasi web kami.</p>
        <br>
        <h4>Tanggung Jawab Utama:</h4>
        <ul>
            <li>Mengembangkan fitur-fitur baru pada aplikasi React.js kami.</li>
            <li>Memastikan implementasi UI sesuai dengan desain dari tim Figma.</li>
            <li>Melakukan optimasi performa <em>frontend</em> (Web Vitals).</li>
            <li>Menulis kode yang bersih dan <em>maintainable</em>.</li>
        </ul>
        <br>
        <h4>Kualifikasi:</h4>
        <ul>
            <li>Mahasiswa S1 semester 6 ke atas dari jurusan Ilmu Komputer/Informatika.</li>
            <li>Memahami fundamental HTML, CSS (TailwindCSS), dan JavaScript (ES6).</li>
            <li>Pernah membuat proyek menggunakan React.js.</li>
            <li>Bisa menggunakan Git untuk kolaborasi (<em>pull request</em>, <em>merge</em>, dsb).</li>
            <li>Mampu bekerja <i>onsite</i> / WFO (atau <em>Hybrid</em> bergantung kesepakatan).</li>
        </ul>
        ''',
        lifecycle_status_id=lifecycle.id,
        moderation_status_id=moderation.id,
        closing_at=datetime.utcnow() + timedelta(days=30)
    )
    db.session.add(internship)
    db.session.commit()

    # Add Tech Stack
    ts = TechStackItem.query.filter_by(tech_stack_name='React.js').first()
    if not ts:
        ts = TechStackItem(tech_stack_code='REACT', tech_stack_name='React.js')
        db.session.add(ts)
        db.session.commit()
    
    req_ts = InternshipRequiredTechStackItem(
        internship_id=internship.id,
        tech_stack_item_id=ts.id,
        required_level='Intermediate'
    )
    db.session.add(req_ts)

    # Add Skills
    skill = Skill.query.filter_by(skill_name='UI Implementation').first()
    if not skill:
        skill = Skill(skill_code='UI_IMPL', skill_name='UI Implementation')
        db.session.add(skill)
        db.session.commit()

    req_skill = InternshipRequiredSkill(
        internship_id=internship.id,
        skill_id=skill.id,
        required_level='Basic'
    )
    db.session.add(req_skill)
    
    db.session.commit()
    print("Seed complete! Added 'Frontend Developer Intern - React' by 'Nusantara Tech'.")
