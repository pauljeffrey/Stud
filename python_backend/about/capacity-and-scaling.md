# Python Backend Capacity and Scaling Guide

## Overview

This document provides comprehensive information about the capacity, performance, and scaling characteristics of the Stud Python backend service. It includes estimates for concurrent users, resource requirements, bottlenecks, optimization strategies, and scaling options.

## Table of Contents

1. [Capacity Estimates](#capacity-estimates)
2. [Resource Breakdown](#resource-breakdown)
3. [Bottlenecks and Limitations](#bottlenecks-and-limitations)
4. [Performance Scenarios](#performance-scenarios)
5. [Optimization Strategies](#optimization-strategies)
6. [Scaling Options](#scaling-options)
7. [Monitoring and Metrics](#monitoring-and-metrics)
8. [Configuration Recommendations](#configuration-recommendations)

---

## Capacity Estimates

### Standard Server Configuration (8GB RAM, 2 CPU)

**Conservative Estimate:** 50-100 concurrent active users  
**Optimized Estimate:** 100-150 concurrent active users  
**Peak Capacity:** 150-200 concurrent users (with optimizations)

### Daily Active Users

- **Realistic:** 200-500 daily active users (not all concurrent)
- **Peak Periods:** 100-150 concurrent users during busy hours
- **Average Concurrent:** 30-60 users throughout the day

---

## Resource Breakdown

### Memory Usage (8GB Total)

| Component | Memory Usage | Notes |
|-----------|--------------|-------|
| Base System | 500MB - 1GB | OS and system processes |
| Python FastAPI + Uvicorn | 200MB - 400MB | Base application |
| Python Workers | 100MB - 200MB per worker | Typically 1-4 workers |
| Database Connection Pool | 100MB - 200MB | 20-40 connections @ 5-10MB each |
| Redis Client | 50MB - 100MB | Connection pool |
| **Per Active Request** | | |
| - Light API call | 10MB - 30MB | Simple endpoints |
| - Medium (agent call) | 30MB - 60MB | AI agent operations |
| - Heavy (document processing) | 100MB - 300MB | Document upload/processing |
| Buffer/Safety Margin | 500MB - 1GB | For spikes and overhead |

**Total Available for Requests:** ~6-7GB

### CPU Usage (2 Cores)

| Operation | CPU Usage | Notes |
|-----------|-----------|-------|
| Base System | 5-10% | OS overhead |
| FastAPI Processing | 10-30% per request | Request handling |
| AI Agent Calls | Low (I/O bound) | Mostly waiting for external APIs |
| Document Processing | 80-100% (spikes) | CPU-intensive operations |
| Concurrent Handling | Limited by CPU threads | Async I/O helps significantly |

**Key Insight:** The backend is primarily **I/O-bound** (waiting for AI APIs and database), which allows many concurrent requests with async/await.

---

## Bottlenecks and Limitations

### 1. External AI API Rate Limits

**Impact:** High - Primary bottleneck for AI operations

- **OpenAI Rate Limits:** Varies by tier (free tier: ~3 RPM, paid: much higher)
- **Google Gemini Rate Limits:** Varies by model and tier
- **Latency:** 2-10 seconds per AI call
- **Effect:** Limits concurrent AI operations regardless of server capacity

**Mitigation:**
- Implement request queuing
- Use multiple API keys (if allowed)
- Cache common responses
- Implement exponential backoff for rate limits

### 2. Database Connection Pool

**Impact:** Medium - Can limit concurrent database operations

- **Default Pool Size:** 20-40 connections
- **Each Connection:** ~5-10MB memory
- **Effect:** Too many concurrent database operations can exhaust the pool

**Mitigation:**
- Increase pool size: `DB_POOL_MAX_SIZE = 50-100`
- Use connection pooling efficiently
- Implement connection timeout and retry logic
- Use read replicas for read-heavy operations

### 3. Document Processing

**Impact:** High - Memory and CPU intensive

- **Memory:** 200-500MB per large document
- **CPU:** High during processing (80-100%)
- **Effect:** Limits concurrent document uploads/processing

**Mitigation:**
- Queue heavy operations
- Process documents sequentially or in small batches
- Use streaming for large files
- Offload to serverless functions (AWS Lambda, etc.)
- Implement file size limits

### 4. Request Handling Capacity

**Impact:** Medium - Limited by workers and async efficiency

- **Uvicorn Workers:** Typically 1-4 workers
- **Async Efficiency:** Handles many concurrent requests per worker
- **Effect:** More workers = more capacity, but more memory usage

**Mitigation:**
- Optimize worker count: `workers = CPU_cores` (typically 2)
- Use async/await efficiently
- Avoid blocking operations
- Implement request timeouts

---

## Performance Scenarios

### Scenario 1: Light API Calls (Simple Endpoints)

**Examples:** Health checks, user profile retrieval, simple queries

- **Concurrent Users:** 100-200
- **Memory per Request:** 10-30MB
- **CPU per Request:** Low (5-15%)
- **Response Time:** <100ms
- **Bottleneck:** Database connection pool

**Optimization:**
- Increase database pool size
- Implement Redis caching
- Use connection pooling efficiently

### Scenario 2: Medium Usage (AI Agent Calls)

**Examples:** Chat with game master, NPC interactions, quiz generation

- **Concurrent Users:** 50-100
- **Memory per Request:** 30-60MB
- **CPU per Request:** Low (mostly I/O wait)
- **Response Time:** 2-10 seconds (waiting for AI APIs)
- **Bottleneck:** External AI API rate limits

**Optimization:**
- Implement request queuing
- Use multiple API keys
- Cache common AI responses
- Optimize prompts to reduce token usage

### Scenario 3: Heavy Usage (Document Processing)

**Examples:** Document upload, PDF processing, vector embedding generation

- **Concurrent Users:** 10-20
- **Memory per Request:** 100-300MB
- **CPU per Request:** High (80-100% spikes)
- **Response Time:** 10-60 seconds
- **Bottleneck:** Memory and CPU

**Optimization:**
- Queue heavy operations
- Process sequentially or in small batches
- Use streaming for large files
- Offload to serverless functions
- Implement file size limits

### Scenario 4: Mixed Workload (Realistic Production)

**Examples:** Combination of all above scenarios

- **Concurrent Users:** 50-100
- **Memory per Request:** Variable (20-150MB average)
- **CPU per Request:** Variable (10-50% average)
- **Response Time:** Variable (100ms - 10 seconds)
- **Bottleneck:** Multiple (AI APIs, memory, CPU)

**Optimization:**
- Implement request prioritization
- Queue heavy operations
- Use caching aggressively
- Monitor and scale based on metrics

---

## Optimization Strategies

### 1. Uvicorn Worker Configuration

**Recommended Settings:**

```python
# Run with multiple workers
uvicorn main:app \
    --workers 2 \
    --host 0.0.0.0 \
    --port 8000 \
    --timeout-keep-alive 5 \
    --timeout-graceful-shutdown 30

# Or in production with Gunicorn
gunicorn main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 60 \
    --keepalive 5
```

**Guidelines:**
- **Workers = CPU cores** (typically 2 for 2 CPU server)
- Each worker handles multiple async requests
- More workers = more memory usage but better CPU utilization
- Too many workers can cause memory issues

### 2. Database Connection Pool Optimization

**Configuration:**

```python
# In configs/config.py
DB_POOL_MIN_SIZE = 10          # Minimum pool size
DB_POOL_MAX_SIZE = 50          # Maximum pool size (increase for more users)
DB_POOL_INCREMENT = 2          # Increment size
DB_POOL_SIZE = 20             # Initial pool size
```

**Best Practices:**
- Set `DB_POOL_MAX_SIZE` based on expected concurrent users
- Use connection pooling efficiently (reuse connections)
- Implement connection timeout and retry logic
- Monitor connection pool usage
- Use read replicas for read-heavy operations

### 3. Redis Caching Strategy

**Configuration:**

```python
# In configs/config.py
REDIS_POOL_SIZE = 20                    # Initial pool size
REDIS_POOL_MAX_CONNECTIONS = 50        # Maximum connections
CHAT_MEMORY_EXPIRE_SECONDS = 86400     # 24 hours
CHAT_HISTORY_WINDOW = 200              # Keep last 200 messages
```

**Caching Opportunities:**
- User sessions and authentication tokens
- Chat history (with expiration)
- Game states (temporary)
- Quiz results (temporary)
- Frequently accessed database queries
- AI agent responses (for common queries)

### 4. Request Queuing for Heavy Operations

**Implementation:**

```python
# Queue heavy operations (document processing)
from asyncio import Queue
import asyncio

processing_queue = Queue(maxsize=10)

async def process_document_async(document_id: str):
    """Queue document processing"""
    await processing_queue.put(document_id)
    # Process sequentially to avoid memory spikes
```

**Benefits:**
- Prevents memory exhaustion
- Smooths CPU usage
- Better resource utilization
- Prevents timeouts

### 5. Async/Await Optimization

**Best Practices:**
- Use `async/await` for all I/O operations
- Avoid blocking operations in async functions
- Use `asyncio.gather()` for parallel operations
- Implement proper error handling
- Use connection pooling for databases

**Example:**

```python
# Good: Parallel operations
results = await asyncio.gather(
    fetch_user_data(user_id),
    fetch_game_state(game_id),
    fetch_chat_history(session_id)
)

# Bad: Sequential operations
user = await fetch_user_data(user_id)
game = await fetch_game_state(game_id)
chat = await fetch_chat_history(session_id)
```

### 6. Memory Management

**Strategies:**
- Implement file size limits (already done: 10MB files, 5MB images)
- Use streaming for large file uploads
- Clean up temporary files promptly
- Implement memory-efficient document processing
- Use generators for large data processing
- Monitor memory usage and implement alerts

---

## Scaling Options

### Vertical Scaling (Scale Up)

**Upgrade Server Resources:**

| Configuration | Concurrent Users | Daily Active Users | Cost Impact |
|---------------|-------------------|-------------------|-------------|
| 8GB RAM, 2 CPU | 50-100 | 200-500 | Baseline |
| 16GB RAM, 4 CPU | 120-200 | 500-1000 | ~2x |
| 32GB RAM, 8 CPU | 250-400 | 1000-2000 | ~4x |
| 64GB RAM, 16 CPU | 500-800 | 2000-5000 | ~8x |

**When to Scale Up:**
- Consistent high CPU usage (>80%)
- Memory usage consistently high (>85%)
- Database connection pool exhausted
- Response times degrading

**Limitations:**
- Diminishing returns after certain point
- Cost increases linearly
- Single point of failure

### Horizontal Scaling (Scale Out)

**Multiple Backend Instances:**

- **Load Balancer:** Distribute requests across instances
- **Shared Services:** Redis and database shared across instances
- **Scaling Factor:** Linear (2 instances = 2x capacity)

**Architecture:**

```
                    Load Balancer
                         |
        +----------------+----------------+
        |                |                |
    Backend 1        Backend 2        Backend 3
        |                |                |
        +----------------+----------------+
                         |
            +------------+------------+
            |                         |
        Redis Cloud              Supabase DB
```

**Benefits:**
- Linear scaling
- High availability (if one instance fails, others continue)
- Can scale based on demand
- Cost-effective for variable workloads

**Challenges:**
- Session management (use Redis)
- Shared state coordination
- Load balancer configuration
- Monitoring multiple instances

### Serverless Scaling

**Offload Heavy Operations:**

- **Document Processing:** AWS Lambda, Google Cloud Functions
- **AI Agent Calls:** Serverless functions with auto-scaling
- **Background Jobs:** Queue-based processing

**Benefits:**
- Pay only for what you use
- Automatic scaling
- No server management
- Cost-effective for sporadic heavy loads

**Use Cases:**
- Document upload and processing
- Large batch operations
- Scheduled tasks
- AI agent operations (if rate limits allow)

### Database Scaling

**Options:**

1. **Read Replicas:** Distribute read operations
2. **Connection Pooling:** Optimize connection usage
3. **Query Optimization:** Index optimization, query caching
4. **Managed Database:** Supabase handles scaling automatically

**Supabase Scaling:**
- Free tier: Limited connections
- Pro tier: Higher limits, better performance
- Enterprise: Custom scaling options

---

## Monitoring and Metrics

### Key Metrics to Monitor

1. **Memory Usage**
   - Current usage vs. total available
   - Peak usage during operations
   - Memory leaks detection

2. **CPU Usage**
   - Average CPU usage
   - Peak CPU usage
   - CPU per request

3. **Request Metrics**
   - Requests per second (RPS)
   - Response times (p50, p95, p99)
   - Error rates
   - Timeout rates

4. **Database Metrics**
   - Connection pool usage
   - Query performance
   - Connection wait times
   - Query timeouts

5. **External API Metrics**
   - AI API response times
   - Rate limit hits
   - API error rates
   - Token usage

6. **User Metrics**
   - Concurrent active users
   - Daily active users
   - Peak concurrent users
   - User session duration

### Monitoring Tools

**Recommended:**
- **Application Monitoring:** Prometheus + Grafana, Datadog, New Relic
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana), CloudWatch
- **APM:** Sentry for error tracking
- **Uptime Monitoring:** UptimeRobot, Pingdom

**Implementation:**

```python
# Example: Add Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
active_users = Gauge('active_users', 'Current active users')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage in bytes')
```

---

## Configuration Recommendations

### Production Configuration (8GB RAM, 2 CPU)

**Uvicorn/Gunicorn:**

```python
# start.sh or systemd service
uvicorn main:app \
    --workers 2 \
    --host 0.0.0.0 \
    --port 8000 \
    --timeout-keep-alive 5 \
    --timeout-graceful-shutdown 30 \
    --log-level info
```

**Environment Variables (.env):**

```env
# Database Connection Pool
DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=50
DB_POOL_INCREMENT=2
DB_POOL_SIZE=20

# Redis Connection Pool
REDIS_POOL_SIZE=20
REDIS_POOL_MAX_CONNECTIONS=50

# Agent Timeouts
AGENT_TIMEOUT=60.0
AGENT_SPECIFIC_TIMEOUT=55.0
MODEL_TIMEOUT=30.0

# Request Limits
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# File Limits
MAX_FILE_SIZE=10485760      # 10MB
MAX_IMAGE_SIZE=5242880      # 5MB

# Chat History
CHAT_MEMORY_EXPIRE_SECONDS=86400
CHAT_HISTORY_WINDOW=200
MAX_ACTIVE_CHAT_MESSAGES=100
```

### High-Traffic Configuration (16GB RAM, 4 CPU)

**Uvicorn/Gunicorn:**

```python
uvicorn main:app \
    --workers 4 \
    --host 0.0.0.0 \
    --port 8000 \
    --timeout-keep-alive 5 \
    --timeout-graceful-shutdown 30
```

**Environment Variables:**

```env
# Database Connection Pool (increased)
DB_POOL_MIN_SIZE=20
DB_POOL_MAX_SIZE=100
DB_POOL_INCREMENT=5
DB_POOL_SIZE=40

# Redis Connection Pool (increased)
REDIS_POOL_SIZE=40
REDIS_POOL_MAX_CONNECTIONS=100

# Request Limits (increased)
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_PER_HOUR=2000
```

---

## Performance Testing

### Load Testing Tools

**Recommended:**
- **Locust:** Python-based, easy to use
- **Apache JMeter:** Feature-rich, Java-based
- **k6:** Modern, JavaScript-based
- **Artillery:** Node.js-based, good for APIs

### Test Scenarios

1. **Baseline Test:** Measure current capacity
2. **Stress Test:** Find breaking point
3. **Spike Test:** Sudden traffic increase
4. **Endurance Test:** Sustained load over time

### Example Load Test (Locust)

```python
# locustfile.py
from locust import HttpUser, task, between

class StudBackendUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(2)
    def get_user_profile(self):
        self.client.get("/api/user/profile")
    
    @task(1)
    def chat_with_game_master(self):
        self.client.post("/api/game/chat", json={
            "message": "Hello",
            "user_id": "test_user"
        })
```

**Run Test:**
```bash
locust -f locustfile.py --host=http://localhost:8000
```

---

## Cost Optimization

### Resource Optimization

1. **Right-Size Servers:** Don't over-provision
2. **Use Managed Services:** Supabase, Redis Cloud (often cheaper than self-hosted)
3. **Implement Caching:** Reduce database and API calls
4. **Optimize AI API Usage:** Cache responses, optimize prompts
5. **Use CDN:** For static assets (if applicable)

### Cost Estimates (Monthly)

**8GB RAM, 2 CPU Server:**
- **VPS (DigitalOcean, Linode):** $40-60/month
- **AWS EC2 (t3.medium):** $30-50/month
- **Railway/Render:** $20-40/month

**Managed Services:**
- **Supabase (Pro):** $25/month
- **Redis Cloud:** $10-30/month
- **AI APIs:** Variable (pay-per-use)

**Total Estimated:** $70-150/month for 50-100 concurrent users

---

## Troubleshooting Common Issues

### High Memory Usage

**Symptoms:**
- Memory usage >85%
- OOM (Out of Memory) errors
- Slow response times

**Solutions:**
- Reduce worker count
- Implement request queuing
- Optimize document processing
- Increase server RAM

### High CPU Usage

**Symptoms:**
- CPU usage >80%
- Slow response times
- Request timeouts

**Solutions:**
- Optimize CPU-intensive operations
- Queue document processing
- Add more CPU cores
- Optimize database queries

### Database Connection Pool Exhausted

**Symptoms:**
- "Too many connections" errors
- Slow database queries
- Connection timeouts

**Solutions:**
- Increase pool size
- Optimize connection usage
- Use connection pooling efficiently
- Implement connection retry logic

### External API Rate Limits

**Symptoms:**
- 429 (Too Many Requests) errors
- Slow AI responses
- Failed AI operations

**Solutions:**
- Implement request queuing
- Use multiple API keys (if allowed)
- Implement exponential backoff
- Cache common responses
- Upgrade API tier

---

## Conclusion

The Stud Python backend can handle **50-100 concurrent active users** on a standard 8GB RAM, 2 CPU server with proper optimization. The system is primarily I/O-bound, which allows efficient handling of many concurrent requests through async/await.

**Key Takeaways:**
- Primary bottleneck: External AI API rate limits
- Memory management is critical for document processing
- Database connection pooling is important for scalability
- Horizontal scaling provides linear capacity increase
- Monitoring is essential for optimization

**Recommended Next Steps:**
1. Implement monitoring and metrics
2. Conduct load testing to validate estimates
3. Optimize based on actual usage patterns
4. Plan for horizontal scaling as user base grows
5. Consider serverless for heavy operations

---

## Additional Resources

- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Configuration](https://www.uvicorn.org/settings/)
- [Async Python Best Practices](https://docs.python.org/3/library/asyncio.html)
- [Database Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)

---

**Last Updated:** 2026-03-14  
**Version:** 1.0
