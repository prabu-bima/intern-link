from app.extensions import db

class TechnologyCategory(db.Model):
    __tablename__ = 'technology_category'
    id = db.Column(db.Integer, primary_key=True)
    category_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Skill(db.Model):
    __tablename__ = 'skill'
    id = db.Column(db.Integer, primary_key=True)
    skill_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    skill_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class TechStackItem(db.Model):
    __tablename__ = 'tech_stack_item'
    id = db.Column(db.Integer, primary_key=True)
    tech_stack_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    tech_stack_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    location_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    city = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=False, default="Indonesia")
