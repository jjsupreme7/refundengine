Stop all services: Docker containers and any running Python processes.

Arguments: None

Stops:
- All Docker containers (docker compose down)
- Streamlit dashboard
- Chatbot/document server
- Any lingering Python processes

```bash
docker compose down && bash scripts/services/stop_web_chatbot.sh 2>/dev/null; pkill -f "streamlit run" 2>/dev/null; echo "All services stopped"
```
