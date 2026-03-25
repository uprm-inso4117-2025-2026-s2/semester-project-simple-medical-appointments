-- ============================================================
-- Issue #10: Role-Based Permissions Configuration in Supabase
-- [DB] Role-Based Permissions Configuration in Supabase
--
-- ============================================================


-- ============================================================
-- SECTION 1: Seed Roles
-- ============================================================

INSERT INTO public.roles (name, description) VALUES
  ('patient', 'A registered user who can book and manage medical appointments'),
  ('doctor',  'A healthcare provider who manages their schedule and assigned patients'),
  ('admin',   'A system administrator with full access to all users and system settings')
ON CONFLICT (name) DO NOTHING;


-- ============================================================
-- SECTION 2: Seed Permissions
-- ============================================================

INSERT INTO public.permissions (name, description) VALUES
  -- Profile
  ('read:own_profile',       'Read own profile data'),
  ('update:own_profile',     'Update own profile data'),
  ('read:all_profiles',      'Read all user profiles'),
  ('update:all_profiles',    'Update any user profile'),
  -- Settings
  ('read:own_settings',      'Read own account and notification settings'),
  ('update:own_settings',    'Update own account and notification settings'),
  ('read:all_settings',      'Read all users settings'),
  -- Patient data
  ('read:own_patient_data',  'Read own patient record'),
  ('update:own_patient_data','Update own patient record'),
  ('read:all_patient_data',  'Read all patient records'),
  -- Provider data
  ('read:own_provider_data', 'Read own provider record'),
  ('update:own_provider_data','Update own provider record'),
  ('read:all_provider_data', 'Read all provider records'),
  -- User management (admin only)
  ('manage:user_roles',      'Assign or revoke roles for any user'),
  ('deactivate:users',       'Deactivate user accounts'),
  ('delete:users',           'Delete user accounts')
ON CONFLICT (name) DO NOTHING;


-- ============================================================
-- SECTION 3: Role-Permission Assignments
-- ============================================================

-- patient
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'patient'
  AND p.name IN (
    'read:own_profile',
    'update:own_profile',
    'read:own_settings',
    'update:own_settings',
    'read:own_patient_data',
    'update:own_patient_data'
  )
ON CONFLICT DO NOTHING;

-- doctor
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'doctor'
  AND p.name IN (
    'read:own_profile',
    'update:own_profile',
    'read:own_settings',
    'update:own_settings',
    'read:own_provider_data',
    'update:own_provider_data',
    'read:all_patient_data'   -- doctors can read patient profiles of their patients
  )
ON CONFLICT DO NOTHING;

-- admin (all permissions)
INSERT INTO public.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM public.roles r
CROSS JOIN public.permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;


-- ============================================================
-- SECTION 4: Helper Function — get_my_role()
--
-- SECURITY DEFINER lets this function bypass RLS on user_roles
-- and roles when resolving the current user's role, avoiding
-- a circular dependency (the policy would need the function,
-- but the function would hit the policy).
-- ============================================================

CREATE OR REPLACE FUNCTION public.get_my_role()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT r.name
  FROM public.user_roles ur
  JOIN public.roles r ON r.id = ur.role_id
  WHERE ur.user_id = auth.uid()
  LIMIT 1;
$$;


-- ============================================================
-- SECTION 5: Enable RLS on User Management Tables
-- ============================================================

ALTER TABLE public.profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_settings  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patients          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_settings  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.providers         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.provider_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permissions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.role_permissions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles        ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- SECTION 6: RLS Policies
-- ============================================================

-- ------------------------------------------------------------
-- profiles
-- ------------------------------------------------------------

-- All authenticated users: read and write their own profile
CREATE POLICY "profiles: read own"
  ON public.profiles FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "profiles: insert own"
  ON public.profiles FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "profiles: update own"
  ON public.profiles FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Admins: read and update all profiles
CREATE POLICY "profiles: admin read all"
  ON public.profiles FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');

CREATE POLICY "profiles: admin update all"
  ON public.profiles FOR UPDATE TO authenticated
  USING (public.get_my_role() = 'admin');

-- Doctors: read profiles of patients with appointments under them
CREATE POLICY "profiles: doctor reads assigned patients"
  ON public.profiles FOR SELECT TO authenticated
  USING (
    public.get_my_role() = 'doctor'
    AND EXISTS (
      SELECT 1 FROM public.appointments a
      JOIN public.doctors d ON d.id = a.doctor_id
      WHERE d.user_id = auth.uid()
        AND a.patient_id = profiles.user_id
    )
  );


-- ------------------------------------------------------------
-- profile_settings
-- ------------------------------------------------------------

CREATE POLICY "profile_settings: read own"
  ON public.profile_settings FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "profile_settings: insert own"
  ON public.profile_settings FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "profile_settings: update own"
  ON public.profile_settings FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "profile_settings: admin read all"
  ON public.profile_settings FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- patients
-- ------------------------------------------------------------

CREATE POLICY "patients: read own"
  ON public.patients FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "patients: insert own"
  ON public.patients FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "patients: update own"
  ON public.patients FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Doctors can read patient records for their assigned patients only
CREATE POLICY "patients: doctor read assigned"
  ON public.patients FOR SELECT TO authenticated
  USING (
    public.get_my_role() = 'doctor'
    AND EXISTS (
      SELECT 1 FROM public.appointments a
      JOIN public.doctors d ON d.id = a.doctor_id
      WHERE d.user_id = auth.uid()
        AND a.patient_id = patients.user_id
    )
  );

CREATE POLICY "patients: admin read all"
  ON public.patients FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');

CREATE POLICY "patients: admin update all"
  ON public.patients FOR UPDATE TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- patient_settings
-- ------------------------------------------------------------

CREATE POLICY "patient_settings: read own"
  ON public.patient_settings FOR SELECT TO authenticated
  USING (
    auth.uid() = (SELECT user_id FROM public.patients WHERE user_id = patient_settings.user_id)
  );

CREATE POLICY "patient_settings: insert own"
  ON public.patient_settings FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "patient_settings: update own"
  ON public.patient_settings FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "patient_settings: admin read all"
  ON public.patient_settings FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- providers
-- ------------------------------------------------------------

CREATE POLICY "providers: read own"
  ON public.providers FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "providers: insert own"
  ON public.providers FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "providers: update own"
  ON public.providers FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "providers: admin read all"
  ON public.providers FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');

CREATE POLICY "providers: admin update all"
  ON public.providers FOR UPDATE TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- provider_settings
-- ------------------------------------------------------------

CREATE POLICY "provider_settings: read own"
  ON public.provider_settings FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "provider_settings: insert own"
  ON public.provider_settings FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "provider_settings: update own"
  ON public.provider_settings FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "provider_settings: admin read all"
  ON public.provider_settings FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- roles  (reference table — all authenticated users can read)
-- ------------------------------------------------------------

CREATE POLICY "roles: authenticated read all"
  ON public.roles FOR SELECT TO authenticated
  USING (true);

CREATE POLICY "roles: admin insert"
  ON public.roles FOR INSERT TO authenticated
  WITH CHECK (public.get_my_role() = 'admin');

CREATE POLICY "roles: admin update"
  ON public.roles FOR UPDATE TO authenticated
  USING (public.get_my_role() = 'admin');

CREATE POLICY "roles: admin delete"
  ON public.roles FOR DELETE TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- permissions  (reference table — all authenticated users can read)
-- ------------------------------------------------------------

CREATE POLICY "permissions: authenticated read all"
  ON public.permissions FOR SELECT TO authenticated
  USING (true);

CREATE POLICY "permissions: admin insert"
  ON public.permissions FOR INSERT TO authenticated
  WITH CHECK (public.get_my_role() = 'admin');

CREATE POLICY "permissions: admin update"
  ON public.permissions FOR UPDATE TO authenticated
  USING (public.get_my_role() = 'admin');

CREATE POLICY "permissions: admin delete"
  ON public.permissions FOR DELETE TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- role_permissions  (reference table — all authenticated users can read)
-- ------------------------------------------------------------

CREATE POLICY "role_permissions: authenticated read all"
  ON public.role_permissions FOR SELECT TO authenticated
  USING (true);

CREATE POLICY "role_permissions: admin insert"
  ON public.role_permissions FOR INSERT TO authenticated
  WITH CHECK (public.get_my_role() = 'admin');

CREATE POLICY "role_permissions: admin delete"
  ON public.role_permissions FOR DELETE TO authenticated
  USING (public.get_my_role() = 'admin');


-- ------------------------------------------------------------
-- user_roles
-- ------------------------------------------------------------

-- Users can read their own role assignments
CREATE POLICY "user_roles: read own"
  ON public.user_roles FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

-- Only admins can assign or revoke roles
CREATE POLICY "user_roles: admin read all"
  ON public.user_roles FOR SELECT TO authenticated
  USING (public.get_my_role() = 'admin');

CREATE POLICY "user_roles: admin insert"
  ON public.user_roles FOR INSERT TO authenticated
  WITH CHECK (public.get_my_role() = 'admin');

CREATE POLICY "user_roles: admin delete"
  ON public.user_roles FOR DELETE TO authenticated
  USING (public.get_my_role() = 'admin');
