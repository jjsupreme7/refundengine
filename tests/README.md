# Tests Directory

This folder contains automated tests for the Refund Engine system.

## Running Tests

### Run All Tests
```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Tests
```bash
# Single test file
pytest tests/test_chatbot.py

# Single test function
pytest tests/test_rag.py::test_search_tax_law

# Tests matching pattern
pytest -k "test_security"
```

---

## Test Files

### `test_chatbot.py`
**Tests**: Chatbot functionality
**Covers**:
- Chat interface
- Message processing
- Response generation
- Context management

**Run**: `pytest tests/test_chatbot.py`

---

### `test_rag.py`
**Tests**: RAG (Retrieval-Augmented Generation) system
**Covers**:
- Vector search
- Document retrieval
- Embedding generation
- Query processing
- RPC function calls

**Run**: `pytest tests/test_rag.py`

---

### `test_pii_protection.py`
**Tests**: PII (Personally Identifiable Information) protection
**Covers**:
- PII detection
- Data redaction
- Secure storage
- Compliance requirements

**Run**: `pytest tests/test_pii_protection.py`

---

### `test_agentic_rag.py`
**Tests**: Agentic RAG features
**Covers**:
- Self-verification (Corrective RAG)
- Query expansion
- Advanced filtering
- Multi-step reasoning

**Run**: `pytest tests/test_agentic_rag.py`

---

## Test Configuration

### Environment Setup
Tests use test-specific environment variables:
```bash
# Use test database/environment
export TEST_MODE=true
export SUPABASE_URL_TEST=https://test-project.supabase.co
```

### Fixtures
Common test fixtures are in `conftest.py`:
- Database connections
- Mock data
- Test clients
- Cleanup functions

---

## Writing New Tests

### Test File Structure
```python
"""
Test module description

Tests for [component name]
"""
import pytest
from module import function_to_test

def test_basic_functionality():
    """Test that basic feature works"""
    result = function_to_test()
    assert result is not None

def test_edge_case():
    """Test edge case handling"""
    result = function_to_test(edge_case_input)
    assert result == expected_value
```

### Naming Conventions
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Best Practices
1. **One assert per test** (when possible)
2. **Descriptive names** that explain what's being tested
3. **Arrange-Act-Assert** pattern
4. **Use fixtures** for common setup
5. **Mock external services** (APIs, databases)

---

## Test Coverage

### Check Coverage
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Goals
- Core modules: 80%+ coverage
- Analysis modules: 70%+ coverage
- Utility scripts: 60%+ coverage

---

## Continuous Integration

Tests run automatically on:
- Every commit (local pre-commit hook)
- Every pull request (GitHub Actions)
- Every merge to main

###GitHub Actions Workflow
See `.github/workflows/tests.yml` for CI configuration

---

## Troubleshooting

### "Module not found" errors
```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Database connection errors
```bash
# Ensure test environment variables are set
export TEST_MODE=true
export SUPABASE_URL_TEST=your-test-url
```

### Tests hang or timeout
```bash
# Run with timeout
pytest --timeout=30

# Run specific slow test
pytest tests/slow_test.py --timeout=60
```

---

## Related Documentation

- [Testing Guide](../docs/guides/TESTING_GUIDE.md) - Comprehensive testing guide
- [Security Best Practices](../docs/security/SECURITY_BEST_PRACTICES.md) - Security testing
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute tests

---

**Last Updated**: 2025-11-13
