---
name: prefer-claude-code-analysis
enabled: true
event: bash
pattern: run_sales_tax_real_run\.py|run_use_tax_phase3\.py|fast_batch_analyzer\.py
action: warn
---

**API Analysis Script Detected!**

You're about to run a script that uses **external APIs (GPT-4o, Gemini)** which will incur costs.

**Did the user ask for "Claude analysis" or say "you do it"?**

If so, you should do the analysis **directly yourself** instead:
1. Read the Excel file to get rows needing analysis
2. Read each invoice PDF directly with the Read tool
3. Analyze the transactions yourself using your knowledge
4. Write results back to the Excel file

**Only proceed with this script if:**
- The user explicitly asked for API-based analysis
- The user confirmed they want to use external APIs

**To do Claude Code analysis instead:**
- Read the source Excel file
- For each row: read the invoice PDF, analyze it, determine refund eligibility
- Write results to the output Excel file
