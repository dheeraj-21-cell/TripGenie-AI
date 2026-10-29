-- =========================================================================
-- TripGenie-AI: Supabase PostgreSQL Schema & Security Rules (Free Tier)
-- =========================================================================
-- Architecture: Backend-Only Storage Gateway Pattern (FastAPI Proxy)
--
-- Security Model:
-- 1. The React frontend NEVER communicates with Supabase directly and holds NO database keys.
-- 2. Direct anonymous access via the Supabase PostgREST API (using the public anon key)
--    is REVOKED at both the permission and RLS layers to prevent scraping or tampering.
-- 3. The FastAPI backend connects securely using SUPABASE_SERVICE_ROLE_KEY stored
--    in backend/.env (server-side only, never committed or exposed to the browser).
-- 4. Multi-tenant user isolation (user A cannot access user B's trips) is enforced
--    at the FastAPI API Gateway layer and validated by automated tests.
-- 5. If Supabase Auth is enabled for users, authenticated user access is restricted
--    strictly to their own rows via auth.uid()::text = user_id.
-- 6. Safe & Idempotent: Can be rerun multiple times without dropping tables or losing data.
--
-- Cost: 100% Free Plan compatible (₹0 spending, no credit card required).
--
-- Setup Instructions:
-- 1. Create a free project at https://database.new (no credit card required).
-- 2. Open the SQL Editor in your Supabase dashboard.
-- 3. Paste and run this SQL script.
-- 4. Under Project Settings > API, copy your Project URL and service_role secret key:
--    SUPABASE_URL=https://your-project-id.supabase.co
--    SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key
-- =========================================================================

-- 1. Create Trips Table (Preserves existing data if table already exists)
-- Note: id and user_id use TEXT to support isolated client guest IDs ('guest-<uuid>')
-- and authenticated Supabase user UUIDs without foreign key or UUID syntax errors.
CREATE TABLE IF NOT EXISTS public.trips (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'local-guest',
    destination TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    itinerary_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable Row-Level Security
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;

-- 3. Explicit Grants & Anonymous Revocation
-- Revoke all table privileges from anon and public roles to block untrusted external PostgREST queries
REVOKE ALL ON TABLE public.trips FROM anon;
REVOKE ALL ON TABLE public.trips FROM public;

-- Grant permissions explicitly only to authenticated users (constrained by RLS) and backend service_role
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.trips TO authenticated;
GRANT ALL ON TABLE public.trips TO service_role;

-- 4. Idempotent Policy Setup (Safe to rerun without dropping tables or losing existing data)
DROP POLICY IF EXISTS "Authenticated users can select own trips" ON public.trips;
DROP POLICY IF EXISTS "Authenticated users can insert own trips" ON public.trips;
DROP POLICY IF EXISTS "Authenticated users can update own trips" ON public.trips;
DROP POLICY IF EXISTS "Authenticated users can delete own trips" ON public.trips;

-- Clean up any prior permissive policies if present
DROP POLICY IF EXISTS "Allow select for all trips" ON public.trips;
DROP POLICY IF EXISTS "Allow insert for all trips" ON public.trips;
DROP POLICY IF EXISTS "Allow update for all trips" ON public.trips;
DROP POLICY IF EXISTS "Allow delete for all trips" ON public.trips;
DROP POLICY IF EXISTS "Allow select for all users" ON public.trips;
DROP POLICY IF EXISTS "Allow insert for all users" ON public.trips;
DROP POLICY IF EXISTS "Allow update for all users" ON public.trips;
DROP POLICY IF EXISTS "Allow delete for all users" ON public.trips;
DROP POLICY IF EXISTS "Users can view own trips" ON public.trips;
DROP POLICY IF EXISTS "Users can create own trips" ON public.trips;
DROP POLICY IF EXISTS "Users can update own trips" ON public.trips;
DROP POLICY IF EXISTS "Users can delete own trips" ON public.trips;

-- Recreate strict authenticated user policies
CREATE POLICY "Authenticated users can select own trips"
    ON public.trips
    FOR SELECT
    TO authenticated
    USING (auth.uid()::text = user_id);

CREATE POLICY "Authenticated users can insert own trips"
    ON public.trips
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Authenticated users can update own trips"
    ON public.trips
    FOR UPDATE
    TO authenticated
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Authenticated users can delete own trips"
    ON public.trips
    FOR DELETE
    TO authenticated
    USING (auth.uid()::text = user_id);

-- 5. Add Performance Indexes for Query Optimization
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON public.trips (user_id);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON public.trips (created_at DESC);
