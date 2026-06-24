// Example: Full Extraction Pipeline (TypeScript)
//
// TypeScript/Node.js version of the extraction pipeline.
// Uses:
//   - Crawlee (Apify OSS) for orchestration
//   - Playwright + optional CloakBrowser for rendering
//   - Ollama for local LLM enrichment
//   - pg for Postgres storage
//
// Prerequisites:
//   npm install crawlee playwright @playwright/test openai pg cheerio

import { PlaywrightCrawler, Router, RequestQueue } from "crawlee";
import { chromium } from "playwright";
import OpenAI from "openai";
import { Pool } from "pg";
import * as cheerio from "cheerio";

// =============================================================================
// Configuration
// =============================================================================

const OLLAMA_URL = process.env.OLLAMA_URL || "http://localhost:11434/v1";
const POSTGRES_URL = process.env.POSTGRES_URL || "postgresql://platform:changeme@localhost:5432/nordic_eu_data";
const LLM_MODEL = process.env.LLM_MODEL || "phi4:14b";

// =============================================================================
// LLM Client (Ollama — local, free)
// =============================================================================

const openai = new OpenAI({ baseURL: OLLAMA_URL, apiKey: "not-needed" });

async function llmExtractContacts(text: string): Promise<Contact[]> {
  if (text.length < 50) return [];

  const prompt = `Extract all people mentioned in this text. Return ONLY a JSON array with objects: {"name": "...", "title": "...", "email": "...", "confidence": 0.xx}. Text: ${text.slice(0, 4000)}`;

  try {
    const resp = await openai.chat.completions.create({
      model: LLM_MODEL,
      messages: [{ role: "user", content: prompt }],
      response_format: { type: "json_object" },
      temperature: 0.1,
    });
    const content = resp.choices[0].message.content || "[]";
    const data = JSON.parse(content);
    return Array.isArray(data) ? data : (data.people || []);
  } catch (e) {
    console.error("LLM extraction failed:", e);
    return [];
  }
}

async function llmExtractCompany(text: string): Promise<Company> {
  const prompt = `Extract company information from this text. Return JSON: {"company_name": "", "org_number": "", "address": "", "website": "", "industry": ""}. Text: ${text.slice(0, 3000)}`;

  try {
    const resp = await openai.chat.completions.create({
      model: LLM_MODEL,
      messages: [{ role: "user", content: prompt }],
      response_format: { type: "json_object" },
      temperature: 0.1,
    });
    return JSON.parse(resp.choices[0].message.content || "{}");
  } catch {
    return {};
  }
}

// =============================================================================
// Cheerio-based extraction (fast, no browser needed for simple pages)
// =============================================================================

function cheerioExtract(html: string): { text: string; emails: string[]; phones: string[] } {
  const $ = cheerio.load(html);

  // Remove scripts, styles, nav, footer
  $("script, style, nav, footer, header, .sidebar, .menu, .cookie-banner").remove();

  const text = $("body").text().replace(/\s+/g, " ").trim();

  const emails = [...new Set(html.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g) || [])];
  const phones = [...new Set(html.match(/\+?\d[\d\s()-]{6,}\d/g) || [])];

  return { text, emails, phones };
}

// =============================================================================
// Database
// =============================================================================

const pool = new Pool({ connectionString: POSTGRES_URL });

async function storeCompany(company: Company) {
  await pool.query(`
    INSERT INTO enriched_companies (company_name, org_number, address, website, industry, source_urls, confidence, country)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (org_number, country) DO UPDATE SET
      company_name = EXCLUDED.company_name,
      confidence = EXCLUDED.confidence
  `, [
    company.company_name,
    company.org_number,
    company.address,
    company.website,
    company.industry,
    [company.source_url],
    0.85,
    company.country || "SE",
  ]);
}

async function storeContacts(orgNumber: string, contacts: Contact[], sourceUrl: string) {
  for (const c of contacts) {
    await pool.query(`
      INSERT INTO enriched_contacts (org_number, full_name, title, email, confidence, source_urls, methods_used)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
      ON CONFLICT (org_number, full_name, email) DO UPDATE SET
        title = EXCLUDED.title,
        confidence = EXCLUDED.confidence
    `, [
      orgNumber,
      c.name,
      c.title,
      c.email,
      c.confidence || 0.7,
      [sourceUrl],
      ["website_scrape", "llm_enrichment"],
    ]);
  }
}

// =============================================================================
// Pipeline Router
// =============================================================================

const router = Router.create();

router.addDefaultHandler(async ({ request, page, log }) => {
  const url = request.loadedUrl || request.url;
  log.info(`Processing: ${url}`);

  // STEP 1: Get page content
  let html: string;
  try {
    html = await page.content();
  } catch {
    log.error(`Failed to load ${url}`);
    return;
  }

  // STEP 2: Cheerio extraction (fast, no LLM needed for basic patterns)
  const { text, emails } = cheerioExtract(html);
  log.info(`Extracted ${text.length} chars, ${emails.length} emails`);

  // STEP 3: LLM enrichment
  const company = await llmExtractCompany(text);
  company.source_url = url;
  company.country = "SE";

  const contacts = await llmExtractContacts(text);
  log.info(`LLM found: ${company.company_name}, ${contacts.length} contacts`);

  // STEP 4: Boost confidence for cross-validated contacts
  for (const contact of contacts) {
    if (contact.email && emails.includes(contact.email)) {
      contact.confidence = Math.min(0.99, (contact.confidence || 0.7) + 0.2);
    }
  }

  // STEP 5: Store
  if (company.company_name) {
    await storeCompany(company);
    log.info(`Stored: ${company.company_name}`);
  }
  if (company.org_number && contacts.length > 0) {
    await storeContacts(company.org_number, contacts, url);
    log.info(`Stored ${contacts.length} contacts`);
  }

  // Output
  console.log(JSON.stringify({ company, topContacts: contacts.slice(0, 3) }, null, 2));
});

// =============================================================================
// Main
// =============================================================================

interface Company {
  company_name?: string;
  org_number?: string;
  address?: string;
  website?: string;
  industry?: string;
  source_url?: string;
  country?: string;
}

interface Contact {
  name: string;
  title?: string;
  email?: string;
  confidence?: number;
}

async function main() {
  const urls = [
    "https://example-company.se/kontakt",
    "https://example-company.se/om-oss",
  ];

  const crawler = new PlaywrightCrawler({
    maxRequestsPerCrawl: urls.length,
    headless: true,
    requestHandler: router,
    launchContext: {
      launcher: chromium,
      launchOptions: {
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
      },
    },
  });

  await crawler.run(urls);
  console.log(`\nPipeline complete. Processed ${urls.length} URLs.`);
  await pool.end();
}

main().catch(console.error);
