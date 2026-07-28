"""
Fix mismatch between ApplicationInterview.interview_status and
InternshipApplication.application_status.

Rules applied:
  - Any application that has at least one ApplicationInterview record
    but whose application_status is 'applied' or 'reviewing'
    → upgrade to 'interviewing'
  - application_status == 'accepted' is intentional (interview happened,
    candidate was accepted) → keep as-is, no downgrade
  - interview_status == 'cancelled' on ALL interviews for an application
    does NOT automatically revert application_status (cancellation could
    be rescheduled); only promote, never demote.

Run: venv\Scripts\python.exe fix_interview_mismatch.py
"""
from app import create_app
from app.extensions import db
from app.models.internship import ApplicationInterview, InternshipApplication
from app.models.lookups import ApplicationStatus

app = create_app()

PROMOTE_FROM = {'applied', 'reviewing', 'shortlisted'}

with app.app_context():
    print("=" * 60)
    print("  Fix ApplicationInterview / ApplicationStatus Mismatch")
    print("=" * 60)

    interviewing_status = ApplicationStatus.query.filter_by(status_code='interviewing').first()
    if not interviewing_status:
        print("[ERROR] 'interviewing' status not found in DB.")
        exit(1)

    # Find all application IDs that have at least one interview record
    app_ids_with_interviews = db.session.query(
        ApplicationInterview.internship_application_id
    ).filter(
        ApplicationInterview.deleted_at.is_(None)
    ).distinct().all()
    app_ids_with_interviews = {row[0] for row in app_ids_with_interviews}

    print(f"\n[INFO] Applications with interview records: {len(app_ids_with_interviews)}")

    # Find which ones have a status that should be promoted
    mismatch_apps = InternshipApplication.query.filter(
        InternshipApplication.id.in_(app_ids_with_interviews),
        InternshipApplication.deleted_at.is_(None)
    ).all()

    fixed = 0
    skipped = 0
    for a in mismatch_apps:
        current_status = ApplicationStatus.query.get(a.application_status_id)
        if not current_status:
            continue
        if current_status.status_code in PROMOTE_FROM:
            print(f"  [FIX] app_id={a.id:4d}  {current_status.status_code:12s} -> interviewing")
            a.application_status_id = interviewing_status.id
            fixed += 1
        else:
            skipped += 1

    db.session.commit()

    print(f"\n[DONE] Fixed: {fixed} | Already correct / accepted: {skipped}")

    # Verify
    print("\n--- Verification: remaining mismatches ---")
    from sqlalchemy import func
    remaining = db.session.query(
        func.count(ApplicationInterview.id)
    ).join(
        InternshipApplication,
        ApplicationInterview.internship_application_id == InternshipApplication.id
    ).join(
        ApplicationStatus,
        InternshipApplication.application_status_id == ApplicationStatus.id
    ).filter(
        ApplicationInterview.deleted_at.is_(None),
        InternshipApplication.deleted_at.is_(None),
        ApplicationStatus.status_code.in_(['applied', 'reviewing'])
    ).scalar()

    print(f"  Applications with interview but wrong status: {remaining}")
    if remaining == 0:
        print("  [v] All mismatches resolved.")
    print("=" * 60)
