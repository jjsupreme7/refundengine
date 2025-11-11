# Async Processing Guide

## Overview

Process thousands of invoices in parallel using **Celery workers** and **Redis message queue**.

## Why Async Processing?

**Without async (sequential):**
- 100,000 invoices × 8 seconds each = **222 hours** (9+ days)

**With async (10 workers):**
- 100,000 invoices ÷ 10 workers = **22 hours**

**With async (50 workers):**
- 100,000 invoices ÷ 50 workers = **4.4 hours** ⚡

## Installation

### 1. Install Redis

**macOS:**
```bash
brew install redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 2. Install Python dependencies
```bash
pip install celery redis flower
# Or: pip install -r requirements.txt
```

## Quick Start

### Option 1: Using Docker (Recommended)

```bash
# Start all services (Redis + 10 workers + monitoring)
docker-compose up

# Queue invoices for processing
docker-compose run app python scripts/async_analyzer.py --excel Master_Refunds.xlsx

# Monitor progress at: http://localhost:5555
```

### Option 2: Manual Setup

**Terminal 1 - Start Redis:**
```bash
redis-server
```

**Terminal 2 - Start Celery workers (10 parallel workers):**
```bash
celery -A tasks worker --loglevel=info --concurrency=10
```

**Terminal 3 - Queue invoices:**
```bash
python scripts/async_analyzer.py --excel Master_Refunds.xlsx
```

**Terminal 4 (Optional) - Start monitoring UI:**
```bash
celery -A tasks flower --port=5555
# Open browser: http://localhost:5555
```

## Usage

### Queue entire Excel file
```bash
python scripts/async_analyzer.py --excel Master_Refunds.xlsx
```

### Queue specific rows
```bash
# Process rows 100-200
python scripts/async_analyzer.py --excel Master_Refunds.xlsx --start-row 100 --num-rows 100
```

### Check progress
```bash
# Get batch ID from queue command output
python scripts/async_analyzer.py --check-progress <batch-id>
```

### Watch progress in real-time
```bash
python scripts/async_analyzer.py --check-progress <batch-id> --watch
```

### List active workers
```bash
python scripts/async_analyzer.py --list-workers
```

## Scaling Workers

### Increase concurrency (more parallel tasks per worker)
```bash
# 50 parallel tasks
celery -A tasks worker --concurrency=50
```

### Multiple worker instances
```bash
# Terminal 1
celery -A tasks worker --concurrency=10 -n worker1@%h

# Terminal 2
celery -A tasks worker --concurrency=10 -n worker2@%h

# Terminal 3
celery -A tasks worker --concurrency=10 -n worker3@%h

# Total: 30 parallel tasks
```

### Auto-scale workers
```bash
# Scale between 5-20 workers based on queue size
celery -A tasks worker --autoscale=20,5
```

## Monitoring

### Flower Web UI (Recommended)
```bash
celery -A tasks flower --port=5555
```

Open browser: `http://localhost:5555`

**Features:**
- Real-time task progress
- Worker status
- Task history
- Performance metrics
- Success/failure rates

### Command-line monitoring
```bash
# Watch tasks
celery -A tasks events

# Inspect active tasks
celery -A tasks inspect active

# Get worker stats
celery -A tasks inspect stats
```

## Error Handling

### Retry failed tasks
Tasks automatically retry up to 3 times with 60-second delays.

### View failed tasks
```bash
# In Flower UI, go to "Tasks" tab and filter by "FAILED"
```

### Manually retry a failed task
```python
from celery.result import AsyncResult

result = AsyncResult('<task-id>')
result.retry()
```

## Performance Optimization

### 1. Tune worker concurrency
```bash
# For CPU-bound tasks: workers = CPU cores
celery -A tasks worker --concurrency=8

# For I/O-bound tasks (our case): workers = 2-4x CPU cores
celery -A tasks worker --concurrency=32
```

### 2. Use prefetch multiplier
```bash
# Process one task at a time (prevents memory issues)
celery -A tasks worker --prefetch-multiplier=1
```

### 3. Set task time limits
```python
# In tasks.py
app.conf.update(
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
)
```

### 4. Restart workers periodically
```bash
# Restart after 100 tasks (prevents memory leaks)
celery -A tasks worker --max-tasks-per-child=100
```

## Production Deployment

### Use supervisor to manage workers
```bash
# Install supervisor
sudo apt-get install supervisor

# Create /etc/supervisor/conf.d/celery.conf:
[program:celery]
command=celery -A tasks worker --loglevel=info --concurrency=50
directory=/app
user=celery
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log
```

### Use systemd
```bash
# Create /etc/systemd/system/celery.service:
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=celery
Group=celery
WorkingDirectory=/app
ExecStart=/usr/local/bin/celery -A tasks worker --detach --loglevel=info --concurrency=50

[Install]
WantedBy=multi-user.target
```

## Architecture

```
Excel File (100K rows)
        ↓
[async_analyzer.py] - Reads Excel, creates tasks
        ↓
    Redis Queue
        ↓
   ┌────┴────┬────┬────┐
   ↓         ↓    ↓    ↓
Worker 1  Worker 2 ... Worker 50
   ↓         ↓    ↓    ↓
Process   Process ... Process
invoices  invoices    invoices
        ↓
    Results saved to database
```

## Troubleshooting

### Redis connection refused
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running:
redis-server
```

### No workers available
```bash
# Check workers
celery -A tasks inspect active

# Start workers
celery -A tasks worker --loglevel=info --concurrency=10
```

### Tasks stuck in queue
```bash
# Check queue size
redis-cli LLEN celery

# Purge all tasks (WARNING: deletes all queued tasks)
celery -A tasks purge
```

### Out of memory errors
```bash
# Reduce concurrency
celery -A tasks worker --concurrency=5

# Or use autoscaling
celery -A tasks worker --autoscale=10,2
```

## Cost Considerations

With 100,000 invoices:
- **Sequential processing**: OpenAI API calls over 9+ days
- **Parallel processing (50 workers)**: Same API calls in 4.4 hours

**API costs are the same**, but you save:
- Development time (finish in hours, not days)
- Cloud compute costs (if running on cloud VM)

## Best Practices

1. **Start small**: Test with 100 rows before processing 100K
2. **Monitor memory**: Check worker memory usage with `htop` or Flower
3. **Use rate limiting**: Respect OpenAI API rate limits
4. **Save checkpoints**: Process in batches of 1,000-10,000
5. **Handle failures gracefully**: Check failed tasks and retry

## Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
