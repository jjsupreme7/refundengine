View Docker service logs (follow mode). Essential for debugging analysis failures.

Arguments: $ARGUMENTS
- Service name: redis, postgres, worker, flower, app
- No argument shows all logs

Examples:
- /logs (all services)
- /logs worker
- /logs redis
- /logs postgres

```bash
docker compose logs -f $ARGUMENTS
```
