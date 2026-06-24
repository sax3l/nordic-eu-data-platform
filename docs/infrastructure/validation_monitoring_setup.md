# Validation Service + Monitoring Complete Setup

## Validation Service Implementation

**File: `services/validator/validator.js`**

```javascript
const redis = require('redis');
const { Pool } = require('pg');
const aws = require('aws-sdk');
const pino = require('pino');
const { Registry, Counter, Histogram, Gauge } = require('prom-client');
const express = require('express');
const crypto = require('crypto');
const cheerio = require('cheerio');

// ===== LOGGING =====
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  base: { service: 'validator' },
});

// ===== METRICS =====
const register = new Registry();

const validationCounter = new Counter({
  name: 'validation_total',
  help: 'Total validations attempted',
  labelNames: ['status'],
  registers: [register],
});

const validationDuration = new Histogram({
  name: 'validation_duration_seconds',
  help: 'Validation duration',
  buckets: [0.1, 0.5, 1, 5, 10],
  registers: [register],
});

const dedupHitRate = new Gauge({
  name: 'dedup_hit_rate',
  help: 'Deduplication hit rate',
  registers: [register],
});

const batchSize = new Gauge({
  name: 'validation_batch_size',
  help: 'Current batch size',
  registers: [register],
});

// ===== CONFIGURATION =====
const CONFIG = {
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  dbHost: process.env.DB_HOST || 'localhost',
  dbPort: parseInt(process.env.DB_PORT) || 5432,
  dbName: process.env.DB_NAME || 'scraping_db',
  dbUser: process.env.DB_USER || 'scraper',
  dbPassword: process.env.DB_PASSWORD || 'password',
  batchSize: parseInt(process.env.BATCH_SIZE) || 100,
  s3Bucket: process.env.S3_BUCKET || 'scraping-raw',
  dedupEnabled: process.env.DEDUP_ENABLED !== 'false',
  metricsPort: 9091,
};

// ===== DEDUPLICATION ENGINE =====
class DedupEngine {
  constructor(redisClient) {
    this.redis = redisClient;
    this.bloomFilters = new Map();
    this.hits = 0;
    this.total = 0;
  }

  canonicalId(data) {
    /**
     * Create deterministic hash of extracted data.
     * Ignores noise (timestamps, URLs) but includes key fields.
     */
    const canonical = {
      name: (data.name || '').trim().toLowerCase(),
      title: (data.title || '').trim().toLowerCase(),
      company: (data.company || '').trim().toLowerCase(),
      email: (data.email || '').trim().toLowerCase(),
      // Add more fields as needed
    };

    const json = JSON.stringify(canonical);
    return crypto
      .createHash('sha256')
      .update(json)
      .digest('hex')
      .substring(0, 32);
  }

  async exists(canonicalId) {
    /**
     * Check if canonical_id already processed.
     * Uses Redis set for durability.
     */
    this.total++;

    const exists = await this.redis.sismember('dedup:canonical_ids', canonicalId);

    if (exists) {
      this.hits++;
      dedupHitRate.set((this.hits / this.total) * 100);
      return true;
    }

    return false;
  }

  async add(canonicalId) {
    /**
     * Record canonical_id (with TTL in case duplicate ingestion).
     */
    await this.redis.sadd('dedup:canonical_ids', canonicalId);
    await this.redis.expire('dedup:canonical_ids', 86400 * 30); // 30 days
  }
}

// ===== DATA EXTRACTOR =====
class DataExtractor {
  constructor() {
    this.cheerio = cheerio;
  }

  extract(html, selectors = {}, fallbackMl = false) {
    /**
     * Extract structured data from HTML using CSS selectors.
     * Falls back to regex/ML if selectors fail.
     */
    const $ = this.cheerio.load(html);
    const extracted = {};

    // Apply selectors
    for (const [field, selector] of Object.entries(selectors)) {
      try {
        const element = $(selector).first();
        if (element.length) {
          extracted[field] = element.text().trim();
        } else if (fallbackMl) {
          // Fallback: regex patterns
          extracted[field] = this._regexFallback(html, field);
        }
      } catch (err) {
        logger.warn(`Failed to extract ${field} with selector ${selector}: ${err.message}`);
      }
    }

    // Default extractions (always run)
    extracted.page_title = $('title').text().trim();
    extracted.meta_description = $('meta[name="description"]').attr('content') || '';
    extracted.headings = $('h1')
      .toArray()
      .map(h => $(h).text().trim())
      .slice(0, 5);
    extracted.links = $('a[href]')
      .toArray()
      .map(a => $(a).attr('href'))
      .slice(0, 10);

    return extracted;
  }

  _regexFallback(html, field) {
    /**
     * Regex patterns for common fields when selectors fail.
     */
    const patterns = {
      email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/,
      phone: /\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b/,
      linkedin: /linkedin\.com\/in\/([a-z0-9-]+)/i,
      twitter: /twitter\.com\/([a-z0-9_]+)/i,
    };

    const pattern = patterns[field];
    if (!pattern) return null;

    const match = html.match(pattern);
    return match ? match[0] : null;
  }
}

// ===== SCHEMA VALIDATOR =====
class SchemaValidator {
  constructor() {
    this.schemas = {
      linkedin_profile: {
        required: ['name', 'title'],
        optional: ['company', 'location', 'email'],
        types: {
          name: 'string',
          title: 'string',
          company: 'string',
        },
      },
      company_page: {
        required: ['company_name'],
        optional: ['industry', 'employees', 'revenue'],
        types: {
          company_name: 'string',
          industry: 'string',
        },
      },
    };
  }

  validate(data, schemaName = 'linkedin_profile') {
    const schema = this.schemas[schemaName] || this.schemas.linkedin_profile;
    const errors = [];

    // Check required fields
    for (const field of schema.required) {
      if (!data[field]) {
        errors.push(`Missing required field: ${field}`);
      }
    }

    // Type checking
    for (const [field, type] of Object.entries(schema.types || {})) {
      if (data[field] && typeof data[field] !== type) {
        errors.push(`Field ${field} should be ${type}, got ${typeof data[field]}`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

// ===== VALIDATION SERVICE =====
class ValidationService {
  constructor(config) {
    this.config = config;
    this.redis = null;
    this.pgPool = null;
    this.s3 = null;
    this.extractor = new DataExtractor();
    this.dedup = null;
    this.validator = new SchemaValidator();
  }

  async initialize() {
    // Redis
    this.redis = redis.createClient({ url: this.config.redisUrl });
    await this.redis.connect();
    logger.info('Connected to Redis');

    // PostgreSQL
    this.pgPool = new Pool({
      host: this.config.dbHost,
      port: this.config.dbPort,
      database: this.config.dbName,
      user: this.config.dbUser,
      password: this.config.dbPassword,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    this.pgPool.on('error', (err) => {
      logger.error(`PG pool error: ${err.message}`);
    });

    logger.info('PostgreSQL pool initialized');

    // S3 client
    this.s3 = new aws.S3({
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      region: process.env.AWS_REGION || 'us-east-1',
    });

    // Dedup engine
    this.dedup = new DedupEngine(this.redis);
    logger.info('Deduplication engine initialized');
  }

  async processLoop() {
    logger.info(`Starting validation loop (batch size: ${this.config.batchSize})`);

    while (true) {
      try {
        // Dequeue batch
        const batch = [];
        for (let i = 0; i < this.config.batchSize; i++) {
          const item = await this.redis.lpop('tasks:validated');
          if (!item) break;
          batch.push(JSON.parse(item));
        }

        if (batch.length === 0) {
          await new Promise(r => setTimeout(r, 5000));
          continue;
        }

        batchSize.set(batch.length);
        logger.info(`Processing batch of ${batch.length} items`);

        const startTime = Date.now();

        // Process in parallel
        const validated = await Promise.all(
          batch.map(item => this._validateSingle(item))
        );

        const elapsed = (Date.now() - startTime) / 1000;
        validationDuration.observe(elapsed);

        // Bulk insert
        const toInsert = validated.filter(v => v.status === 'success');
        if (toInsert.length > 0) {
          await this._bulkInsert(toInsert);
          logger.info(`Inserted ${toInsert.length} profiles`);
        }

        // Handle duplicates
        const duplicates = validated.filter(v => v.status === 'duplicate');
        if (duplicates.length > 0) {
          logger.info(`Found ${duplicates.length} duplicates`);
          for (const dup of duplicates) {
            await this._recordDuplicate(dup);
          }
        }

        // Handle errors
        const errors = validated.filter(v => v.status !== 'success');
        if (errors.length > 0) {
          logger.warn(`${errors.length} items failed validation`);
          for (const err of errors) {
            await this.redis.lpush(
              'tasks:validation_errors',
              JSON.stringify(err)
            );
          }
        }

        validationCounter.inc(
          { status: 'success' },
          toInsert.length
        );
        validationCounter.inc(
          { status: 'duplicate' },
          duplicates.length
        );
        validationCounter.inc(
          { status: 'error' },
          errors.length
        );

      } catch (err) {
        logger.error(`Validation loop error: ${err.message}`);
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }

  async _validateSingle(result) {
    const jobId = result.job_id;

    try {
      // Extract data
      const extracted = this.extractor.extract(
        result.html,
        {},
        true
      );

      // Canonical ID
      const canonicalId = this.dedup.canonicalId(extracted);

      // Check dedup
      if (this.config.dedupEnabled) {
        const isDuplicate = await this.dedup.exists(canonicalId);
        if (isDuplicate) {
          return {
            job_id: jobId,
            status: 'duplicate',
            canonical_id: canonicalId,
          };
        }
      }

      // Validate schema
      const validation = this.validator.validate(extracted);
      if (!validation.valid) {
        return {
          job_id: jobId,
          status: 'validation_error',
          errors: validation.errors,
        };
      }

      // Archive raw
      await this._archiveRaw(jobId, result);

      // Record dedup
      if (this.config.dedupEnabled) {
        await this.dedup.add(canonicalId);
      }

      return {
        job_id: jobId,
        status: 'success',
        data: extracted,
        canonical_id: canonicalId,
        url: result.domain,
        validated_at: new Date().toISOString(),
      };

    } catch (err) {
      logger.error(`Failed to validate ${jobId}: ${err.message}`);
      return {
        job_id: jobId,
        status: 'error',
        error: err.message,
      };
    }
  }

  async _bulkInsert(items) {
    const client = await this.pgPool.connect();

    try {
      await client.query('BEGIN');

      const stmt = await client.prepare(
        'insert_profile',
        `
        INSERT INTO profiles (job_id, url, canonical_id, data, validation_status)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (job_id) DO NOTHING
        `,
        ['uuid', 'varchar', 'varchar', 'jsonb', 'varchar']
      );

      for (const item of items) {
        await client.query(stmt, [
          item.job_id,
          item.url,
          item.canonical_id,
          JSON.stringify(item.data),
          'validated',
        ]);
      }

      await client.query('COMMIT');

    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async _archiveRaw(jobId, result) {
    const params = {
      Bucket: this.config.s3Bucket,
      Key: `raw/${jobId}/${Date.now()}.json`,
      Body: JSON.stringify({
        job_id: jobId,
        html_length: result.html.length,
        screenshot_size: result.screenshot ? result.screenshot.length : 0,
        archived_at: new Date().toISOString(),
      }),
      ContentType: 'application/json',
      ServerSideEncryption: 'AES256',
    };

    try {
      await this.s3.putObject(params).promise();
    } catch (err) {
      logger.warn(`Failed to archive raw for ${jobId}: ${err.message}`);
    }
  }

  async _recordDuplicate(dup) {
    try {
      await this.pgPool.query(
        'INSERT INTO duplicates (job_id, canonical_id) VALUES ($1, $2)',
        [dup.job_id, dup.canonical_id]
      );
    } catch (err) {
      logger.warn(`Failed to record duplicate: ${err.message}`);
    }
  }

  async shutdown() {
    logger.info('Shutting down validation service...');
    if (this.pgPool) await this.pgPool.end();
    if (this.redis) await this.redis.quit();
  }
}

// ===== MAIN =====
async function main() {
  logger.info('Starting validation service');

  const validator = new ValidationService(CONFIG);

  try {
    await validator.initialize();

    // Metrics server
    const app = express();
    app.get('/metrics', async (req, res) => {
      res.set('Content-Type', register.contentType);
      res.end(await register.metrics());
    });
    app.listen(CONFIG.metricsPort);

    // Graceful shutdown
    process.on('SIGTERM', async () => {
      logger.info('SIGTERM received');
      await validator.shutdown();
      process.exit(0);
    });

    // Start processing
    await validator.processLoop();

  } catch (err) {
    logger.error(`Fatal error: ${err.message}`);
    process.exit(1);
  }
}

main().catch(console.error);
```

---

## Prometheus Configuration

**File: `monitoring/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: scraping-prod
    environment: production

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  # API Servers
  - job_name: scraping-api
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - scraping-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: scraping-api
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: instance

  # Workers
  - job_name: scraping-worker
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - scraping-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: scraping-worker
      - source_labels: [__meta_kubernetes_statefulset_name]
        target_label: instance

  # Validator
  - job_name: scraping-validator
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - scraping-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: scraping-validator

  # Redis
  - job_name: redis
    static_configs:
      - targets: ['redis-exporter:9121']

  # PostgreSQL
  - job_name: postgres
    static_configs:
      - targets: ['postgres-exporter:9187']
```

---

## Alert Rules

**File: `monitoring/alerts.yml`**

```yaml
groups:
  - name: scraping.rules
    interval: 30s
    rules:
      # High error rate
      - alert: HighScrapeErrorRate
        expr: |
          (
            increase(scrape_total{status!="success"}[5m])
            /
            increase(scrape_total[5m])
          ) > 0.1
        for: 5m
        annotations:
          summary: "High scrape error rate (>10%)"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Queue backup
      - alert: QueueBackup
        expr: queue_depth > 1000
        for: 10m
        annotations:
          summary: "Queue backup detected"
          description: "Queue depth: {{ $value }}"

      # Worker pod restart loop
      - alert: WorkerCrashLoop
        expr: |
          increase(kube_pod_container_status_restarts_total{pod=~"scraping-worker-.*"}[1h]) > 5
        for: 5m
        annotations:
          summary: "Worker pod {{ $labels.pod }} restarting frequently"

      # Database connection exhaustion
      - alert: DBConnectionExhaustion
        expr: postgres_stat_activity_count > 80
        for: 5m
        annotations:
          summary: "PostgreSQL connection pool near limit"

      # Redis memory pressure
      - alert: RedisMemoryPressure
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.85
        for: 5m
        annotations:
          summary: "Redis memory usage >85%"

      # Validation failure
      - alert: ValidationFailed
        expr: |
          increase(validation_total{status="error"}[5m]) > 100
        for: 5m
        annotations:
          summary: "High validation failure rate"

      # Dedup false positive explosion
      - alert: DedupAnomalies
        expr: dedup_hit_rate > 50
        for: 10m
        annotations:
          summary: "Abnormally high dedup hit rate (possible data quality issue)"
```

---

## Grafana Dashboard (JSON)

**File: `monitoring/grafana-dashboard.json`**

```json
{
  "dashboard": {
    "title": "Scraping Platform",
    "panels": [
      {
        "title": "Queue Depth (Real-time)",
        "targets": [
          {
            "expr": "queue_depth"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Scrape Success Rate",
        "targets": [
          {
            "expr": "increase(scrape_total{status=\"success\"}[5m]) / increase(scrape_total[5m])"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Average Scrape Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, scrape_duration_seconds)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Worker CPU Usage",
        "targets": [
          {
            "expr": "container_cpu_usage_seconds_total{pod=~\"scraping-worker-.*\"}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Worker Memory Usage",
        "targets": [
          {
            "expr": "container_memory_usage_bytes{pod=~\"scraping-worker-.*\"}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Dedup Hit Rate",
        "targets": [
          {
            "expr": "dedup_hit_rate"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Database Connections",
        "targets": [
          {
            "expr": "postgres_stat_activity_count"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Proxy Rotation Rate",
        "targets": [
          {
            "expr": "increase(proxy_rotation_total[5m])"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

## Cost Tracking Query

**SQL: `monitoring/cost_query.sql`**

```sql
-- Monthly cost breakdown
WITH metrics AS (
  SELECT
    COUNT(*) as total_jobs,
    SUM(EXTRACT(EPOCH FROM (validated_at - created_at))) / 3600 as total_compute_hours,
    COUNT(*) FILTER (WHERE validation_status = 'success') as successful_jobs,
    COUNT(*) FILTER (WHERE validation_status = 'duplicate') as duplicate_jobs
  FROM profiles
  WHERE created_at > NOW() - INTERVAL '30 days'
)
SELECT
  total_jobs,
  total_compute_hours,
  successful_jobs,
  duplicate_jobs,
  -- Infrastructure costs
  (total_compute_hours * 0.05) as compute_cost_usd,
  
  -- Proxy costs (assume 50KB per profile)
  ((total_jobs * 50) / 1024 / 1024 * 1.20) as proxy_cost_usd,
  
  -- Storage (archive + DB)
  ((total_jobs * 100) / 1024 / 1024 / 1024 * 0.023) as storage_cost_usd,
  
  -- Total
  (total_compute_hours * 0.05) +
  ((total_jobs * 50) / 1024 / 1024 * 1.20) +
  ((total_jobs * 100) / 1024 / 1024 / 1024 * 0.023) as total_monthly_cost_usd
FROM metrics;
```

---

## Health Check Endpoints

**File: `services/shared/health.js`**

```javascript
const express = require('express');

function createHealthRouter(dependencies) {
  const router = express.Router();

  router.get('/health', async (req, res) => {
    const checks = {
      status: 'ok',
      timestamp: new Date().toISOString(),
      redis: false,
      database: false,
      queue: 0,
    };

    try {
      // Redis health
      if (dependencies.redis) {
        await dependencies.redis.ping();
        checks.redis = true;
      }

      // Database health
      if (dependencies.pgPool) {
        const result = await dependencies.pgPool.query('SELECT 1');
        checks.database = result.rowCount > 0;
      }

      // Queue depth
      if (dependencies.redis) {
        const depth = await dependencies.redis.llen('tasks:pending:high');
        checks.queue = depth;
      }

      res.json(checks);
    } catch (err) {
      res.status(503).json({
        status: 'unhealthy',
        error: err.message,
        ...checks,
      });
    }
  });

  router.get('/ready', async (req, res) => {
    // Readiness check (can accept traffic?)
    try {
      if (dependencies.redis) await dependencies.redis.ping();
      if (dependencies.pgPool) await dependencies.pgPool.query('SELECT 1');
      res.json({ ready: true });
    } catch (err) {
      res.status(503).json({ ready: false, error: err.message });
    }
  });

  return router;
}

module.exports = { createHealthRouter };
```

---

## Performance Baseline

**Typical Metrics (50K profiles/day, 50 workers):**

```
Queue Metrics:
  - Avg queue depth: 20-50 jobs
  - P95 wait time: 2-5 seconds
  - Success rate: 92-96%

Worker Metrics:
  - Avg CPU per pod: 60-75%
  - Avg memory per pod: 1.4-1.8 Gi
  - Tabs in use: 8-10 (out of 15 max)
  - Avg scrape latency: 4-6 seconds
  - Proxy rotation rate: 5-10%

Validation Metrics:
  - Batch processing rate: 100 items / 3-5 seconds
  - Dedup hit rate: 2-5%
  - DB insert latency: 10-50ms

Infrastructure:
  - Compute hours: ~1.44K/day (50 workers × 24h × 1vCPU)
  - Proxy bandwidth: ~2.5TB/day (50K × 50KB)
  - DB storage growth: ~50GB/month
  - Cost: ~$350-400/day
```

---
