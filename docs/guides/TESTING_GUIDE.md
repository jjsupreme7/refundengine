# Testing Guide

## Overview

This project uses **pytest** for testing with coverage tracking to ensure code quality and financial accuracy.

## Installation

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock coverage

# Or install all requirements
pip install -r requirements.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=core --cov=scripts --cov=analysis --cov-report=term-missing
```

### Run specific test file
```bash
pytest tests/test_refund_calculations.py
```

### Run specific test
```bash
pytest tests/test_refund_calculations.py::TestMPUCalculations::test_mpu_basic_calculation
```

### Run with verbose output
```bash
pytest -v
```

### Run only fast tests
```bash
pytest -m "not slow"
```

### Generate HTML coverage report
```bash
pytest --cov=core --cov=scripts --cov=analysis --cov-report=html
open htmlcov/index.html
```

## Test Organization

```
tests/
├── __init__.py
├── conftest.py                    # Pytest configuration and fixtures
├── test_refund_calculations.py    # Critical financial calculations
├── test_vendor_research.py        # Vendor research logic
└── test_analyze_refunds.py        # Invoice analysis
```

## Critical Tests

### Financial Calculation Tests
These tests ensure refund calculations are correct:

- **test_mpu_basic_calculation** - Multi-point use refunds
- **test_professional_services_exemption** - Non-taxable services
- **test_digital_automated_services** - SaaS classification
- **test_refund_amount_calculations** - Actual dollar amounts

### Data Validation Tests
- **test_validates_tax_amount_positive** - Tax amounts must be positive
- **test_validates_date_format** - Dates must be valid
- **test_validates_invoice_number_present** - Invoice numbers required

## Coverage Requirements

- **Minimum coverage: 70%**
- Critical modules (refund calculations) should have >90% coverage
- New code should include tests

## Continuous Integration

Tests run automatically on:
- Every push to `main` or `develop` branch
- Every pull request

See `.github/workflows/test.yml` for CI configuration.

## Writing New Tests

### Example test structure:
```python
def test_my_feature():
    # Arrange - Set up test data
    input_data = {"amount": 10000, "tax": 1000}

    # Act - Execute the code being tested
    result = calculate_refund(input_data)

    # Assert - Verify the result
    assert result == 9000, "Should refund 90%"
```

### Using fixtures:
```python
def test_with_fixture(sample_invoice_data):
    # sample_invoice_data comes from conftest.py
    result = analyze_invoice(sample_invoice_data)
    assert result is not None
```

### Mocking external APIs:
```python
from unittest.mock import patch

@patch('analysis.analyze_refunds.client')
def test_with_mock(mock_openai):
    mock_openai.chat.completions.create.return_value = Mock(...)
    result = my_function()
    assert result == expected
```

## Pre-commit Testing

Before committing code:
```bash
# Run tests
pytest

# Check coverage
pytest --cov=core --cov=scripts --cov=analysis

# Run linting
black core/ scripts/ analysis/ tests/
flake8 core/ scripts/ analysis/
```

## Troubleshooting

### Tests fail with "ModuleNotFoundError"
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check PYTHONPATH
export PYTHONPATH=/Users/jacoballen/Desktop/refund-engine:$PYTHONPATH
```

### Tests fail with API errors
```bash
# Tests use mocked APIs by default
# If you see API errors, check conftest.py fixtures
```

### Coverage too low
```bash
# Identify untested code
pytest --cov=core --cov-report=term-missing

# Look for lines marked with "Missing" in coverage report
```

## Best Practices

1. **Test financial calculations thoroughly** - Bugs here cost money
2. **Mock external APIs** - Tests should be fast and not depend on internet
3. **Use fixtures for common test data** - Defined in conftest.py
4. **Test edge cases** - Empty inputs, negative numbers, etc.
5. **Keep tests isolated** - Each test should be independent
6. **Name tests descriptively** - test_mpu_refund_with_zero_wa_usage

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
