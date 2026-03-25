import sqlite3
import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()


class Config:
    """Base configuration. Values are read from environment variables.
    Add new config values here as the app grows (e.g. database URL, JWT
secret).
    """

    # Used to sign session cookies and tokens — must be set to a strong
random
    # value in production. See backend/.env.example.
    SECRET_KEY = os.getenv('SECRET_KEY',
'dev-secret-key-change-in-production')

    # Flask debug mode — True in development, False in production
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

    # Supabase — used for user management DB operations.
    # Use the service role key on the backend (bypasses RLS for trusted
server ops).
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    # SQLAlchemy — used by the scheduling module.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
'sqlite:///clinic.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn