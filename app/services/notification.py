"""
Notification creation service for InternLink.

Menyediakan fungsi-fungsi reusable untuk membuat notifikasi
ke company maupun student, serta fungsi automation untuk
interview reminder dan job closing reminder.
"""

from datetime import datetime, timedelta
from app.extensions import db


# ─────────────────────────────────────────────
# Helper internal
# ─────────────────────────────────────────────

def _get_or_create_notification_type(type_code: str, type_name: str):
    """Ambil NotificationType berdasarkan type_code, buat jika belum ada."""
    from app.models.lookups import NotificationType
    notif_type = NotificationType.query.filter_by(type_code=type_code).first()
    if not notif_type:
        notif_type = NotificationType(type_code=type_code, type_name=type_name)
        db.session.add(notif_type)
        db.session.flush()
    return notif_type


def _create_notification(recipient_user_id: int, type_code: str, type_name: str, payload: dict):
    """Buat satu record Notification dan tambahkan ke session (belum commit)."""
    from app.models.system import Notification
    notif_type = _get_or_create_notification_type(type_code, type_name)
    notif = Notification(
        recipient_user_id=recipient_user_id,
        notification_type_id=notif_type.id,
        payload_json=payload,
    )
    db.session.add(notif)
    return notif


# ─────────────────────────────────────────────
# Public API — dipanggil dari routes
# ─────────────────────────────────────────────

def notify_new_applicant(application):
    """
    Kirim notifikasi ke company saat ada pelamar baru.

    Dipanggil di route apply internship (student side).

    Args:
        application: instance InternshipApplication yang baru dibuat.
    """
    company_user_id = application.internship.company_profile.user_account_id
    student_name = (
        application.student_profile.user.display_name
        if application.student_profile.user
        else 'Seorang pelamar'
    )
    payload = {
        'title': 'Pelamar Baru',
        'message': (
            f"{student_name} telah melamar posisi "
            f"'{application.internship.internship_title}'."
        ),
        'application_id': application.id,
        'internship_id': application.internship_id,
        'internship_title': application.internship.internship_title,
        'student_name': student_name,
    }
    _create_notification(
        recipient_user_id=company_user_id,
        type_code='new_applicant',
        type_name='Pelamar Baru',
        payload=payload,
    )


def notify_interview_reminder(interview):
    """
    Kirim notifikasi pengingat wawancara ke company (24 jam sebelum jadwal).

    Args:
        interview: instance ApplicationInterview.
    """
    company_user_id = (
        interview.application.internship.company_profile.user_account_id
    )
    student_name = (
        interview.application.student_profile.user.display_name
        if interview.application.student_profile.user
        else 'Pelamar'
    )
    scheduled_str = interview.scheduled_at.strftime('%d %B %Y, %H:%M')
    payload = {
        'title': 'Pengingat Wawancara',
        'message': (
            f"Wawancara dengan {student_name} untuk posisi "
            f"'{interview.application.internship.internship_title}' "
            f"dijadwalkan pada {scheduled_str}."
        ),
        'application_id': interview.internship_application_id,
        'internship_id': interview.application.internship_id,
        'internship_title': interview.application.internship.internship_title,
        'interview_id': interview.id,
        'scheduled_at': interview.scheduled_at.isoformat(),
        'student_name': student_name,
    }
    _create_notification(
        recipient_user_id=company_user_id,
        type_code='interview_reminder',
        type_name='Pengingat Wawancara',
        payload=payload,
    )


def notify_job_closing_reminder(internship):
    """
    Kirim notifikasi pengingat penutupan lowongan ke company.

    Dipanggil saat closing_at <= 3 hari dari sekarang.

    Args:
        internship: instance Internship.
    """
    company_user_id = internship.company_profile.user_account_id
    closing_str = internship.closing_at.strftime('%d %B %Y')
    days_left = (internship.closing_at.date() - datetime.utcnow().date()).days
    payload = {
        'title': 'Lowongan Akan Segera Ditutup',
        'message': (
            f"Lowongan '{internship.internship_title}' akan ditutup pada "
            f"{closing_str} ({days_left} hari lagi). "
            f"Segera tinjau dan tindak lanjuti pelamar yang masuk."
        ),
        'internship_id': internship.id,
        'internship_title': internship.internship_title,
        'closing_at': internship.closing_at.isoformat(),
        'days_left': days_left,
    }
    _create_notification(
        recipient_user_id=company_user_id,
        type_code='job_closing_reminder',
        type_name='Pengingat Penutupan Lowongan',
        payload=payload,
    )


# ─────────────────────────────────────────────
# Automation runners — dipanggil dari CLI command
# ─────────────────────────────────────────────

def run_interview_reminders():
    """
    Kirim pengingat untuk semua wawancara yang dijadwalkan
    dalam rentang 24 jam ke depan dan belum pernah mendapat
    notifikasi reminder.

    Returns:
        int: jumlah notifikasi yang dikirim.
    """
    from app.models.internship import ApplicationInterview
    from app.models.system import Notification
    from app.models.lookups import NotificationType

    now = datetime.utcnow()
    window_start = now
    window_end = now + timedelta(hours=24)

    # Ambil InterviewStatus 'scheduled' agar tidak kirim ke yang sudah selesai
    from app.models.lookups import InterviewStatus
    scheduled_status = InterviewStatus.query.filter_by(status_code='scheduled').first()

    query = ApplicationInterview.query.filter(
        ApplicationInterview.scheduled_at >= window_start,
        ApplicationInterview.scheduled_at <= window_end,
        ApplicationInterview.deleted_at.is_(None),
    )
    if scheduled_status:
        query = query.filter(
            ApplicationInterview.interview_status_id == scheduled_status.id
        )

    interviews = query.all()

    # Cek tipe notifikasi untuk de-duplikasi
    reminder_type = NotificationType.query.filter_by(type_code='interview_reminder').first()

    sent = 0
    for interview in interviews:
        # Skip jika notifikasi reminder sudah pernah dikirim untuk interview ini
        if reminder_type:
            already_sent = Notification.query.filter(
                Notification.notification_type_id == reminder_type.id,
                Notification.payload_json['interview_id'].as_integer() == interview.id,
                Notification.deleted_at.is_(None),
            ).first()
            if already_sent:
                continue

        try:
            notify_interview_reminder(interview)
            sent += 1
        except Exception as e:
            # Log tapi jangan hentikan loop
            import logging
            logging.getLogger(__name__).error(
                f"Gagal mengirim interview reminder untuk interview_id={interview.id}: {e}"
            )

    db.session.commit()
    return sent


def run_job_closing_reminders(days_before: int = 3):
    """
    Kirim pengingat untuk semua internship aktif yang closing_at-nya
    tersisa <= days_before hari dan belum pernah mendapat notifikasi
    closing reminder.

    Args:
        days_before: threshold hari sebelum penutupan (default 3).

    Returns:
        int: jumlah notifikasi yang dikirim.
    """
    from app.models.internship import Internship
    from app.models.lookups import InternshipLifecycleStatus, NotificationType
    from app.models.system import Notification

    now = datetime.utcnow()
    threshold = now + timedelta(days=days_before)

    active_status = InternshipLifecycleStatus.query.filter_by(status_code='active').first()

    query = Internship.query.filter(
        Internship.closing_at.isnot(None),
        Internship.closing_at >= now,
        Internship.closing_at <= threshold,
        Internship.deleted_at.is_(None),
    )
    if active_status:
        query = query.filter(Internship.lifecycle_status_id == active_status.id)

    internships = query.all()

    closing_type = NotificationType.query.filter_by(type_code='job_closing_reminder').first()

    sent = 0
    for internship in internships:
        # De-duplikasi: skip jika sudah ada notifikasi closing_reminder untuk internship ini
        if closing_type:
            already_sent = Notification.query.filter(
                Notification.notification_type_id == closing_type.id,
                Notification.payload_json['internship_id'].as_integer() == internship.id,
                Notification.deleted_at.is_(None),
            ).first()
            if already_sent:
                continue

        try:
            notify_job_closing_reminder(internship)
            sent += 1
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Gagal mengirim job closing reminder untuk internship_id={internship.id}: {e}"
            )

    db.session.commit()
    return sent
