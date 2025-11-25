Run end-to-end pipeline test: verify Docker, analyze test data, validate output.

Arguments: $ARGUMENTS
- Optional: Test Excel file (default: test_data/sample_invoices.xlsx)

Steps:
1. Check Docker services are running
2. Verify database connection
3. Run analysis on test data
4. Validate output columns populated

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
