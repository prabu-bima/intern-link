from app.extensions import db

class UserAccountStatus(db.Model):
    __tablename__ = 'user_account_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status_name = db.Column(db.String(100), nullable=False)

class CompanyVerificationStatus(db.Model):
    __tablename__ = 'company_verification_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status_name = db.Column(db.String(100), nullable=False)

class InternshipLifecycleStatus(db.Model):
    __tablename__ = 'internship_lifecycle_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status_name = db.Column(db.String(100), nullable=False)

class InternshipModerationStatus(db.Model):
    __tablename__ = 'internship_moderation_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status_name = db.Column(db.String(100), nullable=False)

class ApplicationStatus(db.Model):
    __tablename__ = 'application_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status_name = db.Column(db.String(100), nullable=False)

class InterviewStatus(db.Model):
    __tablename__ = 'interview_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status_name = db.Column(db.String(100), nullable=False)

class NotificationType(db.Model):
    __tablename__ = 'notification_type'
    id = db.Column(db.Integer, primary_key=True)
    type_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    type_name = db.Column(db.String(100), nullable=False)

class ReportType(db.Model):
    __tablename__ = 'report_type'
    id = db.Column(db.Integer, primary_key=True)
    type_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    type_name = db.Column(db.String(100), nullable=False)

class AISkillMatchItemRole(db.Model):
    __tablename__ = 'ai_skill_match_item_role'
    id = db.Column(db.Integer, primary_key=True)
    role_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    role_name = db.Column(db.String(100), nullable=False)
