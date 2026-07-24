"""
Fix duplicate locations in master data.
- Migrate all references from duplicate location IDs to canonical ones
- Delete duplicate location records
- Canonical mappings:
  * Jakarta: keep ID=1 (code='jakarta'), delete ID=8 (code='JKT')
  * Bandung: keep ID=2 (code='bandung'), delete ID=9 (code='BDG')
Run: venv\Scripts\python.exe fix_duplicate_locations.py
"""
from app import create_app
from app.extensions import db
from app.models.master import Location
from app.models.identity import CompanyProfile
from app.models.internship import Internship

app = create_app()

# Mapping: (duplicate_id, canonical_id, city_name)
DUPLICATE_MAPPINGS = [
    (8, 1, "Jakarta"),  # JKT -> jakarta
    (9, 2, "Bandung"),  # BDG -> bandung
]

with app.app_context():
    print("=" * 60)
    print("  Fix Duplicate Locations")
    print("=" * 60)

    for dup_id, keep_id, city in DUPLICATE_MAPPINGS:
        print(f"\n[{city}] Migrating ID {dup_id} -> {keep_id}")
        
        # 1. Migrate CompanyProfile
        company_refs = CompanyProfile.query.filter_by(location_id=dup_id).all()
        if company_refs:
            print(f"  -> Updating {len(company_refs)} CompanyProfile records...")
            for cp in company_refs:
                cp.location_id = keep_id
            db.session.flush()
        
        # 2. Migrate Internship
        internship_refs = Internship.query.filter_by(location_id=dup_id).all()
        if internship_refs:
            print(f"  -> Updating {len(internship_refs)} Internship records...")
            for intern in internship_refs:
                intern.location_id = keep_id
            db.session.flush()
        
        # 3. Delete duplicate location
        dup_loc = Location.query.get(dup_id)
        if dup_loc:
            print(f"  -> Deleting duplicate Location ID {dup_id} (code='{dup_loc.location_code}')...")
            db.session.delete(dup_loc)
            db.session.flush()
        
        db.session.commit()
        print(f"  [v] {city} migration complete.")

    print()
    print("--- Verification ---")
    from sqlalchemy import func
    duplicates = Location.query.with_entities(
        Location.city,
        func.count(Location.id).label('count')
    ).group_by(Location.city).having(func.count(Location.id) > 1).all()
    
    if duplicates:
        print("  [!] Still have duplicates:")
        for city, count in duplicates:
            print(f"      {city}: {count} entries")
    else:
        print("  [v] No duplicates found. All locations are unique by city.")
    
    # Summary
    total_locs = Location.query.count()
    total_companies = CompanyProfile.query.filter(CompanyProfile.location_id.isnot(None)).count()
    total_internships = Internship.query.filter(Internship.location_id.isnot(None)).count()
    
    print()
    print(f"  Total Locations      : {total_locs}")
    print(f"  CompanyProfiles w/ loc: {total_companies}")
    print(f"  Internships w/ loc    : {total_internships}")
    print()
    print("Fix selesai!")
    print("=" * 60)
