#!/bin/bash
#
# Start Web Chatbot with Document Server
#
# This script launches both:
# 1. Document server (Flask) for serving PDF files
# 2. Streamlit web UI for the chatbot
#
# Usage:
#   ./scripts/start_web_chatbot.sh
#
# Stop:
#   Press Ctrl+C or run: ./scripts/stop_web_chatbot.sh
#

set -e  # Exit on error

echo "=========================================="
echo "🚀 Starting WA Tax Law Web Chatbot"
echo "=========================================="
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found"
    exit 1
fi

# Check if virtual environment should be activated
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️  Streamlit not found. Installing..."
    pip install streamlit
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing..."
    pip install flask
fi

# Start document server in background
echo "📄 Starting document server on http://localhost:5001..."
python3 chatbot/document_server.py > /dev/null 2>&1 &
DOC_SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Check if document server started successfully
if ! kill -0 $DOC_SERVER_PID 2>/dev/null; then
    echo "❌ Error: Document server failed to start"
    exit 1
fi

echo "✅ Document server running (PID: $DOC_SERVER_PID)"

# Save PID to file for stop script
echo $DOC_SERVER_PID > .doc_server.pid

echo ""
echo "=========================================="
echo "🌐 Starting Streamlit UI on http://localhost:8501..."
echo "=========================================="
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    if [ -f .doc_server.pid ]; then
        DOC_PID=$(cat .doc_server.pid)
        kill $DOC_PID 2>/dev/null || true
        rm .doc_server.pid
        echo "✅ Document server stopped"
    fi
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT TERM

# Start Streamlit (foreground - this will block)
streamlit run chatbot/web_chat.py

# If streamlit exits, cleanup
cleanup
