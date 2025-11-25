---
description: Start all Docker services
---

Start the Docker development environment:

1. **Build and start services:**
   ```bash
   docker-compose up -d --build
   ```

2. **Report service status:**
   ```bash
   docker-compose ps
   ```

3. **Show available services:**
   - Redis (message broker): localhost:6379
   - PostgreSQL (local DB): localhost:5432
   - Celery Worker: Processing async jobs
   - Flower (monitoring): http://localhost:5555

4. **Helpful commands to mention:**
   - View logs: `docker-compose logs -f worker`
   - Stop services: `docker-compose down`
   - Run async analyzer: `docker-compose run app python scripts/async_analyzer.py --excel "file.xlsx"`
