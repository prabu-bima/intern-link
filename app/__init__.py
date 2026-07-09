import os

from flask import Flask, render_template


def create_app(config_name=None):
    """Application factory for creating the Flask app instance."""
    app = Flask(__name__)

    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Load configuration
    config_map = {
        'development': 'config.DevelopmentConfig',
        'testing': 'config.TestingConfig',
        'production': 'config.ProductionConfig',
    }
    app.config.from_object(config_map.get(config_name, 'config.DevelopmentConfig'))

    # Initialize extensions
    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # Register error handlers
    register_error_handlers(app)

    # Root route (temporary, will be replaced by guest blueprint)
    @app.route('/')
    def index():
        return '<h1>InternLink</h1><p>Platform is running.</p>'

    return app


def register_error_handlers(app):
    """Register custom error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
