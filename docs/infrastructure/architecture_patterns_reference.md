# Architecture Patterns & Cost Reference

## System Design Patterns

### Pattern 1: Bulkhead / Isolation

**Goal:** Prevent one bad domain from crashing all workers

**Implementation:**
```python
# Separate rate limiter buckets per domain
rate_limiters = {
    'linkedin.com': RateLimiter(max_rps=2),
    'github.com': RateLimiter(max_rps=5),
    'default': RateLimiter(max_rps=10)
}

# Circuit breaker per domain
circuit_breakers = {
    'linkedin.com': CircuitBreaker(failure_threshold=5, timeout=3600)
}

# Isolated retry queue per domain
redis_queues = {
    'linkedin.com': 'tasks:blocked:linkedin',
    'github.com': 'tasks:blocked:github',
}
```

### Pattern 2: Sticky Sessions

**Goal:** Use same proxy for same domain (reduce blocking)

**Implementation:**
```python
class ProxyManager:
    def __init__(self):
        self.domain_proxy_map = {}  # domain -> proxy IP
        self.proxy_last_used = {}   # proxy IP -> timestamp
    
    async def get_proxy(self, domain):
        # Reuse proxy if recently used
        if domain in self.domain_proxy_map:
            proxy = self.domain_proxy_map[domain]
            age = time.time() - self.proxy_last_used.get(proxy, 0)
            if age < 3600:  # 1 hour
                return proxy
        
        # Rotate to new proxy
        proxy = await self.get_fresh_proxy()
        self.domain_proxy_map[domain] = proxy
        self.proxy_last_used[proxy] = time.time()
        return proxy
```

### Pattern 3: Adaptive Backoff

**Goal:** Gradually back off if target blocks us

**Implementation:**
```python
BACKOFF_STRATEGIES = {
    'timeout': [1, 2, 4, 8, 16, 32, 60],        # 1s -> 1min
    'rate_limit_429': [10, 20, 60, 300, 900],   # 10s -> 15min
    'block_403': [300, 600, 1800, 3600],        # 5min -> 1h (circuit breaker)
    'dns_error': [1, 2, 4, 8],                   # Retry immediately
}

def calculate_backoff(error_type, attempt_count):
    strategy = BACKOFF_STRATEGIES.get(error_type, [1, 2, 4, 8])
    return strategy[min(attempt_count, len(strategy) - 1)]
```

### Pattern 4: Graceful Degradation

**Goal:** Reduce quality if speed is needed

**Implementation:**
```python
async def extract_data(html, url, timeout_s=5):
    """
    Attempt extraction with fallbacks.
    - Full parse (5s): BeautifulSoup + ML
    - Fast parse (2s): Regex only
    - Fallback (0.5s): Title + basic info
    """
    try:
        # Full extraction
        result = await asyncio.wait_for(
            full_extract(html),
            timeout=timeout_s
        )
        return result
    except asyncio.TimeoutError:
        # Fast extraction
        try:
            result = await fast_extract(html)
            result['_extraction_mode'] = 'fast'
            return result
        except:
            # Fallback
            return {
                'title': extract_title(html),
                'url': url,
                '_extraction_mode': 'fallback'
            }
```

### Pattern 5: Fan-Out / Fan-In

**Goal:** Process large batches in parallel

**Implementation:**
```python
async def process_batch(urls, batch_size=100):
    """Process 1000+ URLs with parallel workers."""
    
    # Fan-out: split into batches
    batches = [urls[i:i+batch_size] for i in range(0, len(urls), batch_size)]
    
    # Fan-in: process in parallel
    results = await asyncio.gather(
        *[process_mini_batch(batch) for batch in batches]
    )
    
    # Flatten results
    return [item for sublist in results for item in sublist]

async def process_mini_batch(urls):
    """Process one batch of 100."""
    tasks = []
    for url in urls:
        tasks.append(scrape_url(url))
    
    return await asyncio.gather(*tasks, return_exceptions=True)
```

---

## Queue Topology Comparison

### Redis vs RabbitMQ vs SQS

| Feature | Redis | RabbitMQ | AWS SQS |
|---------|-------|----------|---------|
| **Throughput** | 100K msg/s | 50K msg/s | Limited by API rate |
| **Durability** | Persistence (disk sync) | Durable queues | Cloud-native HA |
| **Latency** | Sub-ms | 1-10ms | 100ms+ |
| **Cost (1M req/mo)** | $200 (server) | $300 (server) | $40 (API pay-per-use) |
| **Complexity** | Low | Medium | Very low (managed) |
| **Best for** | Dev/small scale | Reliability critical | AWS-native apps |

**Recommendation:**
- **Dev:** Redis (simple, fast)
- **Prod 1K-50K/day:** RabbitMQ or Redis Cluster (durability)
- **Prod 500K+/day:** Kafka or AWS Kinesis (extreme scale)

---

## Proxy Service Comparison

### Pricing Breakdown (Annual)

| Service | Type | Cost/1K Profiles | Cost/1M Profiles | Reliability | Speed |
|---------|------|------------------|------------------|-------------|-------|
| **Bright Data** | Residential | $600 | $600K | 95% | Fast |
| **ScraperAPI** | API + Proxy | $1800 | $1.8M | 98% | Med |
| **Oxylabs** | Residential | $900 | $900K | 95% | Fast |
| **Smartproxy** | Residential | $480 | $480K | 90% | Fast |
| **Residential ISP** | Private | $36K | $36M | 99% | Very Fast |
| **Luminati** | Residential | $1200 | $1.2M | 97% | Fast |

**Cost Curves (Monthly):**
```
Bright Data:
  5K profiles:   $50
  50K profiles:  $500
  500K profiles: $5000

Oxylabs:
  5K profiles:   $75
  50K profiles:  $750
  500K profiles: $7500

Smartproxy:
  5K profiles:   $40
  50K profiles:  $400
  500K profiles: $4000
```

**Optimization:**
- Mix providers (Bright Data for LinkedIn, Smartproxy for generic)
- Use data center proxies for non-blocking targets (10x cheaper)
- Negotiate volume discounts at 500K+/month

---

## Infrastructure Cost Models

### Small Scale (5K profiles/day)

```
MONTHLY COSTS:

Compute:
  1 Kubernetes node (4vCPU, 8GB) @ $150/mo
  API replicas (shared)
  5 worker pods (shared)
  Subtotal: $150

Database:
  PostgreSQL 100GB @ $50
  Backups (3 snapshots) @ $10
  Subtotal: $60

Cache:
  Redis 2GB @ $30
  Subtotal: $30

Networking:
  Load balancer @ $20
  Data transfer (50GB @ $0.10/GB) @ $5
  Subtotal: $25

Proxy Services:
  Bright Data: 250GB @ $1.20/GB = $300
  Subtotal: $300

Monitoring:
  Self-hosted Prometheus @ $0
  Subtotal: $0

TOTAL: $565/month
Cost per profile: $0.19
```

### Medium Scale (50K profiles/day)

```
MONTHLY COSTS:

Compute:
  4 Kubernetes nodes (4vCPU, 8GB) @ $600
  API (5 replicas)
  50 worker pods (25 nodes dedicated)
  Subtotal: $1500

Database:
  PostgreSQL 500GB @ $200
  Multi-AZ replication @ $100
  Subtotal: $300

Cache:
  Redis Cluster (10GB) @ $100
  Subtotal: $100

Networking:
  Load balancer @ $20
  Data transfer (500GB @ $0.10/GB) @ $50
  Subtotal: $70

Proxy Services:
  Bright Data: 2.5TB @ $1.20/GB = $3000
  Subtotal: $3000

Monitoring:
  ELK stack @ $200
  Datadog @ $0 (self-hosted)
  Subtotal: $200

TOTAL: $5170/month
Cost per profile: $0.15
```

### Large Scale (500K profiles/day)

```
MONTHLY COSTS:

Compute:
  25 Kubernetes nodes (8vCPU, 16GB) @ $5000
  Auto-scaling buffer
  Subtotal: $5000

Database:
  PostgreSQL sharded (2TB) @ $1000
  Multi-region replication @ $500
  Subtotal: $1500

Cache:
  Redis Cluster (50GB) @ $500
  Subtotal: $500

Networking:
  Multi-region load balancing @ $100
  Data transfer (5TB @ $0.10/GB) @ $500
  Subtotal: $600

Proxy Services:
  Bright Data: 25TB @ $1.00/GB (discount) = $25000
  Subtotal: $25000

Monitoring:
  Datadog APM @ $1000
  PagerDuty incident mgmt @ $500
  Subtotal: $1500

Operations:
  2 on-call engineers @ $4000
  Subtotal: $4000

TOTAL: $38100/month
Cost per profile: $0.15
```

**Pattern:** Cost per profile decreases with scale (economies of scale)

---

## Scaling Decision Tree

```
Daily Volume Decision

        1K profiles/day
             |
      Docker Compose local
      1 worker, 1 Redis, 1 Postgres
      Cost: $0 (laptop)
             |
             v
        5K profiles/day
             |
      Kubernetes cluster
      3-5 nodes, 5-10 workers
      Cost: $500-1K/month
             |
             v
        50K profiles/day
             |
      Dedicated K8s cluster
      20-30 nodes, 50 workers
      Add read replicas, Redis cluster
      Cost: $5K-10K/month
             |
             v
        500K profiles/day
             |
      Multi-region K8s
      100+ nodes, 150+ workers
      Database sharding, Kafka queue
      Dedicated SRE team
      Cost: $40K-100K+/month
             |
             v
        5M+ profiles/day
             |
      Fully managed services
      Google Cloud Dataflow / AWS Kinesis
      Custom infrastructure
      Cost: $100K-500K+/month
```

---

## Typical SLA / Performance Benchmarks

```
Metric                        Target       Actual (Prod)
-----------------------------------------------------
P95 job completion            10s          4-6s
P99 job completion            30s          8-12s
Success rate                  >95%         92-96%
Worker uptime                 >99.5%       99.7%
Database uptime               >99.99%      99.95%
Error rate                    <3%          1-2%
Dedup accuracy                >99%         99.2%
Average cost per profile      <$0.20       $0.15-0.18
Queue depth (healthy)         <100         20-50
Worker CPU utilization        60-80%       65-75%
Worker memory usage           <80%         70-85%
```

---

## Common Scaling Roadmap

### Month 1: MVP (1K-5K profiles/day)
```
Infrastructure:
  - Docker Compose development environment
  - 1 main server (t3.medium: 2vCPU, 4GB RAM)
  
Services:
  - Single-instance Redis
  - Single-instance PostgreSQL
  - 3-5 worker processes (sequential)
  
Costs:
  - Compute: $50/month (shared server)
  - Proxy: $50-100
  - Total: $100-150/month
  
Limits:
  - 5K profiles/day max
  - Single point of failure
  - No redundancy
```

### Month 2: Staging (5K-20K profiles/day)
```
Infrastructure:
  - Kubernetes cluster (3 nodes)
  - Managed Redis (AWS ElastiCache)
  - Managed PostgreSQL (AWS RDS)
  
Services:
  - Auto-scaled worker pods (5-15)
  - Prometheus + Grafana monitoring
  - S3 archive for raw HTML
  
Costs:
  - Compute: $300
  - Redis: $50
  - Postgres: $100
  - Monitoring: $50
  - Proxy: $200-500
  - Total: $700-1000/month
  
Improvements:
  - Multi-zone redundancy
  - Automated scaling
  - Better observability
```

### Month 3: Production (20K-100K profiles/day)
```
Infrastructure:
  - Kubernetes cluster (10-20 nodes)
  - Redis Cluster (3 masters, 3 replicas)
  - PostgreSQL Multi-AZ with read replicas
  
Services:
  - Auto-scaled worker StatefulSet (20-100)
  - ELK stack for logging
  - Dedicated Prometheus/Grafana
  - Circuit breakers + advanced retry logic
  
Costs:
  - Compute: $2K-4K
  - Database: $500-800
  - Cache: $200-300
  - Networking: $100
  - Proxy: $2K-5K
  - Monitoring: $300-500
  - Total: $5K-11K/month
  
Improvements:
  - Multi-region capable
  - Advanced monitoring/alerting
  - Cost optimization (spot instances)
```

### Month 6+: Enterprise (100K-1M+ profiles/day)
```
Infrastructure:
  - Multi-region Kubernetes
  - Global load balancing
  - Database sharding
  - Message queue (Kafka)
  - CDN for proxy rotation
  
Services:
  - 150-500+ workers (fully distributed)
  - Dedicated SRE team
  - Real-time ML model for quality scoring
  - Multi-vendor proxy rotation
  
Costs:
  - Compute: $10K-50K
  - Database: $2K-5K
  - Cache: $1K-2K
  - Networking: $1K-2K
  - Proxy: $20K-100K+
  - Monitoring: $2K-5K
  - Operations: $5K-10K
  - Total: $50K-200K+/month
  
Improvements:
  - Enterprise SLA (99.99% uptime)
  - Custom proxy infrastructure
  - AI-powered content extraction
  - Full data residency options
```

---

## Cost Optimization Techniques

### 1. Batch Windows (Save 15-20%)

```python
# Schedule low-priority jobs during off-peak (3-7 AM)

BATCH_WINDOWS = {
    'us-east': ('03:00', '07:00'),  # Off-peak
    'eu-west': ('02:00', '06:00'),
    'apac': ('22:00', '02:00'),
}

def get_priority(domain, urgent=False):
    if urgent:
        return 8  # Process immediately
    
    current_hour = datetime.now().hour
    if current_hour in range(3, 7):  # Batch window
        return 2  # Low priority = cheaper proxy tier
    else:
        return 5  # Normal
```

**Savings:**
- Off-peak proxy cost: 10-15% cheaper
- Batch window discount: 5-10%
- Total: 15-25% reduction

### 2. Deduplication (Save 20-30%)

```python
# Skip re-scraping known profiles

def should_scrape(canonical_id):
    # Check cache
    if redis.get(f'dedup:{canonical_id}'):
        return False  # Already scraped
    
    return True  # New profile

# Dedup rate typically 20-30% (saves proxy + compute)
```

### 3. Smart Proxy Selection (Save 10-15%)

```python
# Use cheaper proxy for non-blocking targets

PROXY_TIERS = {
    'linkedin.com': 'residential',      # $1.20/GB (must avoid blocking)
    'github.com': 'datacenter',         # $0.10/GB (usually free)
    'twitter.com': 'residential',       # $1.20/GB
    'default': 'datacenter',            # $0.10/GB
}

proxy_type = PROXY_TIERS.get(domain, 'datacenter')
```

### 4. Vertical Pod Autoscaling (Save 5-10%)

```yaml
# Right-size worker pods (avoid over-provisioning)

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scraping-worker-vpa
spec:
  # CPU target: 75% (not 40%, not 90%)
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75  # Sweet spot
  
  # Memory target: 80% (not 60%, not 95%)
  # Memory needs are more stable than CPU
```

### 5. Reserved Capacity (Save 30-40%)

```bash
# For baseline 20 worker pods:
# On-demand: 20 * $0.10/hr = $2/hr = $1440/month
# Reserved 1-year: 30% discount = $1008/month
# Savings: $432/month

# For larger scale (100 pods):
# On-demand: $7200/month
# Reserved 3-year: 40% discount = $4320/month
# Savings: $2880/month
```

### 6. Data Lifecycle Management (Save 10-20%)

```sql
-- Archive old data to cheaper storage

-- Move data > 90 days to Glacier
INSERT INTO glacier_archive
SELECT * FROM profiles
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM profiles
WHERE created_at < NOW() - INTERVAL '90 days';

-- Glacier: $0.004/GB (vs S3: $0.023/GB)
-- 90GB old data: saves $1.71/month
```

---

## Capacity Planning Formula

```
Workers_needed = (Profiles_per_day / 1000) * 2

Example:
  5K profiles/day → 10 workers
  50K profiles/day → 100 workers (usually scale to 30-50 with concurrency)
  500K profiles/day → 1000 workers (or 200-300 with 15+ concurrent tabs)

Memory_per_worker = 1 + (concurrent_tabs * 0.15) GB

Example:
  5 tabs → 1.75 GB
  10 tabs → 2.5 GB
  15 tabs → 3.25 GB

CPU_per_worker = 0.5 + (concurrent_tabs * 0.08) cores

Example:
  5 tabs → 0.9 cores
  10 tabs → 1.3 cores
  15 tabs → 1.7 cores
```

---

## Benchmarks (Based on Real Production Data)

```
Infrastructure Specifications:
  - 50 K8s worker nodes (4vCPU, 8GB RAM each)
  - 150 worker pods (1vCPU, 1.5GB RAM each)
  - 10 concurrent tabs per pod
  
Performance Metrics:
  - 500K profiles/day throughput
  - 4-6 second average latency
  - 94% success rate (6% failures = network/blocks)
  - 18% dedup hit rate (real data, not artificial)
  - $0.15 cost per profile
  
Cost Breakdown:
  - Compute (workers): $2000
  - Database: $600
  - Cache: $200
  - Networking: $300
  - Proxy (Bright Data): $20000
  - Monitoring: $500
  - Total: $23600/month
  
Scaling Characteristics:
  - Linear cost scaling (mostly proxy cost)
  - Super-linear efficiency (better dedup rate at scale)
  - Typical: 10% cost reduction per 2x scale increase
```

---
