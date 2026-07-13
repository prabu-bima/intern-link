import sys
import os
from app import create_app
from app.extensions import db
from app.models.master import Skill
from app.models.student import StudentSkill
from app.models.internship import InternshipRequiredSkill

app = create_app()

with app.app_context():
    print("Deleting existing student skills...")
    StudentSkill.query.delete()
    print("Deleting existing internship required skills...")
    InternshipRequiredSkill.query.delete()
    print("Deleting existing master skills...")
    Skill.query.delete()
    db.session.commit()
    print("Old skills deleted successfully.")

    top_10_skills = [
        {"code": "WEB_DEV", "name": "Web Development", "desc": "Pembuatan dan pemeliharaan situs web"},
        {"code": "MOB_DEV", "name": "Mobile Development", "desc": "Pembuatan aplikasi untuk perangkat bergerak (Android/iOS)"},
        {"code": "DATA_ANALYSIS", "name": "Data Analysis", "desc": "Analisis dan interpretasi data kompleks"},
        {"code": "MACHINE_LEARNING", "name": "Machine Learning", "desc": "Pengembangan algoritma AI dan pemodelan prediktif"},
        {"code": "UI_UX", "name": "UI/UX Design", "desc": "Desain antarmuka dan pengalaman pengguna"},
        {"code": "CLOUD_COMP", "name": "Cloud Computing", "desc": "Manajemen dan implementasi layanan komputasi awan"},
        {"code": "CYBER_SEC", "name": "Cybersecurity", "desc": "Praktik melindungi sistem, jaringan, dan program dari serangan digital"},
        {"code": "DEV_OPS", "name": "DevOps Practices", "desc": "Otomatisasi integrasi, pengiriman, dan manajemen infrastruktur"},
        {"code": "DB_ADMIN", "name": "Database Administration", "desc": "Pengelolaan, perancangan, dan optimasi basis data"},
        {"code": "SYS_ANALYSIS", "name": "System Analysis & Design", "desc": "Analisis kebutuhan sistem dan perancangan arsitektur perangkat lunak"}
    ]

    print("Seeding new pure IT skills...")
    for skill_data in top_10_skills:
        new_skill = Skill(
            skill_code=skill_data['code'],
            skill_name=skill_data['name'],
            description=skill_data['desc']
        )
        db.session.add(new_skill)
    
    db.session.commit()
    print("10 Top IT skills (Non-frameworks) seeded successfully!")
