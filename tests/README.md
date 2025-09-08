# Tests

This directory contains comprehensive tests for the Datadog MCP server.

## Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=../server --cov-report=term-missing

# Run specific test file
python -m pytest test_complete.py -v
```

## Test Files

- `test_complete.py` - Main comprehensive test suite
- `test_integration.py` - Integration tests
- `test_server.py` - Server functionality tests
- `test_tools.py` - Individual tool tests
- `pytest.ini` - Pytest configuration
