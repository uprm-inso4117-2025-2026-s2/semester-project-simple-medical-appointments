-- TABLES

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
);

-- TODO: user_roles
-- TODO: permissions
-- TODO: role_permissions
-- TODO: profiles
-- TODO: profile_settings
-- TODO: patients
-- TODO: patient_settings
-- TODO: providers
-- TODO: provider_settings