# End-to-End Pipeline Test

Runs a complete integration test of the entire system: checks infrastructure, verifies database, runs analysis on test data, and validates output. Use this to confirm everything works together.

## What It Tests

1. **Docker services** - Are redis/postgres running?
2. **Database connection** - Can we reach Supabase? Are tables there?
3. **Analysis pipeline** - Can we process a test Excel file?
4. **Output validation** - Did AI columns get populated?

## How It Fits In The System

```
/12-test-pipeline
        |
        v
    [Check Docker] --> FAIL? --> "Run /01-docker-up"
        |
        v (PASS)
    [Verify Database] --> FAIL? --> "Check Supabase credentials"
        |
        v (PASS)
    [Run Analysis] --> FAIL? --> "Check /03-logs worker"
        |
        v (PASS)
    [Validate Output] --> FAIL? --> "AI not populating columns"
        |
        v (PASS)
    "Pipeline healthy!"
```

This is more comprehensive than `/07-test` (unit tests). This tests the full end-to-end flow.

## Arguments

$ARGUMENTS (optional)
- Default: Uses `test_data/sample_invoices.xlsx`
- Provide path to use different test file

## Examples

```bash
/12-test-pipeline                           # Use default test data
/12-test-pipeline test_data/my_test.xlsx    # Use specific file
```

## Success Looks Like

```
=== Checking Docker services ===
refund-engine-redis: Up 2 hours
refund-engine-postgres: Up 2 hours

=== Verifying database ===
Quick verification complete.
Documents: 1,312 | Chunks: 24,891 | All healthy.

=== Running test analysis ===
Processing 5 rows...
Row 1: MICROSOFT CORP → Exempt (94%)
Row 2: HOME DEPOT → Taxable (98%)
...
Analysis complete.

=== Pipeline test complete ===
```

## Common Failures

- Docker check fails → Run `/01-docker-up`
- Database verification fails → Check `/09-verify-setup`
- Analysis fails → Check `/03-logs worker`
- Test file not found → Verify the path exists

## When To Run

- After setting up a new environment
- After major code changes
- Before demo or presentation
- Weekly sanity check

```bash
echo "=== Checking Docker services ===" && \
docker ps --format "{{.Names}}: {{.Status}}" | grep -E "(redis|postgres)" && \
echo "" && \
echo "=== Verifying database ===" && \
python scripts/utils/verify_chunks.py --quick && \
echo "" && \
echo "=== Running test analysis ===" && \
python analysis/fast_batch_analyzer.py --excel "${ARGUMENTS:-test_data/sample_invoices.xlsx}" --state washington --limit 5 && \
echo "" && \
echo "=== Pipeline test complete ==="
```
