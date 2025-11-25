---
name: env-files
enabled: true
event: file
action: block
pattern: (^|/)\.env$
---

🔒 **SECURITY WARNING: Attempting to edit .env file!**

**CRITICAL:** .env files contain secrets and should NEVER be committed to git!

**Before proceeding:**
1. ✅ Verify `.env` is in `.gitignore`
2. ✅ Use `.env.example` for templates (without real values)
3. ✅ Never commit API keys, passwords, or tokens

**What you should do:**
- Edit `.env` locally only
- Keep secrets out of version control
- Use environment variables in production

**If you need to commit configuration:**
- Create `.env.example` with placeholder values
- Document required variables in README
