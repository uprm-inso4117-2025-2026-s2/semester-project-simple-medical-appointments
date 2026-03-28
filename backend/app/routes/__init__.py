from .main import main_bp
from .closures import closures_bp
from . import appointmenthistory  # noqa: F401 — registers route on
main_bp
from .appointments import appointments_bp
from .auth import auth_bp
from .profile import profile_bp


def register_routes(app):
    """Register all Flask blueprints with the app.
    Each blueprint groups a set of related routes (e.g. all appointment
routes).
    Add new blueprints here as the API grows.
    """
    app.register_blueprint(main_bp, url_prefix='/api')
    app.register_blueprint(appointments_bp,
url_prefix='/api/appointments')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    # app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(closures_bp, url_prefix='/api/closures')
