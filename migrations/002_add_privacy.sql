-- Migration 002: Add Privacy Features
-- Adds session privacy and password protection columns

-- Add privacy columns to cloud_sessions
ALTER TABLE cloud_sessions
ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS password_hash TEXT,
ADD COLUMN IF NOT EXISTS password_salt TEXT,
ADD COLUMN IF NOT EXISTS access_type TEXT DEFAULT 'public';

-- Create index for access control
CREATE INDEX IF NOT EXISTS idx_sessions_access_type ON cloud_sessions(access_type);
