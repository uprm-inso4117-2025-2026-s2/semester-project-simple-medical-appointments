from flask import Blueprint, request, jsonify, current_app
from supabase import create_client
 
from app.middleware.auth import require_auth
from app.services.settings_service import (
    get_user_settings,
    update_user_preferences,
    UPDATABLE_PREFERENCE_FIELDS,
)
 
settings_bp = Blueprint('settings', __name__)
 
 
def _get_supabase():
    url = current_app.config['SUPABASE_URL']
    key = current_app.config['SUPABASE_SERVICE_ROLE_KEY']
    return create_client(url, key)
 
 
@settings_bp.route('/<user_id>', methods=['GET'])
@require_auth
def get_settings(current_user_id: str, user_id: str):
    """GET /api/settings/<user_id>
 
    Returns:
        200: { "profile": { username, full_name, avatar_url, ... },
               "settings": { notifications_enabled, theme, language } }
        403: requesting user != user_id in URL
        404: no profile found
        500: Supabase error
    """
    if current_user_id != user_id:
        return jsonify({'error': 'Forbidden. You can only access your own settings.'}), 403
 
    supabase = _get_supabase()
    try:
        data = get_user_settings(supabase, user_id)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 500
 
    return jsonify(data), 200
 
 
@settings_bp.route('/<user_id>', methods=['PUT'])
@require_auth
def update_settings(current_user_id: str, user_id: str):
    """PUT /api/settings/<user_id>
 
    Accepted JSON fields (all optional, send only what you want to change):
        notifications_enabled   bool
        theme                   string   e.g. "light" | "dark"
        language                string   e.g. "en" | "es"
 
    Returns:
        200: { "updated_preferences": { ... } }
        400: no valid fields / bad JSON
        403: requesting user != user_id in URL
        500: Supabase error
    """
    if current_user_id != user_id:
        return jsonify({'error': 'Forbidden. You can only update your own settings.'}), 403
 
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON.'}), 400
 
    supabase = _get_supabase()
    try:
        updated = update_user_preferences(supabase, user_id, data)
    except ValueError as exc:
        return jsonify({'error': str(exc), 'allowed_fields': sorted(UPDATABLE_PREFERENCE_FIELDS)}), 400
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 500
 
    return jsonify({'updated_preferences': updated}), 200