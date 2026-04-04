import os
from dotenv import load_dotenv

# Load variables from backend/.env using an explicit path so it works
# regardless of which directory Flask is launched from.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))


class Config:
    """Base configuration. Values are read from environment variables.
    Add new config values here as the app grows (e.g. Supabase URL, JWT secret).
    """

    # Used to sign session cookies and tokens — must be set to a strong random
    # value in production.
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Flask debug mode — True in development, False in production
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

    # Supabase settings (pulled from environment)
    SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')
