# Launch TaxDesk Dashboard

Opens the main web UI for the refund-engine system. This is where you manage projects, review analysis results, browse documents, and work with Excel files.

## What You Get

A multi-page Streamlit app at `http://localhost:5001` with these pages:

| Page | Purpose |
|------|---------|
| Dashboard | Overview, recent activity, key metrics |
| Projects | Create/manage analysis projects, upload Excel files |
| Documents | Browse knowledge base (tax laws, vendor docs) |
| Review Queue | Transactions flagged for human review (low confidence) |
| Claims | Draft and track refund claims |
| Rules | Browse tax exemption rules and guidance |
| Excel Manager | Version control for Excel files, track changes |

## How It Fits In The System

```
                    /05-dashboard
                         |
        +----------------+----------------+
        |                |                |
   [Projects]      [Review Queue]    [Documents]
        |                |                |
        v                v                v
   Upload Excel    Fix AI mistakes   Search tax law
        |                |                |
        v                v                v
   /04-analyze     Learn from       Improve RAG
                   corrections      responses
```

## Arguments

None (runs on port 5001 by default)

## Example

```bash
/05-dashboard    # Opens http://localhost:5001
```

## Success Looks Like

Terminal shows:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:5001
```

Browser opens to dashboard home page.

## Common Failures

- "Port 5001 already in use" → Run `/11-stop` or `lsof -i :5001` to find what's using it
- "Module not found" → Run `pip install -r requirements.txt`
- "Cannot connect to database" → Check Supabase credentials in `.env`
- Blank page → Check browser console for JavaScript errors

## Prerequisites

- Supabase connection configured in `.env`
- No other service on port 5001

```bash
streamlit run dashboard/Dashboard.py --server.port 5001
```
