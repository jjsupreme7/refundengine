# Refund Engine Architecture

## Complete Workflow

```
Master Excel File (100,000+ rows)
         ↓
[For Each Line Item]
         ↓
    ┌────────────────────────────────────┐
    │  1. VENDOR RESEARCH (Web Search)   │
    │  • Who is this vendor?             │
    │  • What industry do they serve?    │
    │  • What products do they offer?    │
    └────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────┐
    │  2. PRODUCT RESEARCH (Web Search)  │
    │  • What is this product/service?   │
    │  • Is it software? Service? HW?    │
    │  • How is it deployed/delivered?   │
    │  • Multi-location or single?       │
    └────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────┐
    │  3. PATTERN MATCHING (Historical)  │
    │  • LexisNexis → 100% MPU           │
    │  • Nokia SW dev → 87% Non-taxable  │
    │  • SAP licenses → 86% MPU          │
    │  • Kronos → 100% MPU               │
    └────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────┐
    │  4. LEGAL ANALYSIS (CustomGPT)     │
    │  Focused questions:                │
    │  • Is this taxable in WA?          │
    │  • Professional services exemption?│
    │  • Digital automated service?      │
    │  • MPU allocation required?        │
    │  • Specific WAC/RCW citations?     │
    └────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────┐
    │  5. SYNTHESIZE RECOMMENDATION      │
    │  • Combine all inputs              │
    │  • Suggest refund basis            │
    │  • Calculate confidence score      │
    │  • Generate review checklist       │
    └────────────────────────────────────┘
         ↓
    ┌────────────────────────────────────┐
    │  6. HUMAN REVIEW SUMMARY           │
    │  Reviewer sees:                    │
    │  ✓ Vendor profile                  │
    │  ✓ Product classification          │
    │  ✓ Historical patterns             │
    │  ✓ Legal reasoning                 │
    │  ✓ Recommended action              │
    │  ✓ What to look at                 │
    │  ✓ Confidence score                │
    └────────────────────────────────────┘
```

## Refund Categories (From 7,500+ Historical Analysis)

### 1. **MPU (Multi-Point Use)** - 60% of refunds
**When it applies:**
- Software licenses used in multiple locations
- SaaS/cloud services accessed from multiple states
- Digital automated services (DAS) with multi-state users

**Allocation methodologies:**
- User location (39%) - where employees use the service
- Headcount (10%) - employee count by location
- Equipment location (8%) - where servers/hardware located

**Example vendors:**
- LexisNexis (100% MPU) - credit decisioning tools
- Kronos (100% MPU) - workforce management
- SAP (86% MPU) - enterprise software
- Globys (100% MPU) - billing platform SaaS

**What AI checks:**
- Product type: License, SaaS, Cloud, DAS
- Deployment keywords: "multi-state", "nationwide", "all locations"
- Vendor patterns: Known multi-location vendors

### 2. **Non-taxable** - 21% of refunds
**When it applies:**
- Professional services requiring primarily human effort
- Custom software development/configuration
- Consulting, advisory, help desk services
- Advertising services

**Example vendors:**
- Nokia (87% Non-taxable) - SW development/configuration

**Keywords AI looks for:**
- "professional services"
- "sw development"
- "configuration"
- "custom"
- "consulting"
- "help desk"
- "advertising"

**Legal basis:**
- WAC 458-20-15503(303)(a) - professional services exclusion
- WAC 458-20-15503(203)(m) - advertising services
- WAC 458-20-15503(303)(o) - data processing exclusion

### 3. **Partial OOS Services** - 6.5% of refunds
**When it applies:**
- Services/equipment in multiple locations (some WA, some out-of-state)
- Hardware maintenance with mixed deployment
- Construction/installation partially out-of-state

**Example:**
- "38/144 devices in WA (26.39%)" → 73.61% refund

**What AI checks:**
- Parse deployment location field
- Extract percentages from description
- Calculate WA vs out-of-state split

### 4. **Wrong Rate** - 5% of refunds
**When it applies:**
- Incorrect tax rate applied for location
- Location-based rate lookup needed

**Example vendors:**
- Andersen Construction (98% wrong rate)

**What AI needs:**
- Tax rate table by location and date
- Correct rate lookup capability

### 5. **OOS Services** - 2% of refunds
**When it applies:**
- Services performed entirely outside Washington
- Out-of-state delivery/installation

**What AI checks:**
- Deployment location: "out-of-state", state abbreviations (NJ, CA, TX)
- Service location in description

### 6. **OOS Shipment** - 1-2% of refunds
**When it applies:**
- Goods shipped/delivered outside Washington

**What AI checks:**
- Shipping address
- Delivery location

### 7. **B&O Tax** - 1% of refunds
**When it applies:**
- Business & Occupation tax incorrectly charged
- "Not allowed by contract"

**Requires:**
- Contract review (cannot be fully automated)

## CustomGPT Focused Prompts

### Prompt Template for Legal Analysis:

```
Analyze Washington State tax treatment for this transaction:

VENDOR: [Vendor Name]
[Vendor web research summary]

PRODUCT/SERVICE: [Product Name]
Type: [Service, License, Maintenance, etc.]
Description: [Invoice description]
[Product web research summary]

FOCUSED TAX ANALYSIS - Address these specific questions:

1. TAXABILITY in Washington State:
   - Is this product/service subject to Washington sales tax?
   - Reference specific RCW or WAC that applies

2. PROFESSIONAL SERVICES EXEMPTION:
   - Does this qualify as professional services requiring primarily human effort?
   - Reference WAC 458-20-15503(303)(a) if applicable

3. DIGITAL AUTOMATED SERVICES:
   - Is this a DAS under RCW 82.04.192(3)?
   - Data processing exclusion (WAC 458-20-15503(303)(o))?
   - Advertising services exclusion (WAC 458-20-15503(203)(m))?

4. MULTI-POINT USE (MPU):
   - Is this software/service likely used in multiple locations?
   - Does Washington require allocation based on usage location?
   - Reference WAC 458-20-19402 if MPU applies

5. OUT-OF-STATE CONSIDERATIONS:
   - Is this service performed outside Washington?
   - Delivery location exemptions?

6. SPECIFIC REFUND OPPORTUNITIES:
   - What refund basis applies?
   - Options: Non-taxable, MPU, Partial OOS, OOS services, Wrong rate
   - Confidence level?

Response format (JSON):
{
  "taxable_in_wa": true/false,
  "refund_basis": "Non-taxable" | "MPU" | "OOS services" | "No refund",
  "primary_citation": "WAC/RCW section",
  "confidence": 0-100,
  "reasoning": "Detailed legal reasoning",
  "mpu_required": true/false,
  "allocation_methodology": "User location" | "Equipment location" | "N/A",
  "exemption_type": "Professional services" | "Data processing" | "None"
}
```

## What Information Is Needed

### Immediate (Have or Can Get):
1. ✅ Master Excel with line items
2. ✅ Vendor names
3. ✅ Product/service descriptions
4. ✅ Invoice details
5. ✅ File paths to source documents

### For Web Research (Automatic):
6. ✅ Vendor company profiles (via WebSearch)
7. ✅ Product classifications (via WebSearch)
8. ✅ Industry information (via WebSearch)

### For Legal Analysis (CustomGPT):
9. ✅ Washington tax law citations
10. ✅ Exemption/exclusion analysis
11. ✅ Taxability determinations

### For MPU Calculations (Needed):
12. ⏳ User location data (headcount by state)
13. ⏳ Equipment location data (servers/hardware by state)
14. ⏳ Cost center allocation data

### For Rate Corrections (Needed):
15. ⏳ Tax rate table (WA locations by date)
16. ⏳ Correct rate lookup capability

### For Contract Review (Manual):
17. ⏳ Vendor contracts (for B&O tax cases)

## Output Format

### Human Review Summary for Each Line Item:

```json
{
  "invoice_details": {
    "vendor": "LEXISNEXIS RISK SOLUTIONS FL INC",
    "product": "InstantID Credit Reporting",
    "tax_amount": 10000.00,
    "description": "Credit decisioning tool - DAS license"
  },

  "vendor_research": {
    "company_profile": "LexisNexis is a data analytics and risk assessment company...",
    "industry": "Financial Services - Credit Reporting",
    "business_model": "B2B SaaS - Digital Automated Services"
  },

  "product_research": {
    "product_classification": "Digital Automated Service (DAS)",
    "is_software": true,
    "is_cloud_saas": true,
    "deployment_type": "Multi-location cloud service",
    "description": "Credit reporting and identity verification tool accessed by employees nationwide..."
  },

  "historical_pattern_match": [
    {
      "refund_basis": "MPU",
      "confidence": 95,
      "reasoning": "LexisNexis DAS products historically 100% MPU. Used by employees in multiple states.",
      "methodology": "User location",
      "pattern_source": "Historical: LexisNexis → 100% MPU"
    }
  ],

  "legal_analysis": {
    "taxable_in_wa": true,
    "refund_basis": "MPU",
    "primary_citation": "WAC 458-20-19402",
    "confidence": 90,
    "reasoning": "Digital automated service subject to tax, but requires allocation based on user location. Service accessed by employees in multiple states.",
    "mpu_required": true,
    "allocation_methodology": "User location",
    "exemption_type": "None - but requires MPU allocation"
  },

  "recommended_action": {
    "action": "MPU",
    "confidence": 92,
    "reasoning": "Historical pattern and legal analysis agree - requires multi-point use allocation"
  },

  "what_to_review": [
    "✓ Obtain user location data (employees by state using InstantID)",
    "✓ Calculate Washington percentage vs total users",
    "✓ Allocation methodology: User location (where employees use the tool)",
    "✓ Verify multi-state deployment in contract/SOW",
    "✓ Check invoice period for user count"
  ]
}
```

## File Structure

```
refund-engine/
├── scripts/
│   ├── master_excel_processor.py    # Main processor (just created)
│   ├── customgpt_client.py           # CustomGPT integration
│   ├── web_research_integration.py   # Web search functions
│   ├── historical_refund_matcher.py  # Pattern matching
│   └── universal_document_extractor.py # Read PDFs, Excel, images
│
├── outputs/
│   └── analysis_results.xlsx         # Output with recommendations
│
└── ARCHITECTURE.md                   # This file
```

## Usage

### Process entire master Excel:
```bash
python scripts/master_excel_processor.py --excel master_refunds.xlsx
```

### Process first 10 rows (testing):
```bash
python scripts/master_excel_processor.py --excel master_refunds.xlsx --rows 10
```

### Process specific range:
```bash
python scripts/master_excel_processor.py --excel master_refunds.xlsx --start 100 --rows 50
```

## Next Steps

1. **Test with sample data** - Run on a few rows to verify workflow
2. **Integrate real WebSearch** - Connect to search API or use Claude Code WebSearch
3. **Add MPU calculators** - Build user location and equipment location allocation logic
4. **Create output Excel** - Format results for human review
5. **Build review interface** - Dashboard or Excel add-in for analysts

## Questions to Answer

1. **Master Excel structure** - What are the actual column names?
   - Do you have: "Vendor Name", "Product", "Description", "Type"?
   - Are there existing columns for file paths?

2. **File tracking** - How should file paths be structured?
   - Column name: "Source_File_Path"?
   - Format: Relative or absolute paths?

3. **Output format** - What do reviewers need to see?
   - Separate columns for each insight?
   - Combined "Review Summary" column?
   - Confidence score column?

4. **Batch processing** - How many rows at a time?
   - Process all 100K rows?
   - Process in chunks of 1,000?
   - Save checkpoints?

Let me know and I'll adapt the architecture!
