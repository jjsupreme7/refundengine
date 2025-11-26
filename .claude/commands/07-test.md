# Run Test Suite

Runs automated tests using pytest to verify the system works correctly. Run this before committing code changes, after modifying core logic, or to diagnose failures.

## What Gets Tested

| Test File | What It Checks |
|-----------|----------------|
| test_enhanced_rag.py | RAG retrieval accuracy against known questions |
| test_multiple_questions.py | RAG handles diverse tax law questions |
| test_pattern_integration.py | Vendor patterns correctly influence analysis |

## How It Fits In The System

```
[You make code changes]
        |
        v
    /07-test
        |
        +-- PASS --> Safe to commit
        |
        +-- FAIL --> Fix the bug first
```

Tests verify that:
1. RAG returns relevant tax law chunks for questions
2. AI analysis produces expected outputs for known scenarios
3. Vendor pattern matching works correctly

## Arguments

$ARGUMENTS (optional)
- No args → Run all tests
- File path → Run specific test file
- `-k "pattern"` → Run tests matching pattern
- `-v` → Verbose output (shows each test)
- `-x` → Stop on first failure

## Examples

```bash
/07-test                                    # Run all tests
/07-test tests/test_enhanced_rag.py         # Run one file
/07-test -k "vendor"                        # Tests with "vendor" in name
/07-test -v                                 # Verbose output
/07-test -x                                 # Stop on first failure
```

## Success Looks Like

```
==================== test session starts ====================
collected 15 items

tests/test_enhanced_rag.py::test_manufacturing_exemption PASSED
tests/test_enhanced_rag.py::test_digital_products PASSED
tests/test_multiple_questions.py::test_rcw_citation PASSED
...

==================== 15 passed in 12.34s ====================
```

## Common Failures

- `FAILED test_enhanced_rag` → RAG not returning expected chunks. Check `/06-verify-chunks`
- `Connection error` → Supabase/OpenAI credentials missing
- `ImportError` → Missing package. Run `pip install -r requirements.txt`

## When To Run

- Before git commit/push
- After changing `core/enhanced_rag.py`
- After changing `analysis/fast_batch_analyzer.py`
- After modifying database schema

```bash
pytest tests/ -v $ARGUMENTS
```
