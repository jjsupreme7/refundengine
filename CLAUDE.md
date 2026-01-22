# Data Files

## Source Files (~/Desktop/Files/Files to be Analyzed/)
| File | Description |
|------|-------------|
| `Final 2024 Denodo Review.xlsx` | Sales Tax 2024 - "Real Run" sheet |
| `Use Tax Phase 3 2023.xlsx` | Use Tax 2023 |
| `Use Tax Phase 3 2024 Oct 17.xlsx` | Use Tax 2024 |

## Importing xlsb Files (Version Tracking)

When receiving updated xlsb files from the shared workbook:

```bash
# Import xlsb with date stamp (no format conversion)
python scripts/import_xlsb.py [path_to_xlsb]

# Or auto-detect from Downloads:
python scripts/import_xlsb.py
```

**Workflow:**
1. Copies xlsb to `versions/` folder with date stamp
2. Opens in Excel (via AppleScript)
3. Fixes hyperlinks to use `http://localhost:8888/` for Mac
4. Saves and closes Excel

**Version folder:** `~/Desktop/Files/Files to be Analyzed/versions/`

**xlsb Format (106 columns):** See `scripts/xlsb_column_mapping.py` for column positions.

**No format conversion:** Stays xlsb. All formatting preserved (yellow highlights, column grouping, fonts, conditional formatting).

## Source File Edit Policy

**Ask before editing source files.** When I need to update the source file directly (e.g., marking rows as "Pass not subject to WA tax"), I will always confirm before making changes.

Two operating modes:
- **Analysis → Output**: Read source → Analyze → Write to `Analyzed_Output/` (default)
- **Direct Update**: Update source file columns (Recon Analysis, Notes, Final Decision) - requires explicit permission

## Applicable Law Period (IMPORTANT)

**All transactions occurred BEFORE ESSB 5814 (effective October 1, 2025).**

| Data Set | Transaction Period | Applicable Law |
|----------|-------------------|----------------|
| Sales Tax 2024 | 2024 | Pre-ESSB 5814 |
| Use Tax 2023 | 2023 | Pre-ESSB 5814 |
| Use Tax 2024 | 2024 | Pre-ESSB 5814 |

Apply the law in effect at the time of the transaction. **DO NOT apply ESSB 5814 rules** - they only apply to transactions on or after October 1, 2025.

## Output Files (~/Desktop/Files/Analyzed_Output/)
Always use these output files - they track which rows have been analyzed:

| Source | Output |
|--------|--------|
| `Final 2024 Denodo Review.xlsx` | `Final 2024 Denodo Review - Analyzed.xlsx` |
| `Use Tax Phase 3 2023.xlsx` | `Phase_3_2023_Use Tax - Analyzed.xlsx` |
| `Use Tax Phase 3 2024 Oct 17.xlsx` | `Phase_3_2024_Use Tax - Analyzed.xlsx` |

## Invoices (~/Desktop/Invoices/)
- All invoice PDFs are stored here
- To enable clickable links in Excel on Mac, run: `python scripts/invoice_server.py`

## Output File Requirements
When generating analyzed output files:
- Invoice columns must have HTTP hyperlinks: `=HYPERLINK("http://localhost:8888/filename.pdf","filename.pdf")`
- This allows clicking to view invoices when the invoice server is running
- Applies to all output files (Sales Tax 2024, Use Tax 2023, Use Tax 2024)

## Output File Formatting

**All output files must be professionally formatted:**

### Number Formatting
| Column | Format | Example |
|--------|--------|---------|
| `rate` | Percentage | 10.3% |
| `hwste_tax_amount_lc` | Currency with commas | $1,234,567.89 |
| `hwbas_tax_base_lc` | Currency with commas | $12,345,678.90 |
| `Estimated_Refund` | Currency with commas | $123,456.78 |

### Color-Coded Column Headers
| Column Group | Color | Columns |
|--------------|-------|---------|
| **Input Data** | Light Blue (#D6EAF8) | name1_po_vendor_name through PO_Number |
| **AI Analysis** | Light Green (#D5F5E3) | Product_Desc through Location_Conflict_Type |
| **Human Review** | Light Yellow (#FCF3CF) | Review_Status through Reviewer_Notes |

### Excel Formatting
- **Freeze top row** - Header row stays visible when scrolling
- **Bold header row** - Column names in bold
- **Auto-filter enabled** - Filter dropdowns on all columns
- **Text wrap** on AI_Reasoning column (can be long)

### Column Widths
| Column | Width |
|--------|-------|
| `name1_po_vendor_name` | 30 |
| `hwbas_tax_base_lc` | 18 |
| `hwste_tax_amount_lc` | 18 |
| `Inv 1` | 25 |
| `rate` | 10 |
| `txz01_po_description` | 40 |
| `Product_Desc` | 50 |
| `Product_Type` | 20 |
| `Refund_Basis` | 18 |
| `Final_Decision` | 15 |
| `AI_Reasoning` | 80 |
| `Estimated_Refund` | 18 |

### Applying Formatting
Use `openpyxl` to apply formatting after writing data:
```python
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

# Colors
INPUT_FILL = PatternFill("solid", fgColor="D6EAF8")  # Light blue
AI_FILL = PatternFill("solid", fgColor="D5F5E3")     # Light green
HUMAN_FILL = PatternFill("solid", fgColor="FCF3CF")  # Light yellow

# Freeze top row
ws.freeze_panes = "A2"

# Bold headers
for cell in ws[1]:
    cell.font = Font(bold=True)
```

## Source Column Mappings
Invoice and PO numbers come from source Excel columns (not PDF extraction):

**Sales Tax 2024 (xlsx - 27 columns):**
| Output Column | Source Column |
|---------------|---------------|
| Invoice_Number | `belnr_max_document_number` |
| PO_Number | `ebeln_po_number` |

**Sales Tax 2024 (xlsb - 106 columns):**
See `scripts/xlsb_column_mapping.py` for full mapping. Key columns:
| Output Column | xlsb Position |
|---------------|---------------|
| Invoice_Number | col 7 (`belnr_max_document_number`) |
| PO_Number | col 20 (`ebeln_po_number`) |
| Human Columns | cols 27-33 (Assigned, Recon Analysis, Notes, Final Decision, Tax Category, Add'l info, Refund Basis) |

**Use Tax (2023 & 2024):**
| Output Column | Source Column |
|---------------|---------------|
| Invoice_Number | `INVNO` |
| PO_Number | `PO Number` |

## Sales Tax 2024 Column Order
Output columns should be in this order:

**Input Data:**
1. name1_po_vendor_name
2. hwbas_tax_base_lc
3. hwste_tax_amount_lc
4. Inv 1
5. Inv 2
6. rate
7. txz01_po_description
8. matk1_po_material_group_desc
9. sales_tax_state
10. tax_jurisdiction_state
11. quadrant
12. Invoice_Number
13. PO_Number

**AI Analysis:**
14. Product_Desc
15. Product_Type
16. Service_Classification
17. Refund_Basis
18. Citation
19. Citation_Source
20. Confidence
21. Estimated_Refund
22. Final_Decision
23. Explanation
24. Needs_Review
25. Follow_Up_Questions
26. Vendor_Mismatch
27. Location_Mismatch
28. AI_Reasoning
29. Site_ID
30. Location_Signals
31. Location_Confidence
32. Likely_Tax_State
33. Location_Conflict_Type

**Human Review:**
34. Review_Status
35. Corrected_Product_Desc
36. Corrected_Product_Type
37. Corrected_Refund_Basis
38. Corrected_Citation
39. Corrected_Estimated_Refund
40. Reviewer_Notes

## Use Tax Column Order (2023 & 2024)
Output columns should be in this order:

**Input Data:**
1. Vendor (or name1_po_vendor_name)
2. hwste_tax_amount_lc (or Tax Remitted)
3. Inv 1 File Name
4. Inv 2 File Name
5. Invoice Folder Path
6. tax_jurisdiction_state
7. Invoice_Number
8. PO_Number

**AI Analysis:**
9. Product_Desc
10. Product_Type
11. Service_Classification
12. Refund_Basis
13. Citation
14. Citation_Source
15. Confidence
16. Estimated_Refund
17. Final_Decision
18. Explanation
19. Needs_Review
20. Follow_Up_Questions
21. Vendor_Mismatch
22. Location_Mismatch
23. AI_Reasoning
24. Site_ID

**Human Review:**
25. Review_Status
26. Corrected_Product_Desc
27. Corrected_Product_Type
28. Corrected_Refund_Basis
29. Corrected_Citation
30. Corrected_Estimated_Refund
31. Reviewer_Notes

## Human Feedback Workflow
When the user says "ingest the human feedback" or similar:
1. Read the analyzed output files in `~/Desktop/Files/Analyzed_Output/`
2. Find rows where any Corrected_* column is filled OR Review_Status is set
3. Learn from corrections:
   - Update `knowledge_base/vendors/vendor_locations.json` with vendor info
   - Note patterns in `tax_rules.json` if applicable
4. Report what was ingested

## Invoice Analysis Behavior
- Rows are sorted by vendor name before analysis (same-vendor rows processed together)
- When using --limit, extends past limit to complete the last vendor's transactions
- AI receives full invoice context (all line items from Inv 1 and Inv 2)
- Ship-to addresses are validated against vendor HQ to prevent false out-of-state flags
- Site ID lookup overrides invoice-extracted locations (more reliable)

## Output File Safeguards

**Before writing:**
- Check if output file exists and read it first
- Match exact column structure from this document

**When writing:**
- Append to existing data, never replace the file
- Never overwrite any cell that already has a value
- Skip rows where analysis columns are already populated
- Only output rows with actual analysis (no empty shells)

**Before finishing:**
- Complete committed work (if analyzing X rows, finish X rows)
- Verify output has actual content, not empty columns
- Preserve human review columns: Assigned, Recon Analysis, Notes, Final Decision, Tax Category, Add'l info, Refund Basis

---

# Invoice Analysis Requirements

## Claude Code Analysis Mode
When the user says "Claude analysis", "you do it", "Claude Code analysis", or asks to analyze invoices without using the API:
- Analyze directly by reading the Excel file and invoice PDFs
- Do NOT run run_sales_tax_real_run.py or any script that uses external APIs

## Standard Filters

**Sales Tax 2024** (Real Run sheet):
- Paid? = "PAID"
- Recon Analysis = empty (not yet analyzed)
- Inv 1 = not empty (has invoice)
- Optional: quadrant, min/max rate, min/max amount

**Use Tax (2023 & 2024)**:
- INDICATOR = "Remit" (exact match, not "Do Not Remit")
- KOM Analysis & Notes = empty (not yet analyzed)
- User may provide vendor list to further filter

## Full Research Requirement (NO LAZY REVIEW)
When analyzing invoices, NEVER mark REVIEW without doing thorough research:

1. **Web search the vendor** to understand what they sell
2. **Look up addresses** to verify city/jurisdiction
3. **Research product/service** to determine taxability
4. **Provide informed guidance** with sources

Instead of: `"REVIEW - unclear product type"`
Write: `"Based on web search, [vendor] provides [service type], which is [taxable/exempt] per [RCW citation] because [reason]. Recommend: [specific action]"`

## RCW Citation Rules

**Source of Truth:** `~/Downloads/Summary of Impacts 2024.xlsx` → "ALL Impacts" sheet → Tax Type = "Retail Sales & Use Tax"

| Chapter | Name | Use For |
|---------|------|---------|
| 82.04 | B&O Tax | Definitions only (what IS taxable) |
| 82.08 | Retail Sales Tax | Sales tax EXEMPTIONS (82.08.02XXX) |
| 82.12 | Use Tax | Use tax EXEMPTIONS (82.12.02XXX) |

**Key Exemption RCWs:**
- **M&E Exemption**: 82.08.02565 / 82.12.02565 - **EXCLUDES TELECOM** (T-Mobile cannot claim)
- **Out-of-State**: 82.08.0264 / 82.12.0264
- **Resale**: 82.08.0251 / 82.12.0251
- **Multi-Point Use**: 82.08.0208(4) / 82.12.0208(7)
- **Custom Software**: 82.04.050(6)(a)(i)-(ii) (exclusion from retail sale definition)

**DO NOT cite 82.04.050 as an exemption basis** - it's the taxability definition, not an exemption.

## Analysis Output Requirements
- **AI_Reasoning**: Step-by-step rationale for each determination
- **Invoice hyperlinks**: `=HYPERLINK("http://localhost:8888/filename.pdf","filename.pdf")`
- **Service_Classification**: TOWER_SERVICES, CONSTRUCTION_SERVICES, PROFESSIONAL_SERVICES, etc.
- **For REVIEW rows**: Specific guidance on what to check and why (with research done)

## Mandatory Invoice Reading (VERIFICATION REQUIRED)

**CRITICAL: Every analysis MUST include fields that can ONLY come from reading the actual invoice PDF.**

### Required Verification Fields
For each row analyzed, the AI_Reasoning MUST include:

1. **Invoice Number** - The actual invoice # printed on the PDF (not the filename)
2. **Invoice Date** - Date shown on the invoice
3. **Ship-To Address** - Full address from the invoice (city, state, zip)
4. **Matched Line Item** - The specific line item from the invoice that corresponds to this Excel row

### AI_Reasoning Format (MANDATORY)
```
INVOICE VERIFIED: Invoice #[number] dated [date]
SHIP-TO: [full address from invoice]
MATCHED LINE ITEM: [description] @ $[amount] (Line [X] on invoice)
---
[Rest of analysis...]
```

### Line Item Matching (Multi-Row Invoices)

**When one invoice PDF contains multiple line items and the Excel has multiple rows referencing that invoice:**

1. Read the invoice PDF and list ALL line items with descriptions and amounts
2. For EACH Excel row:
   - Look at `txz01_po_description` and `hwbas_tax_base_lc` (tax base amount)
   - Find the invoice line item that matches by description keywords AND amount
   - Document the match: "Excel row describes '[PO desc]' @ $X → matches Invoice Line [Y]: '[invoice desc]' @ $X"

3. If no clear match exists:
   - Flag as `Needs_Review: Yes`
   - Document: "Could not match Excel description '[desc]' to any invoice line item"

### Example: Multi-Line Invoice Matching

**Invoice PDF shows:**
- Line 1: R660 DC Control Plane/HCI - $15,644,662.79
- Line 3: R660 DC Worker Node - $10,201,126.44
- Line 5: R760 DC Storage Node - $3,248,185.64

**Excel has 3 rows with same Inv 1 file:**
| Row | txz01_po_description | hwbas_tax_base_lc |
|-----|---------------------|-------------------|
| A | R660 DC - Control Plane/HCI Quote #6967... | 15,644,662.79 |
| B | R660 DC - Worker Node Quote #6968... | 10,201,126.44 |
| C | R760 DC - Storage Node Quote #6968... | 3,248,185.64 |

**Analysis for Row A:**
```
INVOICE VERIFIED: Invoice #11512729 dated 18-Sep-2024
SHIP-TO: T-Mobile USA Inc., 15015 NE 90th St, Bay Door 3, REDMOND WA 98052
MATCHED LINE ITEM: R660 DC - Control Plane/HCI @ $15,644,662.79 (Line 1 on invoice)
---
Excel description "R660 DC - Control Plane/HCI Quote #6967" matches Invoice Line 1...
```

### Verification Checklist
Before finalizing any analysis, confirm:
- [ ] Invoice # in AI_Reasoning matches actual PDF (not filename)
- [ ] Ship-to address extracted from PDF, not assumed
- [ ] Each Excel row matched to specific invoice line item
- [ ] Tax amount on invoice matches Excel `hwste_tax_amount_lc`
- [ ] If mismatch found, flagged in `Vendor_Mismatch` or `Location_Mismatch`

### Invalid Analysis (Will Be Rejected)
Analysis is INVALID if:
- AI_Reasoning doesn't include "INVOICE VERIFIED:" header
- No specific line item match documented
- Ship-to address is generic (e.g., "WA" without full address)
- Product description copied from `txz01_po_description` without invoice verification

---

# Development Rules

1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.
8. DO NOT BE LAZY. NEVER BE LAZY. IF THERE IS A BUG FIND THE ROOT CAUSE AND FIX IT. NO TEMPORARY FIXES. YOU ARE A SENIOR DEVELOPER. NEVER BE LAZY
9. MAKE ALL FIXES AND CODE CHANGES AS SIMPLE AS HUMANLY POSSIBLE. THEY SHOULD ONLY IMPACT NECESSARY CODE RELEVANT TO THE TASK AND NOTHING ELSE. IT SHOULD IMPACT AS LITTLE CODE AS POSSIBLE. YOUR GOAL IS TO NOT INTRODUCE ANY BUGS. IT'S ALL ABOUT SIMPLICITY

# Code Size Guidelines

- Flag files over 1,500 lines for potential splitting
- Flag functions over 150 lines for refactoring
- Before adding significant code to a large file, check line count with `wc -l` and ask if we should split first

---

# Output File Rules

**ONLY write to the 3 standard output files** - never create one-off files like `SalesTax_RealRun_All.xlsx` or `MultiVendor_Analyzed.xlsx`:

| Source | Output (ALWAYS use this) |
|--------|--------------------------|
| Sales Tax 2024 | `Final 2024 Denodo Review - Analyzed.xlsx` |
| Use Tax 2023 | `Phase_3_2023_Use Tax - Analyzed.xlsx` |
| Use Tax 2024 | `Phase_3_2024_Use Tax - Analyzed.xlsx` |

Append to existing files. Track which rows are analyzed via empty analysis columns.

---

# Analysis Reference

| Resource | Location |
|----------|----------|
| Tax scenarios & exemptions | `knowledge_base/states/washington/tax_rules.json` |
| Valid RCWs (364 citations) | `knowledge_base/target_rcws.txt` |
| Contextual analysis guide | `.claude/skills/analyze-invoices/analyze-invoices.md` |
| WA tax rates by location | `data/wa_rates/Q424_Excel_LSU-rates.xlsx` |
| Invoice PDFs | `~/Desktop/Invoices/` |
| WACs (administrative rules) | `knowledge_base/wa_tax_law/wac/title_458/` |
| ETAs (DOR guidance) | `knowledge_base/states/washington/ETAs/` |

---

# T-Mobile Specific Notes

**Company Classification:** Telecommunications company (PUBLIC UTILITY under WA law)

**CANNOT Claim:**
- M&E Exemption (RCW 82.08.02565 / 82.12.02565) - statute excludes public utilities including telecom

**Best Refund Opportunities:**
- **Multi-Point Use (MPU)** - T-Mobile has nationwide employees using cloud/SaaS services
- **Out-of-State** - Equipment/services delivered or performed outside WA
- **Professional Services** - Consulting/advisory services (human effort exclusion)
- **Construction OOS** - Tower work at job sites outside WA (sourced to site location per WAC 458-20-170)
- **Wrong Rate** - Vendor charged incorrect local tax rate for delivery location
