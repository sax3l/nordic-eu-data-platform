# Quick Start Guide: Deploy Scraping Platform in 1 Hour

## 5-Minute Local Setup

### 1. Clone & Configure

```bash
git clone <your-repo> scraping-platform
cd scraping-platform

# Copy example env
cp .env.example .env

# Edit .env with your values
nano .env
# BRIGHT_DATA_KEY=your_api_key
# POSTGRES_PASSWORD=secure_password
```

### 2. Start Local Stack

```bash
docker-compose up -d

# Wait for health
sleep 10
curl http://localhost:3000/health

# View logs
docker-compose logs -f api
docker-compose logs -f worker_1
```

### 3. Submit Test Job

```bash
curl -X POST http://localhost:3000/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "priority": 7,
    "selectors": {
      "title": "h1",
      "description": "p"
    }
  }'

# Response:
# {"job_id": "abc-123", "status": "queued"}
```

### 4. Monitor Progress

```bash
# Check queue depth
redis-cli LLEN tasks:pending:medium

# Check validation results
docker-compose logs -f validator

# View Grafana dashboard
# http://localhost:3001 (admin/admin)
```

### 5. Stop

```bash
docker-compose down -v
```

---

## 30-Minute Production Deployment

### Prerequisites

- Kubernetes cluster (AKS/EKS/GKE)
- kubectl configured
- Docker registry (ACR/ECR)
- AWS S3 or Azure Blob access

### 1. Build & Push Images

```bash
# Build worker image
docker build -t scraping-registry.azurecr.io/worker:v1.0.0 \
  -f services/worker/Dockerfile \
  services/worker/

# Build validator image
docker build -t scraping-registry.azurecr.io/validator:v1.0.0 \
  -f services/validator/Dockerfile \
  services/validator/

# Build API image
docker build -t scraping-registry.azurecr.io/api:v1.0.0 \
  -f services/api/Dockerfile \
  services/api/

# Push to registry
docker push scraping-registry.azurecr.io/worker:v1.0.0
docker push scraping-registry.azurecr.io/validator:v1.0.0
docker push scraping-registry.azurecr.io/api:v1.0.0
```

### 2. Set Environment Secrets

```bash
kubectl create namespace scraping-prod

# Create secrets
kubectl create secret generic postgres-secret \
  --from-literal=password=YOUR_POSTGRES_PASSWORD \
  -n scraping-prod

kubectl create secret generic api-secrets \
  --from-literal=BRIGHT_DATA_KEY=YOUR_BRIGHT_DATA_KEY \
  -n scraping-prod

kubectl create secret generic worker-secrets \
  --from-literal=BRIGHT_DATA_KEY=YOUR_BRIGHT_DATA_KEY \
  -n scraping-prod
```

### 3. Deploy

```bash
# Create storage class (fast SSD)
kubectl apply -f k8s/storage-class.yaml

# Apply manifests in order
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-redis.yaml
kubectl apply -f k8s/03-postgres.yaml
kubectl apply -f k8s/04-api.yaml
kubectl apply -f k8s/05-workers.yaml
kubectl apply -f k8s/06-validator.yaml
kubectl apply -f k8s/07-ingress.yaml

# Wait for rollout
kubectl wait --for=condition=ready pod \
  -l app=scraping-api \
  -n scraping-prod \
  --timeout=300s
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n scraping-prod

# Get API service IP
kubectl get svc scraping-api -n scraping-prod

# Test health
curl http://<API_IP>/health

# Check logs
kubectl logs -l app=scraping-api -n scraping-prod --tail=50
```

### 5. Scale

```bash
# Scale workers to 30
kubectl scale statefulset scraping-worker \
  --replicas=30 \
  -n scraping-prod

# Monitor scaling
watch kubectl get pods -n scraping-prod | grep worker
```

---

## Common Patterns & Solutions

### Pattern 1: Retry Failed Jobs

**Problem:** Job failed, want to retry manually

**Solution:**
```bash
# Get failed jobs from DLQ
redis-cli LRANGE tasks:dlq 0 -1

# Re-queue specific job
redis-cli LPUSH tasks:pending:medium '{
  "job_id": "abc-123",
  "url": "https://...",
  "attempt_count": 0,
  ...
}'
```

### Pattern 2: Handle Rate Limiting

**Problem:** Target site blocking requests

**Solution:**
```python
# Automatic: circuit breaker already in place
# Manual rotation if needed:

# Rotate all proxies
redis-cli FLUSHDB  # Nuclear (also clears cache)

# Better: API endpoint
POST /admin/rotate-proxies
# Triggers proxy_pool.rotate_all()
```

### Pattern 3: Monitor Cost

**Query Costs:**
```sql
-- Cost per profile (assuming 50KB per request, $1.20/GB proxy)
SELECT 
  COUNT(*) as profiles,
  (COUNT(*) * 50 / 1024.0 / 1024.0 * 1.20) as proxy_cost_usd,
  (COUNT(*) * 50 / 1024.0 / 1024.0 * 1.20 / COUNT(*)) as cost_per_profile_usd
FROM profiles
WHERE created_at > NOW() - INTERVAL '1 day';
```

### Pattern 4: Batch Scraping

**Enqueue 1000 profiles at once:**
```python
import redis
import json
import uuid

r = redis.Redis(host='localhost', port=6379)

profiles = [
  'https://linkedin.com/in/username1',
  'https://linkedin.com/in/username2',
  # ...
]

for url in profiles:
    task = {
        'job_id': str(uuid.uuid4()),
        'url': url,
        'priority': 5,
        'attempt_count': 0
    }
    r.lpush('tasks:pending:medium', json.dumps(task))

print(f'Enqueued {len(profiles)} tasks')
```

### Pattern 5: Resume After Outage

**Lost queue data, need to resume from backup:**
```bash
# S3 has archive of all jobs
aws s3 ls s3://scraping-dlq-archive/ --recursive

# Find jobs from time window
aws s3 cp s3://scraping-dlq-archive/jobs.ndjson - | \
  jq -r 'select(.created_at > "2024-01-15T10:00:00Z")' | \
  while read job; do
    redis-cli LPUSH tasks:pending:low "$job"
  done
```

### Pattern 6: Pause Scraping

**Need to pause workers (e.g., during maintenance):**
```bash
# Set circuit breaker on all domains
redis-cli EVAL "
  local domains = redis.call('keys', 'rate_limit:*')
  for _,domain in ipairs(domains) do
    redis.call('setex', 'circuit:open:' .. domain, 3600, '1')
  end
" 0

# Or: scale workers to 0
kubectl scale statefulset scraping-worker --replicas=0 -n scraping-prod
```

### Pattern 7: Emergency Data Export

**Need to export all collected data:**
```sql
-- Export to CSV
COPY (
  SELECT 
    job_id, url, data, validated_at
  FROM profiles
  WHERE created_at > NOW() - INTERVAL '7 days'
  ORDER BY created_at DESC
) TO STDOUT WITH CSV HEADER;
```

### Pattern 8: Debug Worker Issue

**Worker pod hanging/OOM:**
```bash
# Check resource usage
kubectl top pod scraping-worker-1 -n scraping-prod

# View logs
kubectl logs scraping-worker-1 -n scraping-prod --tail=200

# Describe pod (see events)
kubectl describe pod scraping-worker-1 -n scraping-prod

# Get into pod (debug)
kubectl exec -it scraping-worker-1 -n scraping-prod -- /bin/sh

# Inside pod, check:
ps aux  # Check Chromium processes
free -h  # Memory usage
df -h   # Disk usage
```

### Pattern 9: Custom Extraction Rules

**Site has unique structure, need custom selectors:**
```python
# Add to validator.js's DataExtractor class

custom_selectors = {
    'https://custom-site.com': {
        'name': '.profile-name',
        'title': '.job-title span',
        'email': 'a[href^="mailto:"]'
    }
}

def extract(self, html, url, selectors=None):
    # Check custom rules first
    domain = urlparse(url).netloc
    selectors = custom_selectors.get(domain, selectors or {})
    
    # Continue with normal extraction
    ...
```

### Pattern 10: Webhook Notifications

**Get real-time updates when jobs complete:**
```python
# When enqueuing:
curl -X POST http://api:3000/v1/scrape \
  -d '{
    "url": "https://...",
    "webhook_url": "https://myapp.com/scraping-webhook"
  }'

# Your webhook receives:
POST /scraping-webhook
{
  "job_id": "abc-123",
  "status": "success|duplicate|failed",
  "data": { ... },
  "completed_at": "2024-01-15T10:05:00Z"
}
```

---

## Troubleshooting Checklist

| Issue | Check | Fix |
|-------|-------|-----|
| Workers OOM | `kubectl top pod` | Reduce `CONCURRENT_TABS`, increase memory limits |
| Queue backing up | `redis-cli LLEN` | Scale workers up, check logs for crashes |
| High error rate | `kubectl logs worker_*` | Check proxy rotation, domain blocking |
| DB connection errors | `psql -c 'SELECT count(*) FROM pg_stat_activity'` | Reduce connection pool, restart validator |
| Validation stuck | `redis-cli LLEN tasks:validated` | Check validator pod health, DB disk space |
| DLQ growing | `redis-cli LLEN tasks:dlq` | Investigate error types, fix parsing rules |
| High costs | `SELECT COUNT(*) ... cost breakdown` | Reduce batch size, enable dedup, use batch windows |

---

## Performance Tuning Reference

```
Bottleneck         | Symptom              | Solution
-------------------|----------------------|----------------------------------
CPU-bound          | High CPU, low memory | Reduce CONCURRENT_TABS, enable resource sharing
Memory-bound       | OOM kills, paging    | Increase pod memory, reduce browser instances
I/O bound          | Slow inserts, paging | Add DB indexes, use batch inserts, upgrade storage
Network bound      | Slow page loads      | Use faster proxy zone, reduce timeout, enable caching
Queue overload     | Queue depth > 1000   | Auto-scale workers, increase concurrency
Proxy exhaustion   | 403/429 rate         | Rotate proxies, increase pool, use residential IPs
```

---

## Cost Optimization Checklist

- [ ] Enable spot instances for workers (30-50% savings)
- [ ] Schedule low-priority jobs in batch windows (3-7 AM)
- [ ] Enable deduplication (skip re-scraping known profiles)
- [ ] Right-size resources (set accurate requests/limits)
- [ ] Archive old data to cheaper storage (Glacier)
- [ ] Use reserved capacity for baseline load (30% discount)
- [ ] Monitor proxy spend (track $/request, rotate providers)
- [ ] Clean up dead-letter queue regularly (purge > 7 days)

---

## Monitoring Dashboard URLs

| Service | URL | Default Creds |
|---------|-----|---|
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Kibana (logs) | http://localhost:5601 | - |
| Redis CLI | `redis-cli` | - |
| PostgreSQL | `psql scraping_db -U scraper` | - |

---

## Emergency Contacts / Runbooks

**System down (all workers failing):**
1. Check K8s cluster health: `kubectl get nodes`
2. Check Redis: `redis-cli ping`
3. Check Postgres: `psql -c 'SELECT 1'`
4. View events: `kubectl get events -n scraping-prod`
5. Rollback latest deployment: `kubectl rollout undo deployment/scraping-api`

**Memory leak (workers growing):**
1. Check browser processes: `kubectl exec <pod> -- ps aux | grep chromium`
2. Review logs for memory spike: `kubectl logs <pod> | grep -i memory`
3. Restart pod: `kubectl delete pod <pod>`
4. Check code for page leaks: `await page.close()`

**Database corruption:**
1. Create backup: `pg_dump scraping_db > backup.sql`
2. Stop writes: `kubectl scale deployment validator --replicas=0`
3. Run VACUUM: `psql -c 'VACUUM ANALYZE'`
4. Resume: `kubectl scale deployment validator --replicas=5`

---

## Next Steps

1. **Week 1:** Deploy to staging, test with 1K profiles
2. **Week 2:** Load test (5K → 50K profiles/day)
3. **Week 3:** Cost optimization, enable spot instances
4. **Week 4:** Production launch, monitor metrics
5. **Month 2:** Add new data sources, expand geographic coverage
6. **Month 3:** Implement ML-based data extraction, improve accuracy

---

## Resources

- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Puppeteer API](https://pptr.dev/)
- [Prometheus Queries](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Redis CLI Reference](https://redis.io/commands/)
- [PostgreSQL Tuning](https://www.postgresql.org/docs/current/runtime-config.html)
- [Bright Data Docs](https://docs.brightdata.com/)

---
