"""Flask extensions module."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions (without linking to the app yet)
db = SQLAlchemy()
migrate = Migrate()
