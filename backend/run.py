# run.py — entry point for starting the Flask development server.
# Run with: python run.py
# In production, use a WSGI server like gunicorn instead:
#   gunicorn "app:create_app()"
import init_db  # Initializes the database on server startup

from app import create_app

# Create the Flask app using the factory function in app/__init__.py
app = create_app()

if __name__ == '__main__':
    # debug=True enables auto-reload on file changes and detailed error pages.
    # This is safe for local development only — never run debug=True in production.
    app.run(debug=True, port=5000)
