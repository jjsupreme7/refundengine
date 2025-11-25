---
description: Start the interactive tax law chatbot
---

Start the interactive tax law chatbot:

1. **Start the chatbot:**
   ```bash
   streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503
   ```

2. **Inform the user:**
   - Chatbot will be available at http://localhost:8503
   - Features:
     - Ask questions about Washington State tax law
     - Get answers with citations to RCW, WAC, and Tax Decisions
     - Provide feedback (thumbs up/down) to improve responses

3. **Keep running** until user stops it (Ctrl+C)
