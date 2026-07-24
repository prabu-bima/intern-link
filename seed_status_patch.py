"""
Seed patch: assign 5 internships to each missing lifecycle & moderation status.
- Lifecycle  : draft (5), cancelled (5)  -- currently both at 0
- Moderation : rejected (5), hidden (4 more to reach 5 total)
Picks from existing internships; does NOT create new rows.
Run: venv\Scripts\python.exe seed_status_patch.py
"""
from app import create_app
from app.extensions import db
from app.models.internship import Internship
from app.models.lookups import InternshipLifecycleStatus, InternshipModerationStatus

app = create_app()

NEED_PER_STATUS = 5

with app.app_context():
    print("=" * 55)
    print("  InternLink Status Patch Seed")
    print("=" * 55)

    # ── Fetch all status objects ──────────────────────────────────
    lc = {s.status_code: s for s in InternshipLifecycleStatus.query.all()}
    md = {s.status_code: s for s in InternshipModerationStatus.query.all()}

    # ── Validate all required status codes exist ──────────────────
    for code in ('draft', 'active', 'closed', 'cancelled'):
        if code not in lc:
            raise RuntimeError(f"Lifecycle status '{code}' not found in DB.")
    for code in ('pending', 'approved', 'rejected', 'flagged', 'hidden'):
        if code not in md:
            raise RuntimeError(f"Moderation status '{code}' not found in DB.")

    # ── 1. Lifecycle: DRAFT (need 5 from active pool) ─────────────
    current_draft = Internship.query.filter_by(
        lifecycle_status_id=lc['draft'].id, deleted_at=None
    ).count()
    needed_draft = max(0, NEED_PER_STATUS - current_draft)

    if needed_draft > 0:
        candidates = Internship.query.filter_by(
            lifecycle_status_id=lc['active'].id, deleted_at=None
        ).order_by(Internship.id.asc()).limit(needed_draft).all()
        for row in candidates:
            row.lifecycle_status_id = lc['draft'].id
        db.session.flush()
        print(f"[+] Lifecycle DRAFT    : {len(candidates)} lowongan diupdate (total -> {current_draft + len(candidates)})")
    else:
        print(f"[=] Lifecycle DRAFT    : sudah ada {current_draft}, skip.")

    # ── 2. Lifecycle: CANCELLED (need 5 from active pool) ─────────
    current_cancelled = Internship.query.filter_by(
        lifecycle_status_id=lc['cancelled'].id, deleted_at=None
    ).count()
    needed_cancelled = max(0, NEED_PER_STATUS - current_cancelled)

    if needed_cancelled > 0:
        # Exclude those just set to draft in this session
        draft_ids = [
            r.id for r in Internship.query.filter_by(
                lifecycle_status_id=lc['draft'].id, deleted_at=None
            ).all()
        ]
        candidates = Internship.query.filter(
            Internship.lifecycle_status_id == lc['active'].id,
            Internship.deleted_at == None,
            ~Internship.id.in_(draft_ids) if draft_ids else True,
        ).order_by(Internship.id.asc()).limit(needed_cancelled).all()
        for row in candidates:
            row.lifecycle_status_id = lc['cancelled'].id
        db.session.flush()
        print(f"[+] Lifecycle CANCELLED: {len(candidates)} lowongan diupdate (total -> {current_cancelled + len(candidates)})")
    else:
        print(f"[=] Lifecycle CANCELLED: sudah ada {current_cancelled}, skip.")

    # ── 3. Moderation: REJECTED (need 5 from approved pool) ───────
    current_rejected = Internship.query.filter_by(
        moderation_status_id=md['rejected'].id, deleted_at=None
    ).count()
    needed_rejected = max(0, NEED_PER_STATUS - current_rejected)

    if needed_rejected > 0:
        candidates = Internship.query.filter_by(
            moderation_status_id=md['approved'].id, deleted_at=None
        ).order_by(Internship.id.desc()).limit(needed_rejected).all()
        for row in candidates:
            row.moderation_status_id = md['rejected'].id
        db.session.flush()
        print(f"[+] Moderation REJECTED: {len(candidates)} lowongan diupdate (total -> {current_rejected + len(candidates)})")
    else:
        print(f"[=] Moderation REJECTED: sudah ada {current_rejected}, skip.")

    # ── 4. Moderation: HIDDEN (need 5 total, pick from approved) ──
    current_hidden = Internship.query.filter_by(
        moderation_status_id=md['hidden'].id, deleted_at=None
    ).count()
    needed_hidden = max(0, NEED_PER_STATUS - current_hidden)

    if needed_hidden > 0:
        # Avoid rows already changed to rejected in this session
        rejected_ids = [
            r.id for r in Internship.query.filter_by(
                moderation_status_id=md['rejected'].id, deleted_at=None
            ).all()
        ]
        candidates = Internship.query.filter(
            Internship.moderation_status_id == md['approved'].id,
            Internship.deleted_at == None,
            ~Internship.id.in_(rejected_ids) if rejected_ids else True,
        ).order_by(Internship.id.desc()).limit(needed_hidden).all()
        for row in candidates:
            row.moderation_status_id = md['hidden'].id
        db.session.flush()
        print(f"[+] Moderation HIDDEN  : {len(candidates)} lowongan diupdate (total -> {current_hidden + len(candidates)})")
    else:
        print(f"[=] Moderation HIDDEN  : sudah ada {current_hidden}, skip.")

    db.session.commit()

    # ── Summary ───────────────────────────────────────────────────
    print()
    print("--- Ringkasan akhir ---")
    from sqlalchemy import func
    for label, model, status_dict in [
        ("Lifecycle ", InternshipLifecycleStatus, lc),
        ("Moderation", InternshipModerationStatus, md),
    ]:
        id_field = Internship.lifecycle_status_id if label.startswith("Life") else Internship.moderation_status_id
        for code, obj in status_dict.items():
            cnt = Internship.query.filter(
                id_field == obj.id,
                Internship.deleted_at == None
            ).count()
            print(f"  {label} [{code:12s}]: {cnt}")
    print()
    print("Patch selesai!")
    print("=" * 55)
