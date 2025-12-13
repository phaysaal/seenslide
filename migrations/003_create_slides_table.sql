-- Migration 003: Create Slides Table
-- Creates table for storing slide metadata

-- Cloud slides table
CREATE TABLE IF NOT EXISTS cloud_slides (
    slide_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    slide_number INTEGER NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL,
    file_path TEXT,
    thumbnail_path TEXT,
    width INTEGER,
    height INTEGER,
    file_size_bytes INTEGER,
    uploaded_at DOUBLE PRECISION,
    metadata JSONB DEFAULT '{}'::jsonb,
    FOREIGN KEY (session_id) REFERENCES cloud_sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, slide_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_slides_session_id ON cloud_slides(session_id);
CREATE INDEX IF NOT EXISTS idx_slides_session_slide ON cloud_slides(session_id, slide_number);
CREATE INDEX IF NOT EXISTS idx_slides_timestamp ON cloud_slides(timestamp);
