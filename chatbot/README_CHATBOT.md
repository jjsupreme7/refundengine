# 💬 Washington Tax Law Chatbot

Simple, clean chatbot interface for querying Washington State tax law using RAG (Retrieval-Augmented Generation).

## 🚀 Quick Start

```bash
python chatbot/simple_chat.py
```

## ✨ Features

### **Smart Search**
- Semantic search using OpenAI embeddings
- RAG-powered answers citing actual tax law
- Returns relevant WAC/RCW references with quotes

### **Advanced Filtering**
Filter search results by:
- **Law Category** (software, digital_goods, exemption, etc.)
- **Tax Types** (sales tax, use tax, B&O tax)
- **Industries** (retail, technology, general)
- **Citation** (specific WAC/RCW reference)

### **Clean UI**
- Clear, structured output
- Easy-to-read answers with citations
- Interactive filter management
- Conversation history

## 📖 How to Use

### **Ask Questions**

Just type naturally:
```
💬 You: How are digital products taxed in Washington?
💬 You: What is the tax treatment of SaaS?
💬 You: Are cloud services subject to sales tax?
```

### **Commands**

| Command | Description |
|---------|-------------|
| `/filter` | Manage search filters |
| `/stats` | View knowledge base statistics |
| `/clear` | Clear conversation history |
| `/help` | Show help |
| `/quit` | Exit |

### **Using Filters**

1. Type `/filter`
2. Choose filter type:
   - Law category (e.g., "software", "digital_goods")
   - Tax types (e.g., "sales tax, use tax")
   - Industries (e.g., "retail, technology")
   - Citation (e.g., "WAC 458-20-15503")
3. Enter value(s)
4. Ask your question - results will be filtered!

**Example workflow:**
```
💬 You: /filter
  → Choose option 2 (tax_types)
  → Enter: sales tax, use tax
  → ✅ Filter set

💬 You: How are SaaS products taxed?
  (Only searches chunks tagged with sales tax or use tax)
```

## 🎯 Example Questions

**General Questions:**
- How are digital products taxed in Washington?
- What is the definition of digital automated services?
- Are SaaS products subject to sales tax?

**Specific Questions:**
- What exemptions exist for software development?
- How do I determine if a product is taxable?
- What is the sourcing rule for digital products?

**With Filters:**
```
/filter → Set tax_types: "sales tax"
💬 How is retail sales tax calculated?
```

## 📊 Sample Output

```
💬 You: How are digital products taxed in Washington?

🔍 Searching knowledge base...
✅ Found 3 relevant sources

💬 ANSWER:

     Digital products in Washington are generally subject to retail sales
     tax or use tax. According to WAC 458-20-15503, digital products include
     "digital goods, digital codes, and digital automated services that are
     transferred electronically."

     The tax treatment depends on:
     1. Whether the product is considered a "digital good" vs. "digital
        automated service"
     2. The location of the buyer (sourcing rules apply)
     3. Whether any exemptions apply

     Specific exemptions may exist for certain industries or use cases.

📚 SOURCES:
     [1] WAC 458-20-15503 (Tax: sales tax, use tax; Industry: general, retail) (relevance: 0.78)
     [2] WAC 458-20-15503 - Page 3 (Tax: sales tax, use tax) (relevance: 0.75)
     [3] Retail Sales and Use Tax Guide (Tax: sales tax) (relevance: 0.68)
```

## 🔧 Technical Details

**Models Used:**
- Embeddings: `text-embedding-3-small` (OpenAI)
- Chat: `gpt-4o` (OpenAI)

**Search Parameters:**
- Similarity threshold: 0.3
- Top results: 3
- Vector search via Supabase pgvector

**Metadata Filtering:**
- Client-side: `citation`
- Server-side (RPC): `law_category`, `tax_types`, `industries`

## 🎨 UI Features

- **Auto-clear screen** between questions
- **Conversation history** (last 2 exchanges)
- **Active filter display** in header
- **Formatted sources** with metadata tags
- **Press Enter to continue** prompts

## 📝 Notes

- Answers are based **only** on ingested documents
- The chatbot will cite specific WAC/RCW references
- Filters help narrow search for more targeted results
- Conversation history provides context for follow-up questions

## 🆚 Comparison with Original Chatbot

| Feature | `chat_rag.py` | `simple_chat.py` |
|---------|---------------|------------------|
| UI | Basic terminal | Clean, structured |
| Filters | Basic | Advanced (multi-select) |
| Screen clearing | No | Yes |
| Filter UI | Command-line | Interactive menu |
| Metadata display | Limited | Full (tax types, industries, topics) |
| Help system | Basic | Comprehensive |

## 🚀 Next Steps

1. **Test with real questions** - Try various tax law queries
2. **Experiment with filters** - See how filtering affects results
3. **Review citations** - Check if answers accurately cite sources
4. **Add more documents** - Ingest additional WAC/RCW documents for broader coverage

---

**Pro Tip:** Use `/stats` to see what documents are available, then use `/filter` to focus on specific areas before asking questions!
