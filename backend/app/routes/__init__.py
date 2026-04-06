from .main import main_bp
from .appointmenthistory import appointment_bp


def register_routes(app):
    """Register all Flask blueprints with the app."""
    app.register_blueprint(main_bp, url_prefix='/api')
    app.register_blueprint(appointment_bp, url_prefix='/api')
