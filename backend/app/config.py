import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration. Values are read from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Supabase — used for user management DB operations.
    # Use the service role key on the backend (bypasses RLS for trusted server ops).
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    # JWT secret from Supabase project settings → API → JWT Secret.
    # Used to verify Supabase-issued access tokens on every protected request.
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

    # SQLAlchemy — used by the scheduling module.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///clinic.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
