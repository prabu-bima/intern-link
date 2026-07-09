from app.extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    notification_type_id = db.Column(db.Integer, db.ForeignKey('notification_type.id'), nullable=False)
    payload_json = db.Column(db.JSON, nullable=False)
    event_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    recipient_user = db.relationship('UserAccount', backref=db.backref('notifications', lazy=True))
    notification_type = db.relationship('NotificationType')

class AdminAuditLog(db.Model):
    __tablename__ = 'admin_audit_log'
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    action_code = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(100), nullable=True) # e.g. 'CompanyProfile', 'Internship'
    target_id = db.Column(db.Integer, nullable=True)
    details_json = db.Column(db.JSON, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    admin_user = db.relationship('UserAccount', backref=db.backref('audit_logs', lazy=True))

class AdminReport(db.Model):
    __tablename__ = 'admin_report'
    id = db.Column(db.Integer, primary_key=True)
    report_type_id = db.Column(db.Integer, db.ForeignKey('report_type.id'), nullable=False)
    generated_by_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    filters_json = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='processing') # e.g. processing, completed, failed
    report_file_asset_id = db.Column(db.Integer, db.ForeignKey('file_asset.id'), nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    report_type = db.relationship('ReportType')
    generated_by_user = db.relationship('UserAccount', backref=db.backref('generated_reports', lazy=True))
    report_file_asset = db.relationship('FileAsset', foreign_keys=[report_file_asset_id])
