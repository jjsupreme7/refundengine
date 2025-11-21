# 💬 Washington Tax Law Chatbot with Learning System

Interactive chatbot for querying Washington State tax law using EnhancedRAG with continuous learning from user feedback.

## 🎯 Current System (Simplified)

The chatbot folder has been streamlined to **3 essential files**:

```
chatbot/
├── rag_ui_with_feedback.py    # Main chat interface (START HERE)
├── feedback_analytics.py       # Analytics dashboard
└── document_server.py          # Serves PDF/HTML documents
```

---

## 🚀 Quick Start

### **Main Chatbot (Recommended)**
```bash
# Start the main chatbot with feedback & learning
streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503

# Then open: http://localhost:8503
```

### **With Document Links (Full Experience)**
```bash
# Terminal 1: Start document server
python chatbot/document_server.py

# Terminal 2: Start chatbot
streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503
```

### **Analytics Dashboard (Optional)**
```bash
# View feedback trends and learning progress
streamlit run chatbot/feedback_analytics.py --server.port 8504

# Then open: http://localhost:8504
```

---

## 📁 File Descriptions

### `rag_ui_with_feedback.py` ⭐ **Main Chatbot**
**Purpose**: Interactive chat interface with feedback collection and continuous learning

**Features**:
- ✅ **EnhancedRAG**: Corrective RAG + AI reranking + query expansion + hybrid search
- ✅ **Feedback Collection**: Thumbs up/down, star ratings, detailed suggestions
- ✅ **Continuous Learning**: System improves from user corrections
- ✅ **Clickable Source Links**: Direct links to WAC/RCW documents
- ✅ **Advanced Filtering**: Law category, tax types, industries, citation
- ✅ **Law Version Comparison**: Compare old law vs new ESSB 5814 (Oct 2025)
- ✅ **Authentication**: Login required (configured in core/auth.py)

**Uses**:
- `core/enhanced_rag.py` - High-quality RAG system
- `core/feedback_system.py` - Learning engine
- `core/law_version_handler.py` - Law version comparison
- `core/auth.py` - User authentication

**Feedback Types**:
- 👍 **Thumbs Up** - Adds to golden Q&A dataset
- 👎 **Thumbs Down** - Triggers improvement analysis
- ⭐ **Star Ratings** (1-5 stars)
- ✍️ **Detailed Feedback**:
  - Suggest better answer
  - Prefer different citations
  - Request different answer structure
  - Free-form comments

---

### `feedback_analytics.py` 📊 **Analytics Dashboard**
**Purpose**: Visualize feedback trends and learning progress

**Shows**:
- 📈 Feedback over time (charts)
- ⭐ Rating distributions
- 📚 Most common questions
- 🧠 Learned improvements
- 💎 Golden Q&A pairs
- 📖 Citation preferences

**Usage**:
```bash
streamlit run chatbot/feedback_analytics.py --server.port 8504
```

---

### `document_server.py` 🗄️ **Document Server**
**Purpose**: Serves PDF and HTML documents for clickable source links

**Features**:
- Serves WAC/RCW HTML files from legs.wa.gov
- Serves local PDF documents
- Security: Path validation, prevents directory traversal
- Runs on: `http://localhost:5001`

**Endpoints**:
- Health check: `http://localhost:5001/health`
- Documents: `http://localhost:5001/documents/<filename>`

**Usage**:
```bash
python chatbot/document_server.py
```

---

## 🧠 How the Learning System Works

### The Flow:

```
User asks question
    ↓
rag_ui_with_feedback.py
    ↓
EnhancedRAG searches knowledge base
    ↓
AI generates answer with citations
    ↓
User gives feedback (👍 👎 ⭐ ✍️)
    ↓
FeedbackSystem (core/feedback_system.py)
    ├─ Saves to database
    ├─ Analyzes patterns
    ├─ Learns improvements
    └─ Updates preferences
    ↓
Database tables updated:
- user_feedback
- learned_improvements
- golden_qa_pairs
- citation_preferences
- answer_templates
    ↓
Next question uses learned knowledge:
    ├─ Better citation selection
    ├─ Better answer structure
    └─ References golden examples
```

### What Each Feedback Type Does:

**👍 Thumbs Up (4-5 stars)**:
- Adds Q&A pair to `golden_qa_pairs` table
- Future answers reference these golden examples
- "This is the correct way to answer this type of question"

**👎 Thumbs Down / Better Answer**:
- AI analyzes what's wrong
- Extracts improvement patterns
- Stores in `learned_improvements` table
- Future similar questions use learned approach

**Better Citations**:
- Tracks which WAC/RCW citations users prefer for topics
- Updates `citation_preferences` table
- Future searches prioritize preferred citations
- Example: Users suggest "WAC 458-20-15502" for SaaS → system learns to prioritize it

**Better Structure**:
- Learns how users want answers formatted
- Creates templates in `answer_templates` table
- Example: For "Is X taxable?" questions → 1) Yes/No, 2) Legal basis, 3) Exceptions

---

## 🎯 Example Usage

### Basic Chat:
```
You: How are SaaS products taxed in Washington?

🔍 Searching knowledge base...
✅ Found 3 relevant sources

💬 ANSWER:
SaaS (Software as a Service) products are generally subject to
Washington sales tax as "digital automated services" under
WAC 458-20-15502. However, multi-point use (MPU) allocation
may reduce the taxable amount if used across multiple states.

📚 SOURCES:
[1] WAC 458-20-15502 - Digital Products (relevance: 0.89)
[2] RCW 82.04.192 - Definitions (relevance: 0.76)

[Thumbs Up] [Thumbs Down] [⭐⭐⭐⭐⭐]
```

### With Feedback:
```
You: [Clicks 👍]

✅ Thanks! Added to golden examples.
   Future "SaaS taxation" questions will reference this answer.
```

Or:
```
You: [Clicks 👎] → [Provide detailed feedback]

Feedback Type: Better citations
Suggested Citations: WAC 458-20-15503
Comment: Should include WAC 458-20-15503 for cloud services

✅ Feedback saved! Citation preference updated.
   Future searches will prioritize WAC 458-20-15503 for cloud questions.
```

---

## 🔧 Dependencies

The chatbot uses these core modules (in `core/` folder):

| Module | Purpose |
|--------|---------|
| `enhanced_rag.py` | High-quality RAG (corrective + reranking + query expansion) |
| `feedback_system.py` | Learning engine (analyzes feedback, creates improvements) |
| `law_version_handler.py` | Compare old vs new tax law versions |
| `auth.py` | User authentication |
| `database.py` | Supabase database connection |

**All of these are REQUIRED** - don't delete them!

---

## 📊 Database Tables

The chatbot system uses these tables:

### Primary Tables:
- `knowledge_chunks` - Tax law document chunks (searched by RAG)
- `knowledge_documents` - Document metadata (citations, titles, URLs)

### Feedback & Learning Tables:
- `user_feedback` - All feedback submissions (thumbs up/down, ratings, comments)
- `learned_improvements` - Extracted improvement patterns from feedback
- `golden_qa_pairs` - High-quality Q&A examples (4-5 star ratings)
- `citation_preferences` - Which citations users prefer for which topics
- `answer_templates` - Preferred answer structures by question type

---

## 🔐 Authentication

`rag_ui_with_feedback.py` requires authentication (line 56):
```python
if not require_authentication():
    st.stop()
```

Configure auth in `.env`:
```bash
# Authentication (for chatbot)
AUTH_USERNAME=your-username
AUTH_PASSWORD=your-password
```

Or configure in `core/auth.py` for more advanced auth methods.

---

## 🎨 UI Features

### Sidebar:
- ⚙️ **Settings**: Enable learning, force retrieval, top-k results
- 📅 **Law Version**: Current law, old law, or comparison mode
- 🔍 **Filters**: Law category, tax types, industries, citation
- 📊 **Session Stats**: Questions asked, cost saved
- ❓ **Help**: Usage instructions
- 🗑️ **Clear Chat**: Reset conversation

### Main Chat:
- 💬 Chat input with conversation history
- 🤖 Decision analysis (shows RAG decision reasoning)
- 📚 Source citations with clickable links
- 👍👎 Feedback buttons on every answer
- ⭐ Star ratings (1-5 stars)
- ✍️ Detailed feedback forms (expandable)

### Law Version Comparison:
- 📕 Old Law (Pre-Oct 2025)
- 📘 New Law (ESSB 5814, Oct 2025+)
- 🔄 Key Changes (side-by-side comparison)

---

## 📈 Performance

Same EnhancedRAG as `fast_batch_analyzer.py` in the analysis folder:
- **Quality**: Corrective RAG + reranking + query expansion + hybrid search
- **Speed**: ~2-3 seconds per question
- **Cost**: ~$0.01-0.02 per question (GPT-4o + embeddings)
- **Accuracy**: Improves over time with user feedback

---

## 🧹 Recent Cleanup (2025-11-20)

**Consolidated from 8 files → 3 files**:

### ❌ **Deleted** (redundant/inferior):
- `web_chat.py` - Basic web UI (no feedback)
- `simple_chat.py` - Terminal UI with basic RAG
- `chat_rag.py` - Terminal UI with EnhancedRAG
- `enhanced_rag_ui.py` - Web UI showing decision reasoning

### ✅ **Kept** (essential):
- `rag_ui_with_feedback.py` - Main chat UI (has everything)
- `feedback_analytics.py` - Analytics dashboard
- `document_server.py` - Document server

**Result**: 62.5% reduction in files, cleaner codebase, same functionality!

---

## 🔗 Integration with Analysis System

The chatbot uses the **same EnhancedRAG** as the batch analysis system:

| Component | Chatbot | Analysis |
|-----------|---------|----------|
| RAG System | EnhancedRAG | EnhancedRAG |
| Learning | FeedbackSystem | import_corrections.py |
| Use Case | Interactive Q&A | Batch Excel processing |
| User | Humans asking questions | Excel automation |

Both systems share:
- Same knowledge base (knowledge_chunks table)
- Same legal documents
- Same RAG quality (corrective + reranking)
- Same database

---

## 🆘 Troubleshooting

### "Authentication failed"
- Check `.env` has AUTH_USERNAME and AUTH_PASSWORD
- Or configure in core/auth.py

### "No sources found"
- Knowledge base may be empty
- Run ingestion scripts to populate knowledge_chunks table
- Check filters - try clearing all filters

### "Document server not running" (source links don't work)
- Start document server: `python chatbot/document_server.py`
- Check it's running on port 5001: `curl http://localhost:5001/health`

### "Error connecting to database"
- Check `.env` has correct SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
- Verify network connectivity
- Check that feedback tables exist (run database/migrations if needed)

### "FeedbackSystem import error"
- Ensure `core/feedback_system.py` exists
- Don't delete core/ folder files - they're required!

---

## 🚀 Next Steps

1. **Start the chatbot**: `streamlit run chatbot/rag_ui_with_feedback.py --server.port 8503`
2. **Ask questions**: Try tax law queries
3. **Give feedback**: Use thumbs up/down to improve the system
4. **View analytics**: `streamlit run chatbot/feedback_analytics.py --server.port 8504`
5. **Watch it learn**: Check learned_improvements table in database

---

**Pro Tip**: The more feedback you give, the smarter the system gets! Every thumbs up/down helps improve future answers.

**Last Updated**: 2025-11-20
