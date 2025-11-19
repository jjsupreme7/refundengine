---
name: test-files-location
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: ^[^/]*test_.*\.py$
  - field: file_path
    operator: not_contains
    pattern: tests/
---

⚠️ **Test file outside tests/ directory detected!**

You're trying to create/edit a test file in the root directory:
- Test files should be in `tests/` directory
- This keeps the project organized and professional

**What to do:**
- Move this file to `tests/` or `tests/utilities/`
- Use the proper test directory structure

**Why this matters:**
- Other engineers expect tests in `tests/` directory
- Keeps root directory clean
- Standard Python project structure
