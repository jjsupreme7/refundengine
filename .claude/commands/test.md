Run the test suite with pytest.

Arguments: $ARGUMENTS
- Optional: specific test file or -k "pattern" to filter tests

Examples:
- /test (run all tests)
- /test tests/test_enhanced_rag.py
- /test -k "vendor"

```bash
pytest tests/ -v $ARGUMENTS
```
