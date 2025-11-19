---
name: temp-files
enabled: true
event: file
action: block
pattern: (^|/)((temp|scratch|debug|try|test123|demo)_.*\.(py|js|ts|sh)|.*_(old|backup|copy|tmp)\.(py|js|ts|sh))
---

🚫 **Temporary/scratch file detected!**

You're trying to create a file that looks temporary:
- `temp_*.py`
- `scratch_*.py`
- `debug_*.py`
- `try_*.py`
- `*_old.py`
- `*_backup.py`

**Why this is blocked:**
- Temporary files clutter the codebase
- They shouldn't be committed to git
- Other engineers will be confused by them

**What to do instead:**
- Use proper file names if this is permanent code
- Create files in a `scratch/` folder (add to .gitignore)
- Delete after testing
