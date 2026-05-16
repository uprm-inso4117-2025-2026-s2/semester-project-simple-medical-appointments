import logging
from supabase import Client
 
logger = logging.getLogger(__name__)
 
UPDATABLE_PREFERENCE_FIELDS = {
    'preferred_contact_method',
    'preferred_language',
    'notify_appointment_reminders',
    'notify_appointment_updates',
    'notify_messages',
    'theme',
    'accessibility_mode',
}
 
 
def get_user_settings(supabase: Client, user_id: str) -> dict:
    """Fetch profile + profile_settings for a user.

    Both tables use user_id as PK — no join needed.
    """
    # Step 1: get profile by user_id
    try:
        profile_resp = (
            supabase.table('profiles')
            .select(
                'user_id, first_name, last_name, display_name, username, '
                'avatar_url, banner_url, phone_number, date_of_birth, gender, created_at'
            )
            .eq('user_id', user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to fetch profile for user %s: %s', user_id, exc)
        raise RuntimeError('Could not retrieve profile.') from exc

    if not profile_resp.data:
        raise ValueError(f'No profile found for user {user_id}.')

    # Step 2: get profile_settings by user_id directly
    try:
        settings_resp = (
            supabase.table('profile_settings')
            .select(
                'user_id, preferred_contact_method, preferred_language, '
                'notify_appointment_reminders, notify_appointment_updates, '
                'notify_messages, theme, accessibility_mode'
            )
            .eq('user_id', user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to fetch profile_settings for user %s: %s', user_id, exc)
        raise RuntimeError('Could not retrieve account settings.') from exc

    return {
        'settings': settings_resp.data or {},
    }
 
 
def update_user_preferences(supabase: Client, user_id: str, updates: dict) -> dict:
    """Update allowed fields in profile_settings for a user.

    profile_settings uses user_id as PK — no profile lookup needed.
    """
    clean = {k: v for k, v in updates.items() if k in UPDATABLE_PREFERENCE_FIELDS}
    if not clean:
        raise ValueError(
            f'No updatable fields provided. Allowed: {sorted(UPDATABLE_PREFERENCE_FIELDS)}'
        )

    try:
        resp = (
            supabase.table('profile_settings')
            .update(clean)
            .eq('user_id', user_id)
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to update profile_settings for user %s: %s', user_id, exc)
        raise RuntimeError('Could not update settings.') from exc

    logger.info('profile_settings updated for user %s: %s', user_id, list(clean.keys()))
    return resp.data[0] if resp.data else clean