# Verify Environment Setup

Comprehensive health check of your development environment. Verifies all dependencies, credentials, and services are properly configured. Run this when things aren't working or on a new machine.

## What It Checks

| Category | Checks |
|----------|--------|
| Python | Version 3.10+, venv activated |
| Packages | All requirements.txt packages installed |
| Environment | .env file exists with required keys |
| Supabase | Can connect, tables exist |
| OpenAI | API key valid, can make requests |
| Directories | Required folders exist (knowledge_base/, outputs/) |

## How It Fits In The System

```
"Nothing is working!"
        |
        v
    /09-verify-setup
        |
        +-- Shows: "OPENAI_API_KEY: MISSING"
        |
        v
    You fix .env file
        |
        v
    Everything works
```

This is your first stop when debugging environment issues.

## Arguments

None

## Example

```bash
/09-verify-setup
```

## Success Looks Like

```
=== Environment Verification ===

Python:
  Version: 3.12.0 ✓
  Virtual env: active ✓

Packages:
  openai: 1.12.0 ✓
  supabase: 2.3.0 ✓
  streamlit: 1.31.0 ✓
  pandas: 2.2.0 ✓
  ... (all packages OK)

Environment Variables:
  OPENAI_API_KEY: ✓ (set)
  SUPABASE_URL: ✓ (set)
  SUPABASE_SERVICE_ROLE_KEY: ✓ (set)

Connections:
  Supabase: ✓ (connected, 12 tables found)
  OpenAI: ✓ (API responding)

Directories:
  knowledge_base/: ✓ (exists, 847 files)
  outputs/: ✓ (exists)

=== All checks passed ===
```

## Red Flags

- `OPENAI_API_KEY: MISSING` → Add to .env file
- `Supabase: FAILED` → Check URL and key in .env
- `Virtual env: not active` → Run `source venv/bin/activate`
- `Package X: MISSING` → Run `pip install -r requirements.txt`

## When To Run

- First time setup on new machine
- After git pull with new dependencies
- When any command fails with import/connection errors
- When you switch between computers

```bash
python scripts/services/verify_setup.py
```
