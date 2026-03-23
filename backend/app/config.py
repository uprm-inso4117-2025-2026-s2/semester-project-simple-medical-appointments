import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()


class Config:
    """Base configuration. Values are read from environment variables.
    Add new config values here as the app grows (e.g. database URL, JWT secret).
    """

    # Used to sign session cookies and tokens — must be set to a strong random
    # value in production. See backend/.env.example.
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Flask debug mode — True in development, False in production
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
    # DATABASE_URL=postgresql://user:password@localhost/clinic_db
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///clinic.db')
 
    # Disable a feature we don't need
    SQLALCHEMY_TRACK_MODIFICATIONS = False