import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

    # Session & Security
    SESSION_PROTECTION = 'strong'
    REMEMBER_COOKIE_HTTPONLY = True

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # Supabase
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
    SUPABASE_STORAGE_BUCKET = os.environ.get('SUPABASE_STORAGE_BUCKET', 'internlink')

    # Groq AI
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

    # Mail (for Forgot Password)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    FLASK_ENV = 'development'


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    FLASK_ENV = 'testing'

    # Use separate test database
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///test.db')


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    FLASK_ENV = 'production'

    # In production, SECRET_KEY must be set via environment variable
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
