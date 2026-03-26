import logging
from supabase import Client
 
logger = logging.getLogger(__name__)
 
UPDATABLE_PREFERENCE_FIELDS = {
    'notifications_enabled',
    'theme',
    'language',
}
 
 
def get_user_settings(supabase: Client, user_id: str) -> dict:
    """Fetch profile + account_settings for a user.
 
    Joins via: auth_users -> profiles -> account_settings
    """
    # Step 1: get profile by user_id
    try:
        profile_resp = (
            supabase.table('profiles')
            .select('id, user_id, username, full_name, avatar_url, created_at')
            .eq('user_id', user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to fetch profile for user %s: %s', user_id, exc)
        raise RuntimeError('Could not retrieve profile.') from exc
 
    if not profile_resp.data:
        raise ValueError(f'No profile found for user {user_id}.')
 
    profile = profile_resp.data
    profile_id = profile['id']
 
    # Step 2: get account_settings by profile_id
    try:
        settings_resp = (
            supabase.table('account_settings')
            .select('id, profile_id, notifications_enabled, theme, language')
            .eq('profile_id', profile_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to fetch account_settings for profile %s: %s', profile_id, exc)
        raise RuntimeError('Could not retrieve account settings.') from exc
 
    return {
        'profile':  profile,
        'settings': settings_resp.data or {},
    }
 
 
def update_user_preferences(supabase: Client, user_id: str, updates: dict) -> dict:
    """Update allowed fields in account_settings for a user.
 
    Looks up the profile_id from the user_id first, then updates account_settings.
    """
    clean = {k: v for k, v in updates.items() if k in UPDATABLE_PREFERENCE_FIELDS}
    if not clean:
        raise ValueError(
            f'No updatable fields provided. Allowed: {sorted(UPDATABLE_PREFERENCE_FIELDS)}'
        )
 
    # Resolve profile_id from user_id
    try:
        profile_resp = (
            supabase.table('profiles')
            .select('id')
            .eq('user_id', user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to resolve profile_id for user %s: %s', user_id, exc)
        raise RuntimeError('Could not resolve profile.') from exc
 
    if not profile_resp.data:
        raise ValueError(f'No profile found for user {user_id}.')
 
    profile_id = profile_resp.data['id']
 
    try:
        resp = (
            supabase.table('account_settings')
            .update(clean)
            .eq('profile_id', profile_id)
            .execute()
        )
    except Exception as exc:
        logger.error('Failed to update account_settings for profile %s: %s', profile_id, exc)
        raise RuntimeError('Could not update settings.') from exc
 
    logger.info('account_settings updated for user %s: %s', user_id, list(clean.keys()))
    return resp.data[0] if resp.data else clean