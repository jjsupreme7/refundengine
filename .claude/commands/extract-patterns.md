---
description: Extract patterns from historical data
---

Extract vendor and keyword patterns from historical data:

1. **Determine data source:**
   - If `$ARGUMENTS` contains "denodo": Extract from Denodo 2019-2023 data
   - If `$ARGUMENTS` contains "phase2": Extract from Phase 2 Master Refunds
   - Otherwise, ask user which source

2. **Run extraction:**

   For Denodo data:
   ```bash
   python scripts/extract_patterns_from_denodo.py
   ```

   For Phase 2 data:
   ```bash
   python scripts/extract_patterns_from_phase2.py
   ```

3. **Report results:**
   - Number of vendor patterns extracted
   - Number of keyword patterns extracted
   - Number of refund basis patterns extracted
   - Location of output JSON files in `extracted_patterns/`

4. **Quality filtering applied:**
   - PDF filenames filtered out
   - Pure numeric codes removed
   - Stopwords and non-text patterns cleaned
