"""Models package for SQLAlchemy database models."""

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

from app.models.master import (
    TechnologyCategory,
    Skill,
    TechStackItem,
    Location
)

from app.models.identity import (
    UserAccount,
    FileAsset,
    StudentProfile,
    CompanyProfile
)

from app.models.student import (
    StudentEducationRecord,
    StudentSkill,
    StudentTechStackItem,
    StudentExperience,
    StudentOrganization,
    StudentCertificate,
    StudentPortfolio,
    StudentGithubProfile,
    StudentLinkedinProfile,
    StudentCvVersion
)

from app.models.company import (
    CompanySocialLink,
    CompanyVerification
)

from app.models.internship import (
    Internship,
    InternshipRequiredSkill,
    InternshipRequiredTechStackItem,
    InternshipApplication,
    ApplicationInterview,
    SavedInternship,
    InternshipModerationEvent
)

from app.models.ai import (
    AISkillMatchRun,
    AISkillMatchSkillItem,
    AISkillMatchTechStackItem,
    AIJobRecommendationRun,
    AIJobRecommendationItem
)

from app.models.system import (
    Notification,
    AdminAuditLog,
    AdminReport
)







