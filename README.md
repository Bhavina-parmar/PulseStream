# PulseStream

A high-throughput, event-driven backend platform for real-time telemetry ingestion, asynchronous event processing, live analytics, and fault-tolerant event delivery.

PulseStream is designed as a production-oriented learning project demonstrating backend engineering concepts including clean architecture, asynchronous processing, Kafka event streaming, Redis, WebSockets, authentication, observability, failure recovery, and load testing.

---

## 1. Problem

Modern applications continuously generate telemetry such as:

* user logins
* page views
* button clicks
* searches
* purchases
* API activity
* system events

A purely synchronous architecture can become difficult to scale when event processing is performed directly inside the request path. Slow downstream operations can increase API latency, create backpressure, and couple ingestion tightly to processing.

PulseStream separates **event ingestion** from **event processing**.

The API:

1. authenticates the request
2. validates the event
3. persists it as `PENDING`
4. publishes it to Kafka when available
5. immediately returns `202 Accepted`

Background workers then process events asynchronously.

Processed events update analytics in Redis and are published through Redis Pub/Sub to connected WebSocket clients.

The result is an architecture designed around:

* asynchronous processing
* horizontal scalability
* eventual consistency
* fault isolation
* retry and recovery mechanisms
* real-time event delivery
* observability

---

# 2. Architecture

```text
                         ┌──────────────────┐
                         │   Client Apps    │
                         │ Web / Mobile/API │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   FastAPI API Gateway   │
                    │                         │
                    │ JWT / RBAC              │
                    │ Rate Limiting           │
                    │ Validation              │
                    │ API Versioning           │
                    └────────────┬────────────┘
                                 │
                                 ▼
                         ┌──────────────┐
                         │ PostgreSQL   │
                         │ Event Store  │
                         └──────┬───────┘
                                │
                         PENDING│
                                ▼
                         ┌──────────────┐
                         │    Kafka     │
                         │ user-events  │
                         └──────┬───────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │    Event Workers       │
                    │ Kafka Consumer Group    │
                    └───────────┬────────────┘
                                │
                 ┌──────────────┼───────────────┐
                 │              │               │
                 ▼              ▼               ▼
            PostgreSQL       Redis         Redis Pub/Sub
          Event Status      Analytics         ws:events
                                │               │
                                │               ▼
                                │       WebSocket Subscriber
                                │               │
                                │               ▼
                                │        WebSocket Clients
                                │
                                ▼
                         Analytics APIs


        ┌────────────────────────────────────────────────┐
        │                Failure Handling                 │
        │                                                │
        │ Kafka failure → PENDING → Recovery Worker      │
        │ Processing failure → Retry → DLQ               │
        │ Redis failure → Rate limiter fails open        │
        └────────────────────────────────────────────────┘


        ┌────────────────────────────────────────────────┐
        │                 Observability                  │
        │                                                │
        │ Prometheus → Grafana                           │
        │ Structured JSON Logs                           │
        │ Health / Readiness Checks                      │
        └────────────────────────────────────────────────┘
```

## Services

| Service                         | Role                                                        |
| ------------------------------- | ----------------------------------------------------------- |
| `fastapi_api`                   | HTTP API, authentication, event ingestion, analytics APIs   |
| `fastapi_worker`                | Kafka consumer and asynchronous event processor             |
| `app_event_worker`              | Additional event consumer/worker instance                   |
| `fastapi_dlq_worker`            | Processes and records dead-lettered events                  |
| `api-gateway-recovery-worker-1` | Re-publishes eligible `PENDING` events after Kafka failures |
| `app_kafka`                     | Event streaming broker                                      |
| `app_zookeeper`                 | Kafka coordination for the local Kafka deployment           |
| `app_postgres`                  | Primary relational database                                 |
| `app_redis`                     | Rate limiting, analytics counters, and Redis Pub/Sub        |
| `app_prometheus`                | Metrics collection                                          |
| `app_grafana`                   | Metrics visualization                                       |

Multiple event-worker containers can participate in the same Kafka consumer group and share partitions.

---

# 3. Clean Architecture

PulseStream follows a layered architecture:

```text
Controller
    ↓
Service
    ↓
Repository
    ↓
Infrastructure
```

### Controllers

Handle HTTP/WebSocket requests and responses.

### Services

Contain business logic and orchestration.

### Repositories

Handle persistence and infrastructure-specific data access.

### Models

SQLAlchemy database models.

### DTOs

Pydantic request/response schemas.

### Validators

Input and business validation.

### Middleware

Cross-cutting concerns such as:

* authentication
* rate limiting
* request processing

This separation keeps HTTP, business logic, and persistence concerns independent.

---

# 4. Request Lifecycle

```text
POST /v1/events/
        ↓
Redis Rate Limiter
        ↓
JWT Authentication
        ↓
Pydantic Validation
        ↓
Persist Event as PENDING
        ↓
Publish to Kafka
        ↓
Return 202 Accepted
```

The API does not wait for event processing to finish.

If Kafka is temporarily unavailable, the event remains `PENDING` in PostgreSQL and the recovery worker can attempt publication later.

This provides availability during temporary Kafka outages at the cost of eventual consistency.

---

# 5. Event Lifecycle

Normal path:

```text
Event Created
     ↓
PENDING
     ↓
Kafka
     ↓
Consumer
     ↓
PROCESSING
     ↓
Business Processing
     ↓
PROCESSED
     ↓
Redis Analytics
     ↓
Redis Pub/Sub
     ↓
WebSocket Clients
```

Failure path:

```text
Kafka Consumer
     ↓
Processing Failure
     ↓
Retry #1 — 1 second
     ↓
Retry #2 — 2 seconds
     ↓
Retry #3
     ↓
DLQ
     ↓
FAILED
```

The exact retry behavior should be treated as **at-least-once processing**, meaning a message may be processed more than once in failure/restart scenarios. Event handlers should therefore be designed to tolerate duplicate delivery.

---

# 6. Authentication

PulseStream implements:

* JWT access tokens
* opaque refresh tokens
* bcrypt password hashing
* role-based access control
* refresh-token revocation

### Access Token

* Algorithm: HS256
* Expiration: 30 minutes

### Refresh Token

* Opaque token
* Stored securely in PostgreSQL
* Expiration: 7 days
* Revocable
* Expired tokens cleaned up periodically

### Authentication Flow

```text
POST /v1/auth/login
        ↓
Verify credentials
        ↓
Access Token + Refresh Token
```

Refresh:

```text
POST /v1/auth/refresh
        ↓
Validate refresh token
        ↓
Issue new access token
```

Logout:

```text
POST /v1/auth/logout
        ↓
Revoke refresh token
```

---

# 7. Kafka Architecture

### Topics

```text
user-events
dead-letter-events
```

### Consumer Groups

```text
event-workers
dlq_processor_group
```

### Producer

Uses an asynchronous `AIOKafkaProducer`.

Events are JSON serialized before publication.

### Scaling

Kafka partitions allow multiple consumers in the same consumer group to process events concurrently.

```text
                    user-events
                 ┌────┬────┬────┐
                 │ P0 │ P1 │ P2 │
                 └─┬──┴─┬──┴─┬──┘
                   │     │     │
                  W1    W2    W3
```

Increasing partitions allows additional consumers to process events concurrently.

### Local Development

The local Docker deployment uses:

```text
Replication Factor = 1
```

This is appropriate for local development but is **not fault tolerant against Kafka node failure**.

A production deployment would use multiple Kafka brokers and a replication factor greater than 1.

---

# 8. Redis Architecture

Redis is used for three independent purposes.

### Rate Limiting

```text
rate_limit:{client_ip}
```

The current implementation limits clients to:

```text
1000 requests / 60 seconds
```

Redis is treated as a shared infrastructure dependency rather than being coupled to the rate-limiter middleware.

### Analytics

Counters are maintained by event type:

```text
analytics:USER_LOGIN
analytics:PAGE_VIEW
analytics:PURCHASE
```

Example:

```text
analytics:USER_LOGIN = 452
```

### WebSocket Pub/Sub

Processed events are published to:

```text
ws:events
```

The WebSocket subscriber consumes these messages and broadcasts them to connected clients.

### Redis Failure Behavior

The rate limiter fails open when Redis is unavailable.

Therefore:

```text
Redis failure
      ↓
Rate limiting disabled temporarily
      ↓
API continues serving requests
```

This favors availability over protection during a Redis outage.

---

# 9. WebSocket Architecture

```text
Kafka Worker
     ↓
Redis Pub/Sub
     ↓
ws:events
     ↓
WebSocket Subscriber
     ↓
ConnectionManager
     ↓
Connected Clients
```

Clients connect using:

```text
/ws
```

WebSocket connections are authenticated using JWT.

The connection manager:

* registers clients
* removes disconnected clients
* broadcasts events
* prunes stale connections

### Important Delivery Semantics

Redis Pub/Sub is not a durable message queue.

If a WebSocket subscriber is disconnected when a Pub/Sub message is published, that client does not receive the missed message.

Therefore WebSocket delivery is **best effort / live-stream delivery**, while PostgreSQL remains the durable event store.

Clients can retrieve historical state through REST APIs.

---

# 10. Failure Handling

## Kafka Outage

```text
API
 ↓
PostgreSQL
 ↓
PENDING
 ↓
Kafka unavailable
```

The API can continue accepting events because persistence happens before asynchronous publication.

The recovery worker periodically finds eligible `PENDING` events and attempts to publish them again.

Current recovery configuration:

```text
Polling interval: 30 seconds
Minimum event age: 60 seconds
```

This provides eventual recovery after temporary Kafka outages.

---

## PostgreSQL Outage

Database operational failures are translated into an HTTP `503 Service Unavailable` response where appropriate.

The system does not claim that events are accepted when durable persistence is unavailable.

---

## Redis Outage

Rate limiting fails open.

Analytics and live Pub/Sub functionality may be temporarily unavailable, while the core API can continue operating.

---

## Worker Failure

Kafka retains the event according to its configured retention policy.

Another worker in the same consumer group can continue processing available partitions.

---

## Processing Failure

```text
Processing failure
       ↓
Exponential retry
       ↓
Maximum retry attempts
       ↓
DLQ
       ↓
FAILED
```

---

# 11. Consistency Model

PulseStream uses **eventual consistency** between event persistence and downstream analytics.

The sequence is:

```text
PostgreSQL write
       ↓
202 Accepted
       ↓
Kafka publication
       ↓
Worker processing
       ↓
Redis analytics
       ↓
WebSocket update
```

Therefore the following can temporarily differ:

```text
PostgreSQL event count
Redis analytics count
WebSocket-visible state
```

This is intentional.

The API prioritizes fast ingestion and durable persistence while downstream processing happens asynchronously.

### Durability Guarantee

For an accepted event, PostgreSQL is the durable source of record.

The system is designed so that a temporarily unavailable Kafka broker does not cause the already-persisted event to disappear.

However, absolute "no data loss" cannot be claimed without additional assumptions around PostgreSQL durability, backups, Kafka configuration, and infrastructure failure.

---

# 12. Scaling Strategy

| Layer      | Scaling Strategy                                                     |
| ---------- | -------------------------------------------------------------------- |
| API        | Horizontal replicas / multiple Uvicorn workers                       |
| Kafka      | Increase partitions and broker count                                 |
| Workers    | Increase consumer instances within consumer group                    |
| PostgreSQL | Connection pooling, indexing, read replicas for read-heavy workloads |
| Redis      | Redis Cluster / managed Redis for larger deployments                 |
| WebSockets | Multiple WebSocket instances with Redis Pub/Sub as the fan-out layer |

### API Database Connections

The configured SQLAlchemy pool applies per API process.

With multiple Uvicorn workers, total possible database connections can multiply across processes.

This must be considered when tuning PostgreSQL capacity.

---

# 13. Current Load Test Results

Tests were performed against the **local Docker deployment** using k6.

These numbers describe the current local environment and should not be interpreted as production capacity.

## GET /v1/events/

|                  VUs |   Throughput |          p95 | Error Rate |
| -------------------: | -----------: | -----------: | ---------: |
|                   20 |  17.58 req/s |       347 ms |         0% |
|                  100 |  75.93 req/s |        90 ms |         0% |
| 1000 — before tuning |  15.94 req/s | 60 s timeout |        61% |
|  1000 — after tuning | 163.69 req/s |      11.92 s |        31% |

## POST /v1/events/

| VUs |  Throughput |    p95 | Error Rate |
| --: | ----------: | -----: | ---------: |
|  50 | 24.32 req/s | 3.11 s |       2.9% |

### Identified Bottlenecks

Current local bottlenecks include:

1. PostgreSQL connection pool saturation around ~300 concurrent VUs
2. Kafka publish latency under burst traffic
3. Local Docker CPU/memory constraints
4. High request latency at extreme concurrency

These results demonstrate that the system has been **measured under load rather than simply described as high-throughput**.

Future optimization targets include:

* async database access
* connection pool tuning
* Kafka batching
* producer configuration
* database indexing/query optimization
* horizontal API scaling
* distributed deployment

---

# 14. Observability

PulseStream exposes metrics through Prometheus.

### Metrics

Worker metrics:

```text
worker_events_processed_total
worker_events_failed_total
dlq_events_total
```

HTTP metrics include:

* request count
* request latency
* HTTP status distribution

### Stack

```text
Application
     ↓
Prometheus
     ↓
Grafana
```

Structured JSON logging is implemented through:

```text
config/logger.py
```

Logs include fields such as:

* timestamp
* level
* service
* event/request information

### Health

```http
GET /health
```

performs dependency health checks for:

* PostgreSQL
* Redis
* Kafka

---

# 15. Testing

Current test suite:

```text
50 tests
50 passing
```

Test framework:

```text
pytest
```

Coverage includes:

* controllers
* services
* repositories
* authentication
* middleware
* validators
* event processing
* analytics

CI runs automatically through GitHub Actions on every push.

---

# 16. API

Base API version:

```text
/v1/
```

### Authentication

```http
POST /v1/auth/login
POST /v1/auth/refresh
POST /v1/auth/logout
```

### Users

```http
POST /v1/users/
GET  /v1/users/{id}
```

### Events

```http
POST /v1/events/
GET  /v1/events/
GET  /v1/events/{id}
```

### Analytics

```http
GET /v1/analytics/
GET /v1/analytics/{type}
```

### Monitoring

```http
GET /health
GET /metrics
```

### WebSocket

```text
/ws
```

Swagger documentation:

```text
/docs
```

---

# 17. Deployment

## Local Development

Prerequisites:

* Docker
* Docker Compose

```bash
git clone <repository>
cd backend/apps/api-gateway
docker-compose up -d --build
```

The local stack includes:

```text
FastAPI API
Event Worker
DLQ Worker
Recovery Worker
PostgreSQL
Redis
Kafka
Zookeeper
Prometheus
Grafana
```

### Local Endpoints

```text
API:
http://localhost:8000

Swagger:
http://localhost:8000/docs

Prometheus:
http://localhost:9090

Grafana:
http://localhost:3000
```

WebSocket:

```text
ws://localhost:8000/ws
```

---

# 18. Environment Variables

See `.env.example`.

Important variables include:

```text
DATABASE_URL
REDIS_URL
KAFKA_BOOTSTRAP_SERVERS
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
```

Secrets must not be committed to source control.

For production deployment, use a dedicated secrets-management solution instead of storing production credentials in `.env` files.

---

# 19. Tradeoffs

| Decision                         | Tradeoff                                                                                           |
| -------------------------------- | -------------------------------------------------------------------------------------------------- |
| 202 after PostgreSQL persistence | Fast ingestion and availability, but downstream processing is asynchronous                         |
| PostgreSQL before Kafka          | Durable local source of record, but recovery is required if Kafka publication fails                |
| Async Kafka processing           | High decoupling and throughput, but introduces eventual consistency                                |
| Redis rate limiter fails open    | API availability is preserved, but rate protection is lost during Redis outages                    |
| Redis Pub/Sub                    | Simple low-latency fan-out, but messages are not durable                                           |
| JWT access tokens                | Stateless request authentication, while refresh-token storage provides revocation control          |
| Single Kafka broker locally      | Simple development setup, but no broker-level fault tolerance                                      |
| Sync SQLAlchemy                  | Simpler implementation, but database operations consume worker threads under high concurrency      |
| Recovery worker polling          | Simple and reliable, but introduces a recovery delay                                               |
| At-least-once event processing   | Better delivery guarantees, but requires idempotent processing                                     |
| Eventual consistency             | Better ingestion latency and decoupling, but analytics may temporarily lag behind persisted events |

---

# 20. Chaos Testing

All chaos tests were performed against the live local Docker stack.

## Kafka Outage

**Test:** `docker stop app_kafka` while the API was running.

**Observed behavior:**
- API continued accepting events and returning `202 Accepted`
- Events were persisted to PostgreSQL with status `PENDING`
- Events were never published to Kafka — stuck as `PENDING` indefinitely
- No crash, no 500 error

**Problem:** Events were orphaned forever. No mechanism existed to re-publish them after Kafka recovered.

**Fix:** Implemented `workers/recovery_worker.py` — a background worker that polls PostgreSQL every 30 seconds for events stuck as `PENDING` for more than 60 seconds and re-publishes them to Kafka.

**Verified:** After Kafka restart, the recovery worker detected event ID 2525, re-published it, and the event worker updated its status to `PROCESSED`.

---

## PostgreSQL Outage

**Test:** `docker stop app_postgres` while the API was running.

**Observed behavior before fix:**
- `POST /v1/events/` returned `500` with generic message `"something went wrong"`
- `GET /v1/events/` returned `500` with generic message `"something went wrong"`
- `/health` correctly reported `postgres: unhealthy`

**Problem:** SQLAlchemy `OperationalError` was being caught by the generic exception handler and returned as a 500 with no useful information for the caller.

**Fix:** Added a dedicated `OperationalError` exception handler in `main.py` that returns `503 Service Unavailable` with the message `"Database unavailable, please try again later"`.

**Verified:** After fix, `POST /v1/events/` with Postgres down correctly returns `503`.

---

## Redis Outage

**Test:** `docker stop app_redis` while the API was running.

**Observed behavior:**
- API continued serving all requests normally — `200 OK` on GET, `202 Accepted` on POST
- Rate limiting was silently disabled — all requests passed through
- `/health` correctly reported `redis: unhealthy`
- No crash, no errors returned to clients

**Assessment:** This is the correct behavior. The rate limiter is intentionally designed to fail open — Redis being down should not take down the API. Availability is prioritized over rate protection during outages.

**Fix:** No fix required. Fail-open is the intended design.

---

# 21. Roadmap

## Stage 1 — Verify
- [x] Load testing (GET /v1/events/)
- [x] Load testing (POST /v1/events/)
- [ ] Kafka throughput testing
- [ ] WebSocket concurrency testing
- [ ] DB performance testing
- [ ] Redis concurrency testing

## Stage 2 — Break
- [x] Kill Kafka
- [x] Kill Redis
- [x] Kill PostgreSQL
- [ ] Kill worker
- [ ] Network failure tests

## Stage 3 — Harden
- [ ] Security audit
- [ ] Graceful shutdown
- [ ] Delivery semantics
- [ ] Consistency documentation
- [ ] Backup/recovery strategy

## Stage 4 — Present
- [ ] Architecture diagram
- [ ] Sequence diagrams
- [x] README
- [ ] Grafana screenshots
- [ ] Load-test results
- [ ] Failure-test results
- [ ] Design tradeoffs

---

# 22. Future Production Improvements

The current system is complete as a production-oriented learning project. Further improvements would focus on scale and infrastructure rather than adding unnecessary technologies.

Potential next steps:

* OpenTelemetry distributed tracing
* centralized log aggregation
* Kafka multi-broker deployment
* Kafka replication factor > 1
* schema registry / event schema evolution
* async PostgreSQL driver
* database partitioning for very large event tables
* Redis Cluster
* automated alerting
* Kubernetes/ECS deployment
* automated production load testing
* disaster recovery and backup automation

These are deployment and scale improvements, not requirements for the core PulseStream architecture.

---

# 23. Project Status

PulseStream currently demonstrates:

```text
✓ Clean layered architecture
✓ REST API
✓ JWT authentication
✓ Refresh-token authentication
✓ RBAC
✓ PostgreSQL persistence
✓ Redis rate limiting
✓ Redis analytics
✓ Kafka event streaming
✓ Kafka consumer groups
✓ Async workers
✓ Retry mechanism
✓ Dead-letter queue
✓ Failed-event recovery
✓ WebSocket live streaming
✓ Redis Pub/Sub
✓ Event pagination
✓ API versioning
✓ Structured logging
✓ Prometheus metrics
✓ Grafana dashboards
✓ Health checks
✓ Docker Compose
✓ GitHub Actions CI
✓ Automated tests
✓ Load testing
✓ Failure handling
✓ Explicit consistency model
```

PulseStream is therefore not simply a CRUD API. It is a **distributed event-driven backend demonstrating asynchronous processing, real-time streaming, fault handling, observability, and scalability considerations under concurrent workloads.**
