# System Architecture

Complete architecture for the Washington State Tax Refund Analysis Engine with Human-in-the-Loop Learning

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         USER WORKFLOW                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Upload Excel    2. AI Analyzes    3. Review Excel    4. Import     │
│     with rows   →     each row    →    corrections   →   & Learn       │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE BASE (Dual System)                       │
├─────────────────────────────┬──────────────────────────────────────────┤
│      TAX LAW KNOWLEDGE      │     VENDOR BACKGROUND KNOWLEDGE          │
├─────────────────────────────┼──────────────────────────────────────────┤
│ • RCW/WAC regulations       │ • Vendor company profiles                │
│ • Exemptions & rules        │ • Product catalogs                       │
│ • Tax rates & definitions   │ • Industry information                   │
│ • Legal citations           │ • Historical context                     │
│                             │                                          │
│ Stored in:                  │ Stored in:                               │
│ - tax_law_chunks            │ - vendor_background_chunks               │
│ - Vector embeddings         │ - Vector embeddings                      │
│ - Indexed by citation       │ - Indexed by vendor name                 │
└─────────────────────────────┴──────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      ANALYSIS ENGINE (AI)                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  For each Excel row:                                                    │
│  1. Read invoice PDF → Extract line item matching amount                │
│  2. Query vendor knowledge → Get context about vendor/products          │
│  3. Query tax law knowledge → Get relevant RCW/WAC rules                │
│  4. Check vendor learning → Any prior corrections for this vendor?      │
│  5. AI analyzes → Determine refund eligibility                          │
│  6. Output to Excel → AI_Product_Desc, AI_Refund_Basis, etc.           │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      HUMAN REVIEW (You!)                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Review each row in Excel:                                              │
│  • Approve (AI got it right)                                            │
│  • Correct (AI made mistakes) → Fill correction columns                 │
│  • Reject (Can't determine)                                             │
│                                                                         │
│  Add notes explaining your corrections                                  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      LEARNING SYSTEM                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Imports corrections from Excel:                                        │
│  1. Stores reviews → analysis_reviews table                             │
│  2. Creates/updates vendor products → vendor_products table             │
│  3. Creates patterns → vendor_product_patterns table                    │
│  4. Logs all changes → audit_trail table                                │
│                                                                         │
│  Future analyses use these learnings!                                   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

```
knowledge_documents                  analysis_results
├─ id (PK)                          ├─ id (PK)
├─ document_type                    ├─ row_id
├─ title                            ├─ vendor_name
├─ citation (tax law)               ├─ ai_product_desc
└─ vendor_name (vendor bg)          ├─ ai_refund_basis
                                    ├─ ai_estimated_refund
         ↓                          └─ analysis_status
         │
    ┌────┴─────┐
    │          │
tax_law_chunks   vendor_background_chunks
├─ chunk_text    ├─ chunk_text
├─ citation      ├─ vendor_name
├─ embedding     ├─ product_categories
└─ law_category  └─ embedding


analysis_reviews                     vendor_products
├─ id (PK)                          ├─ id (PK)
├─ analysis_id (FK)                 ├─ vendor_name
├─ review_status                    ├─ product_description
├─ corrected_product_type           ├─ product_type
├─ corrected_refund_basis           ├─ tax_treatment
├─ reviewer_notes                   ├─ learning_source
└─ reviewed_by                      └─ confidence_score


vendor_product_patterns              audit_trail
├─ id (PK)                          ├─ event_type
├─ vendor_name                      ├─ field_name
├─ product_keyword                  ├─ old_value → new_value
├─ correct_product_type             ├─ changed_by
├─ times_confirmed                  └─ created_at
└─ confidence_score
```

---

## Data Flow

### 1. Knowledge Ingestion Flow

```
PDF Documents
    ↓
[8_ingest_knowledge_base.py]
    ↓
Extract text → Smart chunk → Generate embeddings
    ↓
Store in Supabase:
  - knowledge_documents (metadata)
  - tax_law_chunks OR vendor_background_chunks (vectors)
```

**Tax Law Ingestion:**
```bash
python scripts/8_ingest_knowledge_base.py tax_law \
    "RCW_82.08.02565.pdf" \
    --citation "RCW 82.08.02565" \
    --law-category "exemption"
```

**Vendor Ingestion:**
```bash
python scripts/8_ingest_knowledge_base.py vendor_background \
    "Nokia_Profile.pdf" \
    --vendor-name "Nokia" \
    --vendor-category "manufacturer"
```

---

### 2. Analysis Flow

```
Excel Input (Row 7: Nokia, $8000, inv-54567.pdf)
    ↓
[6_analyze_refunds.py]
    ↓
Step 1: Read inv-54567.pdf
    ↓
Step 2: AI extracts line item matching $8000
    → Result: "5G Radio Equipment Model AAHF"
    ↓
Step 3: Check vendor learning (vendor_products table)
    → Found prior correction: Nokia "5G Radio" → "Telecom Hardware"
    ↓
Step 4: Query vendor background (vector search)
    → Nokia is telecommunications manufacturer
    ↓
Step 5: Query tax law (vector search)
    → RCW 82.08.02565 - Manufacturing exemption
    → RCW 82.08.0267 - High-tech exemption
    ↓
Step 6: AI analyzes with all context
    → Determines: Not eligible (networking, not manufacturing)
    → Confidence: 85%
    ↓
Step 7: Output to Excel
    → AI_Product_Desc: "5G Radio Equipment Model AAHF"
    → AI_Product_Type: "Telecommunications Hardware" (learned!)
    → AI_Refund_Basis: "Not eligible"
    → AI_Estimated_Refund: $0
```

---

### 3. Review & Correction Flow

```
Excel with AI Analysis
    ↓
Human Review (You open Excel)
    ↓
For Row 7:
  - AI_Product_Type: "Telecommunications Hardware" ✓ Correct
  - AI_Refund_Basis: "Not eligible" ✗ WRONG!
    ↓
You correct:
  - Review_Status: "Needs Correction"
  - Corrected_Refund_Basis: "Eligible under RCW 82.08.0267"
  - Corrected_Estimated_Refund: $800
  - Reviewer_Notes: "Actually qualifies for high-tech exemption"
    ↓
Save Excel
    ↓
[7_import_corrections.py]
    ↓
System processes:
  1. Saves review → analysis_reviews table
  2. Updates pattern → vendor_product_patterns
     "Nokia + Telecommunications Hardware + RCW 82.08.0267 → Eligible"
  3. Logs change → audit_trail
  4. Increases confidence for this pattern
    ↓
Next time: AI sees Nokia telecom hardware → uses your correction!
```

---

## Vector Search Strategy

### Dual Search Approach

```python
# When analyzing Nokia $8000 transaction:

# 1. Search vendor background (context)
vendor_results = search_vendor_background(
    query="Nokia 5G Radio Equipment",
    vendor_filter="Nokia",
    match_count=3
)
# Returns:
# - Nokia is telecom manufacturer
# - Products: 5G base stations, antennas, network equipment
# - Industry: telecommunications infrastructure

# 2. Search tax law (rules)
tax_results = search_tax_law(
    query="telecommunications equipment exemption",
    law_category_filter="exemption",
    match_count=5
)
# Returns:
# - RCW 82.08.02565: Manufacturing exemption
# - RCW 82.08.0267: High-tech R&D exemption
# - WAC 458-20-136: Extracted goods exemption

# 3. AI combines both contexts for analysis
analysis = ai_analyze(
    vendor_context=vendor_results,
    tax_rules=tax_results,
    product="5G Radio Equipment",
    amount=8000
)
```

### Why Separate Tables?

**Single table approach:**
- Generic metadata
- Poor search relevance
- Mixed results (law + vendor)

**Dual table approach:**
- Specific metadata per type
- Better search relevance
- Targeted queries
- Easier maintenance

---

## Learning System

### How System Gets Smarter

```
Initial State:
  vendor_products: Empty
  vendor_product_patterns: Empty

Analysis #1:
  Nokia "5G Radio Equipment"
  → AI guesses: "Manufacturing Equipment"
  → You correct to: "Telecommunications Hardware"

After Import:
  vendor_products:
    ├─ Nokia → "5G Radio Equipment" → "Telecommunications Hardware"

  vendor_product_patterns:
    ├─ Nokia + "5G Radio" → "Telecommunications Hardware"
    ├─ confidence: 100% (human corrected)
    ├─ times_confirmed: 1

Analysis #2 (weeks later):
  Nokia "5G Radio Equipment Model XYZ"
  → AI checks vendor_product_patterns
  → Finds: Nokia + "5G Radio" → "Telecommunications Hardware"
  → Uses learned classification!
  → Confidence: 95% (learned from you)

After Your Approval:
  vendor_product_patterns:
    ├─ times_confirmed: 2
    ├─ confidence: 100% (confirmed again)
```

### Learning Triggers

1. **Product Type Correction**
   - Creates/updates vendor_products entry
   - Creates keyword pattern

2. **Refund Basis Correction**
   - Stores tax treatment for product type
   - Links vendor + product → refund eligibility

3. **Citation Correction**
   - Learns which RCW/WAC applies to product type

4. **Approval (no corrections)**
   - Confirms AI decision was correct
   - Increases pattern confidence

---

## AI Models Used

| Task | Model | Why |
|------|-------|-----|
| Document chunking | N/A | Rule-based smart chunking |
| Embeddings | text-embedding-3-small | Cost-effective, 1536 dimensions |
| Line item extraction | gpt-4o-mini | Fast, accurate for structured data |
| Refund analysis | gpt-4o | Complex legal reasoning required |

---

## Scaling Considerations

### Current Capacity

- **Documents:** 1000s of tax law + vendor docs
- **Chunks:** 10,000s of vector chunks
- **Analysis:** 1000s of rows per batch
- **Learning:** Unlimited corrections

### Performance

| Operation | Time | Cost |
|-----------|------|------|
| Ingest 1 PDF (10 pages) | ~30s | $0.10 |
| Analyze 1 row | ~5s | $0.02 |
| Import 100 corrections | ~10s | $0.00 |
| Vector search | <100ms | $0.00 |

### Optimization Strategies

1. **Batch AI calls** (20 items per call)
2. **Cache vendor lookups** (in-memory)
3. **Reuse tax law searches** (same category)
4. **Parallel PDF processing**
5. **pgvector indexes** (IVFFlat)

---

## Security & Privacy

### Data Storage

- **Supabase:** Row-level security enabled
- **Knowledge base:** Public (legal documents)
- **Analysis results:** User-specific access
- **Audit trail:** Complete change history

### API Keys

```bash
# Required
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=...  # Service role key for backend
```

### Access Control

- Knowledge base: Public read
- Analysis results: Authenticated users only
- Corrections: Tracked by reviewer email
- Audit trail: Read-only for compliance

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review system learning stats
- Check audit trail for anomalies

**Monthly:**
- Update vendor documents (new products)
- Clean up old analysis results

**Quarterly:**
- Review tax law updates
- Re-ingest updated RCW/WAC documents

**Annually:**
- Archive old corrections
- Optimize vector indexes

### Monitoring Queries

```sql
-- Check knowledge base stats
SELECT * FROM knowledge_base_stats;

-- Review recent corrections
SELECT * FROM analysis_reviews
WHERE reviewed_at > NOW() - INTERVAL '7 days'
ORDER BY reviewed_at DESC;

-- Vendor learning summary
SELECT vendor_name, COUNT(*) as products_learned
FROM vendor_products
WHERE learning_source = 'human_correction'
GROUP BY vendor_name;

-- Top corrected fields
SELECT field_name, COUNT(*) as correction_count
FROM audit_trail
WHERE event_type = 'human_correction'
GROUP BY field_name
ORDER BY correction_count DESC;
```

---

## Deployment Checklist

- [ ] Deploy database schemas
- [ ] Ingest tax law documents
- [ ] Ingest vendor background documents
- [ ] Verify vector search functions work
- [ ] Run test analysis on sample Excel
- [ ] Review and correct test results
- [ ] Import corrections
- [ ] Verify system learned from corrections
- [ ] Document vendor-specific patterns
- [ ] Set up monitoring queries

---

## Future Enhancements

### Planned

1. **Multi-state support** - California, Texas, etc.
2. **Web UI** - Browser-based review interface
3. **Automated PDF upload** - Direct email ingestion
4. **Confidence thresholds** - Auto-approve high confidence
5. **Bulk pattern import** - Import known vendor/product rules

### Ideas

- Integration with accounting systems (QuickBooks, NetSuite)
- OCR improvement for poor-quality PDFs
- Multi-language support (for foreign vendors)
- Automated refund claim generation
- Real-time collaboration (multiple reviewers)

---

**Last Updated:** 2025-11-07
