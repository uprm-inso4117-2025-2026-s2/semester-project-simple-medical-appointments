import os
import sqlite3

from dotenv import load_dotenv

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))


class Config:
    """Base configuration. Values are read from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_KEY = (
        os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("VITE_SUPABASE_ANON_KEY")
    )
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///clinic.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
