"""Remove duplicate master data (TechnologyCategory, Skill, TechStackItem) by name.

For each group of rows sharing the same name (case-insensitive):
  1. Keep the row with the lowest id.
  2. Re-point every foreign-key reference from the duplicate ids → the kept id.
  3. Delete the duplicate rows.

Run with:  python scripts/dedup_master.py          (dry-run by default)
           python scripts/dedup_master.py --apply   (actually write changes)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from app.extensions import db
from app.models.master import TechnologyCategory, Skill, TechStackItem
from sqlalchemy import text

TABLES_TO_DEDUP = [
    {
        "label": "Technology Category",
        "model": TechnologyCategory,
        "name_col": "category_name",
        "fks": [
            ("internship", "technology_category_id", "technology_category.id"),
        ],
    },
    {
        "label": "Skill",
        "model": Skill,
        "name_col": "skill_name",
        "fks": [
            ("internship_required_skill", "skill_id", "skill.id"),
            ("student_skill", "skill_id", "skill.id"),
            ("ai_skill_match_skill_item", "skill_id", "skill.id"),
        ],
    },
    {
        "label": "Tech Stack Item",
        "model": TechStackItem,
        "name_col": "tech_stack_name",
        "fks": [
            ("internship_required_tech_stack_item", "tech_stack_item_id", "tech_stack_item.id"),
            ("student_tech_stack_item", "tech_stack_item_id", "tech_stack_item.id"),
            ("ai_skill_match_tech_stack_item", "tech_stack_item_id", "tech_stack_item.id"),
        ],
    },
]


def find_duplicates(session, model, name_col):
    """Return {normalised_name: [row, row, ...]} for names appearing >1 time."""
    rows = session.query(model).all()
    groups = {}
    for r in rows:
        key = getattr(r, name_col).strip().lower()
        groups.setdefault(key, []).append(r)
    return {k: v for k, v in groups.items() if len(v) > 1}


def dedup_table(session, cfg, apply=False):
    model = cfg["model"]
    name_col = cfg["name_col"]
    label = cfg["label"]

    dupes = find_duplicates(session, model, name_col)
    if not dupes:
        print(f"  [{label}] Tidak ada duplikat.")
        return

    for name_key, rows in dupes.items():
        rows.sort(key=lambda r: r.id)
        keep = rows[0]
        remove = rows[1:]
        remove_ids = [r.id for r in remove]
        names_display = [f"id={r.id} ({getattr(r, name_col)})" for r in remove]

        print(f"  [{label}] Duplikat '{getattr(keep, name_col)}':")
        print(f"    Simpan : id={keep.id}")
        print(f"    Hapus  : {', '.join(names_display)}")

        if not apply:
            continue

        for tbl, fk_col, _ in cfg["fks"]:
            placeholders = ",".join(str(i) for i in remove_ids)
            stmt = text(
                f"UPDATE {tbl} SET {fk_col} = :keep_id "
                f"WHERE {fk_col} IN ({placeholders})"
            )
            session.execute(stmt, {"keep_id": keep.id})

        for r in remove:
            session.delete(r)

    if apply:
        session.commit()
        print(f"  [{label}] Perubahan tersimpan.")
    else:
        print(f"  [{label}] (dry-run — gunakan --apply untuk menerapkan)")


def main():
    apply = "--apply" in sys.argv
    app = create_app()
    with app.app_context():
        for cfg in TABLES_TO_DEDUP:
            dedup_table(db.session, cfg, apply=apply)


if __name__ == "__main__":
    main()
