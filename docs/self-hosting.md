# Self-Hosting Guide

Complete guide to deploying Kyros on your own infrastructure.

## Overview

Kyros can be self-hosted on any infrastructure that supports Docker containers. This guide covers deployment options from simple Docker Compose setups to production-grade Kubernetes clusters.

## Prerequisites

### Required

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher (for Docker Compose deployment)
- **PostgreSQL**: 16 or higher with pgvector extension
- **Redis**: 7 or higher

### Recommended for Production

- **Kubernetes**: 1.24 or higher (for Kubernetes deployment)
- **Load Balancer**: Nginx, Caddy, or cloud provider load balancer
- **SSL/TLS Certificates**: Let's Encrypt or commercial certificate
- **Monitoring**: Prometheus, Grafana, or cloud provider monitoring
- **Log Aggregation**: ELK Stack, Loki, or cloud provider logging

## Quick Start with Docker Compose

The fastest way to get Kyros running locally or on a single server.

### Step 1: Clone Repository

```bash
git clone https://github.com/Kyros-494/kyros-ai.git
cd kyros-ai
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Configuration:**

```bash
# Generate a secure JWT secret
KYROS_JWT_SECRET_KEY=$(openssl rand -hex 32)

# Set strong database password
KYROS_DATABASE_URL=postgresql+asyncpg://kyros:YOUR_STRONG_PASSWORD@postgres:5432/kyros
KYROS_DB_APP_PASSWORD=YOUR_STRONG_PASSWORD

# Redis configuration
KYROS_REDIS_URL=redis://redis:6379/0

# Environment
KYROS_ENVIRONMENT=production
KYROS_DEBUG=false
KYROS_LOG_LEVEL=INFO
```

### Step 3: Start Services

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f kyros-server
```

### Step 4: Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check readiness (DB + Redis)
curl http://localhost:8000/health/ready

# View API documentation
open http://localhost:8000/docs
```

### Step 5: Create First API Key

```bash
# Access the database
docker compose exec postgres psql -U kyros -d kyros

# Create a tenant and API key
INSERT INTO tenants (tenant_id, name, api_key_hash, tier, created_at)
VALUES (
  'tenant-001',
  'My Organization',
  encode(digest('mk_live_your_secret_key', 'sha256'), 'hex'),
  'pro',
  NOW()
);

# Exit psql
\q
```

### Step 6: Test API

```bash
# Store a memory
curl -X POST http://localhost:8000/v1/memory/episodic/remember \
  -H "Authorization: Bearer mk_live_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "content": "Hello from Kyros!"
  }'

# Recall memories
curl -X POST http://localhost:8000/v1/memory/episodic/recall \
  -H "Authorization: Bearer mk_live_your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "query": "hello"
  }'
```

## Docker Compose Configuration

### Basic Configuration

The default `docker-compose.yml` includes:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: kyros
      POSTGRES_PASSWORD: ${KYROS_DB_APP_PASSWORD}
      POSTGRES_DB: kyros
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  kyros-server:
    build:
      context: ./server
      target: ${KYROS_BUILD_TARGET:-production}
    environment:
      KYROS_DATABASE_URL: ${KYROS_DATABASE_URL}
      KYROS_REDIS_URL: ${KYROS_REDIS_URL}
      KYROS_JWT_SECRET_KEY: ${KYROS_JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Production Configuration

For production, create `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: kyros
      POSTGRES_PASSWORD: ${KYROS_DB_APP_PASSWORD}
      POSTGRES_DB: kyros
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kyros"]
      interval: 10s
      timeout: 5s
      retries: 5
    # Do not expose port publicly
    networks:
      - kyros-internal

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - kyros-internal

  kyros-server:
    build:
      context: ./server
      target: production
    environment:
      KYROS_DATABASE_URL: ${KYROS_DATABASE_URL}
      KYROS_REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      KYROS_JWT_SECRET_KEY: ${KYROS_JWT_SECRET_KEY}
      KYROS_ENVIRONMENT: production
      KYROS_DEBUG: false
      KYROS_LOG_LEVEL: INFO
      KYROS_ALLOWED_ORIGINS: ${KYROS_ALLOWED_ORIGINS}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - kyros-internal
      - kyros-public

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - kyros-server
    restart: unless-stopped
    networks:
      - kyros-public

networks:
  kyros-internal:
    driver: bridge
  kyros-public:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

## Kubernetes Deployment

For production-grade deployments with high availability and scalability.

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3 (optional but recommended)

### Step 1: Create Namespace

```bash
kubectl create namespace kyros
```

### Step 2: Create Secrets

```bash
# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Create secret
kubectl create secret generic kyros-secrets \
  --from-literal=jwt-secret=$JWT_SECRET \
  --from-literal=db-password=$(openssl rand -hex 16) \
  --from-literal=redis-password=$(openssl rand -hex 16) \
  --namespace=kyros
```

### Step 3: Deploy PostgreSQL

Create `postgres-deployment.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: kyros
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: kyros
spec:
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
        image: pgvector/pgvector:pg16
        env:
        - name: POSTGRES_USER
          value: kyros
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: kyros-secrets
              key: db-password
        - name: POSTGRES_DB
          value: kyros
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: kyros
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

Apply:

```bash
kubectl apply -f postgres-deployment.yaml
```

### Step 4: Deploy Redis

Create `redis-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: kyros
spec:
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
        command:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        - --appendonly
        - "yes"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: kyros-secrets
              key: redis-password
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: kyros
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

Apply:

```bash
kubectl apply -f redis-deployment.yaml
```

### Step 5: Deploy Kyros Server

Create `kyros-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kyros-server
  namespace: kyros
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kyros-server
  template:
    metadata:
      labels:
        app: kyros-server
    spec:
      containers:
      - name: kyros-server
        image: kyros/server:latest
        env:
        - name: KYROS_DATABASE_URL
          value: postgresql+asyncpg://kyros:$(DB_PASSWORD)@postgres:5432/kyros
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: kyros-secrets
              key: db-password
        - name: KYROS_REDIS_URL
          value: redis://:$(REDIS_PASSWORD)@redis:6379/0
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: kyros-secrets
              key: redis-password
        - name: KYROS_JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: kyros-secrets
              key: jwt-secret
        - name: KYROS_ENVIRONMENT
          value: production
        - name: KYROS_DEBUG
          value: "false"
        - name: KYROS_LOG_LEVEL
          value: INFO
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: kyros-server
  namespace: kyros
spec:
  selector:
    app: kyros-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Apply:

```bash
kubectl apply -f kyros-deployment.yaml
```

### Step 6: Configure Ingress (Optional)

Create `ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kyros-ingress
  namespace: kyros
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.kyros.yourdomain.com
    secretName: kyros-tls
  rules:
  - host: api.kyros.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kyros-server
            port:
              number: 80
```

Apply:

```bash
kubectl apply -f ingress.yaml
```

## Reverse Proxy Configuration

### Nginx

Create `/etc/nginx/sites-available/kyros`:

```nginx
upstream kyros_backend {
    server localhost:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name api.kyros.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.kyros.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.kyros.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.kyros.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/kyros-access.log;
    error_log /var/log/nginx/kyros-error.log;

    # Proxy Configuration
    location / {
        proxy_pass http://kyros_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
    limit_req zone=api_limit burst=200 nodelay;
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/kyros /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Caddy

Create `Caddyfile`:

```caddy
api.kyros.yourdomain.com {
    reverse_proxy localhost:8000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    # Security Headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
    }

    # Logging
    log {
        output file /var/log/caddy/kyros-access.log
    }

    # Rate Limiting
    rate_limit {
        zone api {
            key {remote_host}
            events 100
            window 1s
        }
    }
}
```

Start Caddy:

```bash
sudo caddy run --config Caddyfile
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.kyros.yourdomain.com

# Auto-renewal (already configured by Certbot)
sudo certbot renew --dry-run
```

### Manual Certificate

```bash
# Generate private key
openssl genrsa -out kyros.key 2048

# Generate CSR
openssl req -new -key kyros.key -out kyros.csr

# Submit CSR to certificate authority
# Receive certificate files: kyros.crt, intermediate.crt

# Combine certificates
cat kyros.crt intermediate.crt > kyros-fullchain.crt

# Configure in Nginx
ssl_certificate /etc/ssl/certs/kyros-fullchain.crt;
ssl_certificate_key /etc/ssl/private/kyros.key;
```

## Database Management

### Backups

#### Automated Backups

Create `/usr/local/bin/backup-kyros-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/kyros"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/kyros_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR

# Backup database
docker compose exec -T postgres pg_dump -U kyros kyros | gzip > $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "kyros_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-kyros-db.sh
```

#### Manual Backup

```bash
# Backup
docker compose exec postgres pg_dump -U kyros kyros > kyros_backup.sql

# Compressed backup
docker compose exec postgres pg_dump -U kyros kyros | gzip > kyros_backup.sql.gz
```

### Restore

```bash
# Restore from backup
docker compose exec -T postgres psql -U kyros kyros < kyros_backup.sql

# Restore from compressed backup
gunzip -c kyros_backup.sql.gz | docker compose exec -T postgres psql -U kyros kyros
```

### Migrations

```bash
# Run migrations
docker compose exec kyros-server alembic upgrade head

# Rollback one migration
docker compose exec kyros-server alembic downgrade -1

# View migration history
docker compose exec kyros-server alembic history

# View current revision
docker compose exec kyros-server alembic current
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Readiness check (DB + Redis)
curl http://localhost:8000/health/ready

# Detailed status
curl http://localhost:8000/health/ready | jq
```

### Prometheus Metrics

Add to `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kyros'
    static_configs:
      - targets: ['kyros-server:8000']
```

### Log Aggregation

#### ELK Stack

Add to `docker-compose.yml`:

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## Scaling

### Horizontal Scaling

Scale Kyros server instances:

```bash
# Docker Compose
docker compose up -d --scale kyros-server=3

# Kubernetes
kubectl scale deployment kyros-server --replicas=5 -n kyros
```

### Database Scaling

#### Read Replicas

Configure PostgreSQL replication:

```yaml
services:
  postgres-primary:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: kyros
      POSTGRES_PASSWORD: ${KYROS_DB_APP_PASSWORD}
      POSTGRES_DB: kyros
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}

  postgres-replica:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_MASTER_SERVICE_HOST: postgres-primary
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
```

### Redis Scaling

#### Redis Cluster

```yaml
services:
  redis-node-1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf

  redis-node-2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf

  redis-node-3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
```

## Security Hardening

### Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### Database Security

```sql
-- Create read-only user
CREATE USER kyros_readonly WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE kyros TO kyros_readonly;
GRANT USAGE ON SCHEMA public TO kyros_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO kyros_readonly;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/server.key';
```

### Redis Security

```bash
# Enable password authentication
redis-cli CONFIG SET requirepass "strong_password"

# Disable dangerous commands
redis-cli CONFIG SET rename-command FLUSHDB ""
redis-cli CONFIG SET rename-command FLUSHALL ""
redis-cli CONFIG SET rename-command CONFIG ""
```

## Troubleshooting

### Server Won't Start

```bash
# Check logs
docker compose logs kyros-server

# Check database connection
docker compose exec kyros-server python -c "from kyros.storage.postgres import get_db; print('DB OK')"

# Check Redis connection
docker compose exec kyros-server python -c "from kyros.storage.redis_cache import get_redis; print('Redis OK')"
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U kyros -d kyros -c "SELECT 1;"

# Check pgvector extension
docker compose exec postgres psql -U kyros -d kyros -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Redis Connection Issues

```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping

# Check memory usage
docker compose exec redis redis-cli INFO memory
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check database performance
docker compose exec postgres psql -U kyros -d kyros -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
docker compose exec postgres psql -U kyros -d kyros -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## Maintenance

### Updates

```bash
# Pull latest images
docker compose pull

# Restart services
docker compose up -d

# Run migrations
docker compose exec kyros-server alembic upgrade head
```

### Cleanup

```bash
# Remove old Docker images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove old logs
find /var/log/kyros -name "*.log" -mtime +30 -delete
```

## Support

For additional help:

- [GitHub Issues](https://github.com/Kyros-494/kyros-ai/issues)
- [Documentation](https://docs.kyros.ai)
- [Community Discord](https://discord.gg/kyros)
