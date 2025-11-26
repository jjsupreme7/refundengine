# Stop All Services

Nuclear option to shut down everything - Docker containers, Streamlit servers, Flask servers, and any lingering Python processes. Use this at end of day or when you need to free up ports.

## What Gets Stopped

1. **Docker containers** - redis, postgres, worker, flower
2. **Streamlit apps** - Dashboard (5001), Chatbot (8501)
3. **Flask servers** - Document server (5001)
4. **Any stray Python processes** related to this project

## How It Fits In The System

```
/11-stop
    |
    +--> docker compose down (stops all containers)
    |
    +--> stop_web_chatbot.sh (stops Flask/Streamlit)
    |
    +--> pkill streamlit (catches strays)
    |
    v
All services stopped, all ports freed
```

## Arguments

None

## Example

```bash
/11-stop    # Stops everything
```

## Success Looks Like

```
Stopping refund-engine-flower ... done
Stopping refund-engine-worker ... done
Stopping refund-engine-redis ... done
Stopping refund-engine-postgres ... done
Removing containers...
All services stopped
```

## When To Use

- End of work day
- Before restarting services fresh
- "Port already in use" errors
- System feeling slow/memory heavy
- Before running `/01-docker-up` after issues

## Verify It Worked

Run `/02-status` - should show no containers running.

```bash
docker compose down && bash scripts/services/stop_web_chatbot.sh 2>/dev/null; pkill -f "streamlit run" 2>/dev/null; echo "All services stopped"
```
