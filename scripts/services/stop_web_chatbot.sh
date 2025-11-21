#!/bin/bash
#
# Stop Web Chatbot and Document Server
#
# Usage:
#   ./scripts/stop_web_chatbot.sh
#

echo "🛑 Stopping Web Chatbot servers..."

# Change to project root
cd "$(dirname "$0")/.."

# Stop document server
if [ -f .doc_server.pid ]; then
    DOC_PID=$(cat .doc_server.pid)
    if kill -0 $DOC_PID 2>/dev/null; then
        kill $DOC_PID
        echo "✅ Document server stopped (PID: $DOC_PID)"
    fi
    rm .doc_server.pid
else
    # Try to find and kill by process name
    pkill -f "document_server.py" && echo "✅ Document server stopped" || echo "⚠️  No document server found"
fi

# Stop Streamlit
pkill -f "streamlit run.*web_chat.py" && echo "✅ Streamlit stopped" || echo "⚠️  No Streamlit process found"

echo "✅ All servers stopped"
