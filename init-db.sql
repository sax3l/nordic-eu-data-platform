-- init-db.sql
-- Nordic+EU Data Platform — PostgreSQL schema
-- Run once: docker compose up postgres, then:
--   docker compose exec postgres psql -U platform -d nordic_eu_data -f /docker-entrypoint-initdb.d/init.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "vector";          -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- For encrypted credential vault

-- ============================================================================
-- ENRICHED COMPANIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS enriched_companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name    TEXT NOT NULL,
    legal_name      TEXT,
    org_number      TEXT,
    tax_id          TEXT,
    lei_number      TEXT,                          -- GLEIF/LEI cross-border key
    country         CHAR(2) NOT NULL,              -- ISO 3166-1 alpha-2
    address         TEXT,
    postal_code     TEXT,
    city            TEXT,
    website         TEXT,
    email           TEXT,
    phone           TEXT,
    industry        TEXT,
    industry_code   TEXT,                          -- NACE/SNI code
    employee_count  INTEGER,
    revenue         NUMERIC,
    revenue_currency TEXT,
    founding_year   INTEGER,
    company_form    TEXT,                          -- AB, GmbH, SAS, etc.
    status          TEXT,                          -- Active, Inactive, Liquidated
    description     TEXT,
    social_links    JSONB DEFAULT '{}',
    source_urls     TEXT[],
    extraction_methods TEXT[],
    confidence      REAL DEFAULT 0.0,
    last_verified   TIMESTAMPTZ,
    extracted_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    raw_data        JSONB,                        -- Original extracted data
    embedding       vector(1024),                 -- For semantic search (BGE-M3)

    UNIQUE (org_number, country)
);

CREATE INDEX idx_companies_country ON enriched_companies(country);
CREATE INDEX idx_companies_industry ON enriched_companies(industry_code);
CREATE INDEX idx_companies_org ON enriched_companies(org_number);
CREATE INDEX idx_companies_lei ON enriched_companies(lei_number) WHERE lei_number IS NOT NULL;
CREATE INDEX idx_companies_name_trgm ON enriched_companies USING gin (company_name gin_trgm_ops);
CREATE INDEX idx_companies_confidence ON enriched_companies(confidence DESC);
CREATE INDEX idx_companies_embedding ON enriched_companies USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- ENRICHED CONTACTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS enriched_contacts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES enriched_companies(id) ON DELETE CASCADE,
    org_number      TEXT,
    first_name      TEXT,
    last_name       TEXT,
    full_name       TEXT NOT NULL,
    title           TEXT,
    department      TEXT,
    email           TEXT,
    phone           TEXT,
    mobile          TEXT,
    linkedin_url    TEXT,
    twitter_url     TEXT,
    country         CHAR(2),
    confidence      REAL DEFAULT 0.0,
    methods_used    TEXT[],
    source_urls     TEXT[],
    last_verified   TIMESTAMPTZ,
    extracted_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    raw_data        JSONB,

    UNIQUE (org_number, full_name, email)
);

CREATE INDEX idx_contacts_company ON enriched_contacts(company_id);
CREATE INDEX idx_contacts_org ON enriched_contacts(org_number);
CREATE INDEX idx_contacts_email ON enriched_contacts(email) WHERE email IS NOT NULL;
CREATE INDEX idx_contacts_name_trgm ON enriched_contacts USING gin (full_name gin_trgm_ops);
CREATE INDEX idx_contacts_confidence ON enriched_contacts(confidence DESC);
CREATE INDEX idx_contacts_country ON enriched_contacts(country);

-- ============================================================================
-- VEHICLES (VehIQ integration)
-- ============================================================================

CREATE TABLE IF NOT EXISTS vehicles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    registration    TEXT NOT NULL,                 -- License plate / reg number
    vin             TEXT,
    make            TEXT,
    model           TEXT,
    year            INTEGER,
    fuel_type       TEXT,
    mileage         INTEGER,
    owner_org_number TEXT,
    owner_name      TEXT,
    country         CHAR(2) NOT NULL,
    status          TEXT,                          -- Active, Deregistered, Exported
    source_urls     TEXT[],
    confidence      REAL DEFAULT 0.0,
    extracted_at    TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (registration, country)
);

CREATE INDEX idx_vehicles_reg ON vehicles(registration);
CREATE INDEX idx_vehicles_vin ON vehicles(vin) WHERE vin IS NOT NULL;
CREATE INDEX idx_vehicles_owner ON vehicles(owner_org_number);
CREATE INDEX idx_vehicles_country ON vehicles(country);

-- ============================================================================
-- FINANCIAL DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS financial_data (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES enriched_companies(id) ON DELETE CASCADE,
    org_number      TEXT NOT NULL,
    fiscal_year     INTEGER NOT NULL,
    country         CHAR(2) NOT NULL,
    currency        TEXT DEFAULT 'SEK',
    revenue         NUMERIC,
    operating_profit NUMERIC,
    net_income      NUMERIC,
    total_assets    NUMERIC,
    total_equity    NUMERIC,
    employee_count  INTEGER,
    filing_type     TEXT,                          -- Annual Report, Tax Return, etc.
    source_url      TEXT,
    extraction_method TEXT,
    confidence      REAL DEFAULT 0.0,
    extracted_at    TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (org_number, fiscal_year, filing_type)
);

CREATE INDEX idx_financial_org ON financial_data(org_number, fiscal_year);

-- ============================================================================
-- CRAWL JOBS
-- ============================================================================

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type        TEXT NOT NULL,                 -- 'country_batch', 'company_list', 'single_url'
    status          TEXT DEFAULT 'pending',        -- pending, running, completed, failed
    target_country  CHAR(2),
    input_data      JSONB,
    total_items     INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    failed_items    INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_log       JSONB DEFAULT '[]',
    worker_id       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_jobs_country ON crawl_jobs(target_country);

-- ============================================================================
-- METHOD STATS (adaptive router feedback)
-- ============================================================================

CREATE TABLE IF NOT EXISTS method_stats (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    host            TEXT NOT NULL,                 -- e.g., bolagsverket.se
    country         CHAR(2),
    method          TEXT NOT NULL,                 -- e.g., curl_cffi, cloakbrowser, sequentum
    requests        INTEGER DEFAULT 0,
    successes       INTEGER DEFAULT 0,
    failures        INTEGER DEFAULT 0,
    blocks          INTEGER DEFAULT 0,
    avg_latency_ms  REAL DEFAULT 0,
    last_used       TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (host, method)
);

CREATE INDEX idx_stats_host ON method_stats(host);

-- ============================================================================
-- SOURCE REGISTRY CACHE
-- ============================================================================

CREATE TABLE IF NOT EXISTS source_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_key      TEXT NOT NULL,                 -- from sources.yaml
    url             TEXT NOT NULL,
    content_hash    TEXT,
    content_size    INTEGER,
    http_status     INTEGER,
    fetched_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    raw_response    BYTEA,

    UNIQUE (source_key, url)
);

CREATE INDEX idx_source_cache_expiry ON source_cache(expires_at);

-- ============================================================================
-- CREDENTIAL VAULT (encrypted)
-- ============================================================================

CREATE TABLE IF NOT EXISTS credentials (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service         TEXT NOT NULL,                 -- 'apollo', 'handelsregister', 'cciaa'
    email           TEXT NOT NULL,
    encrypted_data  BYTEA NOT NULL,                -- Fernet-encrypted JSON with password/tokens
    profile_name    TEXT,
    country         CHAR(2),
    status          TEXT DEFAULT 'active',         -- active, expired, revoked
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_used       TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_creds_service ON credentials(service, status);

-- ============================================================================
-- EXTRACTION LOGS (for debugging + provenance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS extraction_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id          UUID REFERENCES crawl_jobs(id),
    host            TEXT,
    url             TEXT,
    method          TEXT,
    attempt_number  INTEGER DEFAULT 1,
    http_status     INTEGER,
    duration_ms     INTEGER,
    bytes_received  INTEGER,
    error_type      TEXT,                          -- block, timeout, parse_error, etc.
    error_message   TEXT,
    retry_count     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_logs_job ON extraction_logs(job_id);
CREATE INDEX idx_logs_host_method ON extraction_logs(host, method);
CREATE INDEX idx_logs_created ON extraction_logs(created_at);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_companies_updated
    BEFORE UPDATE ON enriched_companies
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_contacts_updated
    BEFORE UPDATE ON enriched_contacts
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
