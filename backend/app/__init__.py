from flask import Flask
from flask_cors import CORS

from .config import Config
from .routes import register_routes
from .supabase import init_supabase


def create_app(testing: bool = False):
    """Application factory — creates and configures the Flask app.
    Using a factory function (instead of a global app object) makes it easier
    to create multiple app instances for testing.
    """
    app = Flask(__name__)

    app.config.from_object(Config)
    if testing:
        app.config["TESTING"] = True

    CORS(app)
    init_supabase(app)
    register_routes(app)

    return app
