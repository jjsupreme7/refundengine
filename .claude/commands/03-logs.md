# View Service Logs

Streams real-time logs from Docker services. This is your PRIMARY debugging tool when analysis fails, services crash, or you see unexpected behavior.

## When To Use This

- Analysis failed with vague error → `/03-logs worker`
- Dashboard won't connect to database → `/03-logs postgres`
- Tasks stuck in queue → `/03-logs redis` or `/03-logs flower`
- Something's wrong but you don't know what → `/03-logs` (all)

## Available Services

| Service | What Its Logs Show |
|---------|-------------------|
| worker | Analysis job processing, AI calls, errors, stack traces |
| redis | Connection events, memory usage |
| postgres | SQL queries, connection errors, slow queries |
| flower | Task queue status, worker health |

## How It Fits In The System

```
/04-analyze --> fails --> /03-logs worker --> See actual error:
                                              "OpenAI rate limit exceeded"
                                              Now you know the problem.
```

## Arguments

$ARGUMENTS
- No args: Shows ALL service logs (can be noisy)
- Service name: Shows only that service's logs

## Examples

```bash
/03-logs                   # All logs (overwhelming but comprehensive)
/03-logs worker            # Most useful - shows analysis processing
/03-logs postgres          # Database issues
/03-logs redis             # Message queue issues
```

## What To Look For

- `ERROR` or `Exception` → The actual problem
- `rate limit` → OpenAI throttling, wait and retry
- `connection refused` → Service not running or wrong port
- `timeout` → Slow query or network issue

## Pro Tip

Logs stream continuously (follow mode). Press `Ctrl+C` to stop watching.

```bash
docker compose logs -f $ARGUMENTS
```
