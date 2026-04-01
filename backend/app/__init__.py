from flask import Flask
from flask_cors import CORS
from .config import Config
from .routes import register_routes
from .models import db     

def create_app():
    """Application factory — creates and configures the Flask app.
    Using a factory function (instead of a global app object) makes it easier
    to create multiple app instances for testing.
    """
    app = Flask(__name__)
    from flask_cors import CORS
    CORS(app)

    # Load configuration from the Config class (reads from .env via config.py)
    app.config.from_object(Config)

    # Enable CORS so the React frontend (on a different port) can call this API.
    # In production, restrict origins to your actual domain instead of allowing all.
    CORS(app)

    # Register all route blueprints (see app/routes/__init__.py)
    register_routes(app)

    db.init_app(app)   
    
    with app.app_context():
        db.create_all()

    return app