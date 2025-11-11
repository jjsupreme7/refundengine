# Production Setup Guide

## Overview

Complete guide to setting up the Refund Engine for production use with all 4 critical components:
1. ✅ Testing (pytest + coverage)
2. ✅ Message Queue (Celery + Redis)
3. ✅ Docker (containerization)
4. ✅ CI/CD (GitHub Actions)

## Prerequisites

- Python 3.10+ (3.12 recommended)
- Docker Desktop OR Docker Engine
- Redis (or use Docker)
- Git
- GitHub account (for CI/CD)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/yourusername/refund-engine.git
cd refund-engine

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies (including testing, Celery, etc.)
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
# OpenAI API
OPENAI_API_KEY=sk-your-actual-key-here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Redis (for async processing)
REDIS_URL=redis://localhost:6379/0
```

### 3. Run Tests (CRITICAL!)

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=core --cov=scripts --cov=analysis --cov-report=term-missing

# You should see:
# ✅ All tests passed
# ✅ Coverage >= 70%
```

**If tests fail, DO NOT proceed to production!**

### 4. Set Up Async Processing

**Option A: Using Docker (Recommended)**
```bash
# Start Redis + Celery workers
docker-compose up -d redis worker flower

# Verify workers are running
docker-compose ps

# Check Flower monitoring UI
open http://localhost:5555
```

**Option B: Manual Setup**
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery workers
celery -A tasks worker --loglevel=info --concurrency=10

# Terminal 3 (optional): Start Flower monitoring
celery -A tasks flower --port=5555
```

### 5. Process Invoices

```bash
# Queue invoices for async processing
python scripts/async_analyzer.py --excel Master_Refunds.xlsx

# Monitor progress
open http://localhost:5555  # Flower UI

# Or check from command line
python scripts/async_analyzer.py --check-progress <batch-id> --watch
```

### 6. Set Up CI/CD

**Configure GitHub Secrets:**
1. Go to GitHub repository > Settings > Secrets and variables > Actions
2. Add secrets:
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

**Enable GitHub Actions:**
```bash
# Push to trigger CI/CD
git add .
git commit -m "Enable CI/CD"
git push

# GitHub Actions will automatically:
# ✅ Run all tests
# ✅ Check code quality
# ✅ Build Docker image
# ✅ Security scan
```

### 7. Production Deployment

**Option 1: Docker on Cloud VM**
```bash
# SSH to your cloud server
ssh user@your-server.com

# Clone repository
git clone https://github.com/yourusername/refund-engine.git
cd refund-engine

# Create .env with production secrets
nano .env

# Start with Docker Compose
docker-compose up -d

# Verify all services running
docker-compose ps
```

**Option 2: AWS ECS (Elastic Container Service)**
```bash
# Build and tag image
docker build -t refund-engine:v1.0.0 .

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <your-ecr-url>
docker tag refund-engine:v1.0.0 <your-ecr-url>/refund-engine:v1.0.0
docker push <your-ecr-url>/refund-engine:v1.0.0

# Create ECS task definition and service
aws ecs create-service --cluster refund-engine --service-name refund-engine-worker
```

**Option 3: Google Cloud Run**
```bash
# Build and push
gcloud builds submit --tag gcr.io/your-project/refund-engine

# Deploy
gcloud run deploy refund-engine \
  --image gcr.io/your-project/refund-engine \
  --platform managed \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

## Production Checklist

Before going live:

### Testing
- [ ] All tests pass (`pytest`)
- [ ] Coverage >= 70% (`pytest --cov`)
- [ ] Critical refund calculations tested
- [ ] Manual testing on sample data

### Security
- [ ] Environment variables in `.env` (not hardcoded)
- [ ] `.env` file in `.gitignore`
- [ ] API keys rotated for production
- [ ] Database access restricted
- [ ] No secrets in Git history

### Performance
- [ ] Redis running and accessible
- [ ] Celery workers configured (10-50 workers recommended)
- [ ] Flower monitoring enabled
- [ ] Memory limits configured for Docker
- [ ] API rate limits respected

### Monitoring
- [ ] Flower UI accessible (`http://localhost:5555`)
- [ ] Logs configured and centralized
- [ ] Error tracking (Sentry, optional)
- [ ] Alerts for failed tasks

### CI/CD
- [ ] GitHub Actions workflows enabled
- [ ] All tests pass in CI
- [ ] Docker builds successfully
- [ ] Secrets configured in GitHub

### Documentation
- [ ] README updated
- [ ] Team trained on async processing
- [ ] Deployment runbook created
- [ ] Disaster recovery plan

## Scaling

### Processing 10,000 invoices
```bash
# 10 workers, ~2 hours
celery -A tasks worker --concurrency=10
```

### Processing 100,000 invoices
```bash
# 50 workers, ~4 hours
celery -A tasks worker --concurrency=50

# Or multiple worker instances
docker-compose up --scale worker=5  # 5 instances × 10 workers = 50 total
```

### Processing 1,000,000 invoices
```bash
# Cloud deployment with autoscaling
# Use AWS ECS with autoscaling group
# Or Kubernetes with Horizontal Pod Autoscaler

# Process in batches
python scripts/async_analyzer.py --excel invoices.xlsx --start-row 0 --num-rows 100000
python scripts/async_analyzer.py --excel invoices.xlsx --start-row 100000 --num-rows 100000
# etc.
```

## Monitoring & Observability

### Flower Dashboard
```bash
# Access at: http://localhost:5555
# Shows:
# - Active tasks
# - Worker status
# - Success/failure rates
# - Task history
```

### Redis Monitoring
```bash
# Check queue size
redis-cli LLEN celery

# Monitor Redis
redis-cli MONITOR

# Get Redis info
redis-cli INFO
```

### Application Logs
```bash
# Docker logs
docker-compose logs -f worker

# Or tail log files
tail -f logs/celery.log
```

### Metrics (Optional - Advanced)
```bash
# Add Prometheus + Grafana
# See: https://docs.celeryproject.org/en/stable/userguide/monitoring.html
```

## Troubleshooting

### Tests fail
```bash
# Check dependencies
pip install -r requirements.txt

# Check environment
cat .env

# Run specific failing test
pytest tests/test_refund_calculations.py::test_mpu_basic_calculation -v
```

### Workers not processing tasks
```bash
# Check Redis connection
redis-cli ping

# Check worker logs
docker-compose logs worker

# Restart workers
docker-compose restart worker
```

### Out of memory
```bash
# Reduce concurrency
celery -A tasks worker --concurrency=5

# Or increase Docker memory
# Docker Desktop > Settings > Resources > Memory
```

### API rate limits hit
```bash
# Reduce worker concurrency
celery -A tasks worker --concurrency=10

# Add delays between tasks (in tasks.py):
@app.task(rate_limit='10/m')  # 10 tasks per minute
```

## Backup & Recovery

### Database Backups
```bash
# Backup Supabase
# Use Supabase dashboard > Database > Backups

# Or use pg_dump
pg_dump $DATABASE_URL > backup.sql
```

### Redis Persistence
```bash
# Redis saves to disk automatically
# Backup: /var/lib/redis/dump.rdb

# Or force save
redis-cli SAVE
```

### Code Backups
```bash
# GitHub is your backup
git push origin main

# Tag releases
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

## Support & Resources

- **Testing**: See `TESTING_GUIDE.md`
- **Async Processing**: See `ASYNC_PROCESSING_GUIDE.md`
- **Docker**: See `DOCKER_GUIDE.md`
- **CI/CD**: See `.github/workflows/`

## Production Best Practices

1. **Always run tests before deploying**
2. **Monitor Flower dashboard during processing**
3. **Start with small batches (100 rows) to verify**
4. **Keep Redis and workers on same network for speed**
5. **Use environment-specific `.env` files**
6. **Rotate API keys regularly**
7. **Review failed tasks daily**
8. **Keep Docker images up to date**
9. **Monitor API costs**
10. **Have rollback plan**

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Run tests and verify 100% pass
3. ✅ Process test batch (100 invoices)
4. ✅ Review results for accuracy
5. ✅ Scale to full production batch
6. ✅ Monitor and optimize

**You're now production-ready! 🚀**
