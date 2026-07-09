from app.extensions import db
from datetime import datetime

class Internship(db.Model):
    __tablename__ = 'internship'
    id = db.Column(db.Integer, primary_key=True)
    company_profile_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    technology_category_id = db.Column(db.Integer, db.ForeignKey('technology_category.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    internship_title = db.Column(db.String(255), nullable=False)
    internship_description = db.Column(db.Text, nullable=False)
    lifecycle_status_id = db.Column(db.Integer, db.ForeignKey('internship_lifecycle_status.id'), nullable=False)
    moderation_status_id = db.Column(db.Integer, db.ForeignKey('internship_moderation_status.id'), nullable=False)
    closing_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    company_profile = db.relationship('CompanyProfile', backref=db.backref('internships', lazy=True))
    technology_category = db.relationship('TechnologyCategory')
    location = db.relationship('Location')
    lifecycle_status = db.relationship('InternshipLifecycleStatus')
    moderation_status = db.relationship('InternshipModerationStatus')

class InternshipRequiredSkill(db.Model):
    __tablename__ = 'internship_required_skill'
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    required_level = db.Column(db.String(50), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    internship = db.relationship('Internship', backref=db.backref('required_skills', lazy=True))
    skill = db.relationship('Skill')

class InternshipRequiredTechStackItem(db.Model):
    __tablename__ = 'internship_required_tech_stack_item'
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    tech_stack_item_id = db.Column(db.Integer, db.ForeignKey('tech_stack_item.id'), nullable=False)
    required_level = db.Column(db.String(50), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    internship = db.relationship('Internship', backref=db.backref('required_tech_stack_items', lazy=True))
    tech_stack_item = db.relationship('TechStackItem')

class InternshipApplication(db.Model):
    __tablename__ = 'internship_application'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    application_status_id = db.Column(db.Integer, db.ForeignKey('application_status.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    canceled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.Text, nullable=True)
    admin_decision_note = db.Column(db.Text, nullable=True)
    submitted_cv_id = db.Column(db.Integer, db.ForeignKey('file_asset.id'), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('applications', lazy=True))
    internship = db.relationship('Internship', backref=db.backref('applications', lazy=True))
    application_status = db.relationship('ApplicationStatus')
    submitted_cv = db.relationship('FileAsset', foreign_keys=[submitted_cv_id])

class ApplicationInterview(db.Model):
    __tablename__ = 'application_interview'
    id = db.Column(db.Integer, primary_key=True)
    internship_application_id = db.Column(db.Integer, db.ForeignKey('internship_application.id'), nullable=False)
    interview_status_id = db.Column(db.Integer, db.ForeignKey('interview_status.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(255), nullable=True)
    interview_notes = db.Column(db.Text, nullable=True)
    interview_completed_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    application = db.relationship('InternshipApplication', backref=db.backref('interviews', lazy=True))
    interview_status = db.relationship('InterviewStatus')

class SavedInternship(db.Model):
    __tablename__ = 'saved_internship'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('saved_internships', lazy=True))
    internship = db.relationship('Internship', backref=db.backref('saved_by_students', lazy=True))

class InternshipModerationEvent(db.Model):
    __tablename__ = 'internship_moderation_event'
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    moderation_status_id = db.Column(db.Integer, db.ForeignKey('internship_moderation_status.id'), nullable=False)
    action_note = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    internship = db.relationship('Internship', backref=db.backref('moderation_events', lazy=True))
    admin_user = db.relationship('UserAccount', foreign_keys=[admin_user_id])
    moderation_status = db.relationship('InternshipModerationStatus')
