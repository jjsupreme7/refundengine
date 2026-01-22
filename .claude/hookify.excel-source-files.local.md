---
name: excel-source-files
enabled: true
event: file
action: block
pattern: Files to be Analyzed/.*\.(xlsx|xlsb)$
---

**Source Excel File Protection**

You're trying to edit a file in the **source data folder**. These are the original input files that should never be modified.

**Why this is blocked:**
- `Files to be Analyzed/` contains original source data
- Modifications could corrupt the audit trail
- The user manages these files manually

**What you should do instead:**
- Write to the **output folder**: `~/Desktop/Files/Analyzed_Output/`
- Use the standard output files:
  - `Final 2024 Denodo Review - Analyzed.xlsx`
  - `Phase_3_2023_Use Tax - Analyzed.xlsx`
  - `Phase_3_2024_Use Tax - Analyzed.xlsx`

**Reading is allowed** - you can read source files for analysis.

