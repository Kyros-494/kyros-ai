# Kyros Server

> **FastAPI server for the Kyros Memory Operating System**

The Kyros server is a high-performance, scalable backend that provides persistent memory capabilities for AI agents. Built with modern Python best practices, it offers enterprise-grade security, comprehensive testing, and production-ready deployment options.

---

## Quick Start

### Prerequisites

- **Python**: 3.12 or higher
- **PostgreSQL**: 16+ with pgvector extension
- **Redis**: 7+
- **Docker** 

### Option 1: Docker (Recommended)

```bash
# From repository root
docker compose up -d

# Check server health
curl http://localhost:8000/health

# View logs
docker compose logs -f kyros-server
```

### Option 2: Local Development

```bash
# Install dependencies with uv (recommended)
cd server
uv sync

# Or with pip
pip install -e .

# Set up environment variables
cp ../.env.example ../.env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn kyros.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Project Structure

```
server/
├── kyros/                      # Main application package
│   ├── api/                    # API endpoints
│   │   └── v1/                 # API version 1
│   │       ├── episodic.py     # Episodic memory endpoints
│   │       ├── semantic.py     # Semantic memory endpoints
│   │       ├── procedural.py   # Procedural memory endpoints
│   │       ├── search.py       # Unified search
│   │       ├── admin.py        # Admin operations
│   │       ├── causal.py       # Causal reasoning
│   │       └── trust.py        # Integrity verification
│   ├── intelligence/           # Advanced memory features
│   │   ├── decay.py            # Ebbinghaus decay curves
│   │   ├── integrity.py        # Cryptographic proofs
│   │   ├── belief.py           # Belief propagation
│   │   ├── causal.py           # Causal reasoning
│   │   ├── compression.py      # Memory compression
│   │   ├── forgetting.py       # Intelligent forgetting
│   │   └── archival.py         # S3 archival
│   ├── middleware/             # Request/response middleware
│   │   ├── auth.py             # API key authentication
│   │   └── usage_tracking.py   # Usage analytics
│   ├── ml/                     # Machine learning
│   │   ├── embedder.py         # Embedding generation
│   │   ├── models.py           # ML model definitions
│   │   └── translation.py      # Cross-language support
│   ├── schemas/                # Pydantic models
│   │   └── memory.py           # Request/response schemas
│   ├── services/               # Business logic
│   │   └── memory_service.py   # Core memory operations
│   ├── storage/                # Data persistence
│   │   ├── postgres.py         # PostgreSQL connection
│   │   └── redis_cache.py      # Redis caching
│   ├── config.py               # Application settings
│   ├── logging.py              # Structured logging
│   ├── main.py                 # FastAPI application
│   └── models.py               # SQLAlchemy ORM models
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Migration environment
├── tests/                      # Test suite
│   ├── integration/            # Integration tests
│   ├── unit/                   # Unit tests
│   └── load/                   # Load tests (Locust)
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Project metadata & dependencies
├── Dockerfile                  # Container image
└── README.md                   # This file
```

---

## Development

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
pytest tests/integration/test_episodic_roundtrip.py -v

# Run with specific markers
pytest -m "not slow" -v

# Run integration tests only
pytest tests/integration/ -v

# Run unit tests only
pytest tests/unit/ -v
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Type check
mypy kyros

# Run all checks (CI simulation)
make ci
```

### Database Migrations

```bash
# Create a new migration
make migrate-new NAME="add_new_feature"

# Apply migrations
make migrate

# Rollback last migration
make migrate-down

# View migration history
alembic history

# View current revision
alembic current
```

### Load Testing

```bash
# Quick benchmark (30 seconds, 50 users)
make benchmark-quick

# Full benchmark suite
make benchmark-all

# Custom Locust test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## Architecture

### Core Components

1. **FastAPI Application** (`main.py`)
   - Async request handling
   - Global exception handlers
   - Security headers
   - CORS configuration
   - Health check endpoints

2. **Authentication** (`middleware/auth.py`)
   - API key authentication
   - SHA-256 key hashing
   - Redis caching (5-minute TTL)
   - Rate limit friendly

3. **Memory Service** (`services/memory_service.py`)
   - Agent management
   - Memory CRUD operations
   - Vector search
   - Integrity proof generation

4. **Storage Layer**
   - **PostgreSQL** (`storage/postgres.py`): Primary data store with pgvector
   - **Redis** (`storage/redis_cache.py`): Caching layer for performance

5. **Intelligence Layer** (`intelligence/`)
   - **Decay Engine**: Ebbinghaus forgetting curves
   - **Integrity Proofs**: SHA-256 + Merkle trees
   - **Belief Propagation**: Confidence update propagation
   - **Causal Reasoning**: Cause-effect relationships
   - **Compression**: Memory summarization
   - **Archival**: S3 backup for deleted memories

### Database Schema

- **Tenant**: Billing unit with API key
- **Agent**: AI agent belonging to tenant
- **EpisodicMemory**: Conversation history, actions
- **SemanticMemory**: Facts (subject-predicate-object triples)
- **ProceduralMemory**: Workflows, procedures, skills
- **UsageEvent**: Billing and analytics
- **MemoryAuditLog**: Cryptographic integrity proofs
- **CausalEdge**: Cause-effect relationships
- **SemanticEdge**: Belief propagation graph
- **SemanticPropagationLog**: Confidence update audit trail

### API Endpoints

#### Health & Status
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (DB + Redis)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

#### Episodic Memory
- `POST /v1/memory/episodic/remember` - Store episodic memory
- `POST /v1/memory/episodic/recall` - Search memories
- `DELETE /v1/memory/episodic/{memory_id}` - Delete memory

#### Semantic Memory
- `POST /v1/memory/semantic/facts` - Store semantic fact
- `POST /v1/memory/semantic/query` - Query facts
- `GET /v1/memory/semantic/graph` - Get knowledge graph

#### Procedural Memory
- `POST /v1/memory/procedural/store` - Store procedure
- `POST /v1/memory/procedural/match` - Find matching procedures
- `POST /v1/memory/procedural/outcome` - Record execution outcome

#### Search
- `POST /v1/search/unified` - Search across all memory types

#### Admin
- `POST /v1/admin/summarise` - Generate agent summary
- `GET /v1/admin/export` - Export all memories
- `POST /v1/admin/import` - Import memories

#### Causal Reasoning
- `POST /v1/memory/causal/edges` - Create causal relationship
- `GET /v1/memory/causal/chain` - Get causal chain

#### Trust & Integrity
- `POST /v1/trust/verify` - Verify memory integrity
- `GET /v1/trust/audit` - Get audit trail

---

## Security

### Authentication

The server uses **API key authentication** with the following security features:

- **SHA-256 hashing**: API keys are hashed before storage
- **Redis caching**: Authenticated requests cached for 5 minutes
- **Constant-time comparison**: Prevents timing attacks
- **Test key blocking**: Test keys blocked in production
- **Safe logging**: Only key prefixes logged, never full keys

### Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Row-Level Security (RLS)

PostgreSQL RLS ensures tenant isolation:
- Each tenant can only access their own data
- Enforced at database level
- Prevents data leakage even if application logic fails

### Integrity Proofs

Cryptographic integrity verification:
- **SHA-256 content hashing**: Detect tampering
- **Merkle trees**: Efficient batch verification
- **Audit logs**: Immutable audit trail

---

## Performance

### Benchmarks

- **Latency**: <50ms p95 for memory operations
- **Throughput**: 1000+ requests/second (single instance)
- **Concurrency**: Handles 100+ concurrent connections
- **Vector Search**: <100ms for 10k+ memories

### Optimization Features

- **Connection pooling**: Configurable pool size
- **Redis caching**: 5-minute TTL for hot data
- **Async operations**: Non-blocking I/O
- **Batch embedding**: Efficient ML inference
- **Prepared statements**: SQL query optimization
- **Indexes**: Optimized for common queries

---

## Production Deployment

### Environment Variables

See `.env.example` for full configuration options. Key variables:

```bash
# Required
KYROS_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
KYROS_REDIS_URL=redis://host:6379/0
KYROS_JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Recommended for production
KYROS_ENVIRONMENT=production
KYROS_DEBUG=false
KYROS_LOG_LEVEL=INFO
KYROS_ALLOWED_ORIGINS=https://yourdomain.com
```

### Docker Deployment

```bash
# Build production image
docker build --target production -t kyros-server:latest .

# Run with docker-compose
docker compose -f docker-compose.prod.yml up -d

# Or with Kubernetes
kubectl apply -f k8s/
```

### Database Setup

```bash
# Create database with pgvector extension
psql -U postgres -c "CREATE DATABASE kyros;"
psql -U postgres -d kyros -c "CREATE EXTENSION vector;"

# Run migrations
alembic upgrade head
```

### Health Checks

Configure your load balancer to use:
- **Liveness**: `GET /health` (returns 200 if server is running)
- **Readiness**: `GET /health/ready` (returns 200 if DB + Redis are accessible)

### Monitoring

The server provides structured JSON logs for easy integration with:
- **Datadog**: Use Datadog agent with JSON log parsing
- **ELK Stack**: Logstash can parse JSON logs directly
- **CloudWatch**: Use CloudWatch Logs with JSON parsing
- **Grafana Loki**: Native JSON support

Key metrics to monitor:
- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Redis cache hit rate
- Memory usage
- CPU usage

---

## Testing

### Test Coverage

- **Integration Tests**: End-to-end API testing
- **Unit Tests**: Component-level testing
- **Load Tests**: Performance and stress testing

### Running Tests

```bash
# All tests with coverage report
pytest --cov=kyros --cov-report=html

# Integration tests only
pytest tests/integration/ -v

# Unit tests only
pytest tests/unit/ -v

# Specific test file
pytest tests/integration/test_episodic_roundtrip.py -v

# With markers
pytest -m "not slow" -v
```

### Test Markers

- `@pytest.mark.integration` - Integration tests (require DB + Redis)
- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.slow` - Slow tests (skip in quick runs)

---

## Troubleshooting

### Common Issues

#### Database Connection Fails

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection string
echo $KYROS_DATABASE_URL

# Test connection
psql $KYROS_DATABASE_URL -c "SELECT 1;"
```

#### Redis Connection Fails

```bash
# Check Redis is running
docker compose ps redis

# Test connection
redis-cli -u $KYROS_REDIS_URL ping
```

#### Migrations Fail

```bash
# Check current revision
alembic current

# View migration history
alembic history

# Rollback and retry
alembic downgrade -1
alembic upgrade head
```

#### Embedding Model Download Fails

```bash
# Check internet connection
curl -I https://huggingface.co

# Manually download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

---

## Additional Resources

- **Root README**: `../README.md` - Project overview and quick start
- **API Documentation**: http://localhost:8000/docs (when server is running)
- **Contributing Guide**: `../CONTRIBUTING.md` - How to contribute
- **Security Policy**: `../SECURITY.md` - Security reporting
- **Changelog**: `../CHANGELOG.md` - Version history

---

## Contributing

We welcome contributions! Please see the [Contributing Guide](../CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `make test`
5. Run linting: `make lint`
6. Commit with conventional commits: `git commit -m "feat: add new feature"`
7. Push and create a pull request

---

## License

The Kyros server is licensed under the **Apache License 2.0**. See [LICENSE](../LICENSE) for details.

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [PostgreSQL](https://www.postgresql.org/) - Powerful database
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search
- [Redis](https://redis.io/) - In-memory data store
- [Sentence Transformers](https://www.sbert.net/) - Embedding models

---

**Made with ❤️ by the Kyros team**
