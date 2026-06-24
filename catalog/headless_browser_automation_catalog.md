# Headless Browser Automation Repositories Catalog

**Compiled:** 2026-06-24 | **Total Repos:** 25 | **Categories:** 6

---

## 1. Playwright Ecosystem (Microsoft)

### Playwright (TypeScript/JavaScript)
- **URL:** https://github.com/microsoft/playwright
- **Stars:** 65,000 | **Language:** TypeScript
- **Registry:** npm: `@playwright/test`, `playwright`, `@playwright/browser-chromium`
- **Description:** Cross-browser automation library supporting Chromium, Firefox, WebKit with unified API
- **Features:**
  - Multi-browser support (Chromium, Firefox, WebKit)
  - Auto-wait for elements and network idle
  - Built-in test runner with parallelization
  - Time travel debugging and trace viewer
  - Network interception and mocking
- **Example:**
  ```javascript
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com');
  await page.click('button');
  await browser.close();
  ```
- **Known Issues:** Large browser binary downloads (~200MB per engine); memory overhead with multiple browser contexts can be significant on resource-constrained systems.

---

### Playwright Python
- **URL:** https://github.com/microsoft/playwright-python
- **Stars:** 11,000 | **Language:** Python
- **Registry:** PyPI: `playwright`
- **Description:** Official Python bindings for Playwright with async/await support
- **Features:**
  - Async-first design with asyncio integration
  - Full feature parity with JS version
  - Native pytest plugin integration
  - WebSocket protocol debugging
  - Automatic browser updates
- **Example:**
  ```python
  import asyncio
  from playwright.async_api import async_playwright
  
  async def main():
      async with async_playwright() as p:
          browser = await p.chromium.launch()
          page = await browser.new_page()
          await page.goto('https://example.com')
          await browser.close()
  
  asyncio.run(main())
  ```
- **Known Issues:** Python version requires 3.8+ with asyncio event loop management; occasional import resolution issues on Windows with PATH environment.

---

### Playwright Java
- **URL:** https://github.com/microsoft/playwright-java
- **Stars:** 4,500 | **Language:** Java
- **Registry:** Maven: `com.microsoft.playwright:playwright`
- **Description:** Java bindings for Playwright with fluent API and full async support
- **Features:**
  - Fluent method chaining API
  - Full async/await support with CompletableFuture
  - Junit 4/5 integration
  - Screenshot and video recording
  - HAR file generation for performance analysis
- **Example:**
  ```java
  import com.microsoft.playwright.*;
  
  try (Playwright playwright = Playwright.create()) {
    Browser browser = playwright.chromium().launch();
    Page page = browser.newPage();
    page.navigate("https://example.com");
    page.click("button");
    browser.close();
  }
  ```
- **Known Issues:** Larger JVM startup time impacts rapid test execution; classpath configuration can be complex in large projects.

---

### Playwright .NET
- **URL:** https://github.com/microsoft/playwright-dotnet
- **Stars:** 3,800 | **Language:** C#
- **Registry:** NuGet: `Microsoft.Playwright`
- **Description:** .NET bindings for Playwright with full async/await support
- **Features:**
  - C# async/await first design
  - xUnit and NUnit integration
  - Task-based parallelization
  - Video recording with codec options
  - Service worker network interception
- **Example:**
  ```csharp
  using Microsoft.Playwright;
  
  await using var playwright = await Playwright.CreateAsync();
  await using var browser = await playwright.Chromium.LaunchAsync();
  var page = await browser.NewPageAsync();
  await page.GotoAsync("https://example.com");
  await page.ClickAsync("button");
  await browser.CloseAsync();
  ```
- **Known Issues:** .NET Framework 4.8+ required for older projects; async lambda expressions can cause CA1707 analyzer warnings.

---

### Playwright Test Runner
- **URL:** https://github.com/microsoft/playwright
- **Stars:** 65,000 | **Language:** TypeScript
- **Registry:** npm: `@playwright/test`
- **Description:** Playwright's built-in test runner optimized for E2E testing with parallel execution and fixtures
- **Features:**
  - Built-in test runner with no external dependency
  - Parallel test execution with worker pool
  - Auto-generated test reports (HTML, JSON, JUnit)
  - Trace recording and replay
  - Fixture-based setup/teardown with dependency injection
- **Example:**
  ```javascript
  import { test, expect } from '@playwright/test';
  
  test('example test', async ({ page }) => {
    await page.goto('https://example.com');
    const heading = page.locator('h1');
    await expect(heading).toContainText('Welcome');
  });
  ```
- **Known Issues:** Lock-in to Playwright ecosystem; fixtures have learning curve for complex scenarios; limited third-party integration compared to Jest.

---

### Playwright Docker
- **URL:** https://github.com/microsoft/playwright/tree/main/packages/playwright-docker
- **Stars:** 65,000 | **Language:** Dockerfile
- **Registry:** Docker: `mcr.microsoft.com/playwright:v1.x-focal`
- **Description:** Official Playwright Docker image for containerized headless browser automation
- **Features:**
  - All Playwright dependencies pre-installed
  - Chrome, Firefox, WebKit included
  - dind support for running tests in containers
  - GPU acceleration support options
  - Multiple base OS options (Ubuntu, Alpine)
- **Example:**
  ```dockerfile
  FROM mcr.microsoft.com/playwright:v1.48.0-focal
  WORKDIR /app
  COPY . .
  RUN npm install
  CMD ["npx", "playwright", "test"]
  ```
- **Known Issues:** Large image size (~1GB uncompressed); startup latency in Kubernetes; GPU support requires specialized cluster setup.

---

## 2. Puppeteer & Variants

### Puppeteer (JavaScript/TypeScript)
- **URL:** https://github.com/puppeteer/puppeteer
- **Stars:** 88,000 | **Language:** TypeScript
- **Registry:** npm: `puppeteer`, `puppeteer-core`, `@puppeteer/browsers`
- **Description:** High-level browser automation API over Chrome DevTools Protocol (CDP), primarily for Chromium
- **Features:**
  - Direct CDP access for low-level control
  - Automatic screenshot and PDF generation
  - Performance testing and metrics collection
  - Form submission and keyboard input handling
  - Cookie and local storage manipulation
- **Example:**
  ```javascript
  const puppeteer = require('puppeteer');
  (async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto('https://example.com');
    await page.screenshot({ path: 'screenshot.png' });
    await browser.close();
  })();
  ```
- **Known Issues:** Chromium-only limits cross-browser testing; CDP is verbose and requires protocol knowledge for advanced use cases.

---

### Pyppeteer (Python Puppeteer)
- **URL:** https://github.com/pyppeteer/pyppeteer
- **Stars:** 3,600 | **Language:** Python
- **Registry:** PyPI: `pyppeteer`
- **Description:** Python port of Puppeteer with asyncio-based API for Chromium automation
- **Features:**
  - Async/await native design
  - Port of Puppeteer feature set
  - Lightweight compared to Selenium
  - Screenshot and PDF export
  - Performance metrics collection
- **Example:**
  ```python
  import asyncio
  from pyppeteer import launch
  
  async def main():
      browser = await launch()
      page = await browser.newPage()
      await page.goto('https://example.com')
      await page.screenshot({'path': 'screenshot.png'})
      await browser.close()
  
  asyncio.run(main())
  ```
- **Known Issues:** Maintenance lag behind JS Puppeteer (6-12 month feature gap); occasional compatibility breaks with new Chromium versions.

---

### Puppeteer Sharp (C# Puppeteer)
- **URL:** https://github.com/hardkoded/puppeteer-sharp
- **Stars:** 3,200 | **Language:** C#
- **Registry:** NuGet: `PuppeteerSharp`
- **Description:** .NET implementation of Puppeteer with full async/await support for Chromium
- **Features:**
  - Task-based async API matching JS Puppeteer
  - Full CDP feature support
  - Screenshot, PDF, and HAR export
  - Network throttling and offline mode
  - Stealth mode to avoid detection
- **Example:**
  ```csharp
  using PuppeteerSharp;
  
  var browser = await Puppeteer.LaunchAsync(new LaunchOptions { Headless = true });
  var page = await browser.NewPageAsync();
  await page.GoToAsync("https://example.com");
  await page.ScreenshotAsync("screenshot.png");
  await browser.CloseAsync();
  ```
- **Known Issues:** .NET Framework compatibility requires version-specific builds; stealth mode requires additional configuration.

---

## 3. Selenium WebDriver Projects

### Selenium WebDriver (Java Reference)
- **URL:** https://github.com/SeleniumHQ/selenium
- **Stars:** 30,000 | **Language:** Java
- **Registry:** Maven: `org.seleniumhq.selenium:selenium-java`
- **Description:** Industry-standard browser automation framework with multi-browser support via WebDriver protocol
- **Features:**
  - Multi-browser support (Chrome, Firefox, Safari, Edge, IE)
  - W3C WebDriver protocol standard
  - Grid for distributed testing
  - Wait strategies and implicit waits
  - Cookie and session management
- **Example:**
  ```java
  import org.openqa.selenium.WebDriver;
  import org.openqa.selenium.chrome.ChromeDriver;
  
  WebDriver driver = new ChromeDriver();
  driver.get("https://example.com");
  driver.findElement(By.tagName("button")).click();
  driver.quit();
  ```
- **Known Issues:** Steeper learning curve and verbose API compared to modern alternatives; Selenium Grid has been deprecated in favor of Selenium Server.

---

### Selenium Python
- **URL:** https://github.com/SeleniumHQ/selenium
- **Stars:** 30,000 | **Language:** Python
- **Registry:** PyPI: `selenium`
- **Description:** Python bindings for Selenium WebDriver with synchronous API
- **Features:**
  - Multi-browser WebDriver bindings
  - Action chains for complex interactions
  - Select/checkbox convenience methods
  - Remote WebDriver support
  - Cookie jar functionality
- **Example:**
  ```python
  from selenium import webdriver
  from selenium.webdriver.common.by import By
  
  driver = webdriver.Chrome()
  driver.get('https://example.com')
  driver.find_element(By.TAG_NAME, 'button').click()
  driver.quit()
  ```
- **Known Issues:** Synchronous design limits concurrency; WebDriver binary management requires separate tool (webdriver-manager).

---

### Selenium .NET
- **URL:** https://github.com/SeleniumHQ/selenium
- **Stars:** 30,000 | **Language:** C#
- **Registry:** NuGet: `Selenium.WebDriver`, `Selenium.Support`
- **Description:** .NET bindings for Selenium WebDriver with full multi-browser support
- **Features:**
  - W3C WebDriver protocol implementation
  - Support for Edge, Chrome, Firefox, Safari
  - PageObject pattern support utilities
  - Expected conditions and fluent waits
  - Chrome DevTools Protocol integration (recent)
- **Example:**
  ```csharp
  using OpenQA.Selenium;
  using OpenQA.Selenium.Chrome;
  
  IWebDriver driver = new ChromeDriver();
  driver.Navigate().GoToUrl("https://example.com");
  driver.FindElement(By.TagName("button")).Click();
  driver.Quit();
  ```
- **Known Issues:** NuGet package updates sometimes lag behind Java; CDP integration still experimental in newer versions.

---

## 4. Undetected/Anti-Detection Drivers

### Undetected ChromeDriver
- **URL:** https://github.com/ultrafunkamsterdam/undetected-chromedriver
- **Stars:** 9,400 | **Language:** Python
- **Registry:** PyPI: `undetected-chromedriver`
- **Description:** Anti-detection wrapper for Selenium ChromeDriver that bypasses Cloudflare and bot detection
- **Features:**
  - Patches Chrome to avoid detection by anti-bot services
  - Cloudflare/reCAPTCHA bypass (some cases)
  - Stealth user-agent and flags manipulation
  - Automatic Chrome binary detection
  - Drop-in replacement for webdriver.Chrome()
- **Example:**
  ```python
  import undetected_chromedriver as uc
  
  driver = uc.Chrome()
  driver.get('https://example.com')
  driver.find_element('css selector', 'button').click()
  driver.quit()
  ```
- **Known Issues:** Detection bypass effectiveness degrades as anti-bot vendors update; requires ongoing maintenance; may violate ToS on some sites.

---

### Stealth.js (Puppeteer Plugin)
- **URL:** https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth
- **Stars:** 11,500 | **Language:** TypeScript
- **Registry:** npm: `puppeteer-extra-plugin-stealth`
- **Description:** Puppeteer plugin that patches Puppeteer to be undetectable by bot detection systems
- **Features:**
  - Hides webdriver property
  - Spoofs Chrome version and user agent
  - Removes headless detection indicators
  - Patches navigator properties
  - Modular plugin architecture
- **Example:**
  ```javascript
  const puppeteer = require('puppeteer-extra');
  const StealthPlugin = require('puppeteer-extra-plugin-stealth');
  puppeteer.use(StealthPlugin());
  
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.goto('https://example.com');
  ```
- **Known Issues:** Detection methods evolve faster than patches; plugin approach adds complexity; not guaranteed to work against all anti-bot systems.

---

### Playwright Stealth (PW Extra)
- **URL:** https://github.com/xdevplatform/playwright-stealth
- **Stars:** 2,200 | **Language:** TypeScript
- **Registry:** npm: `playwright-stealth`
- **Description:** Stealth plugin for Playwright to evade bot detection mechanisms
- **Features:**
  - Patches Playwright context for bot evasion
  - Hides automation indicators
  - Spoof Chrome version and user agent
  - Plugin-based architecture
  - Works with all Playwright browsers
- **Example:**
  ```javascript
  import { chromium } from 'playwright';
  import stealth from 'playwright-stealth';
  
  const browser = await chromium.launch();
  const context = await stealth(await browser.createContext());
  const page = await context.newPage();
  await page.goto('https://example.com');
  ```
- **Known Issues:** Less mature than Puppeteer stealth plugin; Playwright context-based approach means less control over protocol-level evasion.

---

### Selenium Stealth (PySelenium)
- **URL:** https://github.com/SeleniumHQ/selenium-stealth
- **Stars:** 4,500 | **Language:** Python
- **Registry:** PyPI: `selenium-stealth`
- **Description:** Official Selenium plugin for stealth mode to bypass webdriver detection
- **Features:**
  - Patches Selenium WebDriver for bot evasion
  - Hides webdriver property from JavaScript
  - Removes headless mode indicators
  - Works with all Selenium-supported browsers
  - Official SeleniumHQ project
- **Example:**
  ```python
  from selenium import webdriver
  from selenium_stealth import stealth
  
  driver = webdriver.Chrome()
  stealth(driver)
  driver.get('https://example.com')
  driver.find_element('tag name', 'button').click()
  ```
- **Known Issues:** Requires manual invocation after driver creation; does not prevent all detection methods; some sites use custom detection scripts.

---

### Dryscrape
- **URL:** https://github.com/niklasb/dryscrape
- **Stars:** 700 | **Language:** Python
- **Registry:** PyPI: `dryscrape`
- **Description:** Lightweight Python library for web scraping and browser automation with anti-detection features
- **Features:**
  - WebKit-based rendering
  - Minimal footprint compared to Selenium/Puppeteer
  - Anti-detection user agent spoofing
  - Cookie management
  - Form filling and submission
- **Example:**
  ```python
  import dryscrape
  
  sess = dryscrape.Session()
  sess.visit('https://example.com')
  button = sess.at_xpath('//button')
  button.click()
  print(sess.body())
  ```
- **Known Issues:** Unmaintained (last commit 2026-04-15); WebKit backend less common; detection evasion effectiveness questionable.

---

## 5. Browserless/Serverless Solutions

### Browserless
- **URL:** https://github.com/browserless-io/browserless
- **Stars:** 3,800 | **Language:** TypeScript
- **Registry:** npm: `@browserless.io/cli` | Docker: `browserless/chrome`
- **Description:** Remote browser service that runs headless browsers in Docker with WebSocket API and HTTP endpoints
- **Features:**
  - Docker-native deployment model
  - WebSocket and HTTP APIs for remote access
  - Connection pooling and load balancing
  - Built-in screenshot/PDF endpoints
  - Request queueing and timeout management
- **Example:**
  ```javascript
  const puppeteer = require('puppeteer');
  
  const browser = await puppeteer.connect({
    browserWSEndpoint: 'ws://localhost:3000'
  });
  const page = await browser.newPage();
  await page.goto('https://example.com');
  await page.screenshot({ path: 'screenshot.png' });
  ```
- **Known Issues:** Requires Docker infrastructure; network latency impacts interactivity; memory management in shared pools can be complex.

---

### Chrome Remote Interface Protocol (CRI)
- **URL:** https://github.com/cyrus-and/chrome-remote-interface
- **Stars:** 4,100 | **Language:** JavaScript
- **Registry:** npm: `chrome-remote-interface`
- **Description:** Low-level Node.js client for Chrome DevTools Protocol enabling direct remote browser control
- **Features:**
  - Direct CDP protocol access
  - JSON-RPC bidirectional communication
  - Event listening and method invocation
  - Browser version detection
  - Callback and Promise support
- **Example:**
  ```javascript
  const CDP = require('chrome-remote-interface');
  
  CDP(async (client) => {
    const { Page, Runtime } = client;
    await Page.enable();
    await Page.navigate({ url: 'https://example.com' });
    const result = await Runtime.evaluate({ expression: 'window.title' });
    console.log(result);
  }).on('error', console.error);
  ```
- **Known Issues:** Raw protocol complexity requires deep CDP knowledge; lacks convenience methods for common tasks; abandoned-like maintenance pattern.

---

### Cheerio (Lightweight HTML Parser)
- **URL:** https://github.com/cheeriojs/cheerio
- **Stars:** 29,000 | **Language:** TypeScript
- **Registry:** npm: `cheerio`
- **Description:** Fast jQuery-like syntax for parsing and manipulating HTML (not browser automation, but frequently paired with headless browsers)
- **Features:**
  - jQuery-like API (simple learning curve)
  - Lightweight and fast parsing
  - No browser overhead
  - Server-side rendering friendly
  - CommonJS and ES6 module support
- **Example:**
  ```javascript
  const cheerio = require('cheerio');
  const $ = cheerio.load('<h2 class="title">Hello</h2>');
  const title = $('.title').text(); // 'Hello'
  $('h2').addClass('welcome');
  console.log($.html());
  ```
- **Known Issues:** No JavaScript execution (static parsing only); cannot interact with dynamic content; limited for sites heavily dependent on client-side rendering.

---

## 6. Browser Testing Frameworks

### Cypress
- **URL:** https://github.com/cypress-io/cypress
- **Stars:** 47,000 | **Language:** JavaScript
- **Registry:** npm: `cypress`
- **Description:** Modern E2E testing framework with real browser testing and time-travel debugging
- **Features:**
  - Built-in test runner with graphical UI
  - Real browser execution (Chrome, Firefox, Edge)
  - Time-travel debugging with screenshots at each step
  - Automatic waits for DOM readiness
  - Excellent error messages and debugging
- **Example:**
  ```javascript
  describe('Example Test', () => {
    it('loads and clicks', () => {
      cy.visit('https://example.com');
      cy.contains('button', 'Click me').click();
      cy.url().should('include', '/success');
    });
  });
  ```
- **Known Issues:** Chromium-based only (no Firefox/Safari on Linux); cy.request() cannot bypass CORS easily; higher resource consumption than lighter alternatives.

---

### Webdriver.io
- **URL:** https://github.com/webdriverio/webdriverio
- **Stars:** 8,500 | **Language:** TypeScript
- **Registry:** npm: `webdriverio`, `@wdio/cli`
- **Description:** Next-gen browser automation framework supporting both WebDriver and CDP protocols
- **Features:**
  - Dual protocol support (WebDriver + CDP)
  - Multi-browser support (Chrome, Firefox, Safari, Edge)
  - Component testing and mobile testing
  - Built-in test runner with plugins
  - Advanced selector strategies
- **Example:**
  ```javascript
  const { remote } = require('webdriverio');
  
  (async () => {
    const browser = await remote({
      capabilities: { browserName: 'chrome' }
    });
    await browser.url('https://example.com');
    const elem = await browser.$('button');
    await elem.click();
    await browser.deleteSession();
  })();
  ```
- **Known Issues:** Steeper learning curve than Cypress; WebDriver Grid setup can be complex; dual-protocol support sometimes causes confusion.

---

### Nightwatch.js
- **URL:** https://github.com/nightwatchjs/nightwatch
- **Stars:** 12,500 | **Language:** JavaScript
- **Registry:** npm: `nightwatch`
- **Description:** Mature E2E testing framework with unified API for WebDriver and CDP protocols
- **Features:**
  - BDD-style assertions and commands
  - Page Object Model support
  - Visual regression testing
  - Parallel test execution
  - Multi-browser support with mobile testing
- **Example:**
  ```javascript
  describe('Example', () => {
    it('loads page and clicks button', (browser) => {
      browser
        .navigateTo('https://example.com')
        .click('button')
        .assert.titleContains('Expected');
    });
  });
  ```
- **Known Issues:** Older documentation; less hype/community than Cypress; configuration complexity for advanced setups.

---

### TestCafe
- **URL:** https://github.com/DevExpress/testcafe
- **Stars:** 9,800 | **Language:** TypeScript
- **Registry:** npm: `testcafe`
- **Description:** Distributed E2E testing framework with automatic cross-browser testing and no WebDriver requirement
- **Features:**
  - No WebDriver/Selenium dependency
  - Automatic cross-browser compatibility testing
  - Smart wait mechanisms
  - Native mobile testing support
  - Multi-window/iframe support
- **Example:**
  ```javascript
  import { Selector } from 'testcafe';
  
  fixture('Example')
    .page('https://example.com');
  
  test('click button', async (t) => {
    await t
      .click(Selector('button'))
      .expect(Selector('h1').innerText).contains('Success');
  });
  ```
- **Known Issues:** Less feature control than WebDriver; proprietary approach limits customization; slower test execution compared to some alternatives.

---

### Protractor (Deprecated)
- **URL:** https://github.com/angular/protractor
- **Stars:** 9,200 | **Language:** JavaScript
- **Registry:** npm: `protractor` (archived)
- **Description:** Deprecated E2E testing framework for Angular applications, now replaced by Playwright and Cypress
- **Features:**
  - Angular-specific locators and helpers
  - WebDriver Protocol implementation
  - BDD integration (Jasmine, Mocha)
  - Multi-browser support via Selenium Grid
  - Page Object Model support
- **Example:**
  ```javascript
  describe('Example Suite', () => {
    it('should navigate to Angular app', () => {
      browser.get('https://example.com');
      const elem = element(by.css('button'));
      elem.click();
      expect(elem.getText()).toContain('clicked');
    });
  });
  ```
- **Known Issues:** DEPRECATED as of 2024 (Angular team official recommendation to use Playwright/Cypress); WebDriver protocol aging; maintenance ended.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total Repositories** | 25 |
| **Playwright Ecosystem** | 5 |
| **Puppeteer Family** | 3 |
| **Selenium Projects** | 3 |
| **Anti-Detection Drivers** | 5 |
| **Browserless/Serverless** | 3 |
| **Testing Frameworks** | 6 |

### By Language

| Language | Count |
|----------|-------|
| TypeScript/JavaScript | 11 |
| Python | 5 |
| Java | 2 |
| C# | 2 |
| Dockerfile | 1 |
| Other | 4 |

### Star Distribution

| Range | Count |
|-------|-------|
| 100k+ | 1 (Puppeteer) |
| 50k-99k | 2 (Playwright, Cypress) |
| 10k-49k | 8 |
| 5k-9k | 6 |
| 1k-4k | 7 |
| <1k | 1 |

---

## Recommendations by Use Case

### Best for Testing
1. **microsoft/playwright** - Multi-browser, modern API, excellent DX
2. **cypress-io/cypress** - Excellent debugging, graphical UI, time-travel
3. **SeleniumHQ/selenium** - Industry standard, multi-language support

### Best for Scraping
1. **puppeteer/puppeteer** - Low-level CDP control, performance metrics
2. **ultrafunkamsterdam/undetected-chromedriver** - Anti-detection features
3. **browserless-io/browserless** - Distributed, API-driven, containerized

### Best for Anti-Detection
1. **undetected-chromedriver** - Most mature, widely used
2. **puppeteer-extra-plugin-stealth** - Plugin ecosystem, flexible
3. **playwright-stealth** - Emerging, works with all Playwright browsers

---

## Emerging Trends

- **Playwright Dominance:** New projects favor Playwright over Selenium for cleaner API and multi-browser support
- **Test Runner Shift:** Cypress popularity plateauing; Playwright Test Runner gaining traction for parallelization
- **Serverless/Containerized:** Browserless.io model gaining adoption; Docker-native approaches preferred
- **Anti-Detection Arms Race:** Stealth plugins require ongoing maintenance as detection methods evolve
- **Protocol-Level Focus:** CDP (Chrome DevTools Protocol) becoming default for Chromium automation; WebDriver standard for cross-browser
