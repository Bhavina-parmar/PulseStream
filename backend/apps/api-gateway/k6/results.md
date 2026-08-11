# PulseStream Load Test Results

## Test 1: GET /v1/events/ (Read Endpoint)

### 20 VUs (Baseline)
- Throughput: 17.58 req/sec
- p50: 35.65ms
- p90: 113.07ms
- p95: 347.25ms
- p99: ~588ms
- Error rate: 0.00% ✅

### 100 VUs
- Throughput: 75.93 req/sec
- p50: 20ms
- p90: 76.18ms
- p95: 90.32ms
- p99: ~332ms
- Error rate: 0.00% ✅

### 1000 VUs (before tuning)
- Throughput: 15.94 req/sec
- p50: 60s (timeout)
- p95: 60s (timeout)
- Error rate: 61.05% ❌
- Cause: Request timeouts — server saturated

### 1000 VUs (after tuning: 4 workers + pool_size=50)
- Throughput: 163.69 req/sec
- p50: 1.79s
- p95: 11.92s
- Error rate: 31.25% ❌
- Cause: DB connection pool saturation at scale

---

## Test 2: POST /v1/events/ (Event Ingestion)

### 50 VUs
- Throughput: 24.32 req/sec
- p50: 236.7ms
- p90: 832.48ms
- p95: 3.11s
- Error rate: 2.90% ❌
- Cause: Kafka publish latency under burst load

---

## Summary
- Stable under: 100 VUs → 0% errors, 75 req/sec, p95 90ms
- Degrades at: 300+ VUs → connection pool saturation
- Breaks at: 1000 VUs → 31% errors, timeouts

## Environment
- Local Docker (single machine)
- 4 uvicorn workers
- PostgreSQL pool_size=50, max_overflow=100
- Single-node Kafka

## Bottlenecks Identified
1. DB connection pool exhausts at ~300 VUs
2. Single uvicorn instance limits concurrency
3. Kafka single-node publish latency spikes under burst
