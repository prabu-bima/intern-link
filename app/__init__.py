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
    from app.extensions import db, migrate, login_manager, csrf, cache, compress
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    compress.init_app(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    from app.routes import guest, auth, student, company, admin
    app.register_blueprint(guest.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(company.bp)
    app.register_blueprint(admin.bp)

    # Import models so they are registered with SQLAlchemy
    from app import models

    # Register CLI commands
    register_cli_commands(app)

    return app


def register_error_handlers(app):
    """Register custom error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500


def register_cli_commands(app):
    """Register Flask CLI commands for automation tasks."""
    import click

    @app.cli.command('send-interview-reminders')
    def send_interview_reminders():
        """Kirim notifikasi pengingat wawancara 24 jam sebelum jadwal."""
        from app.services.notification import run_interview_reminders
        sent = run_interview_reminders()
        click.echo(f'[interview-reminders] {sent} notifikasi berhasil dikirim.')

    @app.cli.command('send-job-closing-reminders')
    @click.option('--days', default=3, show_default=True,
                  help='Kirim reminder untuk lowongan yang ditutup dalam N hari ke depan.')
    def send_job_closing_reminders(days):
        """Kirim notifikasi pengingat penutupan lowongan yang mendekati deadline."""
        from app.services.notification import run_job_closing_reminders
        sent = run_job_closing_reminders(days_before=days)
        click.echo(f'[job-closing-reminders] {sent} notifikasi berhasil dikirim.')

    @app.cli.command('normalize-industry')
    def normalize_industry():
        """Normalisasi industry_category CompanyProfile menjadi 'Software House'."""
        from app.models.identity import CompanyProfile
        from app.extensions import db
        updated = CompanyProfile.query.filter(
            (CompanyProfile.industry_category != 'Software House') |
            (CompanyProfile.industry_category.is_(None))
        ).update({CompanyProfile.industry_category: 'Software House'}, synchronize_session=False)
        db.session.commit()
        click.echo(f'[normalize-industry] {updated} baris di-update menjadi "Software House".')

