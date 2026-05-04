
# Configuration Reference

Complete reference for all Kyros environment variables and configuration options.

## Overview

Kyros is configured through environment variables defined in a `.env` file. This approach follows the [Twelve-Factor App](https://12factor.net/) methodology and makes configuration portable across environments.

## Setup

### Initial Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit with your values
nano .env
```

### Security Best Practices

- Never commit `.env` to version control
- Use strong, randomly generated secrets
- Rotate credentials regularly (every 90 days minimum)
- Use different credentials for each environment
- Store production secrets in a secrets manager (AWS Secrets Manager, HashiCorp Vault)

## Application Configuration

### KYROS_APP_NAME

**Type:** String  
**Default:** `Kyros`  
**Required:** No

Application name used in logs and monitoring.

```bash
KYROS_APP_NAME=Kyros
```

### KYROS_ENVIRONMENT

**Type:** String  
**Default:** `development`  
**Required:** Yes  
**Options:** `development`, `staging`, `production`

Environment mode that affects logging, error handling, and performance optimizations.

**Development:**
- Enables debug features
- Verbose logging
- Detailed error messages
- Hot reload enabled

**Staging:**
- Production-like environment
- Standard logging
- Error tracking enabled
- Performance monitoring

**Production:**
- Optimized for performance
- Minimal logging
- Error tracking enabled
- Security hardening

```bash
# Development
KYROS_ENVIRONMENT=development

# Production
KYROS_ENVIRONMENT=production
```

### KYROS_DEBUG

**Type:** Boolean  
**Default:** `false`  
**Required:** No

Enable debug mode for detailed error messages and stack traces.

**WARNING:** Never enable in production as it exposes sensitive information.

```bash
# Development
KYROS_DEBUG=true

# Production
KYROS_DEBUG=false
```

### KYROS_LOG_LEVEL

**Type:** String  
**Default:** `INFO`  
**Required:** No  
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Logging verbosity level.

**DEBUG:** Verbose logging for development (includes SQL queries, cache hits/misses)  
**INFO:** Standard operational logging (recommended for production)  
**WARNING:** Only warnings and errors  
**ERROR:** Only errors and critical issues  
**CRITICAL:** Only critical failures

```bash
# Development
KYROS_LOG_LEVEL=DEBUG

# Production
KYROS_LOG_LEVEL=INFO
```

## Database Configuration

### KYROS_DATABASE_URL

**Type:** String  
**Required:** Yes

PostgreSQL connection URL with asyncpg driver.

**Format:**
```
postgresql+asyncpg://username:password@host:port/database
```

**Production Recommendations:**
- Use strong password (minimum 32 characters)
- Enable SSL/TLS: add `?ssl=require` to URL
- Use managed database service (AWS RDS, Google Cloud SQL)
- Enable automated backups
- Configure connection pooling

```bash
# Development
KYROS_DATABASE_URL=postgresql+asyncpg://kyros:password@localhost:5433/kyros

# Production with SSL
KYROS_DATABASE_URL=postgresql+asyncpg://kyros:strong_password@db.example.com:5432/kyros?ssl=require
```

### KYROS_DB_POOL_SIZE

**Type:** Integer  
**Default:** `10`  
**Required:** No

Maximum number of database connections in the pool.

**Recommendations:**
- Development: 5-10 connections
- Production: 20-50 connections (adjust based on load)
- Formula: `(CPU cores * 2) + effective_spindle_count`

```bash
# Development
KYROS_DB_POOL_SIZE=10

# Production
KYROS_DB_POOL_SIZE=30
```

### KYROS_DB_MAX_OVERFLOW

**Type:** Integer  
**Default:** `20`  
**Required:** No

Maximum overflow connections beyond pool size for handling traffic spikes.

**Recommendations:**
- Development: 10-20
- Production: 30-100 (adjust based on traffic patterns)

```bash
# Development
KYROS_DB_MAX_OVERFLOW=20

# Production
KYROS_DB_MAX_OVERFLOW=50
```

### KYROS_DB_APP_PASSWORD

**Type:** String  
**Required:** Yes

Database password for the application user. Must match the password in `KYROS_DATABASE_URL`.

Used by database migrations for row-level security setup.

```bash
KYROS_DB_APP_PASSWORD=your_strong_password
```

## Redis Configuration

### KYROS_REDIS_URL

**Type:** String  
**Required:** Yes

Redis connection URL for caching and session storage.

**Format:**
```
redis://[username:password@]host:port/database
```

**Production Recommendations:**
- Enable password authentication
- Use Redis 6+ with ACL for fine-grained access control
- Enable TLS: use `rediss://` (note the 's')
- Use managed Redis service (AWS ElastiCache, Redis Cloud)
- Configure maxmemory and eviction policy
- Enable persistence (AOF or RDB)

```bash
# Development (no auth)
KYROS_REDIS_URL=redis://localhost:6379/0

# Production with auth
KYROS_REDIS_URL=redis://:your_redis_password@localhost:6379/0

# Production with TLS
KYROS_REDIS_URL=rediss://:your_redis_password@redis.example.com:6380/0
```

## Authentication & Security

### KYROS_JWT_SECRET_KEY

**Type:** String  
**Required:** Yes  
**Minimum Length:** 32 characters

Secret key for signing JWT tokens.

**CRITICAL SECURITY:**
- Generate with: `openssl rand -hex 32`
- Must be at least 32 characters
- Never reuse across environments
- Rotate regularly (requires re-authentication)
- Store in secrets manager in production

```bash
# Generate secure secret
KYROS_JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### KYROS_JWT_ALGORITHM

**Type:** String  
**Default:** `HS256`  
**Required:** No  
**Options:** `HS256`, `RS256`

JWT signing algorithm.

**HS256 (Symmetric):**
- Faster performance
- Simpler setup
- Uses shared secret
- Suitable for single-server deployments

**RS256 (Asymmetric):**
- More secure
- Uses public/private key pair
- Recommended for production
- Required for distributed systems

```bash
# Development
KYROS_JWT_ALGORITHM=HS256

# Production
KYROS_JWT_ALGORITHM=RS256
```

### KYROS_JWT_EXPIRY_MINUTES

**Type:** Integer  
**Default:** `60`  
**Required:** No

JWT token expiration time in minutes.

**Recommendations:**
- Development: 60-1440 (1 hour to 1 day)
- Production: 15-60 (15 minutes to 1 hour)

Shorter expiration = more secure but more frequent re-authentication.

```bash
# Development
KYROS_JWT_EXPIRY_MINUTES=1440

# Production
KYROS_JWT_EXPIRY_MINUTES=30
```

## CORS Configuration

### KYROS_ALLOWED_ORIGINS

**Type:** String (comma-separated)  
**Default:** `*`  
**Required:** No

Allowed origins for Cross-Origin Resource Sharing (CORS) requests.

**SECURITY WARNING:** Never use `*` in production!

```bash
# Development (allow all)
KYROS_ALLOWED_ORIGINS=*

# Production (specific domains)
KYROS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com

# Production (with subdomains)
KYROS_ALLOWED_ORIGINS=https://app.example.com,https://*.example.com
```

## Embedding Models

### KYROS_EMBEDDING_MODEL

**Type:** String  
**Default:** `all-MiniLM-L6-v2`  
**Required:** No

Primary embedding model for vector search.

**Available Models:**

| Model | Dimensions | Size | Quality | Speed |
|-------|------------|------|---------|-------|
| all-MiniLM-L6-v2 | 384 | 80MB | Good | Fast |
| all-mpnet-base-v2 | 768 | 420MB | Better | Medium |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 470MB | Good | Medium |

**Production Considerations:**
- Larger models = better quality but slower inference
- Consider GPU acceleration for high-throughput
- Model is cached after first download
- No API key required (runs locally)

```bash
# Fast, good quality (default)
KYROS_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Better quality, slower
KYROS_EMBEDDING_MODEL=all-mpnet-base-v2

# Multilingual support
KYROS_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

### KYROS_EMBEDDING_DIMENSION

**Type:** Integer  
**Default:** `384`  
**Required:** No

Embedding vector dimension. Must match the selected model.

| Model | Dimension |
|-------|-----------|
| all-MiniLM-L6-v2 | 384 |
| all-mpnet-base-v2 | 768 |
| text-embedding-ada-002 | 1536 |

```bash
KYROS_EMBEDDING_DIMENSION=384
```

### KYROS_SECONDARY_EMBEDDING_MODEL

**Type:** String  
**Required:** No

Secondary embedding model for dual-embedding strategy.

Enables model portability by storing embeddings from two models simultaneously.

```bash
# Disable dual embeddings (default)
KYROS_SECONDARY_EMBEDDING_MODEL=

# Enable dual embeddings
KYROS_SECONDARY_EMBEDDING_MODEL=all-mpnet-base-v2
```

## LLM Provider API Keys

**Note:** LLM API keys are OPTIONAL. The core memory engine works without them.

Required only for:
- Causal edge extraction
- LLM-based memory compression
- Advanced semantic analysis

### OPENAI_API_KEY

**Type:** String  
**Required:** No

OpenAI API key for GPT models.

**Get from:** https://platform.openai.com/api-keys

**Models:** gpt-4, gpt-3.5-turbo, text-embedding-ada-002

```bash
OPENAI_API_KEY=sk-...
```

### GEMINI_API_KEY

**Type:** String  
**Required:** No

Google Gemini API key.

**Get from:** https://makersuite.google.com/app/apikey

**Models:** gemini-pro, gemini-pro-vision

```bash
GEMINI_API_KEY=...
```

### ANTHROPIC_API_KEY

**Type:** String  
**Required:** No

Anthropic API key for Claude models.

**Get from:** https://console.anthropic.com/

**Models:** claude-3-opus, claude-3-sonnet, claude-3-haiku

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## Proxy Server Configuration

### KYROS_PROXY_ADMIN_TOKEN

**Type:** String  
**Required:** No

Admin token for runtime proxy configuration API.

Required for `GET/PUT /proxy/config` endpoints. If unset, runtime configuration is disabled.

**Security:**
- Generate with: `openssl rand -hex 32`
- Use different token than JWT secret
- Restrict access to admin users only
- Rotate regularly

```bash
KYROS_PROXY_ADMIN_TOKEN=$(openssl rand -hex 32)
```

## Memory Compression

### KYROS_COMPRESSION_LLM_PROVIDER

**Type:** String  
**Default:** `extractive`  
**Required:** No  
**Options:** `extractive`, `openai`, `anthropic`, `gemini`

Compression strategy for memory summarization.

**extractive:** Fast local compression (no API key needed, default)  
**openai:** Use OpenAI for summarization (requires OPENAI_API_KEY)  
**anthropic:** Use Anthropic Claude (requires ANTHROPIC_API_KEY)  
**gemini:** Use Google Gemini (requires GEMINI_API_KEY)

**Cost Considerations:**
- extractive: Free, fast, but less sophisticated
- LLM-based: Better quality but costs API credits

```bash
# Free local compression
KYROS_COMPRESSION_LLM_PROVIDER=extractive

# OpenAI-based compression
KYROS_COMPRESSION_LLM_PROVIDER=openai
```

### KYROS_COMPRESSION_LLM_API_KEY

**Type:** String  
**Required:** No (only if using LLM-based compression)

API key for LLM-based compression. Can be same as provider keys or separate key with lower rate limits.

```bash
KYROS_COMPRESSION_LLM_API_KEY=sk-...
```

### KYROS_COMPRESSION_LLM_MODEL

**Type:** String  
**Required:** No (only if using LLM-based compression)

LLM model for compression.

**Examples:**
- OpenAI: `gpt-3.5-turbo`, `gpt-4`
- Anthropic: `claude-3-haiku`, `claude-3-sonnet`
- Gemini: `gemini-pro`

```bash
KYROS_COMPRESSION_LLM_MODEL=gpt-3.5-turbo
```

## Stripe Billing Integration

**Note:** Only needed if building a SaaS product on top of Kyros.

### KYROS_STRIPE_API_KEY

**Type:** String  
**Required:** No

Stripe API key for billing and subscription management.

**Get from:** https://dashboard.stripe.com/apikeys

**Use test key (`sk_test_...`) for development**  
**Use live key (`sk_live_...`) for production**

```bash
# Development
KYROS_STRIPE_API_KEY=sk_test_...

# Production
KYROS_STRIPE_API_KEY=sk_live_...
```

### KYROS_STRIPE_WEBHOOK_SECRET

**Type:** String  
**Required:** No (only if using Stripe)

Stripe webhook secret for verifying webhook signatures.

**Get from:** https://dashboard.stripe.com/webhooks

**Format:** `whsec_...`

```bash
KYROS_STRIPE_WEBHOOK_SECRET=whsec_...
```

## Memory Archival (S3)

**Note:** Optional feature for compliance with data retention policies.

### KYROS_ARCHIVE_BUCKET

**Type:** String  
**Required:** No

S3 bucket name for archived memories.

Deleted memories are moved to S3 instead of permanent deletion.

```bash
KYROS_ARCHIVE_BUCKET=kyros-memory-archive
```

### AWS_REGION

**Type:** String  
**Required:** No (only if using S3 archival)

AWS region for S3 bucket.

```bash
AWS_REGION=us-east-1
```

### AWS_ACCESS_KEY_ID

**Type:** String  
**Required:** No (only if using S3 archival)

AWS access key ID. Use IAM roles in production instead.

```bash
AWS_ACCESS_KEY_ID=AKIA...
```

### AWS_SECRET_ACCESS_KEY

**Type:** String  
**Required:** No (only if using S3 archival)

AWS secret access key. Use IAM roles in production instead.

```bash
AWS_SECRET_ACCESS_KEY=...
```

## Additional Configuration

### NEXT_PUBLIC_SITE_URL

**Type:** String  
**Required:** No

Public site URL for metadata and redirects.

```bash
NEXT_PUBLIC_SITE_URL=https://kyros.ai
```

### NEXT_PUBLIC_API_URL

**Type:** String  
**Required:** No

API base URL for SDKs and frontend.

```bash
NEXT_PUBLIC_API_URL=https://api.kyros.ai
```

## Environment-Specific Examples

### Development Environment

```bash
# Application
KYROS_APP_NAME=Kyros
KYROS_ENVIRONMENT=development
KYROS_DEBUG=true
KYROS_LOG_LEVEL=DEBUG

# Database
KYROS_DATABASE_URL=postgresql+asyncpg://kyros:dev_password@localhost:5433/kyros
KYROS_DB_POOL_SIZE=5
KYROS_DB_MAX_OVERFLOW=10
KYROS_DB_APP_PASSWORD=dev_password

# Redis
KYROS_REDIS_URL=redis://localhost:6379/0

# Security
KYROS_JWT_SECRET_KEY=dev_secret_key_not_for_production
KYROS_JWT_ALGORITHM=HS256
KYROS_JWT_EXPIRY_MINUTES=1440

# CORS
KYROS_ALLOWED_ORIGINS=*

# Embedding
KYROS_EMBEDDING_MODEL=all-MiniLM-L6-v2
KYROS_EMBEDDING_DIMENSION=384
```

### Production Environment

```bash
# Application
KYROS_APP_NAME=Kyros
KYROS_ENVIRONMENT=production
KYROS_DEBUG=false
KYROS_LOG_LEVEL=INFO

# Database
KYROS_DATABASE_URL=postgresql+asyncpg://kyros:STRONG_PASSWORD@db.example.com:5432/kyros?ssl=require
KYROS_DB_POOL_SIZE=30
KYROS_DB_MAX_OVERFLOW=50
KYROS_DB_APP_PASSWORD=STRONG_PASSWORD

# Redis
KYROS_REDIS_URL=rediss://:REDIS_PASSWORD@redis.example.com:6380/0

# Security
KYROS_JWT_SECRET_KEY=GENERATED_WITH_OPENSSL_RAND_HEX_32
KYROS_JWT_ALGORITHM=RS256
KYROS_JWT_EXPIRY_MINUTES=30

# CORS
KYROS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com

# Embedding
KYROS_EMBEDDING_MODEL=all-mpnet-base-v2
KYROS_EMBEDDING_DIMENSION=768

# LLM (optional)
OPENAI_API_KEY=sk-...

# Monitoring
NEXT_PUBLIC_SITE_URL=https://kyros.example.com
NEXT_PUBLIC_API_URL=https://api.kyros.example.com
```

## Production Deployment Checklist

Before deploying to production, verify:

- [ ] Replace all `CHANGE_ME` placeholders with strong, random values
- [ ] Set `KYROS_ENVIRONMENT=production`
- [ ] Set `KYROS_DEBUG=false`
- [ ] Set `KYROS_LOG_LEVEL=INFO` or `WARNING`
- [ ] Configure `KYROS_ALLOWED_ORIGINS` with specific domains (not `*`)
- [ ] Enable database SSL/TLS
- [ ] Enable Redis authentication and TLS
- [ ] Use secrets manager for sensitive values
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Test disaster recovery procedures
- [ ] Review and apply security headers
- [ ] Enable rate limiting
- [ ] Set up log aggregation
- [ ] Configure health check endpoints
- [ ] Document runbook procedures

## Security Reminders

- Never commit `.env` to version control
- Rotate secrets regularly (every 90 days minimum)
- Use different credentials for each environment
- Enable MFA on all cloud provider accounts
- Audit access logs regularly
- Keep dependencies updated
- Run security scans regularly
- Use principle of least privilege
- Enable encryption at rest and in transit
- Implement proper backup and disaster recovery

## Troubleshooting

### Configuration Not Loading

```bash
# Check .env file exists
ls -la .env

# Check file permissions
chmod 600 .env

# Verify environment variables are set
docker compose config
```

### Database Connection Fails

```bash
# Test connection string
psql "$KYROS_DATABASE_URL" -c "SELECT 1;"

# Check SSL requirement
psql "$KYROS_DATABASE_URL?ssl=require" -c "SELECT 1;"
```

### Redis Connection Fails

```bash
# Test connection
redis-cli -u "$KYROS_REDIS_URL" ping

# Test with password
redis-cli -u "redis://:password@localhost:6379/0" ping
```

## Links

- [Environment Variables Best Practices](https://12factor.net/config)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
- [Redis Connection URLs](https://redis.io/docs/manual/cli/#host-port-password-and-database)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
