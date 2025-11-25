Verify all critical components are installed and configured:
1. Testing Framework (pytest, coverage)
2. Message Queue (Celery, Redis)
3. Database (Supabase connection)
4. API Services (OpenAI key)

Use this after environment changes, troubleshooting, or on a new machine.

```bash
python scripts/services/verify_setup.py
```
