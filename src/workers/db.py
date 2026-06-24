# Database Helpers — Shared DB utilities for workers
# Postgres connection pooling, upsert helpers, caching.

import os
import json
from contextlib import contextmanager
from typing import Optional
from datetime import datetime, timezone

import psycopg2
import psycopg2.pool
import psycopg2.extras

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://platform:changeme@localhost:5432/nordic_eu_data")

pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=POSTGRES_URL,
)

@contextmanager
def get_db():
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)

def store_company(data: dict) -> Optional[str]:
    """Upsert a company record. Returns the company UUID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO enriched_companies
                    (company_name, org_number, country, address, postal_code, city,
                     website, email, phone, industry, industry_code, employee_count,
                     revenue, founding_year, company_form, status, description,
                     source_urls, extraction_methods, confidence, last_verified, raw_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (org_number, country) DO UPDATE SET
                    company_name = COALESCE(EXCLUDED.company_name, enriched_companies.company_name),
                    confidence = GREATEST(enriched_companies.confidence, EXCLUDED.confidence),
                    source_urls = enriched_companies.source_urls || EXCLUDED.source_urls,
                    extraction_methods = enriched_companies.extraction_methods || EXCLUDED.extraction_methods,
                    last_verified = EXCLUDED.last_verified,
                    raw_data = COALESCE(EXCLUDED.raw_data, enriched_companies.raw_data)
                RETURNING id
            """, (
                data.get("company_name"),
                data.get("org_number"),
                data.get("country", "SE"),
                data.get("address"),
                data.get("postal_code"),
                data.get("city"),
                data.get("website"),
                data.get("email"),
                data.get("phone"),
                data.get("industry"),
                data.get("industry_code"),
                data.get("employee_count"),
                data.get("revenue"),
                data.get("founding_year"),
                data.get("company_form"),
                data.get("status"),
                data.get("description"),
                data.get("source_urls", []),
                data.get("extraction_methods", ["website_scrape"]),
                data.get("confidence", 0.5),
                datetime.now(timezone.utc),
                json.dumps(data.get("raw_data", {})),
            ))
            row = cur.fetchone()
            return str(row[0]) if row else None

def store_contact(company_id: str, org_number: str, contact: dict):
    """Upsert a contact record."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO enriched_contacts
                    (company_id, org_number, full_name, first_name, last_name,
                     title, department, email, phone, mobile, linkedin_url,
                     country, confidence, methods_used, source_urls, last_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (org_number, full_name, email) DO UPDATE SET
                    title = COALESCE(EXCLUDED.title, enriched_contacts.title),
                    email = COALESCE(EXCLUDED.email, enriched_contacts.email),
                    confidence = GREATEST(enriched_contacts.confidence, EXCLUDED.confidence),
                    methods_used = enriched_contacts.methods_used || EXCLUDED.methods_used,
                    last_verified = EXCLUDED.last_verified
            """, (
                company_id,
                org_number,
                contact.get("name") or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                contact.get("first_name"),
                contact.get("last_name"),
                contact.get("title"),
                contact.get("department"),
                contact.get("email"),
                contact.get("phone"),
                contact.get("mobile"),
                contact.get("linkedin_url"),
                contact.get("country"),
                contact.get("confidence", 0.5),
                contact.get("methods_used", ["llm_enrichment"]),
                contact.get("source_urls", []),
                datetime.now(timezone.utc),
            ))

def store_vehicle(data: dict):
    """Upsert a vehicle record."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO vehicles
                    (registration, vin, make, model, year, fuel_type, mileage,
                     owner_org_number, owner_name, country, status, source_urls, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (registration, country) DO UPDATE SET
                    status = EXCLUDED.status,
                    mileage = COALESCE(EXCLUDED.mileage, vehicles.mileage),
                    confidence = GREATEST(vehicles.confidence, EXCLUDED.confidence)
            """, (
                data.get("registration"),
                data.get("vin"),
                data.get("make"),
                data.get("model"),
                data.get("year"),
                data.get("fuel_type"),
                data.get("mileage"),
                data.get("owner_org_number"),
                data.get("owner_name"),
                data.get("country", "SE"),
                data.get("status", "active"),
                data.get("source_urls", []),
                data.get("confidence", 0.5),
            ))

def store_financial(org_number: str, fiscal_year: int, country: str, data: dict):
    """Upsert financial data."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO financial_data
                    (org_number, fiscal_year, country, currency, revenue,
                     operating_profit, net_income, total_assets, total_equity,
                     employee_count, filing_type, source_url, extraction_method, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (org_number, fiscal_year, filing_type) DO UPDATE SET
                    revenue = COALESCE(EXCLUDED.revenue, financial_data.revenue),
                    net_income = COALESCE(EXCLUDED.net_income, financial_data.net_income),
                    total_assets = COALESCE(EXCLUDED.total_assets, financial_data.total_assets),
                    employee_count = COALESCE(EXCLUDED.employee_count, financial_data.employee_count)
            """, (
                org_number,
                fiscal_year,
                country,
                data.get("currency", "SEK"),
                data.get("revenue"),
                data.get("operating_profit"),
                data.get("net_income"),
                data.get("total_assets"),
                data.get("total_equity"),
                data.get("employee_count"),
                data.get("filing_type", "annual_report"),
                data.get("source_url"),
                data.get("extraction_method", "ocr"),
                data.get("confidence", 0.5),
            ))

def log_extraction(job_id: str, host: str, url: str, method: str,
                   attempt: int, http_status: int, duration_ms: int,
                   bytes_received: int, error_type: str = None, error_message: str = None):
    """Log extraction to method_stats for adaptive router feedback."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO extraction_logs
                    (job_id, host, url, method, attempt_number, http_status,
                     duration_ms, bytes_received, error_type, error_message, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                job_id, host, url, method, attempt,
                http_status, duration_ms, bytes_received,
                error_type, error_message, 0 if not error_type else 1,
            ))

            # Update method stats for the adaptive router
            cur.execute("""
                INSERT INTO method_stats (host, method, requests, successes, failures, avg_latency_ms, last_used)
                VALUES (%s, %s, 1, %s, %s, %s, NOW())
                ON CONFLICT (host, method) DO UPDATE SET
                    requests = method_stats.requests + 1,
                    successes = method_stats.successes + %s,
                    failures = method_stats.failures + %s,
                    avg_latency_ms = (method_stats.avg_latency_ms * method_stats.requests + %s) / (method_stats.requests + 1),
                    last_used = NOW()
            """, (
                host, method,
                1 if not error_type else 0,
                1 if error_type else 0,
                duration_ms,
                1 if not error_type else 0,
                1 if error_type else 0,
                duration_ms,
            ))
