# Check Running Services

Quick health check to see what Docker containers are running and on which ports. Use this after `/01-docker-up` to confirm services started, or anytime something isn't working.

## What You're Looking For

| Container | Status | Meaning |
|-----------|--------|---------|
| refund-engine-redis | Up | Good - message broker ready |
| refund-engine-postgres | Up | Good - database ready |
| refund-engine-worker | Up | Good - can process analysis jobs |
| refund-engine-flower | Up | Good - can monitor at localhost:5555 |

## How It Fits In The System

This is a diagnostic command. When `/04-analyze` or `/05-dashboard` fails, run this first to see if infrastructure is even running.

```
Problem: "Connection refused"
  |
  v
/02-status --> Shows containers are down --> /01-docker-up --> Fixed
```

## Arguments

None

## Example Output

```
NAMES                    STATUS          PORTS
refund-engine-redis      Up 2 hours      0.0.0.0:6379->6379/tcp
refund-engine-postgres   Up 2 hours      0.0.0.0:5432->5432/tcp
refund-engine-worker     Up 2 hours
refund-engine-flower     Up 2 hours      0.0.0.0:5555->5555/tcp
```

## Red Flags

- Empty output → Nothing running. Run `/01-docker-up`
- "Exited" status → Container crashed. Check `/03-logs <service>`
- Missing worker → Analysis jobs won't process

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
