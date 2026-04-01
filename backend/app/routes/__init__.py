from .main import main_bp
from .dailySlots import slots_bp
# Import new blueprint modules here as you add them, for example:
# from .appointments import appointments_bp
# from .users import users_bp


def register_routes(app):
    """Register all Flask blueprints with the app.
    Each blueprint groups a set of related routes (e.g. all appointment routes).
    Add new blueprints here as the API grows.
    """
    app.register_blueprint(main_bp, url_prefix='/api')
    # app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    # app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(slots_bp)
