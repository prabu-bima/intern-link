from app.extensions import db
from datetime import datetime

class CompanySocialLink(db.Model):
    __tablename__ = 'company_social_link'
    id = db.Column(db.Integer, primary_key=True)
    company_profile_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False) # e.g. LinkedIn, Twitter, Facebook
    url = db.Column(db.String(255), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    company_profile = db.relationship('CompanyProfile', backref=db.backref('social_links', lazy=True))

class CompanyVerification(db.Model):
    __tablename__ = 'company_verification'
    id = db.Column(db.Integer, primary_key=True)
    company_profile_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    verification_status_id = db.Column(db.Integer, db.ForeignKey('company_verification_status.id'), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=True)
    admin_note = db.Column(db.Text, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    company_profile = db.relationship('CompanyProfile', backref=db.backref('verifications', lazy=True))
    verification_status = db.relationship('CompanyVerificationStatus')
    admin_user = db.relationship('UserAccount', foreign_keys=[admin_user_id])
