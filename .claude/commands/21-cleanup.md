# Clean Up Project Files

Interactive cleanup command that helps you find and remove unnecessary files from the project. Use this periodically to keep the codebase clean.

## What It Looks For

1. **Test artifacts:**
   - `*_test.*`, `test_*.py` (outside tests/ folder)
   - `*.tmp`, `*.bak` files
   - Files in `/tmp/` directories

2. **Code quality issues:**
   - Commented-out code blocks
   - Unused imports
   - Debug print statements
   - Duplicate functions

3. **Outdated files:**
   - Old scripts no longer referenced
   - Deprecated folders
   - Orphaned configuration files

## How It Works

This is an INTERACTIVE command - it doesn't blindly delete. It:
1. Scans for potential cleanup targets
2. Shows you what it found
3. Asks before deleting anything

```
/21-cleanup
        |
        v
    [Scan project]
        |
        v
    "Found 15 items to review:"
    - test_output.xlsx (tmp file)
    - old_analyzer.py (not imported anywhere)
    - debug_logs/ (empty folder)
        |
        v
    "Delete test_output.xlsx? [y/N]"
```

## Arguments

None (interactive)

## Example Session

```bash
/21-cleanup

=== Project Cleanup ===

Scanning for cleanup targets...

Found 8 items:

Temporary files (3):
  1. outputs/test_output.xlsx (2.1 MB)
  2. outputs/debug_log.txt (45 KB)
  3. .DS_Store

Potentially unused code (2):
  4. scripts/old_importer.py (not imported)
  5. core/deprecated_rag.py (not imported)

Empty directories (1):
  6. tmp/

Large files (2):
  7. knowledge_base/backup_2024.zip (500 MB)
  8. outputs/full_export.xlsx (150 MB)

Review each item? [y/N]
```

## Safety

- **Always asks first** - Nothing deleted without confirmation
- **Shows context** - File size, last modified, why flagged
- **Skips important files** - Won't suggest deleting core code

## When To Use

- Before major commits
- When disk space is low
- Quarterly maintenance
- After completing a project phase

## What It Won't Touch

- Anything in `core/`, `analysis/`, `dashboard/`
- Files tracked in git (unless explicitly orphaned)
- Configuration files (`.env`, `requirements.txt`)
- The knowledge base PDFs

---

Be proactive but ASK before deleting anything that might be important.
