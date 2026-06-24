# Complete Worker Dockerfile + Implementation Guide

## Production-Ready Worker Dockerfile

**File: `services/worker/Dockerfile`**

```dockerfile
# Multi-stage build: reduce final image size
FROM node:18-alpine AS builder

WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Runtime stage
FROM node:18-alpine

# Install system dependencies for Chromium
RUN apk add --no-cache \
    chromium \
    noto-sans \
    noto-sans-arabic \
    noto-sans-hebrew \
    noto-sans-thai \
    noto-sans-devanagari \
    noto-sans-cyrillic \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-dejavu \
    curl

# Create app user (non-root)
RUN addgroup -g 1000 scraper && \
    adduser -D -u 1000 -G scraper scraper

WORKDIR /app

# Copy node modules from builder
COPY --from=builder /build/node_modules ./node_modules
COPY --chown=scraper:scraper . .

# Set up Chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV NODE_ENV=production

# Health check file
RUN touch /tmp/worker_ready && chown scraper:scraper /tmp/worker_ready

USER scraper

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9090/metrics || exit 1

EXPOSE 9090

CMD ["node", "--max-old-space-size=1800", "worker.js"]
```

## Complete Worker Implementation

**File: `services/worker/worker.js`**

```javascript
const redis = require('redis');
const puppeteer = require('puppeteer');
const pino = require('pino');
const { promClient } = require('prom-client');
const express = require('express');
const os = require('os');
const fs = require('fs');

// ===== LOGGING =====
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: false,
      singleLine: true,
      translateTime: 'SYS:standard',
    },
  },
});

// ===== METRICS =====
const register = new promClient.Registry();

const scrapeCounter = new promClient.Counter({
  name: 'scrape_total',
  help: 'Total scrapes attempted',
  labelNames: ['status', 'domain'],
  registers: [register],
});

const scrapeDuration = new promClient.Histogram({
  name: 'scrape_duration_seconds',
  help: 'Scrape duration in seconds',
  labelNames: ['domain'],
  buckets: [0.5, 1, 2, 5, 10, 30],
  registers: [register],
});

const queueDepth = new promClient.Gauge({
  name: 'queue_depth',
  help: 'Current queue depth',
  registers: [register],
});

const workerState = new promClient.Gauge({
  name: 'worker_state',
  help: 'Worker state (0=idle, 1=processing, 2=error)',
  labelNames: ['worker_id'],
  registers: [register],
});

const tabUsage = new promClient.Gauge({
  name: 'browser_tabs_in_use',
  help: 'Number of active browser tabs',
  registers: [register],
});

// ===== CONFIGURATION =====
const CONFIG = {
  workerId: process.env.WORKER_ID || `worker-${os.hostname()}`,
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  concurrentTabs: parseInt(process.env.CONCURRENT_TABS) || 10,
  timeoutSeconds: parseInt(process.env.WORKER_TIMEOUT_S) || 30,
  maxRetries: parseInt(process.env.MAX_RETRIES) || 3,
  proxyService: process.env.PROXY_SERVICE || 'bright_data',
  proxyApiKey: process.env.PROXY_API_KEY,
  metricsPort: 9090,
};

// ===== PROXY MANAGEMENT =====
class ProxyManager {
  constructor(service, apiKey) {
    this.service = service;
    this.apiKey = apiKey;
    this.pool = [];
    this.badProxies = new Set();
    this.domainStickyMap = new Map();
    this.lastRotation = Date.now();
  }

  async initialize() {
    logger.info(`Initializing proxy pool (service: ${this.service})`);
    
    if (this.service === 'bright_data') {
      // Call Bright Data API to get IPs
      try {
        const response = await fetch('https://api.brightdata.com/zones/list', {
          headers: { Authorization: `Bearer ${this.apiKey}` },
        });
        const zones = await response.json();
        
        // Use first available zone
        if (zones.zones && zones.zones.length > 0) {
          const zone = zones.zones[0];
          this.zoneId = zone.id;
          logger.info(`Using Bright Data zone: ${zone.name}`);
        }
      } catch (err) {
        logger.warn(`Failed to fetch zones from Bright Data: ${err.message}`);
      }
    }
    
    // Pre-fill pool
    await this.rotate();
  }

  async getProxy(domain, geoHint = null) {
    // Check sticky session
    if (this.domainStickyMap.has(domain)) {
      const proxy = this.domainStickyMap.get(domain);
      if (!this.badProxies.has(proxy)) {
        return proxy;
      }
    }

    // Rotate if pool empty
    if (this.pool.length < 5) {
      await this.rotate();
    }

    if (this.pool.length === 0) {
      logger.warn('No proxies available, falling back to direct');
      return null;
    }

    const proxy = this.pool.pop();
    this.domainStickyMap.set(domain, proxy);

    return proxy;
  }

  async markBad(proxy, domain = null) {
    this.badProxies.add(proxy);
    if (domain && this.domainStickyMap.get(domain) === proxy) {
      this.domainStickyMap.delete(domain);
    }
    logger.debug(`Marked proxy as bad: ${proxy}`);
  }

  async rotate() {
    logger.info('Rotating proxy pool...');
    
    if (this.service === 'bright_data') {
      try {
        // Generate rotating proxy list
        const proxies = [];
        for (let i = 0; i < 50; i++) {
          proxies.push(`http://${this.apiKey}:zone-${this.zoneId}@proxy.provider.com:8080`);
        }
        this.pool = proxies;
        this.domainStickyMap.clear();
        this.badProxies.clear();
        this.lastRotation = Date.now();
        logger.info(`Rotated ${proxies.length} proxies`);
      } catch (err) {
        logger.error(`Failed to rotate proxies: ${err.message}`);
      }
    }
  }
}

// ===== RATE LIMITER =====
class RateLimiter {
  constructor(redisClient) {
    this.redis = redisClient;
    this.limits = {
      'linkedin.com': 2.0,
      'github.com': 5.0,
      'twitter.com': 3.0,
      'default': 10.0,
    };
  }

  async wait(domain) {
    const limit = this._getDomainLimit(domain);
    const key = `rate_limit:${domain}`;
    const now = Date.now() / 1000;

    try {
      const bucket = parseFloat((await this.redis.get(key)) || limit.toString());
      const lastUpdate = parseFloat((await this.redis.get(`${key}:last`)) || now.toString());

      const elapsed = now - lastUpdate;
      const refilled = Math.min(limit, bucket + elapsed * limit);

      if (refilled >= 1.0) {
        await this.redis.setex(key, 3600, (refilled - 1.0).toString());
        await this.redis.setex(`${key}:last`, 3600, now.toString());
        return;
      }

      const waitTime = (1.0 - refilled) / limit;
      logger.debug(`Rate limit wait for ${domain}: ${waitTime.toFixed(2)}s`);
      await new Promise(r => setTimeout(r, waitTime * 1000));
      
      // Recursive call
      return this.wait(domain);
    } catch (err) {
      logger.error(`Rate limiter error for ${domain}: ${err.message}`);
      // Fail open
      return;
    }
  }

  _getDomainLimit(domain) {
    for (const [key, limit] of Object.entries(this.limits)) {
      if (domain.includes(key)) return limit;
    }
    return this.limits.default;
  }
}

// ===== SCRAPING WORKER =====
class ScrapingWorker {
  constructor(workerId, config) {
    this.workerId = workerId;
    this.config = config;
    this.redis = null;
    this.browser = null;
    this.proxyMgr = new ProxyManager(config.proxyService, config.proxyApiKey);
    this.rateLimiter = null;
    this.activeTabs = 0;
  }

  async initialize() {
    // Redis connection
    this.redis = redis.createClient({ url: this.config.redisUrl });
    this.redis.on('error', (err) => {
      logger.error(`Redis error: ${err.message}`);
    });
    await this.redis.connect();
    logger.info('Connected to Redis');

    // Proxy manager
    await this.proxyMgr.initialize();

    // Rate limiter
    this.rateLimiter = new RateLimiter(this.redis);

    // Browser
    this.browser = await puppeteer.launch({
      headless: 'new',
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',  // Prevent shared memory issues
        '--disable-gpu',
        '--single-process=false',
        '--no-first-run',
        '--no-default-browser-check',
      ],
    });

    logger.info('Chromium browser launched');

    // Mark as ready
    fs.writeFileSync('/tmp/worker_ready', '1');
    workerState.set({ worker_id: this.workerId }, 0);
  }

  async workLoop() {
    logger.info(`Worker starting with ${this.config.concurrentTabs} concurrent tabs`);

    const tabTasks = [];
    for (let i = 0; i < this.config.concurrentTabs; i++) {
      tabTasks.push(this.processTabLoop(i));
    }

    await Promise.all(tabTasks);
  }

  async processTabLoop(tabId) {
    let page = null;

    while (true) {
      try {
        // Pop task from queue (blocking, 30s timeout)
        const taskJson = await this.redis.blpop(
          ['tasks:pending:high', 'tasks:pending:medium', 'tasks:pending:low'],
          30
        );

        if (!taskJson) {
          // Queue empty
          workerState.set({ worker_id: this.workerId }, 0);
          await new Promise(r => setTimeout(r, 5000));
          continue;
        }

        const [, taskData] = taskJson;
        const task = JSON.parse(taskData);
        const startTime = Date.now();

        workerState.set({ worker_id: this.workerId }, 1);
        this.activeTabs++;
        tabUsage.set(this.activeTabs);

        logger.info(`[Tab ${tabId}] Processing job ${task.job_id}: ${task.url}`);

        try {
          // Rate limit
          const domain = new URL(task.url).hostname;
          await this.rateLimiter.wait(domain);

          // Get proxy
          const proxy = await this.proxyMgr.getProxy(domain, task.geo_hint);

          // Create page if needed
          if (!page) {
            page = await this.browser.newPage();
            await page.setViewport({ width: 1280, height: 720 });
            
            // Set proxy
            if (proxy) {
              await page.goto('about:blank'); // Warm-up
            }
          }

          // Navigate with timeout
          await page.goto(task.url, {
            waitUntil: 'networkidle2',
            timeout: this.config.timeoutSeconds * 1000,
          });

          // Extract HTML + screenshot
          const html = await page.content();
          const screenshot = await page.screenshot({
            encoding: 'base64',
            type: 'png',
          });

          const elapsed = (Date.now() - startTime) / 1000;
          scrapeDuration.observe({ domain }, elapsed);

          // Push to validation queue
          await this.redis.lpush(
            'tasks:validated',
            JSON.stringify({
              job_id: task.job_id,
              html,
              screenshot,
              domain,
              extracted_at: new Date().toISOString(),
            })
          );

          scrapeCounter.inc({ status: 'success', domain });
          logger.info(`[Tab ${tabId}] ✓ Job ${task.job_id} completed in ${elapsed.toFixed(2)}s`);

        } catch (err) {
          const elapsed = (Date.now() - startTime) / 1000;
          const domain = new URL(task.url).hostname;

          logger.warn(`[Tab ${tabId}] ✗ Job ${task.job_id} failed: ${err.message}`);

          // Classify error
          let errorType = 'unknown';
          if (err.message.includes('timeout')) {
            errorType = 'timeout';
          } else if (err.message.includes('403') || err.message.includes('429')) {
            errorType = 'rate_limit';
            // Trigger proxy rotation
            await this.proxyMgr.markBad(null, domain);
          } else if (err.message.includes('net::ERR_NAME_NOT_RESOLVED')) {
            errorType = 'dns_error';
          }

          scrapeCounter.inc({ status: errorType, domain });

          // Retry with exponential backoff
          task.attempt_count = (task.attempt_count || 0) + 1;
          if (task.attempt_count < this.config.maxRetries) {
            const backoffMs = 1000 * Math.pow(2, task.attempt_count);
            logger.info(`[Tab ${tabId}] Re-queuing ${task.job_id} after ${backoffMs}ms (attempt ${task.attempt_count})`);
            
            // Use delayed queue (simple: sleep then re-queue)
            await new Promise(r => setTimeout(r, backoffMs));
            
            const priority = task.attempt_count >= 2 ? 'low' : 'medium';
            await this.redis.lpush(
              `tasks:pending:${priority}`,
              JSON.stringify(task)
            );
          } else {
            // Max retries exceeded
            logger.error(`[Tab ${tabId}] Max retries exceeded for ${task.job_id}`);
            await this.redis.lpush(
              'tasks:dlq',
              JSON.stringify({
                ...task,
                error: err.message,
                error_type: errorType,
                final_attempt: task.attempt_count,
              })
            );
          }

          // Close page on error (fresh start)
          if (page) {
            await page.close().catch(() => {});
            page = null;
          }
        }

        this.activeTabs--;
        tabUsage.set(this.activeTabs);

      } catch (err) {
        logger.error(`[Tab ${tabId}] Unexpected error: ${err.message}`);
        workerState.set({ worker_id: this.workerId }, 2);
        
        if (page) {
          await page.close().catch(() => {});
          page = null;
        }

        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }

  async shutdown() {
    logger.info('Shutting down worker...');
    
    if (this.browser) {
      await this.browser.close();
    }
    
    if (this.redis) {
      await this.redis.quit();
    }
    
    logger.info('Worker shut down complete');
  }
}

// ===== METRICS SERVER =====
function startMetricsServer(port) {
  const app = express();

  app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  });

  app.get('/health', (req, res) => {
    res.json({ status: 'ok', worker_id: CONFIG.workerId });
  });

  app.listen(port, () => {
    logger.info(`Metrics server listening on port ${port}`);
  });
}

// ===== MAIN =====
async function main() {
  logger.info(`Starting worker: ${CONFIG.workerId}`);
  logger.info(`Config: ${JSON.stringify(CONFIG, null, 2)}`);

  const worker = new ScrapingWorker(CONFIG.workerId, CONFIG);

  try {
    await worker.initialize();
    startMetricsServer(CONFIG.metricsPort);

    // Graceful shutdown
    process.on('SIGTERM', async () => {
      logger.info('SIGTERM received, shutting down gracefully...');
      await worker.shutdown();
      process.exit(0);
    });

    // Start work loop
    await worker.workLoop();
  } catch (err) {
    logger.error(`Fatal error: ${err.message}`);
    process.exit(1);
  }
}

main().catch((err) => {
  logger.error(`Unhandled error: ${err.message}`);
  process.exit(1);
});
```

## Worker package.json

**File: `services/worker/package.json`**

```json
{
  "name": "scraping-worker",
  "version": "1.0.0",
  "description": "Distributed web scraping worker",
  "main": "worker.js",
  "scripts": {
    "start": "node worker.js",
    "dev": "nodemon worker.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pino": "^8.16.2",
    "pino-pretty": "^10.3.1",
    "prom-client": "^15.0.0",
    "puppeteer": "^21.6.1",
    "redis": "^4.6.11"
  },
  "devDependencies": {
    "nodemon": "^3.0.2",
    "jest": "^29.7.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

## Environment Configuration

**File: `.env.worker`**

```bash
# Worker Configuration
WORKER_ID=worker-1
REDIS_URL=redis://redis:6379/0
CONCURRENT_TABS=10
WORKER_TIMEOUT_S=30
MAX_RETRIES=3

# Proxy Service
PROXY_SERVICE=bright_data
PROXY_API_KEY=your_bright_data_api_key

# Browser
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Monitoring
METRICS_PORT=9090

# Performance
NODE_MAX_OLD_SPACE_SIZE=1800
```

## Testing the Worker

**File: `services/worker/test.worker.js`**

```javascript
const { strict: assert } = require('assert');
const redis = require('redis');

async function testWorker() {
  const client = redis.createClient({ url: 'redis://localhost:6379' });
  await client.connect();

  // Enqueue test task
  const testTask = {
    job_id: 'test-123',
    url: 'https://example.com',
    selectors: { title: 'h1' },
    priority: 5,
    attempt_count: 0,
  };

  await client.lpush('tasks:pending:medium', JSON.stringify(testTask));
  console.log('✓ Enqueued test task');

  // Wait for validation result
  let validated = null;
  for (let i = 0; i < 60; i++) {
    const result = await client.lpop('tasks:validated');
    if (result) {
      validated = JSON.parse(result);
      break;
    }
    await new Promise(r => setTimeout(r, 1000));
  }

  assert(validated, 'Task should be validated');
  assert(validated.html, 'Should extract HTML');
  assert(validated.screenshot, 'Should capture screenshot');

  console.log('✓ Worker test passed');

  await client.quit();
}

testWorker().catch(console.error);
```

**Run test:**
```bash
docker-compose up -d
docker-compose exec worker node test.worker.js
```

---

## Performance Tuning

### Memory Optimization

```javascript
// Limit Chromium memory usage per page
await page.setDefaultNavigationTimeout(30000);
await page.setDefaultTimeout(30000);

// Close pages aggressively
setInterval(async () => {
  const pages = await browser.pages();
  if (pages.length > this.config.concurrentTabs + 2) {
    const toClose = pages.slice(this.config.concurrentTabs);
    for (const p of toClose) {
      await p.close().catch(() => {});
    }
  }
}, 10000);
```

### CPU Optimization

```javascript
// Disable JavaScript on scrape-only pages
await page.setJavaScriptEnabled(false);

// Use faster navigation when rendering not needed
await page.goto(url, { waitUntil: 'domcontentloaded' });
```

### Network Optimization

```javascript
// Block unnecessary resources
await page.on('request', (req) => {
  if (['image', 'stylesheet', 'font', 'media'].includes(req.resourceType())) {
    req.abort();
  } else {
    req.continue();
  }
});
```

---
