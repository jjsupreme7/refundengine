---
name: database-credentials
enabled: true
event: code
action: block
pattern: (supabase_url|api_key|password|secret_key|service_role)\s*=\s*["'][^"']+["']
---

**Hardcoded Credentials Detected**

You're attempting to hardcode credentials directly in source code.

**Why this is blocked:**
- Credentials in code can be accidentally committed to git
- Secrets should be in `.env` files (which are gitignored)
- Hardcoded values make rotation difficult

**What you should do instead:**
- Add the credential to `.env` (manually)
- Reference it via `os.getenv("VARIABLE_NAME")`
- Use the existing config patterns in `core/config.py`

**Example:**
```python
# Bad (blocked)
supabase_url = "https://xxx.supabase.co"

# Good (allowed)
supabase_url = os.getenv("SUPABASE_URL")
```

