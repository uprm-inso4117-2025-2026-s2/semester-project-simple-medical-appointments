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

CREATE TABLE permissions (
    id SERIAL,
    PRIMARY KEY (id),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    permission_id INT NOT NULL,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE,
    granted_by UUID NULL,
    FOREIGN KEY (granted_by) REFERENCES auth.users (id) ON DELETE SET NULL,
    PRIMARY KEY (role_id, permission_id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
    user_id UUID PRIMARY KEY NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    username VARCHAR(32) UNIQUE NOT NULL,
    avatar_url TEXT,
    banner_url TEXT,
    phone_number VARCHAR(20) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profile_settings (
    user_id UUID PRIMARY KEY NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    preferred_contact_method VARCHAR(50) NOT NULL,
    preferred_language VARCHAR(10) NOT NULL,
    notify_appointment_reminders BOOLEAN NOT NULL DEFAULT TRUE,
    notify_appointment_updates BOOLEAN NOT NULL DEFAULT TRUE,
    notify_messages BOOLEAN NOT NULL DEFAULT TRUE,
    theme VARCHAR(20) NOT NULL,
    accessibility_mode VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patients (
    user_id UUID PRIMARY KEY NOT NULL,
    FOREIGN KEY (user_id) REFERENCES auth.users (id) ON DELETE CASCADE,
    insurance_provider VARCHAR(100) NOT NULL,
    insurance_member_id VARCHAR(50) NOT NULL,
    emergency_contact_name VARCHAR(100) NOT NULL,
    emergency_contact_phone_number VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- TODO: patient_settings
-- TODO: providers
-- TODO: provider_settings