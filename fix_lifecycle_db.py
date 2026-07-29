from app import create_app
from app.extensions import db
from app.models.lookups import InternshipLifecycleStatus
from app.models.internship import Internship

app = create_app()
with app.app_context():
    # Ambil status objects
    cancelled = InternshipLifecycleStatus.query.filter_by(status_code='cancelled').first()
    hidden = InternshipLifecycleStatus.query.filter_by(status_code='hidden').first()
    
    if not hidden:
        hidden = InternshipLifecycleStatus(status_code='hidden', status_name='Hidden')
        db.session.add(hidden)
        db.session.flush()
        print('added hidden')
    
    # Migrasi semua internship dari cancelled ke hidden
    if cancelled:
        affected = Internship.query.filter_by(lifecycle_status_id=cancelled.id).update(
            {'lifecycle_status_id': hidden.id}
        )
        print(f'migrated {affected} internships from cancelled to hidden')
        
        # Hapus cancelled
        db.session.delete(cancelled)
        print('deleted cancelled')
    
    db.session.commit()
    
    # Cek hasil
    for s in InternshipLifecycleStatus.query.all():
        cnt = Internship.query.filter_by(lifecycle_status_id=s.id).count()
        print(f'{s.status_code}: {s.status_name} ({cnt} internships)')
