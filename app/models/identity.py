from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

class UserAccount(db.Model, UserMixin):
    __tablename__ = 'user_account'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False) # 'student', 'company', 'admin'
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    account_status_id = db.Column(db.Integer, db.ForeignKey('user_account_status.id'), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    status = db.relationship('UserAccountStatus')
    student_profile = db.relationship('StudentProfile', back_populates='user', uselist=False)
    company_profile = db.relationship('CompanyProfile', back_populates='user', uselist=False)
    file_assets = db.relationship('FileAsset', back_populates='owner')

@login_manager.user_loader
def load_user(user_id):
    return UserAccount.query.get(int(user_id))

class FileAsset(db.Model):
    __tablename__ = 'file_asset'
    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id', ondelete='CASCADE'), nullable=False)
    file_purpose = db.Column(db.String(50), nullable=False)
    storage_bucket = db.Column(db.String(100), nullable=False)
    object_key = db.Column(db.String(255), nullable=False, unique=True)
    file_name = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    @property
    def url(self):
        from app.services.storage import get_file_url
        if not self.storage_bucket or not self.object_key:
            return None
        return get_file_url(self.storage_bucket, self.object_key, public=True)

    # Relationships
    owner = db.relationship('UserAccount', back_populates='file_assets')

class StudentProfile(db.Model):
    __tablename__ = 'student_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_account_id = db.Column(db.Integer, db.ForeignKey('user_account.id', ondelete='CASCADE'), unique=True, nullable=False)
    profile_photo_file_id = db.Column(db.Integer, db.ForeignKey('file_asset.id', ondelete='SET NULL'), nullable=True)
    
    bio = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('UserAccount', back_populates='student_profile')
    profile_photo = db.relationship('FileAsset', foreign_keys=[profile_photo_file_id])

class CompanyProfile(db.Model):
    __tablename__ = 'company_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_account_id = db.Column(db.Integer, db.ForeignKey('user_account.id', ondelete='CASCADE'), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    company_description = db.Column(db.Text, nullable=True)
    industry_category = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)
    founding_year = db.Column(db.Integer, nullable=True)
    company_logo_file_id = db.Column(db.Integer, db.ForeignKey('file_asset.id'), nullable=True)
    address_line = db.Column(db.String(255), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('UserAccount', back_populates='company_profile')
    company_logo = db.relationship('FileAsset', foreign_keys=[company_logo_file_id])
    location = db.relationship('Location')