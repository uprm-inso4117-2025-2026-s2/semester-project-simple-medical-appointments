import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from flask import Blueprint, current_app, jsonify, request

profile_bp = Blueprint('profile', __name__)

ALLOWED_UPDATE_FIELDS = {'name', 'avatar', 'specialty', 'notify_appointment_reminders', 'notify_appointment_updates', 'notify_messages'}

BOOLEAN_SETTINGS_FIELDS = {'notify_appointment_reminders', 'notify_appointment_updates', 'notify_messages'}


def _get_supabase_credentials() -> tuple[str | None, str | None]:
    url = current_app.config.get('SUPABASE_URL')
    key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')
    return url, key


def _supabase_request(
    method: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
    json_body: dict | None = None,
    user_token: str | None = None,
    prefer: str | None = None,
) -> tuple[int | None, object | None, str | None]:
    """Issue a request to Supabase REST/Auth API.

    Returns: (status_code, parsed_json_or_text, transport_error_message)
    """
    base_url, service_key = _get_supabase_credentials()
    if not base_url or not service_key:
        return None, None, 'Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env.'

    base_url = base_url.rstrip('/')
    url = f"{base_url}{path}"
    if query:
        from urllib.parse import urlencode
        url = f"{url}?{urlencode(query)}"

    headers = {
        'apikey': service_key,
        'Authorization': f"Bearer {user_token or service_key}",
    }
    if json_body is not None:
        headers['Content-Type'] = 'application/json'
    if prefer:
        headers['Prefer'] = prefer

    data = json.dumps(json_body).encode('utf-8') if json_body is not None else None
    req = Request(url=url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=20) as resp:
            raw = resp.read().decode('utf-8')
            if not raw:
                return resp.status, None, None
            try:
                return resp.status, json.loads(raw), None
            except json.JSONDecodeError:
                return resp.status, raw, None
    except HTTPError as exc:
        raw = exc.read().decode('utf-8') if exc.fp else ''
        parsed: object | None
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw or None
        return exc.code, parsed, None
    except URLError as exc:
        return None, None, f'Supabase request failed: {exc.reason}'
    except Exception as exc:
        return None, None, f'Supabase request failed: {exc}'


def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:].strip()
    return token or None


def _parse_user_id(user_obj) -> str | None:
    if user_obj is None:
        return None
    if isinstance(user_obj, dict):
        return user_obj.get('id')
    return getattr(user_obj, 'id', None)


def _get_request_user_and_role() -> tuple[str | None, str | None, tuple | None]:
    """Authenticate request using Bearer token and resolve the requester's role."""
    token = _extract_bearer_token()
    if not token:
        return None, None, (jsonify({'error': 'Missing or invalid Authorization header.'}), 401)

    status, user_response, transport_error = _supabase_request(
        'GET',
        '/auth/v1/user',
        user_token=token,
    )

    if transport_error:
        return None, None, (jsonify({'error': 'Supabase backend configuration error.', 'detail': transport_error}), 500)

    if status != 200 or not isinstance(user_response, dict):
        return None, None, (jsonify({'error': 'Invalid or expired access token.'}), 401)

    user_id = _parse_user_id(user_response)
    if not user_id:
        user_id = _parse_user_id(user_response.get('user')) if isinstance(user_response, dict) else None

    if not user_id:
        return None, None, (jsonify({'error': 'Invalid or expired access token.'}), 401)

    role_name = None
    role_status, role_response, _ = _supabase_request(
        'GET',
        '/rest/v1/user_roles',
        query={
            'user_id': f'eq.{user_id}',
            'select': 'roles(name)',
        },
    )
    if role_status == 200 and isinstance(role_response, list):
        role_names = [(row.get('roles') or {}).get('name') for row in role_response if isinstance(row, dict)]
        role_names = [name for name in role_names if name]
        if 'admin' in role_names:
            role_name = 'admin'
        elif role_names:
            role_name = role_names[0]

    return user_id, role_name, None


def _can_access_target(request_user_id: str, request_role: str | None, target_user_id: str) -> bool:
    return request_user_id == target_user_id or request_role == 'admin'


def _is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except Exception:
        return False
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def _normalize_profile_response(
    profile_row: dict,
    provider_row: dict | None,
    provider_settings_row: dict | None,
    patient_row: dict | None,
    settings_row: dict | None,
) -> dict:
    return {
        # Core identity
        'user_id':      profile_row.get('user_id'),
        'name':         profile_row.get('display_name'),
        'avatar':       profile_row.get('avatar_url'),
        # Personal information
        'first_name':   profile_row.get('first_name'),
        'last_name':    profile_row.get('last_name'),
        'display_name': profile_row.get('display_name'),
        'username':     profile_row.get('username'),
        'phone_number': profile_row.get('phone_number'),
        'date_of_birth': profile_row.get('date_of_birth'),
        'gender':       profile_row.get('gender'),
        'member_since': profile_row.get('created_at'),
        # Provider-specific (None for non-providers)
        'specialty':         provider_row.get('specialty')         if provider_row else None,
        'profession_title':  provider_row.get('profession_title')  if provider_row else None,
        'license_number':    provider_row.get('license_number')    if provider_row else None,
        'license_state':     provider_row.get('license_state')     if provider_row else None,
        'bio':               provider_row.get('bio')               if provider_row else None,
        # Provider settings (None for non-providers)
        'auto_accept_appointments':      provider_settings_row.get('auto_accept_appointments')      if provider_settings_row else None,
        'appointment_buffer_minutes':    provider_settings_row.get('appointment_buffer_minutes')    if provider_settings_row else None,
        'default_appointment_duration':  provider_settings_row.get('default_appointment_duration')  if provider_settings_row else None,
        # Patient-specific (None for non-patients)
        'insurance_provider':      patient_row.get('insurance_provider')      if patient_row else None,
        'insurance_member_id':     patient_row.get('insurance_member_id')     if patient_row else None,
        'emergency_contact_name':  patient_row.get('emergency_contact_name')  if patient_row else None,
        'emergency_contact_phone': patient_row.get('emergency_contact_phone') if patient_row else None,
        # Settings (None if no settings row exists)
        'preferred_contact_method':     settings_row.get('preferred_contact_method')     if settings_row else None,
        'preferred_language':           settings_row.get('preferred_language')           if settings_row else None,
        'notify_appointment_reminders': settings_row.get('notify_appointment_reminders') if settings_row else None,
        'notify_appointment_updates':   settings_row.get('notify_appointment_updates')   if settings_row else None,
        'notify_messages':              settings_row.get('notify_messages')              if settings_row else None,
        'accessibility_mode':           settings_row.get('accessibility_mode')           if settings_row else None,
    }


def _fetch_profile_payload(user_id: str) -> tuple[dict | None, tuple | None]:
    # ── profiles ──────────────────────────────────────────────────────────────
    profile_status, profile_response, transport_error = _supabase_request(
        'GET',
        '/rest/v1/profiles',
        query={
            'user_id': f'eq.{user_id}',
            'select': 'user_id,first_name,last_name,display_name,username,avatar_url,phone_number,date_of_birth,gender,created_at',
        },
    )
    if transport_error:
        return None, (jsonify({'error': 'Failed to fetch profile.', 'detail': transport_error}), 500)

    if profile_status != 200 or not isinstance(profile_response, list):
        return None, (jsonify({'error': 'Failed to fetch profile.'}), 500)

    if not profile_response:
        return None, (jsonify({'error': 'Profile not found.'}), 404)

    profile_row = profile_response[0]

    # ── providers (only present for doctor accounts) ──────────────────────────
    provider_row = None
    provider_status, provider_response, _ = _supabase_request(
        'GET',
        '/rest/v1/providers',
        query={
            'user_id': f'eq.{user_id}',
            'select': 'profession_title,specialty,license_number,license_state,bio',
            'limit': '1',
        },
    )
    if provider_status == 200 and isinstance(provider_response, list) and provider_response:
        provider_row = provider_response[0]

    # ── provider_settings (only present for doctor accounts) ──────────────────
    provider_settings_row = None
    ps_status, ps_response, _ = _supabase_request(
        'GET',
        '/rest/v1/provider_settings',
        query={
            'user_id': f'eq.{user_id}',
            'select': 'auto_accept_appointments,appointment_buffer_minutes,default_appointment_duration',
            'limit': '1',
        },
    )
    if ps_status == 200 and isinstance(ps_response, list) and ps_response:
        provider_settings_row = ps_response[0]

    # ── patients (insurance + emergency contact — only present for patient accounts) ──
    patient_row = None
    patient_status, patient_response, _ = _supabase_request(
        'GET',
        '/rest/v1/patients',
        query={
            'user_id': f'eq.{user_id}',
            'select': 'insurance_provider,insurance_member_id,emergency_contact_name,emergency_contact_phone',
            'limit': '1',
        },
    )
    if patient_status == 200 and isinstance(patient_response, list) and patient_response:
        patient_row = patient_response[0]

    # ── profile_settings (notifications + preferences) ────────────────────────
    settings_row = None
    settings_status, settings_response, _ = _supabase_request(
        'GET',
        '/rest/v1/profile_settings',
        query={
            'user_id': f'eq.{user_id}',
            'select': 'preferred_contact_method,preferred_language,notify_appointment_reminders,notify_appointment_updates,notify_messages,accessibility_mode',
            'limit': '1',
        },
    )
    if settings_status == 200 and isinstance(settings_response, list) and settings_response:
        settings_row = settings_response[0]

    return _normalize_profile_response(profile_row, provider_row, provider_settings_row, patient_row, settings_row), None


@profile_bp.route('/<user_id>', methods=['GET'])
def get_profile(user_id: str):
    """GET /api/profile/<user_id> — return profile for self or admin."""
    request_user_id, request_role, auth_error = _get_request_user_and_role()
    if auth_error:
        return auth_error

    if not _can_access_target(request_user_id, request_role, user_id):
        return jsonify({'error': 'Forbidden: you can only access your own profile.'}), 403

    payload, fetch_error = _fetch_profile_payload(user_id)
    if fetch_error:
        return fetch_error

    return jsonify(payload), 200


@profile_bp.route('/<user_id>', methods=['PUT'])
def update_profile(user_id: str):
    """PUT /api/profile/<user_id> — update allowed profile fields for self or admin."""
    request_user_id, request_role, auth_error = _get_request_user_and_role()
    if auth_error:
        return auth_error

    if not _can_access_target(request_user_id, request_role, user_id):
        return jsonify({'error': 'Forbidden: you can only update your own profile.'}), 403

    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON (Content-Type: application/json).'}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid JSON body.'}), 400

    unknown_fields = sorted(set(data.keys()) - ALLOWED_UPDATE_FIELDS)
    if unknown_fields:
        return jsonify({'error': f"Unknown fields: {', '.join(unknown_fields)}"}), 400

    if not data:
        return jsonify({'error': 'No fields provided for update.'}), 400

    profile_updates = {}
    provider_updates = {}
    settings_updates = {}

    if 'name' in data:
        name = data.get('name')
        if not isinstance(name, str) or not name.strip():
            return jsonify({'error': 'Field "name" must be a non-empty string.'}), 400
        name = name.strip()
        if len(name) > 100:
            return jsonify({'error': 'Field "name" must be at most 100 characters.'}), 400
        profile_updates['display_name'] = name

    if 'avatar' in data:
        avatar = data.get('avatar')
        if avatar is None:
            profile_updates['avatar_url'] = None
        else:
            if not isinstance(avatar, str) or not avatar.strip():
                return jsonify({'error': 'Field "avatar" must be a valid URL string or null.'}), 400
            avatar = avatar.strip()
            if len(avatar) > 2048 or not _is_valid_http_url(avatar):
                return jsonify({'error': 'Field "avatar" must be a valid http/https URL.'}), 400
            profile_updates['avatar_url'] = avatar

    if 'specialty' in data:
        specialty = data.get('specialty')
        if specialty is None:
            provider_updates['specialty'] = None
        else:
            if not isinstance(specialty, str) or not specialty.strip():
                return jsonify({'error': 'Field "specialty" must be a non-empty string or null.'}), 400
            specialty = specialty.strip()
            if len(specialty) > 100:
                return jsonify({'error': 'Field "specialty" must be at most 100 characters.'}), 400
            provider_updates['specialty'] = specialty

    for field in BOOLEAN_SETTINGS_FIELDS:
        if field in data:
            value = data.get(field)
            if not isinstance(value, bool):
                return jsonify({'error': f'Field "{field}" must be a boolean.'}), 400
            settings_updates[field] = value

    if not profile_updates and not provider_updates and not settings_updates:
        return jsonify({'error': 'No valid fields provided for update.'}), 400

    if profile_updates:
        update_status, _, transport_error = _supabase_request(
            'PATCH',
            '/rest/v1/profiles',
            query={'user_id': f'eq.{user_id}'},
            json_body=profile_updates,
            prefer='return=minimal',
        )
        if transport_error:
            return jsonify({'error': 'Failed to update profile.', 'detail': transport_error}), 500
        if update_status not in (200, 204):
            return jsonify({'error': 'Failed to update profile.'}), 500

    if provider_updates:
        provider_status, provider_exists_response, transport_error = _supabase_request(
            'GET',
            '/rest/v1/providers',
            query={
                'user_id': f'eq.{user_id}',
                'select': 'user_id',
                'limit': '1',
            },
        )
        if transport_error:
            return jsonify({'error': 'Failed to update profile.', 'detail': transport_error}), 500
        if provider_status != 200 or not isinstance(provider_exists_response, list):
            return jsonify({'error': 'Failed to update profile.'}), 500
        if not provider_exists_response:
            return jsonify({'error': 'Field "specialty" can only be updated for provider profiles.'}), 400

        provider_update_status, _, transport_error = _supabase_request(
            'PATCH',
            '/rest/v1/providers',
            query={'user_id': f'eq.{user_id}'},
            json_body=provider_updates,
            prefer='return=minimal',
        )
        if transport_error:
            return jsonify({'error': 'Failed to update profile.', 'detail': transport_error}), 500
        if provider_update_status not in (200, 204):
            return jsonify({'error': 'Failed to update profile.'}), 500

    if settings_updates:
        settings_update_status, _, transport_error = _supabase_request(
            'PATCH',
            '/rest/v1/profile_settings',
            query={'user_id': f'eq.{user_id}'},
            json_body=settings_updates,
            prefer='return=minimal',
        )
        if transport_error:
            return jsonify({'error': 'Failed to update settings.', 'detail': transport_error}), 500
        if settings_update_status not in (200, 204):
            return jsonify({'error': 'Failed to update settings.'}), 500

    payload, fetch_error = _fetch_profile_payload(user_id)
    if fetch_error:
        return fetch_error

    return jsonify(payload), 200
