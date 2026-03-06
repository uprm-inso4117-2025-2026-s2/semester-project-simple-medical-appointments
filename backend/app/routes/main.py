from flask import Blueprint, jsonify

# A Blueprint groups related routes together.
# 'main' is the name used internally by Flask to identify this blueprint.
# To add more route files: create a new file (e.g. appointments.py), define a blueprint,
# then import and register it in routes/__init__.py.
main_bp = Blueprint('main', __name__)


@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint — confirms the API is running.
    Useful for deployment checks and debugging connectivity.
    Access at: GET /api/health
    """
    return jsonify({'status': 'ok'})
