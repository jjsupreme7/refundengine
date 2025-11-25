---
description: Verify environment setup and connectivity
---

Verify the RefundEngine environment is properly configured:

1. **Run setup verification:**
   ```bash
   python scripts/verify_setup.py
   ```

2. **Check environment variables:**
   - OPENAI_API_KEY
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE_KEY

3. **Verify database connectivity:**
   ```bash
   python scripts/check_supabase_tables.py
   ```

4. **Report status:**
   - Which components are working
   - What's missing or misconfigured
   - Suggested fixes for any issues

5. **Optional: Check storage usage**
   ```bash
   python scripts/check_storage_usage.py
   ```
