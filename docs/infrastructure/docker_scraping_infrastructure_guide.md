# Production-Grade Docker Infrastructure for Web Scraping Platform

**Target: 1000+ profiles/day, 5K-500K+ profiles/day scalable**  
**Scope: Dev → Staging → Prod with geographic distribution**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Docker Compose (Development)](#docker-compose-development)
4. [Kubernetes Manifests (Production)](#kubernetes-manifests-production)
5. [Worker Pool Architecture](#worker-pool-architecture)
6. [Queue System Design](#queue-system-design)
7. [Proxy Integration](#proxy-integration)
8. [Monitoring & Observability](#monitoring--observability)
9. [Scaling Strategy](#scaling-strategy)
10. [Cost Breakdown](#cost-breakdown)
11. [Implementation Timeline](#implementation-timeline)
12. [Troubleshooting & Failure Recovery](#troubleshooting--failure-recovery)

---

## Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
│  (Target Sites, Proxy Services, Rate Limiting)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    INGRESS / API GATEWAY                        │
│  (Kong / Nginx / CloudFlare / ALB)                              │
│  - TLS/SSL termination                                          │
│  - Request rate limiting (global)                               │
│  - Request routing to task submission service                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  TASK SUBMISSION SERVICE                        │
│  (Node.js / Python API)                                         │
│  - Validate input payloads                                      │
│  - Enrich task metadata (priority, geo, domain)                │
│  - Publish to queue                                             │
│  - Return job_id + webhook URL                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼────────┐              ┌────────────▼──────┐
│   TASK QUEUE   │              │  TASK QUEUE DLQ   │
│  (Redis/       │              │  (Dead Letter)    │
│   RabbitMQ)    │              │                   │
│                │              │  - Failed tasks   │
│ - Priority     │              │  - Manual retry   │
│ - Persistence  │              │  - Analysis       │
│ - TTL          │              │                   │
└───────┬────────┘              └───────────────────┘
        │
        │ (Fan-out to N workers)
        │
    ┌───┴──────────────────────────────────────────────┐
    │                                                   │
┌───▼──────────────┬──────────┬────────────┬─────────┐ │
│ WORKER POD 1     │ WORKER 2 │ WORKER 3  │ WORKER N│ │
│ ┌──────────────┐ │          │           │        │ │
│ │ Chromium     │ │          │           │        │ │
│ │ Puppeteer/   │ │          │           │        │ │
│ │ Playwright   │ │          │           │        │ │
│ │              │ │          │           │        │ │
│ │ Rate Limiter │ │          │           │        │ │
│ │ Proxy Mgr    │ │          │           │        │ │
│ │ Backoff Logic│ │          │           │        │ │
│ └──────────────┘ │          │           │        │ │
└───┬──────────────┴──────────┴────────────┴─────────┘ │
    │  (Parallel scraping with per-domain              │
    │   rate limits, proxy rotation)                   │
    └───────────────────────────┬─────────────────────┘
                                │
    ┌───────────────────────────┴────────────────────┐
    │                                                │
┌───▼──────────────────┐        ┌──────────────────┐│
│ VALIDATION SERVICE   │        │ DEDUPLICATION    ││
│ - HTML parsing       │        │ - Bloom filter   ││
│ - Data extraction    │        │ - Redis set      ││
│ - Schema validation  │        │ - Checksums      ││
│ - Quality scoring    │        │ - Full-text idx  ││
└───┬──────────────────┘        └──────────────────┘│
    │                                                │
    └────────────────────────┬─────────────────────┘
                             │
                ┌────────────┴───────────┐
                │                        │
        ┌───────▼────────┐      ┌───────▼────────┐
        │   DATABASE     │      │   OBJECT STORE │
        │   (PostgreSQL/ │      │   (S3/Azure    │
        │    MongoDB)    │      │    Blob)       │
        │                │      │                │
        │ - Canonical    │      │ - Raw HTML     │
        │ - Deduplicated │      │ - Screenshots  │
        │ - Enriched     │      │ - Archives     │
        └────────────────┘      └────────────────┘
                │                        │
                └────────────┬───────────┘
                             │
        ┌────────────────────▼──────────────────┐
        │  CACHE LAYER (Redis)                  │
        │  - Extracted profile cache (TTL)      │
        │  - Dedup bloom filter                 │
        │  - Session state                      │
        │  - Rate limit counters                │
        └────────────────────┬──────────────────┘
                             │
        ┌────────────────────▼──────────────────┐
        │  QUERY/ANALYTICS API                  │
        │  - Profile lookup                     │
        │  - Async job status                   │
        │  - Metrics & reporting                │
        └──────────────────────────────────────┘
```

### Key Characteristics

- **Fully decoupled**: Task submission → Queue → Workers → Validation → Storage
- **Horizontally scalable**: Add/remove workers without code changes
- **Fault-tolerant**: Dead-letter queues, exponential backoff, circuit breakers
- **Rate-limited**: Per-domain, per-proxy, global adaptive throttling
- **Geo-aware**: Regional worker pools, proxy affinity, CDN proxies
- **Observable**: Prometheus metrics, structured logging, distributed tracing
- **Cost-efficient**: Spot instances, batch windows, rightsized containers

---

## Component Design

### 1. **Task Submission Service**

Purpose: Accept scraping requests, validate, and enqueue.

**API Endpoints:**
```
POST /v1/scrape           → Submit single profile
POST /v1/scrape/batch     → Submit bulk list
POST /v1/jobs/:id         → Get job status
GET  /v1/jobs/:id/result  → Fetch extracted data
```

**Input Validation:**
- Domain whitelist (prevent infinite loops)
- Payload size limits (< 10KB metadata)
- Required fields: `url`, `selector_rules` (or `ml_model`)
- Optional: `priority` (0-10), `geo` (region), `webhook_url`

**Output:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_completion": "2024-01-15T10:05:00Z",
  "webhook_url": "https://...",
  "queue_position": 12
}
```

### 2. **Task Queue (Redis or RabbitMQ)**

**Redis-based (simpler, fine for < 10K jobs/day):**
```
Key structure:
  tasks:pending:{priority}:{domain}  → [job_id, ...]
  tasks:{job_id}                     → {payload, created_at, attempts}
  tasks:dlq                          → failed jobs
  rate_limit:{domain}:{window}       → counter
  dedup:bloom                        → bloom filter (optional)
```

**RabbitMQ-based (more resilient, > 50K jobs/day):**
```
Exchanges:
  scraping.tasks     (topic)
Queues:
  scraping.high    (priority 8-10, TTL 4h)
  scraping.medium  (priority 5-7, TTL 6h)
  scraping.low     (priority 1-4, TTL 8h)
  scraping.dlq     (dead letter, TTL 7d)
Routing keys:
  scraping.*.linkedin
  scraping.*.github
  scraping.*.techcrunch
```

**Task Payload:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://www.linkedin.com/in/username",
  "selectors": {
    "name": "h1.text-heading-xlarge",
    "title": "div.text-body-small span",
    "experience": "li.base-card"
  },
  "priority": 7,
  "geo_hint": "US",
  "proxy_type": "residential",
  "attempt_count": 0,
  "max_retries": 3,
  "backoff_ms": 0,
  "created_at": "2024-01-15T10:00:00Z",
  "timeout_s": 30,
  "webhook_url": "https://api.example.com/webhook"
}
```

### 3. **Worker Architecture**

**Per-Worker Concurrency:** 5-15 parallel tabs (browser contexts)

**Pseudo-code:**
```python
class ScrapingWorker:
    def __init__(self):
        self.browser = None
        self.rate_limiter = DomainRateLimiter()
        self.proxy_pool = ProxyPool(service='bright_data')
        self.queue = RedisQueue()
        self.metrics = PrometheusMetrics()
        
    async def work_loop(self):
        async with aiohttp.ClientSession() as session:
            while True:
                # Pop task from queue (with timeout backoff)
                task = await self.queue.pop_task(
                    timeout=30,
                    batch_keys=[
                        'tasks:pending:high:*',
                        'tasks:pending:medium:*',
                        'tasks:pending:low:*'
                    ]
                )
                
                if not task:
                    await asyncio.sleep(5)  # Queue empty
                    continue
                
                try:
                    # Rate limit per domain
                    await self.rate_limiter.wait(task['url'])
                    
                    # Acquire proxy
                    proxy = await self.proxy_pool.get_proxy(
                        fallback_to_direct=False,
                        geo_hint=task.get('geo_hint')
                    )
                    
                    # Execute scrape with timeout
                    result = await self.scrape_with_timeout(
                        task['url'],
                        task['selectors'],
                        proxy=proxy,
                        timeout=task['timeout_s']
                    )
                    
                    # Return proxy (marks as available)
                    await self.proxy_pool.return_proxy(proxy)
                    
                    # Emit metrics
                    self.metrics.increment('scrape.success')
                    self.metrics.histogram('scrape.duration_ms', 
                        elapsed_ms)
                    
                    # Push to validation queue
                    await self.queue.push_validated(
                        job_id=task['job_id'],
                        raw_html=result['html'],
                        screenshot=result['screenshot'],
                        metadata=result['metadata']
                    )
                    
                except RateLimitError as e:
                    # Exponential backoff + re-queue
                    await self.requeue_with_backoff(task, e)
                    
                except ProxyRotationError as e:
                    # Try next proxy in pool
                    await self.proxy_pool.mark_bad(proxy)
                    await self.requeue_with_backoff(task, e)
                    
                except TargetBlockedError as e:
                    # Circuit breaker + deadletter
                    self.circuit_breaker.mark_open(task['url'])
                    await self.queue.push_dlq(task, 'target_blocked')
                    
                except Exception as e:
                    # Generic error + retry
                    task['attempt_count'] += 1
                    if task['attempt_count'] < task['max_retries']:
                        await self.requeue_with_backoff(task, e)
                    else:
                        await self.queue.push_dlq(task, 'max_retries')
```

### 4. **Validation Service**

Parallel extraction, deduplication, schema validation.

```python
class ValidationService:
    def __init__(self):
        self.extractor = DataExtractor()  # BeautifulSoup / lxml
        self.dedup = DedupEngine(redis_client)
        self.validator = SchemaValidator()
        self.db = PostgreSQL()
        
    async def process_batch(self, raw_results: List[Dict]):
        """Process scraped data in parallel."""
        
        tasks = []
        for result in raw_results:
            task = asyncio.create_task(
                self._validate_single(result)
            )
            tasks.append(task)
        
        validated = await asyncio.gather(*tasks)
        
        # Bulk insert into DB
        await self.db.insert_batch(validated)
        
        return validated
        
    async def _validate_single(self, result: Dict) -> Dict:
        job_id = result['job_id']
        
        # Extract structured data
        extracted = self.extractor.extract(
            html=result['html'],
            selectors=result.get('selectors', {}),
            fallback_ml=True
        )
        
        # Check dedup (bloom filter fast path)
        canonical_id = self._canonical_id(extracted)
        if await self.dedup.exists(canonical_id):
            self.metrics.increment('dedup.hit')
            return {
                'job_id': job_id,
                'status': 'duplicate',
                'canonical_id': canonical_id
            }
        
        # Schema validation
        validation = self.validator.validate(
            extracted,
            schema_name=result.get('schema')
        )
        
        if not validation.valid:
            return {
                'job_id': job_id,
                'status': 'validation_error',
                'errors': validation.errors
            }
        
        # Archive raw HTML + screenshot
        await self._archive_raw(job_id, result)
        
        # Record dedup
        await self.dedup.add(canonical_id)
        
        self.metrics.increment('validation.success')
        
        return {
            'job_id': job_id,
            'status': 'success',
            'data': extracted,
            'canonical_id': canonical_id,
            'validated_at': datetime.now().isoformat()
        }
        
    async def _archive_raw(self, job_id: str, result: Dict):
        """Store raw HTML and screenshot in S3/Azure Blob."""
        s3 = boto3.client('s3')
        
        # Raw HTML
        s3.put_object(
            Bucket='scraping-raw-archive',
            Key=f'html/{job_id}.html',
            Body=result['html'].encode(),
            ContentType='text/html',
            ServerSideEncryption='AES256'
        )
        
        # Screenshot
        if result.get('screenshot'):
            s3.put_object(
                Bucket='scraping-raw-archive',
                Key=f'screenshots/{job_id}.png',
                Body=result['screenshot'],
                ContentType='image/png'
            )
```

---

## Docker Compose (Development)

**File: `docker-compose.yml`**

```yaml
version: '3.9'

services:
  # ===== TASK SUBMISSION API =====
  api:
    build:
      context: ./services/api
      dockerfile: Dockerfile
    container_name: scraping_api
    environment:
      NODE_ENV: development
      REDIS_URL: redis://redis:6379
      LOG_LEVEL: debug
      WORKERS_POOL_SIZE: 3
    ports:
      - "3000:3000"
    depends_on:
      - redis
    volumes:
      - ./services/api:/app
      - /app/node_modules
    networks:
      - scraping_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ===== REDIS (Queue + Cache) =====
  redis:
    image: redis:7-alpine
    container_name: scraping_redis
    command:
      - redis-server
      - --appendonly
      - "yes"
      - --maxmemory
      - "2gb"
      - --maxmemory-policy
      - "allkeys-lru"
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - scraping_net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ===== SCRAPING WORKERS (N=3 for dev) =====
  worker_1:
    build:
      context: ./services/worker
      dockerfile: Dockerfile
    container_name: scraping_worker_1
    environment:
      WORKER_ID: worker_1
      REDIS_URL: redis://redis:6379
      PROXY_SERVICE: bright_data
      PROXY_API_KEY: ${BRIGHT_DATA_KEY}
      PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: "false"
      LOG_LEVEL: info
      CONCURRENT_TABS: 5
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./services/worker:/app
      - /app/node_modules
    networks:
      - scraping_net
    restart: on-failure

  worker_2:
    extends:
      service: worker_1
    container_name: scraping_worker_2
    environment:
      WORKER_ID: worker_2
      REDIS_URL: redis://redis:6379
      PROXY_SERVICE: bright_data
      PROXY_API_KEY: ${BRIGHT_DATA_KEY}
      LOG_LEVEL: info

  worker_3:
    extends:
      service: worker_1
    container_name: scraping_worker_3
    environment:
      WORKER_ID: worker_3
      REDIS_URL: redis://redis:6379
      PROXY_SERVICE: bright_data
      PROXY_API_KEY: ${BRIGHT_DATA_KEY}
      LOG_LEVEL: info

  # ===== VALIDATION SERVICE =====
  validator:
    build:
      context: ./services/validator
      dockerfile: Dockerfile
    container_name: scraping_validator
    environment:
      REDIS_URL: redis://redis:6379
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: scraping_db
      DB_USER: scraper
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      S3_BUCKET: scraping-raw
      LOG_LEVEL: info
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./services/validator:/app
      - /app/node_modules
    networks:
      - scraping_net
    restart: on-failure

  # ===== POSTGRESQL =====
  postgres:
    image: postgres:15-alpine
    container_name: scraping_postgres
    environment:
      POSTGRES_DB: scraping_db
      POSTGRES_USER: scraper
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/01-init.sql
    networks:
      - scraping_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scraper -d scraping_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===== MONITORING =====
  prometheus:
    image: prom/prometheus:latest
    container_name: scraping_prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
    ports:
      - "9090:9090"
    networks:
      - scraping_net

  grafana:
    image: grafana/grafana:latest
    container_name: scraping_grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - ./monitoring/grafana-dashboards.json:/etc/grafana/provisioning/dashboards/scraping.json
      - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/prometheus.yml
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - scraping_net

  # ===== LOGGING (optional: ELK) =====
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    container_name: scraping_elasticsearch
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - scraping_net

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    container_name: scraping_logstash
    volumes:
      - ./monitoring/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      LS_JAVA_OPTS: "-Xmx256m -Xms256m"
    depends_on:
      - elasticsearch
    networks:
      - scraping_net

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    container_name: scraping_kibana
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - scraping_net

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  scraping_net:
    driver: bridge
```

**Environment File: `.env.example`**

```bash
# Proxy Service
BRIGHT_DATA_KEY=your_key_here
BRIGHT_DATA_API_URL=https://api.brightdata.com

# Database
POSTGRES_PASSWORD=secure_password_123
DB_HOST=postgres
DB_PORT=5432
DB_NAME=scraping_db

# Monitoring
GRAFANA_PASSWORD=admin_password_123

# Worker Config
CONCURRENT_TABS=5
WORKER_TIMEOUT_S=30
BATCH_SIZE=100

# Rate Limiting
DOMAIN_RATE_LIMIT_RPS=2
GLOBAL_RATE_LIMIT_RPS=100

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

**Run:**
```bash
cp .env.example .env
docker-compose up -d

# View logs
docker-compose logs -f worker_1
docker-compose logs -f validator

# Stop
docker-compose down -v
```

---

## Kubernetes Manifests (Production)

### Namespace & RBAC

**File: `k8s/01-namespace.yaml`**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: scraping-prod
  labels:
    environment: production
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: scraping-worker
  namespace: scraping-prod
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: scraping-worker-role
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: scraping-worker-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: scraping-worker-role
subjects:
  - kind: ServiceAccount
    name: scraping-worker
    namespace: scraping-prod
```

### Redis StatefulSet

**File: `k8s/02-redis.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: scraping-prod
data:
  redis.conf: |
    maxmemory 4gb
    maxmemory-policy allkeys-lru
    appendonly yes
    appendfsync everysec
    save 900 1
    save 300 10
    save 60 10000
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: scraping-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: scraping-prod
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - name: redis
              containerPort: 6379
          resources:
            requests:
              memory: "2Gi"
              cpu: "500m"
            limits:
              memory: "4Gi"
              cpu: "2"
          volumeMounts:
            - name: redis-data
              mountPath: /data
            - name: redis-config
              mountPath: /etc/redis
          command:
            - redis-server
            - /etc/redis/redis.conf
          livenessProbe:
            exec:
              command:
                - redis-cli
                - ping
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - redis-cli
                - ping
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: redis-config
          configMap:
            name: redis-config
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: scraping-prod
spec:
  clusterIP: None
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
```

### PostgreSQL StatefulSet

**File: `k8s/03-postgres.yaml`**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: scraping-prod
type: Opaque
stringData:
  password: ${POSTGRES_PASSWORD}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init
  namespace: scraping-prod
data:
  01-init.sql: |
    CREATE DATABASE scraping_db;
    CREATE USER scraper WITH PASSWORD 'password';
    ALTER ROLE scraper SET client_encoding TO 'utf8';
    GRANT CONNECT ON DATABASE scraping_db TO scraper;
    
    \c scraping_db
    
    CREATE TABLE profiles (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      job_id UUID NOT NULL UNIQUE,
      url VARCHAR(2048) NOT NULL,
      canonical_id VARCHAR(256),
      data JSONB NOT NULL,
      raw_html TEXT,
      screenshot_url VARCHAR(2048),
      validation_status VARCHAR(50) NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_job_id (job_id),
      INDEX idx_canonical_id (canonical_id),
      INDEX idx_created_at (created_at)
    );
    
    CREATE TABLE scrape_events (
      id BIGSERIAL PRIMARY KEY,
      job_id UUID NOT NULL,
      event_type VARCHAR(50),
      event_data JSONB,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_job_id (job_id),
      INDEX idx_created_at (created_at)
    );
    
    GRANT ALL PRIVILEGES ON DATABASE scraping_db TO scraper;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scraper;
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: scraping-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: scraping-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: scraping_db
            - name: POSTGRES_USER
              value: scraper
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "4Gi"
              cpu: "2"
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
            - name: postgres-init
              mountPath: /docker-entrypoint-initdb.d
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U scraper -d scraping_db
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U scraper -d scraping_db
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: postgres-init
          configMap:
            name: postgres-init
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: scraping-prod
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

### API Service Deployment

**File: `k8s/04-api.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: scraping-prod
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  LOG_FORMAT: "json"
  WORKERS_POOL_SIZE: "50"
---
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: scraping-prod
type: Opaque
stringData:
  REDIS_URL: redis://redis:6379
  DB_HOST: postgres
  DB_PORT: "5432"
  DB_NAME: scraping_db
  DB_USER: scraper
  DB_PASSWORD: ${POSTGRES_PASSWORD}
  BRIGHT_DATA_KEY: ${BRIGHT_DATA_KEY}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraping-api
  namespace: scraping-prod
  labels:
    app: scraping-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: scraping-api
  template:
    metadata:
      labels:
        app: scraping-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - scraping-api
                topologyKey: kubernetes.io/hostname
      containers:
        - name: api
          image: scraping-registry.azurecr.io/api:v1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 3000
          envFrom:
            - configMapRef:
                name: api-config
            - secretRef:
                name: api-secrets
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsNonRoot: true
            runAsUser: 1000
---
apiVersion: v1
kind: Service
metadata:
  name: scraping-api
  namespace: scraping-prod
  labels:
    app: scraping-api
spec:
  type: LoadBalancer
  selector:
    app: scraping-api
  ports:
    - port: 80
      targetPort: 3000
      name: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scraping-api-hpa
  namespace: scraping-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: scraping-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
```

### Worker StatefulSet (Critical)

**File: `k8s/05-workers.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: worker-config
  namespace: scraping-prod
data:
  CONCURRENT_TABS: "10"
  PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: "false"
  WORKER_TIMEOUT_S: "30"
  DOMAIN_RATE_LIMIT_RPS: "2"
  LOG_LEVEL: "info"
---
apiVersion: v1
kind: Secret
metadata:
  name: worker-secrets
  namespace: scraping-prod
type: Opaque
stringData:
  REDIS_URL: redis://redis:6379
  PROXY_SERVICE: bright_data
  PROXY_API_KEY: ${BRIGHT_DATA_KEY}
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: scraping-worker
  namespace: scraping-prod
spec:
  serviceName: scraping-worker
  replicas: 10  # Start with 10, scale to 50+ dynamically
  podManagementPolicy: Parallel  # Don't wait for 1 before 2
  selector:
    matchLabels:
      app: scraping-worker
  template:
    metadata:
      labels:
        app: scraping-worker
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: scraping-worker
      terminationGracePeriodSeconds: 30
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - scraping-worker
                topologyKey: kubernetes.io/hostname
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: workload
                    operator: In
                    values:
                      - scraping
                      - general
      
      containers:
        - name: worker
          image: scraping-registry.azurecr.io/worker:v1.0.0
          imagePullPolicy: IfNotPresent
          
          envFrom:
            - configMapRef:
                name: worker-config
            - secretRef:
                name: worker-secrets
          
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
              ephemeral-storage: "2Gi"
            limits:
              memory: "2Gi"
              cpu: "1"
              ephemeral-storage: "5Gi"
          
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - curl -f http://localhost:9090/metrics || exit 1
            initialDelaySeconds: 30
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          
          readinessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - test -f /tmp/worker_ready
            initialDelaySeconds: 10
            periodSeconds: 5
          
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            runAsUser: 1000
            capabilities:
              drop:
                - ALL
          
          volumeMounts:
            - name: ephemeral
              mountPath: /tmp
            - name: chromium-cache
              mountPath: /home/scraper/.cache
      
      volumes:
        - name: ephemeral
          emptyDir: {}
        - name: chromium-cache
          emptyDir: {}
      
      initContainers:
        - name: download-chromium
          image: scraping-registry.azurecr.io/worker:v1.0.0
          command: ["/bin/sh", "-c", "npx playwright install chromium"]
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1"
          volumeMounts:
            - name: chromium-cache
              mountPath: /home/scraper/.cache
---
apiVersion: v1
kind: Service
metadata:
  name: scraping-worker
  namespace: scraping-prod
spec:
  clusterIP: None
  selector:
    app: scraping-worker
  ports:
    - port: 9090
      name: metrics
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scraping-worker-hpa
  namespace: scraping-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: scraping-worker
  minReplicas: 10
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: queue_depth
        target:
          type: AverageValue
          averageValue: "30"  # Scale if avg queue > 30 per pod
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
        - type: Pods
          value: 5
          periodSeconds: 30
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
```

### Validation Deployment

**File: `k8s/06-validator.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: validator-config
  namespace: scraping-prod
data:
  BATCH_SIZE: "100"
  DEDUP_ENABLED: "true"
  LOG_LEVEL: "info"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraping-validator
  namespace: scraping-prod
spec:
  replicas: 5
  selector:
    matchLabels:
      app: scraping-validator
  template:
    metadata:
      labels:
        app: scraping-validator
    spec:
      containers:
        - name: validator
          image: scraping-registry.azurecr.io/validator:v1.0.0
          envFrom:
            - configMapRef:
                name: validator-config
            - secretRef:
                name: validator-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1"
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - curl -f http://localhost:9090/metrics || exit 1
            initialDelaySeconds: 20
            periodSeconds: 10
```

### Ingress (API Gateway)

**File: `k8s/07-ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: scraping-network-policy
  namespace: scraping-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 3000
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443  # External APIs
        - protocol: TCP
          port: 6379  # Redis
        - protocol: TCP
          port: 5432  # Postgres
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: scraping-ingress
  namespace: scraping-prod
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.scraping.example.com
      secretName: scraping-tls-cert
  rules:
    - host: api.scraping.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: scraping-api
                port:
                  number: 80
```

**Deploy:**
```bash
kubectl apply -f k8s/
kubectl rollout status statefulset/scraping-worker -n scraping-prod
```

---

## Worker Pool Architecture

### Scaling Strategy

| Profiles/Day | Workers | Concurrent Tabs | Queue Depth | Infra Cost |
|---|---|---|---|---|
| 1K | 2 | 5 | < 10 | $200 |
| 5K | 10 | 10 | 20-50 | $800 |
| 50K | 50 | 15 | 100-200 | $4K |
| 500K | 150 | 15 | 500-1K | $12K |
| 5M | 500+ | 20 | 2K-5K | $40K+ |

### Per-Worker Metrics

```
Worker Pod:
  - Memory: 1-2 Gi (Chromium is heavy)
  - CPU: 500m-1000m nominal, bursts to 1-2
  - Disk: 2Gi working + 3Gi Chromium cache
  - Network: 1-10 Mbps per concurrent tab
  
Concurrency sweet spot:
  - 5-10 tabs: reliably stays < 1.5 Gi
  - 15 tabs: 1.8-2 Gi (push limits)
  - 20+ tabs: needs 2.5+ Gi per worker

Job Throughput:
  - 1 tab: ~2-5 profiles/min (depends on site)
  - 10 tabs: ~20-50 profiles/min
  - "Perfect" worker = 100 profiles/day = 0.07 profiles/min
    → means 10 workers can handle 700 profiles/day
    → 100 workers = 70K profiles/day
```

### Failure Recovery

**Worker Crash / Out of Memory:**
1. K8s detects failed probe → kills pod
2. StatefulSet automatically respawns
3. Redis queue retains job (TTL 6h)
4. Job re-queued with `attempt_count++`
5. Circuit breaker prevents retry storm

**Stuck Worker (Unresponsive Tabs):**
```python
class WatchdogTimer:
    async def monitor_tabs(self):
        for tab in self.tabs:
            if tab.age_ms > TIMEOUT_MS:
                await tab.close()
                self.metrics.increment('tab.timeout')
                # Tab auto-restarted in next cycle
```

**Queue Overflow:**
1. Publish rate limits kick in (429 Busy)
2. Client backs off exponentially
3. Cache layer absorbs read-heavy queries
4. Dead-letter queue captures failed jobs for analysis

---

## Queue System Design

### Task Lifecycle

```
SUBMITTED
   ↓
QUEUED (pending:medium:domain.com)
   ├─ Delay: 0-60s (backoff if failed)
   │
PROCESSING (being scraped by worker)
   ├─ Timeout: 30s
   ├─ Retries: 0-3
   │
EXTRACTED
   ↓
VALIDATING (dedup + schema check)
   ├─ Dedup cache hit → DUPLICATE
   │  (still archived, not inserted)
   │
VALIDATED (ready for DB insert)
   ↓
STORED
   │
   └─ Webhook → Client
        ↓
    COMPLETE
```

### Priority Levels

```
Level | TTL   | Use Case
------|-------|------------------------------------------
10    | 2h    | Ad-hoc high-priority: C-suite, deal flow
7-8   | 4h    | Sales automation: prospect batch lists
5-6   | 6h    | Regular refresh: daily list updates
1-4   | 8h    | Backfill / historical archive
DLQ   | 7d    | Failed jobs (max retries exceeded)
```

### Dead-Letter Queue (DLQ) Handling

```python
class DLQHandler:
    async def process_dlq(self):
        """Analyze and escalate failed jobs."""
        dlq_jobs = await self.redis.lrange('tasks:dlq', 0, -1)
        
        for job in dlq_jobs:
            # Classify failure
            if job['error_type'] == 'target_blocked':
                # Circuit breaker tripped
                # Notify admin, escalate proxy rotation
                self.circuit_breaker.log_block(job['url'])
            elif job['error_type'] == 'max_retries':
                # Genuinely failed (network, parsing, etc)
                # Notify webhook with failure reason
                await self.webhook_client.notify(
                    job['webhook_url'],
                    {'status': 'failed', 'reason': job['error']}
                )
            
            # Archive + cleanup
            await self.s3.put_object(
                Bucket='dlq-archive',
                Key=f"dlq/{job['job_id']}.json",
                Body=json.dumps(job)
            )
            await self.redis.lrem('tasks:dlq', 0, job)
```

---

## Proxy Integration

### Cost Models (Monthly)

| Service | Type | Cost/GB | Cost/Req | Min | 1000 req/day |
|---------|------|---------|----------|-----|--------------|
| **Bright Data** | Residential | $1.20 | $0.001-0.003 | $100 | $100-150 |
| **ScraperAPI** | Proxy + Parser | N/A | $0.003-0.01 | $50 | $100-300 |
| **Oxylabs** | Residential | $1.50 | $0.003-0.005 | $500 | $150-250 |
| **Smartproxy** | Residential | $1.10 | $0.0008-0.003 | $5 | $80-150 |
| **Residential ISP** | Private ISP | N/A | $0.05+ | $5K | $1500+ |

**Recommendation for 1K-100K profiles/day:** Bright Data (reliable, fast rotation, data center + residential mix)

### Proxy Manager Architecture

```python
class ProxyManager:
    def __init__(self):
        self.service = BrightDataClient(api_key=os.getenv('BRIGHT_DATA_KEY'))
        self.pool = asyncio.Queue(maxsize=200)
        self.bad_proxies = set()
        self.domain_proxy_map = {}  # Sticky sessions per domain
        
    async def initialize(self):
        """Pre-load proxy pool on startup."""
        proxies = await self.service.get_zone_ips(zone_id='2468K6-2')
        for proxy in proxies:
            await self.pool.put(proxy)
    
    async def get_proxy(self, domain: str, geo_hint: str = None) -> str:
        """
        Return a working proxy, with domain stickiness.
        
        Strategy:
        1. Check sticky session cache (same domain = same proxy)
        2. Fall back to random from pool
        3. If depleted, request fresh from Bright Data
        """
        if domain in self.domain_proxy_map:
            proxy = self.domain_proxy_map[domain]
            if proxy not in self.bad_proxies:
                return proxy
        
        # Rotate
        if self.pool.empty():
            proxies = await self.service.get_zone_ips(
                zone_id='2468K6-2',
                count=50,
                state='active'
            )
            for p in proxies:
                await self.pool.put(p)
        
        proxy = await asyncio.wait_for(self.pool.get(), timeout=5.0)
        
        # Sticky session
        self.domain_proxy_map[domain] = proxy
        
        return proxy
    
    async def mark_bad(self, proxy: str, domain: str = None):
        """Mark proxy as bad, remove from sticky map."""
        self.bad_proxies.add(proxy)
        if domain and self.domain_proxy_map.get(domain) == proxy:
            del self.domain_proxy_map[domain]
        
        # Rotate bad proxy back to Bright Data
        await self.service.mark_bad(proxy)
    
    async def rotate_all(self):
        """Force complete pool rotation (after block detection)."""
        self.domain_proxy_map.clear()
        self.bad_proxies.clear()
        
        # Drain + refill
        while not self.pool.empty():
            try:
                self.pool.get_nowait()
            except:
                pass
        
        proxies = await self.service.get_zone_ips(zone_id='2468K6-2', count=100)
        for p in proxies:
            await self.pool.put(p)
```

### Rate Limiting + Exponential Backoff

```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    async def wait(self, domain: str, max_rps: float = 2.0):
        """
        Token bucket rate limiter.
        
        Rules:
        - linkedin.com: max 2 RPS (aggressive)
        - github.com: max 5 RPS
        - Other: max 10 RPS
        """
        domain_rps = self._get_domain_limit(domain)
        bucket_key = f'rate_limit:bucket:{domain}'
        last_key = f'rate_limit:last:{domain}'
        
        now = time.time()
        
        # Get bucket state
        bucket = float(await self.redis.get(bucket_key) or domain_rps)
        last = float(await self.redis.get(last_key) or now)
        
        # Refill tokens
        elapsed = now - last
        refill = elapsed * domain_rps
        bucket = min(domain_rps, bucket + refill)
        
        if bucket >= 1.0:
            # Consume token
            bucket -= 1.0
            await self.redis.setex(bucket_key, 60, bucket)
            await self.redis.setex(last_key, 60, now)
            return  # Proceed
        
        # Wait
        wait_time = (1.0 - bucket) / domain_rps
        await asyncio.sleep(wait_time)
        
        # Recursive call (will succeed this time)
        return await self.wait(domain, max_rps)
    
    def _get_domain_limit(self, domain: str) -> float:
        """Return RPS limit for domain."""
        limits = {
            'linkedin.com': 2.0,
            'github.com': 5.0,
            'twitter.com': 3.0,
            'crunchbase.com': 1.0,
        }
        return limits.get(domain, 10.0)

class ExponentialBackoff:
    """Retry with backoff: 1s, 2s, 4s, 8s, ..., max 60s"""
    
    @staticmethod
    def calculate_backoff(attempt: int, base: float = 1.0) -> float:
        backoff = base * (2 ** attempt)
        return min(backoff, 60.0)
```

---

## Monitoring & Observability

### Prometheus Metrics

**File: `monitoring/prometheus.yml`**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'scraping-prod'
    environment: 'production'

scrape_configs:
  - job_name: 'scraping-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - scraping-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: scraping-api
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: "true"

  - job_name: 'scraping-worker'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - scraping-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: scraping-worker

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Grafana Dashboards

**Key Dashboards:**

1. **System Health**
   - Redis memory usage (goal: < 80%)
   - Postgres connections (goal: < 80)
   - API response time (p50, p95, p99)
   - Worker pod count vs. target

2. **Scraping Metrics**
   - Jobs queued (rate + depth)
   - Jobs completed (rate)
   - Success rate (%)
   - Avg extraction latency (ms)
   - Dedup hit rate (%)

3. **Worker Performance**
   - CPU per pod (goal: 60-80%)
   - Memory per pod (goal: 70-90%)
   - Chromium crash count
   - Proxy rotation rate
   - Tab timeout rate

4. **Cost Tracking**
   - Proxy spend ($ per day)
   - Compute hours (instance-hours)
   - Storage cost
   - Data transfer

### Structured Logging (JSON)

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:05:30.123Z",
  "service": "worker-1",
  "level": "info",
  "event": "scrape_success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://linkedin.com/in/username",
  "duration_ms": 4200,
  "proxy": "1.2.3.4:8080",
  "extracted_fields": 12,
  "canonical_id": "hash_xyz",
  "trace_id": "a1b2c3d4"
}
```

**Log Aggregation (ELK):**
```
Logstash → Elasticsearch → Kibana (index rotation: daily)
Retention: 30 days
Queries: job_id lookup, error analysis, performance trends
```

---

## Scaling Strategy

### Horizontal Scaling (Workers)

**Phase 1: 1K-5K profiles/day**
- 2-5 workers, shared Redis/Postgres
- Cost: $300-500/month
- Single region (US-East)

**Phase 2: 5K-50K profiles/day**
- 20-50 workers, auto-scaling on queue depth
- Dedicated Redis StatefulSet, Postgres with read replicas
- Cost: $3K-8K/month
- Multi-region (US, EU optionally)

**Phase 3: 50K-500K profiles/day**
- 100-150 workers, multiple StatefulSets per region
- Redis cluster (3 nodes, replication)
- Postgres with sharding (by domain/geo)
- Cost: $15K-40K/month
- Multi-region (US, EU, APAC)

**Phase 4: 500K+ profiles/day**
- 200-500 workers, fully distributed
- Kafka instead of Redis (durability at scale)
- Postgres sharding + multi-region failover
- Cost: $50K+/month
- Global infrastructure (edge scraping)

### Autoscaling Configuration

```yaml
# HPA for workers (based on queue depth)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scraping-worker-hpa
spec:
  scaleTargetRef:
    kind: StatefulSet
    name: scraping-worker
  minReplicas: 10
  maxReplicas: 100
  metrics:
    # Scale if queue depth > 30 per pod
    - type: Pods
      pods:
        metric:
          name: redis_queue_depth
        target:
          type: AverageValue
          averageValue: "30"
    # Scale if CPU > 75%
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100  # Double if needed
          periodSeconds: 30
        - type: Pods
          value: 5    # Add 5 pods if queue is huge
          periodSeconds: 30
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50   # Scale down by 50%
          periodSeconds: 120
```

**Custom Metric (queue depth):**
```python
# Exposed by worker on /metrics
queue_depth = redis.llen('tasks:pending:high') + \
              redis.llen('tasks:pending:medium') + \
              redis.llen('tasks:pending:low')

# Prometheus scrapes this, HPA reacts
```

---

## Cost Breakdown

### 5K Profiles/Day Scenario

```
INFRASTRUCTURE (Monthly)
  Kubernetes Cluster (AKS/EKS managed)
    - 10 worker nodes (4vCPU, 8GB RAM)          $500-800
    - Master node (managed, no extra cost)
  
  API Servers (3 pods, 250m CPU, 256MB mem)     $50
  Workers (15 pods, 1vCPU, 1GB mem)              $400
  Database (Postgres, 100GB)                     $200
  Redis (4GB, HA 2 replicas)                     $150
  
  Load Balancer + Ingress                        $20
  Data Transfer (5TB/month @ $0.05/GB)           $250
  Object Storage (100GB S3 archive)              $2.30
  
  SUBTOTAL (COMPUTE)                            $1,472

PROXY COSTS
  Bright Data: 5K profiles × 50KB = 250GB
  @ $1.20/GB                                     $300

MONITORING & LOGGING
  Prometheus + Grafana (self-hosted)             $50
  ELK Stack (Elasticsearch 50GB)                 $100
  
TOTAL/MONTH                                      $1,922
COST PER PROFILE                                 $0.38
```

### 50K Profiles/Day Scenario

```
INFRASTRUCTURE
  Kubernetes Cluster
    - 30 worker nodes (4vCPU, 8GB RAM)           $2,400
    
  API Servers (5 pods, scaled for load)          $150
  Workers (50 pods, 1vCPU, 1GB mem)              $1,800
  Database (Postgres, HA 2 replicas, 500GB)     $800
  Redis Cluster (10GB, 3 masters + replicas)    $500
  
  Load Balancer + Ingress + NAT                  $80
  Data Transfer (50TB/month @ $0.05/GB)          $2,500
  Object Storage (500GB)                         $11
  
  SUBTOTAL (COMPUTE)                             $8,241

PROXY COSTS
  50K profiles × 50KB = 2,500GB
  @ $1.20/GB                                     $3,000

MONITORING
  CloudWatch or ELK (managed)                    $300
  
TOTAL/MONTH                                      $11,541
COST PER PROFILE                                 $0.23
```

### 500K Profiles/Day Scenario

```
INFRASTRUCTURE
  Kubernetes Cluster
    - 100 worker nodes (8vCPU, 16GB RAM)         $12,000
    
  API Servers (10 pods, auto-scaled)             $300
  Workers (150 pods, 1vCPU, 2GB mem)             $6,000
  Database (Postgres sharded, 2TB total)         $4,000
  Redis Cluster (50GB, HA)                       $1,500
  
  Load Balancer + Multi-region                   $200
  Data Transfer (500TB/month)                    $25,000
  Object Storage (5TB)                           $115
  
  SUBTOTAL (COMPUTE)                             $49,115

PROXY COSTS
  500K profiles × 50KB = 25,000GB
  @ $1.00/GB (volume discount)                   $25,000

MONITORING + SRE
  Managed observability                          $1,000
  On-call rotation (2 engineers)                 $5,000
  
TOTAL/MONTH                                      $80,115
COST PER PROFILE                                 $0.16
```

### Cost Optimization Tactics

1. **Spot Instances** (30-50% discount on compute)
   ```yaml
   # Spot worker nodes for non-critical tasks
   nodeSelector:
     capacity-type: spot
   tolerations:
     - key: aws.amazon.com/ec2spot
       operator: Equal
       value: "true"
   ```

2. **Batch Processing Windows**
   - 3-7 AM off-peak: free tier proxy rotation
   - Schedule low-priority jobs (level 1-4) during batch windows
   - Save 10-15% on proxy costs

3. **Resource Rightsizing**
   - Monitor actual CPU/memory usage
   - Adjust requests/limits quarterly
   - Auto-downscale idle workers after 5 min no jobs

4. **Reserved Capacity**
   - Commit to 1-3 year plans for core infrastructure
   - 30-40% discount vs. on-demand

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Set up Docker Compose locally
- [ ] Build API + Worker Docker images
- [ ] Test with 1K mock profiles
- [ ] Create Postgres schema + indexes

### Week 2: Queue & Proxy
- [ ] Integrate Redis queue + task lifecycle
- [ ] Implement Bright Data proxy rotation
- [ ] Build rate limiter + circuit breaker
- [ ] Add retry logic with exponential backoff

### Week 3: Validation & Storage
- [ ] Build validation service (BeautifulSoup extraction)
- [ ] Implement deduplication (Bloom filter)
- [ ] S3 archival for raw HTML/screenshots
- [ ] Test end-to-end on 5K profiles

### Week 4: Monitoring
- [ ] Deploy Prometheus + Grafana
- [ ] Create dashboards (queue depth, latency, errors)
- [ ] Set up Elasticsearch logging
- [ ] Add Slack alerts for critical metrics

### Week 5: Kubernetes
- [ ] Create K8s manifests (namespace, RBAC, secrets)
- [ ] Deploy to staging cluster
- [ ] Test scaling: 5 → 50 workers
- [ ] Load test: 1K job bursts

### Week 6: Production Hardening
- [ ] Security: pod security policies, network policies
- [ ] Disaster recovery: backup strategy, failover tests
- [ ] Cost optimization: spot instances, autoscaling tuning
- [ ] Documentation + runbooks

### Week 7: Soft Launch
- [ ] Canary deployment (10% traffic)
- [ ] Monitor error rates, latencies
- [ ] Scale up to 20% traffic
- [ ] Full production launch

---

## Troubleshooting & Failure Recovery

### Common Issues

#### 1. Workers OOM Killed
**Symptom:** Pods restart repeatedly, CrashLoopBackOff

**Root Cause:** Chromium + too many concurrent tabs

**Fix:**
```bash
# Check actual memory usage
kubectl top pods -n scraping-prod

# Reduce concurrency
kubectl set env statefulset/scraping-worker \
  CONCURRENT_TABS=8 -n scraping-prod

# Increase pod limits
kubectl patch statefulset scraping-worker \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"worker","resources":{"limits":{"memory":"2.5Gi"}}}]}}}}' \
  -n scraping-prod
```

#### 2. Queue Backup (Tasks Piling Up)
**Symptom:** Queue depth > 1000, jobs waiting > 30 min

**Root Cause:** Proxy rotation failures, target block, worker stalls

**Fix:**
```bash
# Check worker health
kubectl get pods -n scraping-prod | grep worker

# Check proxy errors
kubectl logs deployment/scraping-worker -n scraping-prod --tail=100 | grep proxy_error

# Scale up workers
kubectl scale statefulset scraping-worker --replicas=50 -n scraping-prod

# Rotate all proxies
redis-cli -h redis FLUSHDB  # Nuclear option (clear cache + queue!)
                              # Better: API endpoint to trigger rotation
```

#### 3. Database Connection Exhaustion
**Symptom:** "too many connections" errors in validator logs

**Root Cause:** Validator pods not closing connections

**Fix:**
```python
# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://...',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Test connection before use
    pool_recycle=3600     # Recycle stale connections
)
```

#### 4. Redis Memory Pressure
**Symptom:** Evictions logged, `maxmemory-policy allkeys-lru` evicting recent data

**Root Cause:** Queue not draining, TTL set too long

**Fix:**
```bash
# Check memory usage
redis-cli INFO memory

# Reduce TTL for old tasks
redis-cli EVAL "
  local keys = redis.call('keys', 'tasks:*')
  for _,key in ipairs(keys) do
    local ttl = redis.call('ttl', key)
    if ttl > 7200 then  -- > 2 hours
      redis.call('expire', key, 3600)  -- 1 hour
    end
  end
" 0

# Scale Redis cluster
kubectl patch statefulset redis --replicas=3 -n scraping-prod
```

#### 5. Target Site Blocking
**Symptom:** HTTP 403/429 responses spike

**Root Cause:** Rate limit exceeded, detected as bot

**Fix:**
```python
class CircuitBreaker:
    async def check_block(self, domain: str):
        """If 10% of requests fail in 5min window, trip circuit."""
        key = f'circuit:fail:{domain}'
        fails = await redis.incr(key)
        await redis.expire(key, 300)
        
        if fails > 10:  # 10 failures in 5 min
            await redis.setex(f'circuit:open:{domain}', 3600, '1')
            # Prevent new jobs for this domain for 1 hour
            # Alert: escalate to manual retry
            await notify_admin(f'{domain} circuit open')

class RateLimiter:
    async def wait(self, domain: str):
        # Check if circuit is open
        if await redis.get(f'circuit:open:{domain}'):
            raise CircuitBreakerOpenError()
        
        # Normal rate limiting...
```

#### 6. Worker Stuck in Infinite Loop
**Symptom:** Worker pod running but no progress, metrics flat

**Root Cause:** Chromium hung, network timeout, browser crash

**Fix:**
```python
async def work_with_timeout():
    try:
        await asyncio.wait_for(self.scrape(), timeout=30)
    except asyncio.TimeoutError:
        # Kill tab + restart
        await tab.close()
        self.metrics.increment('tab.timeout')
        # Re-queue task
        await self.queue.push_task(task)

# Liveness probe catches hung workers
livenessProbe:
  exec:
    command:
      - /bin/sh
      - -c
      - test $(redis-cli get worker_last_heartbeat) > $(date +%s - 60)
  failureThreshold: 3
```

---

## Code Example: Minimal Docker Compose Setup

### `docker-compose.minimal.yml`

```yaml
version: '3.9'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build:
      context: ./worker
      dockerfile: Dockerfile
    environment:
      REDIS_URL: redis://redis:6379
      CONCURRENT_TABS: 5
    depends_on:
      - redis
    restart: on-failure

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      REDIS_URL: redis://redis:6379
    depends_on:
      - redis
```

### `worker/Dockerfile`

```dockerfile
FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache chromium

COPY package.json package-lock.json ./
RUN npm install --production

COPY . .

ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

CMD ["node", "worker.js"]
```

### `worker/worker.js`

```javascript
const redis = require('redis');
const puppeteer = require('puppeteer');

const client = redis.createClient({
  url: process.env.REDIS_URL
});

async function work() {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const concurrentTabs = parseInt(process.env.CONCURRENT_TABS) || 5;
    const tasks = [];

    for (let i = 0; i < concurrentTabs; i++) {
      tasks.push(processJobs(browser, client));
    }

    await Promise.all(tasks);
  } catch (err) {
    console.error('Worker error:', err);
  } finally {
    if (browser) await browser.close();
  }
}

async function processJobs(browser, client) {
  while (true) {
    try {
      // Pop task from queue
      const task = await client.blpop(
        ['tasks:pending:high', 'tasks:pending:medium', 'tasks:pending:low'],
        30
      );

      if (!task) {
        await new Promise(r => setTimeout(r, 1000));
        continue;
      }

      const [, taskJson] = task;
      const taskData = JSON.parse(taskJson);

      const page = await browser.newPage();
      try {
        await page.goto(taskData.url, { waitUntil: 'networkidle2', timeout: 30000 });

        const html = await page.content();
        const screenshot = await page.screenshot({ encoding: 'base64' });

        // Push to validation queue
        await client.lpush(
          'tasks:validated',
          JSON.stringify({
            job_id: taskData.job_id,
            html,
            screenshot,
          })
        );

        console.log(`✓ Job ${taskData.job_id} scraped`);
      } catch (err) {
        console.error(`✗ Job ${taskData.job_id} failed:`, err.message);
        
        // Retry with backoff
        if (taskData.attempt_count < 3) {
          taskData.attempt_count++;
          await new Promise(r => setTimeout(r, 1000 * Math.pow(2, taskData.attempt_count)));
          await client.lpush('tasks:pending:low', JSON.stringify(taskData));
        } else {
          await client.lpush('tasks:dlq', JSON.stringify(taskData));
        }
      } finally {
        await page.close();
      }
    } catch (err) {
      console.error('Processing error:', err);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
}

work().catch(console.error);
```

### `api/app.js`

```javascript
const express = require('express');
const { v4: uuidv4 } = require('uuid');
const redis = require('redis');

const app = express();
const client = redis.createClient({ url: process.env.REDIS_URL });

app.use(express.json());

app.post('/v1/scrape', async (req, res) => {
  const { url, selectors, priority = 5, webhook_url } = req.body;

  if (!url) return res.status(400).json({ error: 'url required' });

  const job_id = uuidv4();
  const task = {
    job_id,
    url,
    selectors,
    priority,
    webhook_url,
    attempt_count: 0,
    max_retries: 3,
    created_at: new Date().toISOString(),
  };

  const queue_key = `tasks:pending:${priority >= 7 ? 'high' : priority >= 5 ? 'medium' : 'low'}`;
  await client.lpush(queue_key, JSON.stringify(task));

  res.json({
    job_id,
    status: 'queued',
  });
});

app.get('/v1/jobs/:id', async (req, res) => {
  const result = await client.get(`job:result:${req.params.id}`);
  res.json(result ? JSON.parse(result) : { status: 'processing' });
});

app.listen(3000, () => console.log('API listening on port 3000'));
```

**Run:**
```bash
docker-compose -f docker-compose.minimal.yml up
curl -X POST http://localhost:3000/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","priority":7}'
```

---

## Summary

This architecture scales from development (3-5 containers) to production (100+ workers) with:

✅ **Fully decoupled** task pipeline  
✅ **Horizontal scaling** on queue depth  
✅ **Fault tolerance** with DLQ + retries  
✅ **Rate limiting** per domain + exponential backoff  
✅ **Proxy rotation** integrated with cost tracking  
✅ **Observability** (Prometheus, Grafana, ELK)  
✅ **Cost tracking** down to $/profile  
✅ **Production hardening** (RBAC, network policies, health checks)  

**Next Steps:**
1. Build + test Docker images locally
2. Deploy to K8s staging
3. Load test: 1K → 5K → 50K profiles
4. Cost optimize via spot instances + batch windows
5. Monitor + iterate on scaling thresholds
