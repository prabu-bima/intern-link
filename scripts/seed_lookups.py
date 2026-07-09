import sys
import os

# Add the project root to the python path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.lookups import (
    UserAccountStatus,
    CompanyVerificationStatus,
    InternshipLifecycleStatus,
    InternshipModerationStatus,
    ApplicationStatus,
    InterviewStatus,
    NotificationType,
    ReportType,
    AISkillMatchItemRole
)

app = create_app()

def seed_data():
    with app.app_context():
        # User Account Status
        user_statuses = [
            {'code': 'active', 'name': 'Active'},
            {'code': 'inactive', 'name': 'Inactive'},
            {'code': 'suspended', 'name': 'Suspended'}
        ]
        for s in user_statuses:
            if not UserAccountStatus.query.filter_by(status_code=s['code']).first():
                db.session.add(UserAccountStatus(status_code=s['code'], status_name=s['name']))

        # Company Verification Status
        company_verifications = [
            {'code': 'pending', 'name': 'Pending Verification'},
            {'code': 'verified', 'name': 'Verified'},
            {'code': 'rejected', 'name': 'Rejected'}
        ]
        for s in company_verifications:
            if not CompanyVerificationStatus.query.filter_by(status_code=s['code']).first():
                db.session.add(CompanyVerificationStatus(status_code=s['code'], status_name=s['name']))

        # Internship Lifecycle Status
        internship_lifecycles = [
            {'code': 'draft', 'name': 'Draft'},
            {'code': 'active', 'name': 'Active'},
            {'code': 'closed', 'name': 'Closed'},
            {'code': 'cancelled', 'name': 'Cancelled'}
        ]
        for s in internship_lifecycles:
            if not InternshipLifecycleStatus.query.filter_by(status_code=s['code']).first():
                db.session.add(InternshipLifecycleStatus(status_code=s['code'], status_name=s['name']))

        # Internship Moderation Status
        internship_moderations = [
            {'code': 'pending', 'name': 'Pending Approval'},
            {'code': 'approved', 'name': 'Approved'},
            {'code': 'rejected', 'name': 'Rejected'}
        ]
        for s in internship_moderations:
            if not InternshipModerationStatus.query.filter_by(status_code=s['code']).first():
                db.session.add(InternshipModerationStatus(status_code=s['code'], status_name=s['name']))

        # Application Status
        application_statuses = [
            {'code': 'applied', 'name': 'Applied'},
            {'code': 'reviewing', 'name': 'Under Review'},
            {'code': 'shortlisted', 'name': 'Shortlisted'},
            {'code': 'interviewing', 'name': 'Interviewing'},
            {'code': 'accepted', 'name': 'Accepted'},
            {'code': 'rejected', 'name': 'Rejected'},
            {'code': 'withdrawn', 'name': 'Withdrawn'}
        ]
        for s in application_statuses:
            if not ApplicationStatus.query.filter_by(status_code=s['code']).first():
                db.session.add(ApplicationStatus(status_code=s['code'], status_name=s['name']))

        # Interview Status
        interview_statuses = [
            {'code': 'scheduled', 'name': 'Scheduled'},
            {'code': 'completed', 'name': 'Completed'},
            {'code': 'cancelled', 'name': 'Cancelled'}
        ]
        for s in interview_statuses:
            if not InterviewStatus.query.filter_by(status_code=s['code']).first():
                db.session.add(InterviewStatus(status_code=s['code'], status_name=s['name']))

        # Notification Type
        notification_types = [
            {'code': 'info', 'name': 'Information'},
            {'code': 'alert', 'name': 'Alert'},
            {'code': 'message', 'name': 'Direct Message'},
            {'code': 'application', 'name': 'Application Update'},
            {'code': 'system', 'name': 'System'}
        ]
        for s in notification_types:
            if not NotificationType.query.filter_by(type_code=s['code']).first():
                db.session.add(NotificationType(type_code=s['code'], type_name=s['name']))

        # Report Type
        report_types = [
            {'code': 'spam', 'name': 'Spam'},
            {'code': 'abuse', 'name': 'Abusive Content'},
            {'code': 'fraud', 'name': 'Fraud / Scam'},
            {'code': 'bug', 'name': 'System Bug'},
            {'code': 'other', 'name': 'Other'}
        ]
        for s in report_types:
            if not ReportType.query.filter_by(type_code=s['code']).first():
                db.session.add(ReportType(type_code=s['code'], type_name=s['name']))

        # AI Skill Match Item Role
        skill_roles = [
            {'code': 'required', 'name': 'Required'},
            {'code': 'optional', 'name': 'Optional / Nice to have'}
        ]
        for s in skill_roles:
            if not AISkillMatchItemRole.query.filter_by(role_code=s['code']).first():
                db.session.add(AISkillMatchItemRole(role_code=s['code'], role_name=s['name']))

        db.session.commit()
        print("Successfully seeded lookup tables.")

if __name__ == '__main__':
    seed_data()
