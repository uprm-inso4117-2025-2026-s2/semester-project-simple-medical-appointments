import logging
from supabase import create_client, Client
from flask import current_app

logger = logging.getLogger(__name__)


def _get_supabase() -> Client:
    """Creates a Supabase client using the service role key.
    Service role bypasses RLS — only use on trusted server-side operations.
    """
    url = current_app.config['SUPABASE_URL']
    key = current_app.config['SUPABASE_SERVICE_ROLE_KEY']
    return create_client(url, key)


def _get_role_id(supabase: Client, role_name: str) -> int:
    """Looks up the integer ID for a role name from public.roles."""
    response = supabase.table('roles').select('id').eq('name', role_name).single().execute()
    return response.data['id']


def sync_user_after_registration(user_id: str, data: dict) -> dict:
    """
    Syncs a newly registered Supabase Auth user into the application DB.

    Runs after supabase.auth.signUp() succeeds on the frontend.
    Inserts: profiles → profile_settings → patients or providers → user_roles.

    If any step fails, already-inserted rows are cleaned up and the error
    is returned so the caller can surface it to the user.

    Args:
        user_id: The UUID from auth.users (returned by Supabase signUp).
        data: Validated registration payload (see auth.py for expected fields).

    Returns:
        { 'success': True } on full sync, or { 'error': str, 'step': str } on failure.
    """
    supabase = _get_supabase()
    inserted = []  # tracks what was inserted so we can clean up on failure

    try:
        # ── Step 1: profiles ──────────────────────────────────────────────
        profile_row = {
            'user_id':      user_id,
            'first_name':   data['first_name'],
            'last_name':    data['last_name'],
            'display_name': data.get('display_name', f"{data['first_name']} {data['last_name']}"),
            'username':     data['username'],
            'phone_number': data.get('phone_number'),
            'date_of_birth':data.get('date_of_birth'),
            'gender':       data.get('gender'),
        }
        supabase.table('profiles').insert(profile_row).execute()
        inserted.append(('profiles', user_id))
        logger.info('profiles row created for user %s', user_id)

        # ── Step 2: profile_settings (defaults) ───────────────────────────
        settings_row = {
            'user_id':                        user_id,
            'preferred_contact_method':       'email',
            'preferred_language':             'en',
            'notify_appointment_reminders':   True,
            'notify_appointment_updates':     True,
            'notify_messages':                True,
            'theme':                          'light',
            'accessibility_mode':             'default',
        }
        supabase.table('profile_settings').insert(settings_row).execute()
        inserted.append(('profile_settings', user_id))
        logger.info('profile_settings row created for user %s', user_id)

        # ── Step 3: role-specific table ───────────────────────────────────
        role = data['role']

        if role == 'patient':
            patient_row = {
                'user_id':                      user_id,
                'insurance_provider':           data.get('insurance_provider'),
                'insurance_member_id':          data.get('insurance_member_id'),
                'emergency_contact_name':       data.get('emergency_contact_name'),
                'emergency_contact_phone':      data.get('emergency_contact_phone'),
            }
            supabase.table('patients').insert(patient_row).execute()
            inserted.append(('patients', user_id))
            logger.info('patients row created for user %s', user_id)

            patient_settings_row = {
                'user_id':              user_id,
                'notify_laboratory':    True,
                'notify_prescription':  True,
            }
            supabase.table('patient_settings').insert(patient_settings_row).execute()
            inserted.append(('patient_settings', user_id))
            logger.info('patient_settings row created for user %s', user_id)

        elif role == 'doctor':
            provider_row = {
                'user_id':          user_id,
                'profession_title': data.get('profession_title'),
                'specialty':        data.get('specialty'),
                'license_number':   data.get('license_number'),
                'license_state':    data.get('license_state'),
                'bio':              data.get('bio'),
            }
            supabase.table('providers').insert(provider_row).execute()
            inserted.append(('providers', user_id))
            logger.info('providers row created for user %s', user_id)

            provider_settings_row = {
                'user_id':                      user_id,
                'auto_accept_appointments':     False,
                'appointment_buffer_minutes':   0,
                'default_appointment_duration': 30,
            }
            supabase.table('provider_settings').insert(provider_settings_row).execute()
            inserted.append(('provider_settings', user_id))
            logger.info('provider_settings row created for user %s', user_id)

        # ── Step 4: user_roles ────────────────────────────────────────────
        role_id = _get_role_id(supabase, role)
        supabase.table('user_roles').insert({
            'user_id': user_id,
            'role_id': role_id,
        }).execute()
        inserted.append(('user_roles', user_id))
        logger.info('user_roles row created for user %s with role %s', user_id, role)

        return {'success': True}

    except Exception as exc:
        logger.error(
            'DB sync failed for user %s at step after %s: %s',
            user_id, inserted[-1] if inserted else 'none', exc
        )
        _cleanup(supabase, inserted, user_id)
        return {'error': str(exc), 'step': inserted[-1][0] if inserted else 'profiles'}


def _cleanup(supabase: Client, inserted: list, user_id: str):
    """
    Best-effort removal of rows inserted before the failure.
    Logs any cleanup errors but does not raise — the original error takes priority.
    """
    # Reverse order to respect FK constraints
    for table, uid in reversed(inserted):
        try:
            supabase.table(table).delete().eq('user_id', uid).execute()
            logger.info('Cleanup: deleted %s row for user %s', table, uid)
        except Exception as cleanup_exc:
            logger.error('Cleanup failed for %s / user %s: %s', table, uid, cleanup_exc)
