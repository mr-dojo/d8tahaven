-- Personal Data Collector (PDC) - Database Initialization
-- This script runs automatically when PostgreSQL container starts

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable additional useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- Trigram similarity for text search

-- Confirm extensions are installed
SELECT extname, extversion FROM pg_extension;
