# Start Infrastructure Services

Starts the Docker containers that power the refund-engine backend. This is the FIRST command you run when starting work - nothing else works without these services running.

## What Gets Started

| Service | Port | Purpose |
|---------|------|---------|
| redis | 6379 | Message broker for Celery task queue |
| postgres | 5432 | Local database (optional - you use Supabase in production) |
| worker | - | Celery worker that processes invoice analysis jobs |
| flower | 5555 | Web UI to monitor Celery task queue |

## How It Fits In The System

```
[You] --> /04-analyze --> [Celery Worker] --> [Redis Queue] --> [Analysis Results]
                              ^
                              |
                         /01-docker-up starts this
```

## Arguments

$ARGUMENTS (optional)
- No args: Starts all services
- Service name: Starts only that service (redis, postgres, worker, flower)

## Examples

```bash
/01-docker-up              # Start everything (typical)
/01-docker-up redis        # Start only Redis
/01-docker-up worker       # Start only the Celery worker
```

## Success Looks Like

```
Creating refund-engine-redis ... done
Creating refund-engine-postgres ... done
Creating refund-engine-worker ... done
Creating refund-engine-flower ... done
```

Then run `/02-status` to confirm everything is healthy.

## Common Failures

- "port already in use" → Another process using 6379/5432. Run `/11-stop` first.
- "image not found" → Run `docker compose build` to build images
- Worker won't start → Check `/03-logs worker` for missing env vars

```bash
docker compose up -d $ARGUMENTS
```
