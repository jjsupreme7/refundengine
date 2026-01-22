# Analyze Use Tax 2023

## Before Starting
Invoke the `/analyze-invoices` skill to load the full analysis methodology.

Analyze invoices from the Use Tax 2023 workbook using Claude Code (direct analysis, no external APIs).

## Source & Output
- **Source:** `~/Desktop/Files/Files to be Analyzed/Use Tax Phase 3 2023.xlsx`
- **Output:** `~/Desktop/Files/Analyzed_Output/Phase_3_2023_Use Tax - Analyzed.xlsx`

## Standard Filters (Always Applied)
- `INDICATOR` = "Remit" (exact match, not "Do Not Remit")
- `KOM Analysis & Notes` = empty (not yet analyzed)

## When This Command Runs

1. Load the source file and apply standard filters
2. Show summary: "Found X unanalyzed rows (total tax: $Y)"
3. **ASK the user** what to analyze using AskUserQuestion:
   - Specific vendor(s)?
   - High-value rows only (min amount)?
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
| Vendor | `Vendor` | "ACME", "B & C TOWER" |
| Invoice Number | `INVNO` | "12345", list of numbers |
| PO Number | `PO Number` | "4900123456" |
| Tax Amount | `hwste_tax_amount_lc` | min: 500, max: 10000 |
| Limit | (row count) | 5, 10, 20 |

## Column Order for Output

See CLAUDE.md "Use Tax Column Order (2023 & 2024)" section for the full 31-column specification.

## References
- Analysis guidance: `.claude/skills/analyze-invoices/analyze-invoices.md`
- Tax scenarios: `knowledge_base/states/washington/tax_rules.json`
- Valid RCWs: `knowledge_base/target_rcws.txt`
- Invoices: `~/Desktop/Invoices/`
