# UiPath — Enterprise RPA + Document Understanding

> **Tool:** UiPath Studio + Orchestrator | **License:** Paid ($500-$2000/mo enterprise)
> **Key Feature:** Enterprise-grade RPA with built-in Document Understanding, AI Center, and Orchestrator API

The platform's Tier 3 RPA escalation — used when Sequentum can't handle a workflow, or when Document Understanding (AI-powered PDF/invoice/image extraction) is needed for complex unstructured documents. UiPath's AI Center can run custom ML models for document classification and extraction, making it uniquely suited for financial filings and procurement documents.

## What it solves

Some European registries and government portals have:
- Citrix/Virtual desktop interfaces (no DOM, pixel-based only)
- Legacy terminal applications (green screens)
- Complex multi-system workflows (Registry → Tax authority → Chamber of Commerce → back to Registry)
- Batch document processing (10,000 PDFs → extract structured data from each)

UiPath handles all of these at enterprise scale. Its Document Understanding module is especially relevant for financial filings (annual reports, balance sheets, tax returns) that come as PDFs in 15+ languages.

## Key Features

1. **Document Understanding** — AI-powered extraction from PDFs, images, scanned documents. Classifies, extracts, validates. Supports 50+ languages including Swedish, Danish, Norwegian, Finnish, German, French, etc.
2. **Orchestrator API** — Full REST API for trigger, monitor, retrieve results. REST + OData.
3. **AI Center** — Deploy custom ML models. Could host our own NER/fusion models.
4. **Citrix Automation** — Pixel-based automation for virtual desktops (some gov portals use Citrix)
5. **Activity Library** — 500+ pre-built activities
6. **Unattended Robots** — Run 24/7 without human intervention

## Document Understanding Pipeline

```
PDF Filing → UiPath Document Understanding
               │
               ├── Classification: "Annual Report", "Tax Return", "Registration Certificate"
               ├── Extraction: Company name, org number, revenue, profit, board members
               ├── Validation: Cross-check extracted values against rules (e.g., assets = liabilities + equity)
               └── Export: JSON → platform database
```

## When UiPath > Sequentum

| Situation | Sequentum | UiPath |
|---|---|---|
| Stateful web portals (Handelsregister) | Better (visual matching) | Works but heavier |
| **Document Understanding (PDFs)** | No | **Yes — this is UiPath's killer feature** |
| **Citrix/VDI portals** | No | **Yes — pixel-based automation** |
| **Legacy terminal apps** | No | **Yes** |
| **Multi-system orchestration** | No | **Yes — Orchestrator chaining** |
| **Batch document processing** | No | **Yes** |
| Simple web scraping | Works | Overkill |

## Orchestrator Integration

```python
import requests
import time
from typing import Optional

UIPATH_ORCHESTRATOR = "https://cloud.uipath.com/your-tenant"
UIPATH_API_KEY = os.getenv("UIPATH_API_KEY")

def uipath_start_job(process_key: str, inputs: dict) -> str:
    """Start a UiPath job, return job ID."""
    resp = requests.post(
        f"{UIPATH_ORCHESTRATOR}/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs",
        headers={"Authorization": f"Bearer {UIPATH_API_KEY}"},
        json={"startInfo": {
            "ReleaseKey": process_key,
            "Strategy": "Specific",
            "RobotIds": [12345],
            "InputArguments": json.dumps(inputs),
        }}
    )
    return resp.json()["value"][0]["Id"]

def uipath_wait_for_completion(job_id: str, timeout: int = 600) -> Optional[dict]:
    """Wait for job completion, return output."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{UIPATH_ORCHESTRATOR}/odata/Jobs({job_id})",
            headers={"Authorization": f"Bearer {UIPATH_API_KEY}"}
        )
        state = resp.json()["State"]
        if state == "Successful":
            return resp.json()["OutputArguments"]
        if state in ("Faulted", "Stopped"):
            return None
        time.sleep(10)
    return None

# Example: Process 1000 PDF annual reports through Document Understanding
def process_documents_batch(pdf_paths: list[str]) -> list[dict]:
    job_id = uipath_start_job("DocumentUnderstanding_AnnualReports", {
        "inputFolder": r"\\server\filings\2024",
        "outputFolder": r"\\server\extracted\2024",
        "documentType": "AnnualReport",
        "language": "auto",        # UiPath auto-detects language
        "extractionFields": ["company_name", "org_number", "revenue", "profit", "board_members"],
    })
    result = uipath_wait_for_completion(job_id)
    if result:
        return json.loads(result.get("extractedData", "[]"))
    return []
```

## Document Understanding: What It Can Extract

From financial filings in 15+ languages:

| Field | Example | Languages Tested |
|---|---|---|
| Company name | "AB Volvo" | sv, no, da, fi, de, fr, it, es, nl, pl, cs, hu |
| Org number | "556000-0754" | All (numeric pattern) |
| Revenue (SEK/EUR) | "45 678 000" | All (numeric + context) |
| Profit/loss | "+3 200 000" | All |
| Board members | "Anna Wahlberg, Styrelseordförande" | sv, no, da, fi, de, fr, it, es |
| Auditor | "Ernst & Young AB" | All |
| Fiscal year | "2024-01-01 - 2024-12-31" | All (date patterns) |
| Registered address | "Göteborgsvägen 1, 112 34 Stockholm" | All (address patterns) |

## Cost

| Tier | Monthly | Robots | Document Understanding |
|---|---|---|---|
| **Studio (dev only)** | $0 (community) | 0 | Limited |
| **Enterprise Trial** | $0 (60 days) | 1 attended | Full (60 days) |
| **Enterprise** | $500-$2000+ | 1-10 unattended | Full |
| **Enterprise + AI Center** | $2000+ | 10+ unattended | Full + custom ML |

## Seat Management

```python
class UiPathPool:
    """UiPath robot pool — most expensive, used last."""
    def __init__(self):
        self.robots = [
            {"id": 12345, "type": "unattended", "status": "available"},
            {"id": 12346, "type": "unattended", "status": "available"},
        ]
        self.semaphore = asyncio.Semaphore(len(self.robots))

    async def run_job(self, process_key: str, inputs: dict) -> dict:
        async with self.semaphore:
            return await uipath_run(process_key, inputs)
```

## Document Understanding vs Unstructured + Ollama

| Capability | UiPath DU | Unstructured + Ollama |
|---|---|---|
| **Cost** | $500-2000/mo | $0 (your GPU) |
| **Accuracy** | 90-95% (trained) | 85-92% (general) |
| **Languages** | 50+ (commercial) | 20+ (model-dependent) |
| **Handwriting** | Good | Weak (Qwen3-VL helps) |
| **Complex tables** | Excellent | Good (Surya helps) |
| **Setup time** | 1-2 days per document type | 1-2 hours per document type |
| **Custom models** | Yes (AI Center) | Yes (fine-tune OSS models) |
| **Citrix/VDI** | Yes | No |

**Recommendation:** Use Unstructured + Ollama as the DEFAULT (free, good enough for 90% of documents). Escalate to UiPath Document Understanding ONLY for:
1. Handwritten filings (German/Italian registries)
2. Complex, dense tables (financial statements with 20+ columns)
3. Citrix/VDI portals (gov portals on virtual desktops)
4. Batch processing of 10,000+ documents where accuracy matters more than cost

## Related

- [Sequentum](sequentum.md) — better for stateful web portals
- [Ranorex](ranorex.md) — desktop app automation
- [Unstructured + LM Studio](lmstudio-ollama.md) — the OSS document processing alternative
- [OCR Pipeline](ocr-pipeline.md) — the free OCR cascade
