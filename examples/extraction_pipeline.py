# Example: Full Extraction Pipeline (Python)
#
# Walks a company website through the complete adaptive pipeline:
#   1. Enqueue via Crawlee → Playwright + CloakBrowser
#   2. Raw HTML/PDF → Unstructured partition
#   3. Elements → spaCy base NER
#   4. spaCy output → Ollama enrichment (contact extraction)
#   5. Multi-source confidence scoring
#   6. Store in Postgres + export JSON
#
# Prerequisites:
#   - docker compose -f docker-compose.full-stack.yml up -d
#   - pip install crawlee playwright unstructured-client spacy openai psycopg2-binary

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

import spacy
from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.router import Router
from openai import OpenAI
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
import psycopg2
import psycopg2.extras

# =============================================================================
# Configuration
# =============================================================================

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
UNSTRUCTURED_URL = os.getenv("UNSTRUCTURED_URL", "http://localhost:8002")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://platform:changeme@localhost:5432/nordic_eu_data")
CLOAKBROWSER_CDP = os.getenv("CLOAKBROWSER_CDP", "http://localhost:9222")

# =============================================================================
# LLM Client (local Ollama — free)
# =============================================================================

client = OpenAI(base_url=OLLAMA_URL, api_key="not-needed")

async def llm_extract_contacts(text: str) -> list[dict]:
    """Extract structured contacts from unstructured text."""
    if len(text) < 50:
        return []
    prompt = f"""Extract all people mentioned in this text. For each person, return:
    - name (full name)
    - title (job title)
    - email (if present)
    - phone (if present)
    - confidence (0.0-1.0 based on how clearly identifiable)

    Text: {text[:4000]}

    Return ONLY valid JSON array. No explanation."""
    try:
        resp = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "phi4:14b"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        return data if isinstance(data, list) else data.get("people", [])
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        return []

async def llm_extract_company(text: str) -> dict:
    """Extract company metadata from text."""
    prompt = f"""Extract company information from this text. Return JSON:
    {{
        "company_name": "...",
        "org_number": "...",
        "address": "...",
        "website": "...",
        "industry": "...",
        "description_short": "..."
    }}
    Text: {text[:3000]}
    Return ONLY JSON."""
    try:
        resp = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "phi4:14b"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {}

# =============================================================================
# spaCy NER (base pass — fast, local, free)
# =============================================================================

nlp_sv = spacy.load("sv_core_news_lg")  # Swedish
nlp_en = spacy.load("en_core_web_lg")   # English fallback

def spacy_extract(text: str, lang: str = "sv") -> dict:
    """Extract PER/ORG/LOC entities with spaCy."""
    nlp = nlp_sv if lang == "sv" else nlp_en
    doc = nlp(text[:100000])  # Truncate to avoid memory issues
    entities = {"persons": [], "organizations": [], "locations": [], "emails": [], "phones": []}
    for ent in doc.ents:
        if ent.label_ == "PER":
            entities["persons"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["organizations"].append(ent.text)
        elif ent.label_ in ("LOC", "GPE"):
            entities["locations"].append(ent.text)
    # Regex for emails and phones (spaCy doesn't always catch them)
    import re
    entities["emails"] = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    entities["phones"] = re.findall(r"\+?\d[\d\s()-]{6,}\d", text)
    return entities

# =============================================================================
# Unstructured (document parsing)
# =============================================================================

unstructured = UnstructuredClient(server_url=UNSTRUCTURED_URL)

async def parse_document(content: bytes, content_type: str) -> str:
    """Parse a document into clean text via Unstructured."""
    try:
        req = shared.PartitionParameters(
            files=shared.Files(
                content=content,
                file_name=f"doc.{content_type}",
                content_type=f"application/{content_type}" if content_type != "html" else "text/html",
            ),
            strategy="auto",
        )
        resp = unstructured.general.partition(req)
        return " ".join([e.get("text", "") for e in resp.elements if e.get("text")])
    except Exception as e:
        print(f"Unstructured parse failed: {e}")
        return ""

# =============================================================================
# Database
# =============================================================================

def store_company(company_data: dict):
    with psycopg2.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO enriched_companies
                    (company_name, org_number, address, website, industry, description,
                     extracted_at, source_url, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (org_number) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    extracted_at = EXCLUDED.extracted_at,
                    confidence = EXCLUDED.confidence
            """, (
                company_data.get("company_name"),
                company_data.get("org_number"),
                company_data.get("address"),
                company_data.get("website"),
                company_data.get("industry"),
                company_data.get("description_short"),
                datetime.now(timezone.utc),
                company_data.get("source_url"),
                company_data.get("confidence", 0.0),
            ))
    print(f"  Stored: {company_data.get('company_name')}")

def store_contacts(org_number: str, contacts: list[dict], source_url: str):
    with psycopg2.connect(POSTGRES_URL) as conn:
        with conn.cursor() as cur:
            for c in contacts:
                cur.execute("""
                    INSERT INTO enriched_contacts
                        (org_number, name, title, email, phone, confidence,
                         source_url, extracted_at, methods_used)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (org_number, name, email) DO UPDATE SET
                        title = EXCLUDED.title,
                        confidence = EXCLUDED.confidence,
                        extracted_at = EXCLUDED.extracted_at
                """, (
                    org_number,
                    c.get("name"),
                    c.get("title"),
                    c.get("email"),
                    c.get("phone"),
                    c.get("confidence", 0.5),
                    source_url,
                    datetime.now(timezone.utc),
                    json.dumps(["website_scrape", "spacy_ner", "llm_enrichment"]),
                ))
    print(f"  Stored {len(contacts)} contacts for {org_number}")

# =============================================================================
# The Pipeline
# =============================================================================

router = Router[PlaywrightCrawlingContext]()

@router.default_handler
async def pipeline_handler(context: PlaywrightCrawlingContext) -> None:
    url = context.request.loaded_url
    print(f"\n{'='*60}\nProcessing: {url}")

    # STEP 1: Get page content via Playwright + CloakBrowser
    try:
        html = await context.page.content()
        status = context.response.status if context.response else 0
    except Exception as e:
        print(f"  Failed to load page: {e}")
        return

    if status >= 400:
        print(f"  HTTP {status} — skipping")
        return

    print(f"  Page loaded: {len(html)} chars, HTTP {status}")

    # STEP 2: Parse with Unstructured
    clean_text = await parse_document(html.encode(), "html")
    if not clean_text:
        clean_text = html  # Fallback: raw HTML as text
    print(f"  Parsed: {len(clean_text)} chars of clean text")

    # STEP 3: spaCy base NER
    spacy_entities = spacy_extract(clean_text, "sv")
    print(f"  spaCy: {len(spacy_entities['persons'])} persons, "
          f"{len(spacy_entities['organizations'])} orgs, "
          f"{len(spacy_entities['emails'])} emails")

    # STEP 4: LLM enrichment (company + contacts)
    company_data = await llm_extract_company(clean_text)
    company_data["source_url"] = url
    company_data["confidence"] = 0.85  # Single-source from website

    contacts = await llm_extract_contacts(clean_text)
    print(f"  LLM: {len(contacts)} contacts extracted")

    # STEP 5: Multi-source confidence (boosted by spaCy+LLM agreement)
    for contact in contacts:
        name_parts = contact.get("name", "").lower().split()
        if any(p in " ".join(spacy_entities["persons"]).lower() for p in name_parts if len(p) > 2):
            contact["confidence"] = min(0.99, contact.get("confidence", 0.7) + 0.2)
            contact["methods"] = contact.get("methods", []) + ["spacy_cross_validated"]

    # STEP 6: Store
    org_number = company_data.get("org_number")
    if company_data.get("company_name"):
        store_company(company_data)
    if org_number and contacts:
        store_contacts(org_number, contacts, url)

    # Output summary
    print(f"\n  Result: {json.dumps(company_data, ensure_ascii=False, indent=2)}")
    print(f"  Top contacts:")
    for c in contacts[:5]:
        print(f"    {c.get('name')} — {c.get('title')} ({c.get('confidence', '?')*100:.0f}%)")

async def main():
    # Test URLs — replace with your target list
    urls = [
        "https://example-company.se/kontakt",
        "https://example-company.se/om-oss",
        "https://example-company.se/medarbetare",
    ]

    crawler = PlaywrightCrawler(
        max_requests_per_crawl=len(urls),
        headless=True,
        browser_type="chromium",
        request_handler=router,
        # Connect to CloakBrowser CDP if available
        # browser_launch_options={"executable_path": None, "channel": None},
    )

    await crawler.run(urls)
    print(f"\n{'='*60}\nPipeline complete. Processed {len(urls)} URLs.")

if __name__ == "__main__":
    asyncio.run(main())
