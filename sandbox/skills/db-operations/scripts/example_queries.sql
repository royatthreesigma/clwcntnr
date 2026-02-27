-- =============================================================
-- Example SQL queries for common database operations
-- Use with:  python3 scripts/run_query.py "<query>"
-- =============================================================

-- -----------------------------------------------
-- EXPLORATION
-- -----------------------------------------------

-- List all schemas
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name NOT LIKE 'pg_%'
  AND schema_name != 'information_schema'
ORDER BY schema_name;

-- List all tables in a schema with row estimates
SELECT
    schemaname,
    relname       AS table_name,
    n_live_tup    AS estimated_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;

-- Describe a table (columns, types, nullability)
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'your_table'
ORDER BY ordinal_position;

-- List indexes on a table
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'your_table';

-- List foreign keys
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name  AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';

-- -----------------------------------------------
-- DATA OPERATIONS
-- -----------------------------------------------

-- Paginated select
SELECT * FROM public.your_table
ORDER BY id
LIMIT 100 OFFSET 0;

-- Count rows
SELECT COUNT(*) FROM public.your_table;

-- Insert with returning
INSERT INTO public.your_table (col1, col2)
VALUES (%s, %s)
RETURNING id;

-- Upsert (insert or update on conflict)
INSERT INTO public.your_table (id, name, value)
VALUES (%s, %s, %s)
ON CONFLICT (id) DO UPDATE
SET name = EXCLUDED.name,
    value = EXCLUDED.value;

-- Bulk delete with condition
DELETE FROM public.your_table
WHERE created_at < NOW() - INTERVAL '30 days';

-- -----------------------------------------------
-- DDL
-- -----------------------------------------------

-- Create table
CREATE TABLE IF NOT EXISTS public.events (
    id          SERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    payload     JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Add column
ALTER TABLE public.events
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;

-- Create index
CREATE INDEX IF NOT EXISTS idx_events_type
ON public.events (event_type);

-- Create schema
CREATE SCHEMA IF NOT EXISTS analytics;

-- -----------------------------------------------
-- ANALYTICS
-- -----------------------------------------------

-- Table sizes
SELECT
    relname                                    AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid))        AS data_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Active connections
SELECT
    pid,
    usename,
    application_name,
    state,
    query_start,
    LEFT(query, 100) AS query_preview
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start DESC;
