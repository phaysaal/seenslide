-- Migration 001: Initial Schema
-- Creates base tables for cloud sessions

-- Cloud sessions table
CREATE TABLE IF NOT EXISTS cloud_sessions (
    session_id TEXT PRIMARY KEY,
    presenter_name TEXT,
    presenter_email TEXT,
    created_at DOUBLE PRECISION NOT NULL,
    last_active DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    total_slides INTEGER NOT NULL DEFAULT 0,
    max_slides INTEGER NOT NULL DEFAULT 50,
    viewer_count INTEGER NOT NULL DEFAULT 0,
    settings JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_status ON cloud_sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON cloud_sessions(last_active);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON cloud_sessions(created_at);
