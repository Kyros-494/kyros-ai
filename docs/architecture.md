# Architecture

System design and internals of the Kyros Memory Operating System.

## Overview

Kyros is a production-grade memory system for AI agents built with modern Python best practices. It provides persistent, searchable memory with advanced features like decay curves, integrity proofs, and causal reasoning.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Python SDK   │  │TypeScript SDK│  │  HTTP API    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FastAPI      │  │ Auth         │  │ Rate Limit   │      │
│  │ Application  │  │ Middleware   │  │ Middleware   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Memory       │  │ Intelligence │  │ ML           │      │
│  │ Service      │  │ Engine       │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ Redis        │  │ S3           │      │
│  │ + pgvector   │  │ Cache        │  │ Archive      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway Layer

#### FastAPI Application

**Location:** `server/kyros/main.py`

The FastAPI application serves as the entry point for all HTTP requests.

**Features:**
- Async request handling for high concurrency
- Automatic OpenAPI documentation generation
- Request validation with Pydantic
- Global exception handlers
- CORS configuration
- Security headers

**Key Endpoints:**
- `/health` - Basic health check
- `/health/ready` - Readiness check (DB + Redis)
- `/docs` - Interactive API documentation (Swagger UI)
- `/redoc` - Alternative API documentation (ReDoc)
- `/v1/*` - API version 1 endpoints

#### Authentication Middleware

**Location:** `server/kyros/middleware/auth.py`

Handles API key authentication for all requests.

**Flow:**
1. Extract API key from `Authorization: Bearer <key>` header
2. Check Redis cache for authenticated key (5-minute TTL)
3. If not cached, hash key with SHA-256 and query database
4. Cache successful authentication in Redis
5. Attach tenant and agent context to request

**Security Features:**
- SHA-256 key hashing (prevents plaintext storage)
- Constant-time comparison (prevents timing attacks)
- Redis caching (reduces database load)
- Test key blocking in production
- Safe logging (only key prefixes logged)

#### Usage Tracking Middleware

**Location:** `server/kyros/middleware/usage_tracking.py`

Tracks API usage for billing and analytics.

**Tracked Metrics:**
- Request count
- Response time
- Memory operations (store, recall, delete)
- Embedding generation count
- Error rates

### 2. Business Logic Layer

#### Memory Service

**Location:** `server/kyros/services/memory_service.py`

Core service for memory operations.

**Responsibilities:**
- Agent management (create, get, list)
- Memory CRUD operations
- Vector search
- Session management
- Metadata handling

**Key Methods:**
- `create_agent()` - Create new agent
- `store_memory()` - Store episodic memory
- `recall_memories()` - Semantic search
- `delete_memory()` - Delete memory
- `export_memories()` - Export all memories
- `import_memories()` - Import memories

#### Intelligence Engine

**Location:** `server/kyros/intelligence/`

Advanced memory features and algorithms.

**Components:**

**Decay Engine** (`decay.py`)
- Implements Ebbinghaus forgetting curves
- Calculates freshness scores based on time and importance
- Configurable decay rates per memory category
- Formula: `freshness = e^(-decay_rate * time_elapsed)`

**Integrity System** (`integrity.py`)
- SHA-256 content hashing
- Merkle tree construction for batch verification
- Cryptographic proof generation
- Tamper detection

**Belief Propagation** (`belief.py`)
- Confidence score propagation through semantic graph
- Contradiction detection and resolution
- Bayesian belief updates
- Graph-based inference

**Causal Reasoning** (`causal.py`)
- Cause-effect relationship extraction
- Causal chain construction
- Temporal reasoning
- Counterfactual analysis

**Compression** (`compression.py`)
- Memory summarization
- Extractive compression (local)
- LLM-based compression (OpenAI, Anthropic, Gemini)
- Importance-based pruning

**Forgetting** (`forgetting.py`)
- Intelligent memory deletion
- Importance-based retention
- Archival to S3 before deletion
- Compliance with data retention policies

**Archival** (`archival.py`)
- S3 integration for deleted memories
- Versioning support
- Lifecycle policies
- Compliance and audit trail

#### ML Service

**Location:** `server/kyros/ml/`

Machine learning and embedding generation.

**Components:**

**Embedder** (`embedder.py`)
- Sentence Transformers integration
- Batch embedding generation
- Model caching
- GPU acceleration support
- Dual-embedding strategy

**Models** (`models.py`)
- Model registry
- Model loading and caching
- Version management
- Performance monitoring

**Translation** (`translation.py`)
- Cross-language embedding translation
- Multilingual support
- Language detection
- Translation caching

### 3. Storage Layer

#### PostgreSQL + pgvector

**Location:** `server/kyros/storage/postgres.py`

Primary data store with vector similarity search.

**Schema:**

**Tenants Table:**
```sql
CREATE TABLE tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    api_key_hash TEXT UNIQUE NOT NULL,
    tier TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

**Agents Table:**
```sql
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    name TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL
);
```

**Episodic Memories Table:**
```sql
CREATE TABLE episodic_memories (
    memory_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    role TEXT,
    session_id TEXT,
    importance FLOAT NOT NULL DEFAULT 0.5,
    embedding VECTOR(384) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_episodic_agent ON episodic_memories(agent_id);
CREATE INDEX idx_episodic_session ON episodic_memories(session_id);
CREATE INDEX idx_episodic_embedding ON episodic_memories USING ivfflat (embedding vector_cosine_ops);
```

**Semantic Memories Table:**
```sql
CREATE TABLE semantic_memories (
    fact_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    source_type TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_semantic_agent ON semantic_memories(agent_id);
CREATE INDEX idx_semantic_triple ON semantic_memories(subject, predicate, value);
CREATE INDEX idx_semantic_embedding ON semantic_memories USING ivfflat (embedding vector_cosine_ops);
```

**Procedural Memories Table:**
```sql
CREATE TABLE procedural_memories (
    procedure_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    task_type TEXT NOT NULL,
    steps JSONB NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    embedding VECTOR(384) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_procedural_agent ON procedural_memories(agent_id);
CREATE INDEX idx_procedural_task_type ON procedural_memories(task_type);
CREATE INDEX idx_procedural_embedding ON procedural_memories USING ivfflat (embedding vector_cosine_ops);
```

**Row-Level Security:**

Ensures tenant isolation at the database level.

```sql
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON agents
    USING (tenant_id = current_setting('app.current_tenant_id')::TEXT);
```

#### Redis Cache

**Location:** `server/kyros/storage/redis_cache.py`

In-memory cache for performance optimization.

**Cached Data:**
- Authenticated API keys (5-minute TTL)
- Frequently accessed memories (10-minute TTL)
- Embedding cache (1-hour TTL)
- Session data (30-minute TTL)
- Rate limit counters (1-minute TTL)

**Cache Strategies:**
- Write-through for critical data
- Write-behind for analytics
- Cache-aside for read-heavy data
- TTL-based expiration
- LRU eviction policy

#### S3 Archive

**Location:** `server/kyros/intelligence/archival.py`

Long-term storage for deleted memories.

**Features:**
- Automatic archival on deletion
- Versioning support
- Lifecycle policies (transition to Glacier after 90 days)
- Server-side encryption (SSE-S3)
- Compliance and audit trail

## Data Flow

### Memory Storage Flow

```
1. Client sends POST /v1/memory/episodic/remember
   ↓
2. Auth middleware validates API key
   ↓
3. Request validated with Pydantic schema
   ↓
4. ML service generates embedding
   ↓
5. Memory service stores in PostgreSQL
   ↓
6. Integrity service generates proof
   ↓
7. Usage tracking records operation
   ↓
8. Response returned to client
```

### Memory Recall Flow

```
1. Client sends POST /v1/memory/episodic/recall
   ↓
2. Auth middleware validates API key
   ↓
3. Request validated with Pydantic schema
   ↓
4. ML service generates query embedding
   ↓
5. PostgreSQL performs vector similarity search
   ↓
6. Decay engine calculates freshness scores
   ↓
7. Results ranked by relevance + freshness
   ↓
8. Response returned to client
```

### Causal Reasoning Flow

```
1. Client requests causal explanation
   ↓
2. Causal engine retrieves memory
   ↓
3. Traverse causal edges (BFS/DFS)
   ↓
4. Build causal chain
   ↓
5. LLM generates natural language explanation
   ↓
6. Response returned to client
```

## Performance Characteristics

### Latency

| Operation | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| Store Memory | 20ms | 40ms | 80ms |
| Recall (10 results) | 30ms | 60ms | 120ms |
| Vector Search | 15ms | 35ms | 70ms |
| Embedding Generation | 10ms | 25ms | 50ms |
| Integrity Proof | 5ms | 15ms | 30ms |

### Throughput

- **Single Instance:** 1,000+ requests/second
- **With Caching:** 5,000+ requests/second
- **Horizontal Scaling:** Linear scaling up to 10 instances

### Storage

- **Memory per Agent:** ~1KB per memory (average)
- **Embedding Size:** 384 dimensions × 4 bytes = 1.5KB
- **Index Overhead:** ~20% of data size
- **Compression Ratio:** 3:1 (with compression enabled)

## Scaling Strategies

### Horizontal Scaling

**Application Layer:**
- Stateless design allows easy horizontal scaling
- Load balancer distributes requests across instances
- Session affinity not required

**Database Layer:**
- Read replicas for read-heavy workloads
- Connection pooling to manage connections
- Partitioning by tenant_id for large deployments

**Cache Layer:**
- Redis Cluster for distributed caching
- Consistent hashing for key distribution
- Replication for high availability

### Vertical Scaling

**Application:**
- Increase CPU for faster embedding generation
- Increase memory for larger model caching
- GPU acceleration for high-throughput scenarios

**Database:**
- Increase CPU for faster query processing
- Increase memory for larger working set
- NVMe SSDs for faster I/O

**Cache:**
- Increase memory for larger cache size
- Faster network for reduced latency

## Security Architecture

### Defense in Depth

**Layer 1: Network**
- Firewall rules
- VPC isolation
- Private subnets for database and cache
- Public subnet for API gateway only

**Layer 2: Application**
- API key authentication
- Rate limiting
- Input validation
- Output sanitization
- CORS configuration

**Layer 3: Data**
- Row-level security (RLS)
- Encryption at rest
- Encryption in transit (TLS)
- API key hashing (SHA-256)
- Secrets management

**Layer 4: Audit**
- Access logs
- Audit trail
- Integrity proofs
- Anomaly detection

### Threat Model

**Threats Mitigated:**
- Unauthorized access (API key authentication)
- Data tampering (integrity proofs)
- SQL injection (parameterized queries)
- XSS attacks (output sanitization)
- CSRF attacks (CORS configuration)
- Timing attacks (constant-time comparison)
- Brute force (rate limiting)

**Threats Not Mitigated:**
- DDoS attacks (requires external mitigation)
- Zero-day vulnerabilities (requires patching)
- Social engineering (requires user education)

## Monitoring and Observability

### Metrics

**Application Metrics:**
- Request rate
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active connections
- Memory usage
- CPU usage

**Database Metrics:**
- Query latency
- Connection pool usage
- Cache hit rate
- Replication lag
- Disk usage
- Index efficiency

**Cache Metrics:**
- Hit rate
- Miss rate
- Eviction rate
- Memory usage
- Connection count

### Logging

**Structured Logging:**
- JSON format for easy parsing
- Request ID for tracing
- Timestamp with timezone
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Context (tenant_id, agent_id, user_id)

**Log Aggregation:**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki
- CloudWatch Logs
- Datadog

### Tracing

**Distributed Tracing:**
- OpenTelemetry integration
- Trace ID propagation
- Span creation for key operations
- Performance profiling

## Disaster Recovery

### Backup Strategy

**Database Backups:**
- Automated daily backups
- Point-in-time recovery (PITR)
- Cross-region replication
- Retention: 30 days

**Configuration Backups:**
- Version control for code
- Secrets in secrets manager
- Infrastructure as code (Terraform)

### Recovery Procedures

**RTO (Recovery Time Objective):** 1 hour  
**RPO (Recovery Point Objective):** 5 minutes

**Failure Scenarios:**

**Single Instance Failure:**
- Load balancer redirects to healthy instances
- Auto-scaling launches replacement instance
- Recovery time: < 5 minutes

**Database Failure:**
- Automatic failover to read replica
- Promote replica to primary
- Recovery time: < 15 minutes

**Region Failure:**
- DNS failover to secondary region
- Restore from cross-region backup
- Recovery time: < 1 hour

## Future Enhancements

### Planned Features

**Short-term (3-6 months):**
- GraphQL API
- WebSocket support for real-time updates
- Multi-modal embeddings (images, audio)
- Advanced query language

**Medium-term (6-12 months):**
- Federated learning for privacy
- On-device embedding generation
- Blockchain-based integrity proofs
- Advanced analytics dashboard

**Long-term (12+ months):**
- Distributed memory system
- Cross-agent memory sharing
- Automated memory optimization
- AI-powered memory curation

## Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Redis Documentation](https://redis.io/documentation)
- [Sentence Transformers](https://www.sbert.net/)
