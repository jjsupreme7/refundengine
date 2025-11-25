Show running Docker containers and their status/ports.

Arguments: None

Shows: Container name, status (Up/Exited), exposed ports

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
