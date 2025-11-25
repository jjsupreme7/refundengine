Start Docker services (Redis, Celery worker, Flower monitoring).

Arguments: $ARGUMENTS (optional)
- Specific service name to start only that service

Examples:
- /docker-up (start all)
- /docker-up redis
- /docker-up worker

```bash
docker-compose up -d $ARGUMENTS
```
