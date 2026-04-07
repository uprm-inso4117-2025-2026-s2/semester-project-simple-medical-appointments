from supabase import create_client

# Module-level client — populated by init_supabase() during app startup.
supabase = None


def init_supabase(app):
    """Initialize the Supabase client from Flask app config and attach it to the app.
    Call this inside create_app() after loading config.
    Routes can access the client via current_app.supabase or by importing supabase from this module.
    """
    global supabase

    if app.config.get("TESTING"):
        supabase = None
        app.supabase = None
        return None

    url = app.config.get('SUPABASE_URL')
    key = app.config.get('SUPABASE_KEY')

    if not url or not key:
        raise RuntimeError(
            'Supabase environment variables are missing. '
            'Set SUPABASE_URL and SUPABASE_KEY (or VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY) in backend/.env'
        )

    supabase = create_client(url, key)
    app.supabase = supabase
    return supabase
