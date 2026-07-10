import sys
from app import create_app
from app.extensions import db
from app.models.master import TechStackItem

app = create_app()

with app.app_context():
    existing_count = TechStackItem.query.count()
    if existing_count == 0:
        print("Seeding Tech Stack Items...")
        tools = [
            {"code": "GIT", "name": "Git / GitHub", "desc": "Version Control System"},
            {"code": "DOCKER", "name": "Docker", "desc": "Containerization platform"},
            {"code": "POSTGRES", "name": "PostgreSQL", "desc": "Relational Database"},
            {"code": "MONGO", "name": "MongoDB", "desc": "NoSQL Database"},
            {"code": "REDIS", "name": "Redis", "desc": "In-memory data structure store"},
            {"code": "AWS", "name": "AWS (Amazon Web Services)", "desc": "Cloud platform"},
            {"code": "FIGMA", "name": "Figma", "desc": "Design tool"},
            {"code": "POSTMAN", "name": "Postman", "desc": "API Testing tool"},
            {"code": "LINUX", "name": "Linux OS", "desc": "Operating System"},
            {"code": "KUBERNETES", "name": "Kubernetes", "desc": "Container Orchestration"}
        ]
        for t in tools:
            new_item = TechStackItem(
                tech_stack_code=t['code'],
                tech_stack_name=t['name'],
                description=t['desc']
            )
            db.session.add(new_item)
        db.session.commit()
        print("Seeded 10 Tech Stack items.")
    else:
        print(f"Database already has {existing_count} Tech Stack items.")
