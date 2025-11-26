# Launch RAG Chatbot

Starts an interactive chatbot UI where you can ask tax law questions and see how the RAG system responds. Use this to test the knowledge base, debug retrieval issues, or demonstrate the system.

## What You Get

Two services:
1. **Flask document server** (port 5001) - Serves PDF files when you click citations
2. **Streamlit chatbot UI** (port 8501) - The actual chat interface

## How It Fits In The System

```
[You ask]: "Is cloud computing taxable in Washington?"
         |
         v
    [Chatbot UI]
         |
         v
    [RAG System]
         |
         +--> Searches tax_law_chunks for relevant WAC/RCW sections
         |
         +--> Returns top 5 most relevant chunks
         |
         v
    [AI generates answer with citations]
         |
         v
[Answer]: "Under WAC 458-20-15502, cloud computing is generally
          subject to retail sales tax unless..."
         |
         +--> [Click citation to view source PDF]
```

## Features

- **Chat interface** - Ask natural language questions
- **Source citations** - See which WAC/RCW sections were used
- **Feedback collection** - Rate answers (thumbs up/down)
- **PDF viewer** - Click citations to see actual source documents

## Arguments

None

## Example

```bash
/08-chatbot    # Starts both servers
```

Then open `http://localhost:8501` in your browser.

## Success Looks Like

Terminal shows:
```
Starting document server on port 5001...
Starting Streamlit chatbot on port 8501...
Document server PID: 12345
```

Browser opens to chat interface.

## Good Test Questions

- "Is software taxable in Washington?"
- "What is the manufacturing M&E exemption?"
- "How does WAC 458-20-19301 define digital products?"
- "Are SaaS subscriptions taxable?"

## Common Failures

- "Port already in use" → Run `/11-stop` first
- "No documents found" → Knowledge base empty. Run document ingestion.
- Citations don't load → Document server not running. Check port 5001.

## To Stop

Press `Ctrl+C` in terminal, or run `/11-stop`

```bash
./scripts/services/start_web_chatbot.sh
```
