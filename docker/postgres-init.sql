-- ============================================================================
-- PostgreSQL Initialization Script
-- ============================================================================
-- This script runs automatically when the postgres container starts
-- It creates the necessary databases, schemas, users, and roles
-- ============================================================================

-- ============================================================================
-- Create PostgREST Authenticator and Role Hierarchy
-- ============================================================================
-- DO $$ BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') THEN
--         CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'super-secret-password';
--     END IF;
-- END $$;

-- DO $$ BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anonymous') THEN
--         CREATE ROLE anonymous NOINHERIT;
--     END IF;
-- END $$;

-- DO $$ BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
--         CREATE ROLE authenticated NOINHERIT;
--     END IF;
-- END $$;

-- ============================================================================
-- Grant role memberships for PostgREST access control
-- ============================================================================
-- GRANT anonymous TO authenticator;
-- GRANT authenticated TO authenticator;

-- ============================================================================
-- Create application user (if it doesn't already exist from POSTGRES_USER)
-- ============================================================================
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'taskmanager_user') THEN
        CREATE USER taskmanager_user WITH PASSWORD 'securepassword123' CREATEROLE;
    END IF;
END $$;

-- ============================================================================
-- Create dev schema (public schema for application)
-- ============================================================================
-- Note: The 'dev' schema must exist before alembic migrations run
-- CREATE SCHEMA IF NOT EXISTS dev AUTHORIZATION taskmanager_user;

-- ============================================================================
-- Grant schema permissions
-- ============================================================================
-- GRANT USAGE ON SCHEMA dev TO authenticator, anonymous, authenticated, taskmanager_user;
-- GRANT USAGE ON SCHEMA public TO authenticator, anonymous, authenticated, taskmanager_user;

-- ============================================================================
-- Create private schema for system data
-- ============================================================================
-- CREATE SCHEMA IF NOT EXISTS private AUTHORIZATION taskmanager_user;
-- GRANT USAGE ON SCHEMA private TO authenticator, anonymous, authenticated, taskmanager_user;

-- ============================================================================
-- Set default privileges for future tables
-- ============================================================================
-- ALTER DEFAULT PRIVILEGES FOR USER taskmanager_user IN SCHEMA dev GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;
-- ALTER DEFAULT PRIVILEGES FOR USER taskmanager_user IN SCHEMA dev GRANT USAGE, SELECT ON SEQUENCES TO authenticated;

-- ============================================================================
-- Create verify_token function for PostgREST authentication
-- ============================================================================
-- CREATE OR REPLACE FUNCTION dev.verify_token() RETURNS void AS $$
-- DECLARE
--     v_token TEXT;
--     v_claims JSONB;
-- BEGIN
--     v_token := current_setting('request.jwt.claim.sub', true);
--     IF v_token IS NOT NULL THEN
--         PERFORM set_config('request.jwt.claim.role', 'authenticated'::text, false);
--     ELSE
--         PERFORM set_config('request.jwt.claim.role', 'anonymous'::text, false);
--     END IF;
-- END;
-- $$ LANGUAGE plpgsql;

-- ============================================================================
-- Setup complete
-- ============================================================================
-- All schemas, roles, and permissions are now configured
-- Alembic migrations can now run safely
