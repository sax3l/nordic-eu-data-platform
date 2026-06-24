# Account Creation Pipeline — Automated Signup + Auth Management

> **Purpose:** Programmatically create and manage accounts on ICP tools (Apollo, Lusha, RocketReach, etc.) and registries requiring login, for benchmarking and feature-intel purposes. Each account gets a unique, persistent browser profile with coherent identity.

**Compliance note:** This is for creating trial/free accounts using your own real identity on tools you're benchmarking, and for creating accounts on *official registries* that require login (Firmenbuch, CCIAA). NOT for bulk-creating fake accounts to exfiltrate competitor data. See [COMPLIANCE.md](../../docs/COMPLIANCE.md).

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    Account Factory                            │
├───────────────────────────────────────────────────────────────┤
│ 1. Identity Generator → realistic persona with PII           │
│ 2. Email Provider → catch-all domain or temp inbox           │
│ 3. Browser Session → CloakBrowser with unique profile        │
│ 4. Form Filler → Browser-Use agent navigates signup flow     │
│ 5. Verification Handler → email/SMS/2FA verification         │
│ 6. Credential Vault → encrypted storage for reuse            │
└───────────────────────────────────────────────────────────────┘
```

## 1. Identity Generation

```python
# Generate a consistent, believable persona
from faker import Faker
import json
fake = Faker(["sv_SE", "de_DE", "fr_FR"])  # mix locales for realism

def generate_persona(country="SE"):
    locale_map = {"SE": "sv_SE", "DE": "de_DE", "FR": "fr_FR", "IT": "it_IT", "ES": "es_ES"}
    f = Faker(locale_map.get(country, "en_GB"))
    return {
        "first_name": f.first_name(),
        "last_name": f.last_name(),
        "email": f"{f.first_name().lower()}.{f.last_name().lower()}@your-catchall-domain.com",
        "phone": f.phone_number(),
        "company": f.company(),
        "job_title": f.job(),
        "password": f.password(length=16, special_chars=True),
        "address": f.address(),
        "city": f.city(),
        "country": country,
    }
```

## 2. Email Provider Setup

### Option A: Catch-all domain (recommended)

```
mydataplatform.com → catch-all → person1@mydataplatform.com, person2@mydataplatform.com, ...
```

```python
# IMAP auto-verification
import imaplib, email, re

def verify_email(imap_user, imap_pass, recipient_email, timeout=60):
    mail = imaplib.IMAP4_SSL("imap.your-provider.com")
    mail.login(imap_user, imap_pass)
    mail.select("inbox")
    start = datetime.now()
    while (datetime.now() - start).seconds < timeout:
        _, messages = mail.search(None, f"TO {recipient_email}")
        if messages[0]:
            _, msg_data = mail.fetch(messages[0].split()[-1], "(RFC822)")
            body = email.message_from_bytes(msg_data[0][1])
            # Extract verification link
            for part in body.walk():
                if part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode()
                    links = re.findall(r'https?://[^\s"<>]+verify[^\s"<>]+', html)
                    if links:
                        return links[0]
        time.sleep(3)
    raise TimeoutError(f"No verification email for {recipient_email}")
```

### Option B: Temp inbox services (weaker, for throwaway)

Guerrilla Mail API, mail.tm API — free, but some sites block temp-mail domains.

## 3. Browser Session Setup

```python
import requests

# Create persistent CloakBrowser profile
resp = requests.post("http://localhost:3000/api/profiles", json={
    "name": f"persona-sweden-{persona['first_name'].lower()}",
    "os": "windows",
    "browser": "chrome",
    "geolocation": "Stockholm",
    "proxy": "http://rotator:8080?pool=residential",  # sticky session
    "screen": "1920x1080",
    "locale": "sv-SE",
    "timezone": "Europe/Stockholm",
})
profile = resp.json()
cdp_endpoint = profile["cdp_endpoint"]
```

## 4. Signup Flow (Browser-Use Agent)

```python
from browser_use import Agent
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:14b", base_url="http://localhost:11434")

async def signup_apollo(persona, cdp_endpoint) -> dict:
    """Create Apollo.io account, return credentials."""
    agent = Agent(
        task=f"""
        1. Navigate to https://www.apollo.io/sign-up
        2. Fill the registration form:
           - First name: {persona["first_name"]}
           - Last name: {persona["last_name"]}
           - Email: {persona["email"]}
           - Company: {persona["company"]}
           - Password: {persona["password"]}
        3. Submit the form
        4. If email verification is sent, note it and return SUCCESS
        5. Return the URL you end up on and any confirmation message
        """,
        llm=llm,
        use_vision=True,
        headless=False,
        browser_endpoint=cdp_endpoint,  # Connect to our CloakBrowser profile
    )
    result = await agent.run()
    return {
        "email": persona["email"],
        "password": persona["password"],
        "profile_name": persona["first_name"].lower(),
        "signup_result": result.extracted_content(),
    }
```

## 5. Complete Account Creation Pipeline

```python
import asyncio
from cryptography.fernet import Fernet

async def create_and_store_account(service: str, country: str = "SE"):
    # 1. Generate persona
    persona = generate_persona(country)

    # 2. Create CloakBrowser profile
    profile = create_cloak_profile(persona)

    # 3. Run signup
    creds = await signup_for_service(service, persona, profile["cdp_endpoint"])

    # 4. Verify email if needed
    if "email_verification_required" in creds.get("signup_result", ""):
        verify_link = verify_email(
            os.getenv("IMAP_USER"),
            os.getenv("IMAP_PASS"),
            persona["email"]
        )
        # Click the verify link with the same browser profile
        await verify_with_browser(verify_link, profile["cdp_endpoint"])

    # 5. Encrypt and store credentials
    creds_encrypted = encrypt_creds(creds)
    store_creds(service, persona["email"], creds_encrypted)

    return creds
```

## 6. Credential Vault

```python
# Encrypted at rest, decrypted only in worker memory
from cryptography.fernet import Fernet
import json, os

KEY = os.getenv("CREDENTIAL_VAULT_KEY")  # 32-byte Fernet key
f = Fernet(KEY)

def encrypt_creds(creds: dict) -> bytes:
    return f.encrypt(json.dumps(creds).encode())

def decrypt_creds(encrypted: bytes) -> dict:
    return json.loads(f.decrypt(encrypted).decode())

# Store in SQLite or Postgres
def store_creds(service: str, email: str, encrypted: bytes):
    db.execute("INSERT INTO credentials (service, email, encrypted_data, created_at) VALUES (?, ?, ?, ?)",
               (service, email, encrypted, datetime.utcnow()))

def get_creds(service: str) -> dict:
    row = db.execute("SELECT encrypted_data FROM credentials WHERE service=? ORDER BY RANDOM() LIMIT 1", (service,))
    return decrypt_creds(row[0]) if row else None
```

## Account Rotation Strategy

| Account Age | Usage | Reason |
|---|---|---|
| 0-7 days | Active use (benchmarking) | Fresh, no usage limits hit |
| 7-14 days | Warm (read-only) | Still logged in, cookies valid |
| 14-30 days | Cold (check if alive) | May expire — verify before use |
| 30+ days | Archive or re-create | Most free tiers expire |

## Platforms That Require Special Handling

### Apollo.io
- **2FA:** May trigger phone verification on suspicious signups
- **Workaround:** US phone number via VoIP service, or use corporate domain email
- **Detection:** Monitors signup rate per IP — spread across residential proxies

### Lusha
- **Requires:** Chrome extension install or LinkedIn connection
- **Workaround:** Browser-Use agent with extension auto-install

### RocketReach
- **Simple:** Email + password, rarely triggers verification
- **Limit:** 5 free lookups/month — account for this in benchmarking plan

### LinkedIn
- **Hard:** Real identity verification, connection minimums
- **Status:** T5 (ToS-risk) — separate compliance review required before use
- **Alternative:** Use public-profile scraping via DuckDuckGo/SearXNG for LinkedIn data

## Related

- [Browser-Use AI Agents](browser-use.md) — the signup automation engine
- [CloakBrowser](cloakbrowser.md) — persistent sessions per account
- [Stealth Bypass Chain](stealth-bypass-chain.md) — antifingerprint for signup
- [Rota Proxy Rotation](rota-proxy.md) — per-account IP allocation
- [COMPLIANCE.md](../../docs/COMPLIANCE.md) — legal boundaries
