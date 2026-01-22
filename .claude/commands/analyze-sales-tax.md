# Analyze Sales Tax 2024

## Before Starting
Invoke the `/analyze-invoices` skill to load the full analysis methodology.

Analyze invoices from the Sales Tax 2024 workbook using Claude Code (direct analysis, no external APIs).

## Source & Output
- **Source:** `~/Desktop/Files/Files to be Analyzed/Final 2024 Denodo Review.xlsx` (sheet: "Real Run")
- **Output:** `~/Desktop/Files/Analyzed_Output/Final 2024 Denodo Review - Analyzed.xlsx`

## Standard Filters (Always Applied)
- `Paid?` = "PAID"
- `Recon Analysis` = empty (not yet analyzed)
- `Inv 1` = not empty (has invoice)

## When This Command Runs

1. Load the source file and apply standard filters
2. Show summary: "Found X unanalyzed rows (total tax: $Y)"
3. **ASK the user** what to analyze using AskUserQuestion:
   - Specific vendor(s)?
   - High-value rows only (min amount)?
   - Specific quadrant?
   - Limit to N rows?
   - Other filter?
4. Apply user's filter selection
5. Run contextual analysis per `.claude/skills/analyze-invoices/analyze-invoices.md`
6. Write results to output file with:
   - Invoice hyperlinks: `=HYPERLINK("http://localhost:8888/filename.pdf","filename.pdf")`
   - Full AI_Reasoning for each row
   - Proper citations from `knowledge_base/target_rcws.txt`

## Available Filter Columns

| Filter | Column | Examples |
|--------|--------|----------|
| Vendor | `name1_po_vendor_name` | "MICROSOFT", "B & C TOWER" |
| Document Number | `belnr_max_document_number` | "1234567", list of numbers |
| PO Number | `ebeln_po_number` | "4900123456" |
| Tax Amount | `hwste_tax_amount_lc` | min: 500, max: 10000 |
| Quadrant | `quadrant` | "In WA", "Out WA" |
| Rate | `rate` | min: 0.08, max: 0.12 |
| Material Group | `matk1_po_material_group_desc` | "SOFTWARE", "HARDWARE" |
| Limit | (row count) | 5, 10, 20 |

## Column Order for Output

See CLAUDE.md "Sales Tax 2024 Column Order" section for the full 36-column specification.

## References
- Analysis guidance: `.claude/skills/analyze-invoices/analyze-invoices.md`
- Tax scenarios: `knowledge_base/states/washington/tax_rules.json`
- Valid RCWs: `knowledge_base/target_rcws.txt`
- Invoices: `~/Desktop/Invoices/`
