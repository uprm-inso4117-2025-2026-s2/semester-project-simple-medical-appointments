-- TABLES

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    granted_by UUID NULL,
    FOREIGN KEY (granted_by) REFERENCES auth.users (id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, role_id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- TODO: permissions
-- TODO: role_permissions
-- TODO: profiles
-- TODO: profile_settings
-- TODO: patients
-- TODO: patient_settings
-- TODO: providers
-- TODO: provider_settings