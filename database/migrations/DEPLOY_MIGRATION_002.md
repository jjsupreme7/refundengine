# How to Deploy Migration 002: Compatibility Layer

## ⚠️ IMPORTANT: Use the FIXED Version

Use **migration_002_compatibility_layer_FIXED.sql** instead of the original.
The fixed version works with your actual schema (without hierarchy_level columns).

## Quick Deploy (5 minutes)

### Option 1: Via Supabase Dashboard (Easiest)

1. **Open Supabase Dashboard**
   - Go to https://supabase.com
   - Select your project

2. **Open SQL Editor**
   - Click "SQL Editor" in left sidebar
   - Click "New query"

3. **Copy & Paste Migration**
   - Open `database/migrations/migration_002_compatibility_layer_FIXED.sql` ← Use FIXED version
   - Copy entire contents
   - Paste into SQL Editor

4. **Run Migration**
   - Click "Run" button (or press Cmd/Ctrl + Enter)
   - Wait for "Success" message

5. **Verify It Worked**
   Run these test queries in SQL Editor:
   ```sql
   -- Test 1: Check view exists
   SELECT COUNT(*) FROM legal_chunks;

   -- Test 2: Check function exists
   SELECT * FROM match_legal_chunks('[0.1]'::vector(1536), 0.5, 1);
   ```

---

### Option 2: Via Command Line

```bash
# Get your database URL from Supabase dashboard
# Settings → Database → Connection string (URI)

# Use the FIXED version:
psql "your-connection-string-here" -f database/migrations/migration_002_compatibility_layer_FIXED.sql
```

---

## What This Migration Does

Creates **compatibility wrappers** so old code continues working:

### Before Migration:
```
Old Code: match_legal_chunks()
         ↓
         ❌ Uses old legal_chunks table (might not exist)
```

### After Migration:
```
Old Code: match_legal_chunks()
         ↓
         ✅ Redirects to → search_tax_law()
         ↓
         ✅ Uses new tax_law_chunks table
```

**Result**: Old code works without changes while we migrate it!

---

## Success Checklist

After running migration, verify:

- [ ] ✅ No errors in SQL Editor
- [ ] ✅ `legal_chunks` view exists
- [ ] ✅ `match_legal_chunks()` function exists
- [ ] ✅ `match_documents()` function exists
- [ ] ✅ Test queries return results
- [ ] ✅ Python code still works (test below)

---

## Test Python Code Still Works

After deploying SQL migration, test that existing Python code works:

```bash
# Test 1: Enhanced RAG (uses old schema)
python3 -c "
from core.enhanced_rag import EnhancedRAG
from core.database import get_supabase_client
rag = EnhancedRAG(get_supabase_client())
results = rag.basic_search('software tax', top_k=2)
print(f'✅ Enhanced RAG works! Found {len(results)} results')
"

# Test 2: Chat RAG (uses new schema)
python3 -c "
from chatbot.chat_rag import RAGChatbot
bot = RAGChatbot()
docs = bot.search_knowledge_base('software', top_k=2)
print(f'✅ Chat RAG works! Found {len(docs)} results')
"
```

**Expected**: Both tests pass ✅

---

## Rollback (If Needed)

If something goes wrong, run this to remove the compatibility layer:

```sql
-- Rollback migration_002
DROP VIEW IF EXISTS legal_chunks;
DROP FUNCTION IF EXISTS match_legal_chunks(vector, float, int);
DROP FUNCTION IF EXISTS match_documents(vector, float, int);
```

---

## Next Steps After Deployment

Once compatibility layer is deployed:

1. ✅ Old code works via compatibility wrappers
2. ✅ New code works with new schema
3. 🚀 Now safe to migrate Python files to use new schema
4. 🚀 After all files migrated, remove compatibility layer

---

## Troubleshooting

### Error: "relation 'tax_law_chunks' does not exist"

**Problem**: New schema tables don't exist yet

**Solution**: Run these schema files first:
```bash
psql "your-connection-string" -f database/schema/schema_knowledge_base.sql
```

### Error: "function search_tax_law does not exist"

**Problem**: New functions not deployed yet

**Solution**: Same as above - deploy schema_knowledge_base.sql first

### Python code gets empty results

**Problem**: New tables exist but have no data

**Solution**:
1. Check if old tables have data:
   ```sql
   SELECT COUNT(*) FROM legal_documents;
   SELECT COUNT(*) FROM document_chunks;
   ```
2. If yes, run data migration (see MIGRATION_PLAN.md Appendix A)
3. If no, just use new tables going forward

---

## Support

- 📖 Full migration guide: [MIGRATION_PLAN.md](../MIGRATION_PLAN.md)
- 📊 Implementation status: [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)
- 📚 Database docs: [README.md](../README.md)
