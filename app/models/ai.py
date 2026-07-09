from app.extensions import db
from datetime import datetime

class AISkillMatchRun(db.Model):
    __tablename__ = 'ai_skill_match_run'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    match_percentage = db.Column(db.Float, nullable=True)
    ai_explanation = db.Column(db.Text, nullable=True)
    suggested_skills_summary = db.Column(db.Text, nullable=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(50), nullable=True)
    input_snapshot_hash = db.Column(db.String(255), nullable=True)
    input_snapshot_json = db.Column(db.JSON, nullable=True)
    generation_status = db.Column(db.String(50), nullable=False) # e.g. success, pending, failed
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('skill_match_runs', lazy=True))
    internship = db.relationship('Internship', backref=db.backref('skill_match_runs', lazy=True))

class AISkillMatchSkillItem(db.Model):
    __tablename__ = 'ai_skill_match_skill_item'
    id = db.Column(db.Integer, primary_key=True)
    ai_skill_match_run_id = db.Column(db.Integer, db.ForeignKey('ai_skill_match_run.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    item_role_id = db.Column(db.Integer, db.ForeignKey('ai_skill_match_item_role.id'), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    match_run = db.relationship('AISkillMatchRun', backref=db.backref('skill_items', lazy=True))
    skill = db.relationship('Skill')
    item_role = db.relationship('AISkillMatchItemRole')

class AISkillMatchTechStackItem(db.Model):
    __tablename__ = 'ai_skill_match_tech_stack_item'
    id = db.Column(db.Integer, primary_key=True)
    ai_skill_match_run_id = db.Column(db.Integer, db.ForeignKey('ai_skill_match_run.id'), nullable=False)
    tech_stack_item_id = db.Column(db.Integer, db.ForeignKey('tech_stack_item.id'), nullable=False)
    item_role_id = db.Column(db.Integer, db.ForeignKey('ai_skill_match_item_role.id'), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    match_run = db.relationship('AISkillMatchRun', backref=db.backref('tech_stack_items', lazy=True))
    tech_stack_item = db.relationship('TechStackItem')
    item_role = db.relationship('AISkillMatchItemRole')

class AIJobRecommendationRun(db.Model):
    __tablename__ = 'ai_job_recommendation_run'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(50), nullable=True)
    input_snapshot_hash = db.Column(db.String(255), nullable=True)
    input_snapshot_json = db.Column(db.JSON, nullable=True)
    generation_status = db.Column(db.String(50), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    student_profile = db.relationship('StudentProfile', backref=db.backref('job_recommendation_runs', lazy=True))

class AIJobRecommendationItem(db.Model):
    __tablename__ = 'ai_job_recommendation_item'
    id = db.Column(db.Integer, primary_key=True)
    ai_job_recommendation_run_id = db.Column(db.Integer, db.ForeignKey('ai_job_recommendation_run.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    recommendation_reason = db.Column(db.Text, nullable=True)
    rank_no = db.Column(db.Integer, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    recommendation_run = db.relationship('AIJobRecommendationRun', backref=db.backref('items', lazy=True, order_by='AIJobRecommendationItem.rank_no'))
    internship = db.relationship('Internship')
