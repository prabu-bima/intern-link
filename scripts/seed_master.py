import sys
import os

# Add the project root to the python path so we can import 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.master import (
    TechnologyCategory,
    Skill,
    TechStackItem,
    Location
)

app = create_app()

def seed_data():
    with app.app_context():
        # Technology Categories
        tech_categories = [
            {'code': 'frontend', 'name': 'Frontend Development', 'desc': 'Technologies used for building user interfaces.'},
            {'code': 'backend', 'name': 'Backend Development', 'desc': 'Technologies used for server-side logic and APIs.'},
            {'code': 'database', 'name': 'Database & Storage', 'desc': 'SQL and NoSQL database systems.'},
            {'code': 'cloud', 'name': 'Cloud & DevOps', 'desc': 'Cloud platforms and deployment tools.'},
            {'code': 'mobile', 'name': 'Mobile Development', 'desc': 'Technologies for iOS and Android development.'},
            {'code': 'aiml', 'name': 'AI & Machine Learning', 'desc': 'Tools for artificial intelligence and data science.'}
        ]
        for c in tech_categories:
            if not TechnologyCategory.query.filter_by(category_code=c['code']).first():
                db.session.add(TechnologyCategory(category_code=c['code'], category_name=c['name'], description=c['desc']))

        # Skills
        skills = [
            {'code': 'python', 'name': 'Python', 'desc': 'General-purpose programming language.'},
            {'code': 'javascript', 'name': 'JavaScript', 'desc': 'Core language of the web.'},
            {'code': 'java', 'name': 'Java', 'desc': 'Object-oriented programming language.'},
            {'code': 'sql', 'name': 'SQL', 'desc': 'Structured Query Language for databases.'},
            {'code': 'problem_solving', 'name': 'Problem Solving', 'desc': 'Analytical skills and critical thinking.'},
            {'code': 'communication', 'name': 'Communication', 'desc': 'Effective verbal and written communication.'},
            {'code': 'teamwork', 'name': 'Teamwork', 'desc': 'Ability to work collaboratively in a team.'}
        ]
        for s in skills:
            if not Skill.query.filter_by(skill_code=s['code']).first():
                db.session.add(Skill(skill_code=s['code'], skill_name=s['name'], description=s['desc']))

        # Tech Stack Items
        tech_stacks = [
            {'code': 'flask', 'name': 'Flask', 'desc': 'Python micro web framework.'},
            {'code': 'django', 'name': 'Django', 'desc': 'High-level Python Web framework.'},
            {'code': 'react', 'name': 'React', 'desc': 'JavaScript library for building user interfaces.'},
            {'code': 'vue', 'name': 'Vue.js', 'desc': 'Progressive JavaScript Framework.'},
            {'code': 'postgresql', 'name': 'PostgreSQL', 'desc': 'Advanced open source relational database.'},
            {'code': 'mysql', 'name': 'MySQL', 'desc': 'Open-source relational database management system.'},
            {'code': 'docker', 'name': 'Docker', 'desc': 'Platform for developing, shipping, and running applications.'},
            {'code': 'aws', 'name': 'AWS', 'desc': 'Amazon Web Services.'}
        ]
        for t in tech_stacks:
            if not TechStackItem.query.filter_by(tech_stack_code=t['code']).first():
                db.session.add(TechStackItem(tech_stack_code=t['code'], tech_stack_name=t['name'], description=t['desc']))

        # Locations
        locations = [
            {'code': 'jakarta', 'city': 'Jakarta', 'region': 'DKI Jakarta', 'country': 'Indonesia'},
            {'code': 'bandung', 'city': 'Bandung', 'region': 'Jawa Barat', 'country': 'Indonesia'},
            {'code': 'yogyakarta', 'city': 'Yogyakarta', 'region': 'DI Yogyakarta', 'country': 'Indonesia'},
            {'code': 'surabaya', 'city': 'Surabaya', 'region': 'Jawa Timur', 'country': 'Indonesia'},
            {'code': 'purwokerto', 'city': 'Purwokerto', 'region': 'Jawa Tengah', 'country': 'Indonesia'},
            {'code': 'remote', 'city': 'Remote', 'region': 'Anywhere', 'country': 'Indonesia'}
        ]
        for loc in locations:
            if not Location.query.filter_by(location_code=loc['code']).first():
                db.session.add(Location(location_code=loc['code'], city=loc['city'], region=loc['region'], country=loc['country']))

        db.session.commit()
        print("Successfully seeded master data tables.")

if __name__ == '__main__':
    seed_data()
