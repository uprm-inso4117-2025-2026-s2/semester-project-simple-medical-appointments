from .main import main_bp
from .appointmenthistory import appointment_bp
from .profile import profile_bp
from .account_settings import settings_bp
from .appointments import appointments_bp
from .admin import admin_bp


def register_routes(app):
    """Register all Flask blueprints with the app."""
    app.register_blueprint(main_bp, url_prefix='/api')
    app.register_blueprint(appointment_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')