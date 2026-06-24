# Ranorex — Desktop + Web UI Test Automation

> **Tool:** Ranorex Studio | **License:** Paid ($99-$350/mo) | **Key Feature:** Object-based UI recognition for desktop AND web apps

Desktop and web UI automation platform with strong object recognition (not just pixel/image-based — recognizes UI elements by their accessibility tree). Best for: desktop applications, thick clients, and hybrid apps where web+desktop automation is needed in the same workflow.

## What it solves

Some European data sources are desktop applications, not websites:
- **Hogia** (Swedish payroll/accounting — desktop app) — Simon uses this
- **German ELSTER** (tax filing — desktop app or web)
- **Swedish Skatteverket** tax tool (desktop)
- **Financial data terminals** (Bloomberg, Refinitiv — thick clients)
- **Legacy government portals** (Java applets, Silverlight — dying but still exist)

Ranorex automates these where web-based tools can't reach.

## Key Features

1. **Object Recognition** — Finds buttons, fields, tables by accessibility properties. Survives UI redesigns better than pixel/image matching.
2. **Cross-platform** — Desktop (WinForms, WPF, Java Swing, Qt) + Web (full browser) in the same workflow.
3. **Record + Replay** — Record interactions, replay with data-driven inputs
4. **Code Modules** — C# or VB.NET for complex logic beyond recording
5. **Data Binding** — Feed CSV/Excel as input data, run same workflow 10,000 times with different inputs
6. **CI/CD Integration** — Command-line runner, Jenkins/Azure DevOps plugins

## When Ranorex > Everything Else

| Situation | Best Tool |
|---|---|
| **Desktop app (Hogia, Skatteverket, ELSTER)** | **Ranorex** (only tool that handles desktop + web together) |
| **Thick client (Bloomberg, Refinitiv)** | **Ranorex** |
| **Java applet / Silverlight gov portal** | **Ranorex** (no one else handles these) |
| Stateful web portal | Sequentum or Browser-Use |
| PDF batch processing | UiPath Document Understanding or Unstructured |
| Bulk web crawling | Screaming Frog |
| WAF-protected website | CloakBrowser |
| Standard web scraping | Crawlee + Playwright |

## Orchestrator Integration

```python
import subprocess
import json
import os

def ranorex_run_test_suite(suite_path: str, data_source: str, output_dir: str) -> list[dict]:
    """Run a Ranorex test suite with data-driven inputs."""

    # Ranorex CLI runner
    result = subprocess.run([
        "Ranorex.Core.TestSuiteRunner.exe",
        f"--testsuite={suite_path}",
        f"--testdata={data_source}",   # CSV with inputs per row
        f"--reportfile={output_dir}/report.rxzlog",
        f"--reportformat=json",
        "--runconfig=Headless",         # Custom config: no UI needed
    ], capture_output=True, text=True, timeout=1800, check=True)

    # Parse Ranorex JSON report
    with open(f"{output_dir}/report.json") as f:
        report = json.load(f)

    # Extract data from report
    results = []
    for test_case in report.get("TestCases", []):
        if test_case["Result"] == "Success":
            for action in test_case.get("Data", []):
                results.append({
                    "test_case": test_case["Name"],
                    "extracted_fields": action.get("Output", {}),
                })
    return results

# Example: Extract data from Hogia desktop app
data = ranorex_run_test_suite(
    suite_path=r"C:\ranorex\hogia-extract.rxtst",
    data_source=r"C:\data\org_numbers.csv",  # One org number per row
    output_dir=r"C:\data\hogia_output"
)
```

## Data-Driven Extraction Pattern

```
1. Create CSV with 10,000 org numbers to query
2. Record Ranorex workflow once:
   - Open Hogia / Skatteverket / ELSTER
   - Click "Search"
   - Type org number
   - Click "Search" button
   - Wait for result
   - Extract fields: company name, revenue, employees, etc.
   - Save to file
   - Loop to next row in CSV
3. Run: Ranorex replays the workflow 10,000 times with each org number
4. Collect: 10,000 result files → merge → platform database
```

## Desktop Apps That Matter

| App | Country | Data Available | Access |
|---|---|---|---|
| **Hogia Lön/Ekonomi** | Sweden | Payroll, accounting, company data | Licensed (Simon has this) |
| **Skatteverket tool** | Sweden | Tax filings, financial data | Free government tool |
| **ELSTER** | Germany | Tax declarations, company data | Free government tool |
| **Bloomberg Terminal** | Global | Financial data, company profiles | $24K/year (skip — use open data) |
| **Refinitiv Eikon** | Global | Financial, ESG, ownership | $20K/year (skip — use open data) |
| **Legacy gov portals** | Various | Registry data | Free, but no API |

## Seat Management

```python
class RanorexPool:
    """Ranorex seat pool — used for desktop app automation."""
    def __init__(self, max_seats: int = 1):
        self.semaphore = asyncio.Semaphore(max_seats)

    async def run_suite(self, suite: str, data: str, output: str) -> list[dict]:
        async with self.semaphore:
            return await asyncio.to_thread(ranorex_run_test_suite, suite, data, output)

ranorex = RanorexPool(max_seats=1)  # 1 seat = 1 desktop app at a time
```

## Cost

| Tier | Monthly | What You Get |
|---|---|---|
| **Studio (dev)** | $99/mo | Record + replay, 1 machine |
| **Runtime** | $199/mo | Run on any machine (no recording) |
| **Enterprise** | $350/mo | CI/CD, data binding, remote execution |

## Related

- [Sequentum](sequentum.md) — better for web portals (not desktop apps)
- [UiPath](uipath.md) — enterprise RPA + Document Understanding
- [Screaming Frog](screaming-frog.md) — bulk web crawling
- [Account Creation Pipeline](account-creation.md) — credential management for desktop apps
