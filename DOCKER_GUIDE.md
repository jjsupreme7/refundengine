# Docker Guide

## Overview

Run the entire Refund Engine stack with Docker - no manual dependency installation needed.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (macOS/Windows)
- OR Docker Engine (Linux)
- OR [Colima](https://github.com/abiosoft/colima) (lightweight macOS alternative)

## Quick Start

### 1. Build the image
```bash
docker build -t refund-engine .
```

### 2. Run tests
```bash
docker run --rm refund-engine pytest tests/ -v
```

### 3. Start full stack
```bash
docker-compose up
```

This starts:
- ✅ Redis (message broker)
- ✅ PostgreSQL (optional local database)
- ✅ Celery workers (10 parallel workers)
- ✅ Flower (monitoring UI at http://localhost:5555)
- ✅ Main app

## Services

### Redis (Message Broker)
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Check queue size
docker-compose exec redis redis-cli LLEN celery
```

### PostgreSQL (Optional Local Database)
```bash
# Access database
docker-compose exec postgres psql -U postgres -d refund_engine

# Create tables
docker-compose exec postgres psql -U postgres -d refund_engine -f /app/database/schema.sql
```

### Celery Workers
```bash
# View worker logs
docker-compose logs -f worker

# Scale workers
docker-compose up --scale worker=5

# Restart workers
docker-compose restart worker
```

### Flower (Monitoring UI)
```bash
# Open in browser
open http://localhost:5555
```

## Common Commands

### Start services
```bash
# Start all services in background
docker-compose up -d

# Start specific service
docker-compose up redis

# Start with custom concurrency
docker-compose up --scale worker=3
```

### Stop services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100
```

### Run commands inside container
```bash
# Run tests
docker-compose run test

# Run analyzer
docker-compose run app python scripts/async_analyzer.py --list-workers

# Interactive shell
docker-compose run app bash
```

## Development Workflow

### 1. Code locally, test in Docker
```bash
# Edit code on your machine
# Then test in clean Docker environment:
docker-compose run test
```

### 2. Hot reloading (changes reflected immediately)
```yaml
# docker-compose.yml already has volumes mounted:
volumes:
  - ./core:/app/core
  - ./scripts:/app/scripts
  - ./analysis:/app/analysis
```

### 3. Run specific tests
```bash
docker-compose run test pytest tests/test_refund_calculations.py -v
```

## Production Deployment

### Build for production
```bash
# Build with tag
docker build -t refund-engine:v1.0.0 .

# Push to registry
docker tag refund-engine:v1.0.0 myregistry/refund-engine:v1.0.0
docker push myregistry/refund-engine:v1.0.0
```

### Deploy to cloud

**AWS ECS:**
```bash
# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Run task
aws ecs run-task --cluster refund-engine --task-definition refund-engine:1
```

**Azure Container Instances:**
```bash
az container create \
  --resource-group refund-engine \
  --name refund-engine \
  --image myregistry/refund-engine:v1.0.0 \
  --environment-variables OPENAI_API_KEY=$OPENAI_API_KEY
```

**Google Cloud Run:**
```bash
gcloud run deploy refund-engine \
  --image gcr.io/myproject/refund-engine:v1.0.0 \
  --platform managed
```

## Environment Variables

Create `.env` file:
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# Redis (optional, defaults to redis://redis:6379/0)
REDIS_URL=redis://localhost:6379/0

# PostgreSQL (optional for local dev)
DB_PASSWORD=securepassword123
```

Load in docker-compose:
```yaml
services:
  worker:
    env_file:
      - .env
```

## Volumes

### Persistent data
```yaml
volumes:
  redis-data:      # Redis data
  postgres-data:   # PostgreSQL data
```

### Shared folders
```yaml
volumes:
  - ./client_documents:/app/client_documents  # Invoices
  - ./outputs:/app/outputs                     # Results
  - ./knowledge_base:/app/knowledge_base       # Legal docs
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs worker

# Check image
docker images | grep refund-engine

# Rebuild
docker-compose build --no-cache
```

### Out of memory
```bash
# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory > 8GB

# Or reduce worker concurrency
docker-compose up --scale worker=1
```

### Permission errors
```bash
# Fix permissions
chmod -R 755 client_documents outputs

# Or run as root (not recommended for production)
docker-compose run --user root app bash
```

### Network errors
```bash
# Check if services can talk to each other
docker-compose exec worker ping redis
docker-compose exec worker ping postgres

# Recreate network
docker-compose down
docker-compose up
```

## Optimization

### Multi-stage builds (reduce image size)
```dockerfile
# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . /app
WORKDIR /app
```

### Layer caching
```dockerfile
# Copy requirements first (changes less frequently)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes frequently)
COPY . .
```

## CI/CD Integration

### GitHub Actions
See `.github/workflows/docker.yml`:
```yaml
- name: Build Docker image
  run: docker build -t refund-engine .

- name: Test in Docker
  run: docker run --rm refund-engine pytest tests/
```

### GitLab CI
```.gitlab-ci.yml
build:
  script:
    - docker build -t refund-engine .

test:
  script:
    - docker run --rm refund-engine pytest tests/
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Best Practices for Dockerfiles](https://docs.docker.com/develop/dev-best-practices/)
