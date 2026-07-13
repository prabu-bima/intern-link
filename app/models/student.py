from app.extensions import db
from datetime import datetime

class StudentEducationRecord(db.Model):
    __tablename__ = 'student_education_record'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    degree_name = db.Column(db.String(100), nullable=False)
    field_of_study = db.Column(db.String(100), nullable=False)
    institution_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    grade = db.Column(db.String(20), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('education_records', lazy=True))

class StudentSkill(db.Model):
    __tablename__ = 'student_skill'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    proficiency_level = db.Column(db.String(50), nullable=True) # e.g. Beginner, Intermediate, Expert
    years_experience = db.Column(db.Integer, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('skills', lazy=True))
    skill = db.relationship('Skill')

class StudentTechStackItem(db.Model):
    __tablename__ = 'student_tech_stack_item'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    tech_stack_item_id = db.Column(db.Integer, db.ForeignKey('tech_stack_item.id'), nullable=False)
    proficiency_level = db.Column(db.String(50), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('tech_stack_items', lazy=True))
    tech_stack_item = db.relationship('TechStackItem')

class StudentExperience(db.Model):
    __tablename__ = 'student_experience'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    organization_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('experiences', lazy=True))

class StudentOrganization(db.Model):
    __tablename__ = 'student_organization'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    organization_name = db.Column(db.String(200), nullable=False)
    role_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('organizations', lazy=True))

class StudentCertificate(db.Model):
    __tablename__ = 'student_certificate'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    certificate_title = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    credential_url = db.Column(db.String(500), nullable=True)
    certificate_file_id = db.Column(db.Integer, db.ForeignKey('file_asset.id'), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('certificates', lazy=True))
    certificate_file = db.relationship('FileAsset', foreign_keys=[certificate_file_id])

class StudentPortfolio(db.Model):
    __tablename__ = 'student_portfolio'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    portfolio_title = db.Column(db.String(200), nullable=False)
    portfolio_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('portfolios', lazy=True))

class StudentGithubProfile(db.Model):
    __tablename__ = 'student_github_profile'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), unique=True, nullable=False)
    github_username = db.Column(db.String(100), nullable=False)
    github_url = db.Column(db.String(255), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('github_profile', uselist=False))

class StudentLinkedinProfile(db.Model):
    __tablename__ = 'student_linkedin_profile'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), unique=True, nullable=False)
    linkedin_url = db.Column(db.String(255), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('linkedin_profile', uselist=False))

class StudentCvVersion(db.Model):
    __tablename__ = 'student_cv_version'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    file_asset_id = db.Column(db.Integer, db.ForeignKey('file_asset.id'), nullable=False)
    version_no = db.Column(db.Integer, nullable=False, default=1)
    is_current = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('cv_versions', lazy=True))
    cv_file = db.relationship('FileAsset', foreign_keys=[file_asset_id])
