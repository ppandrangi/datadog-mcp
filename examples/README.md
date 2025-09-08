# Examples

This directory contains example clients and utilities for the Datadog MCP server.

## Files

- `demo_client.py` - Demonstrates available queries and response formats
- `real_client.py` - Example of connecting to actual Datadog API
- `test_client.py` - Mock client for testing server functionality
- `validate_syntax.py` - Code validation utility

## Usage

```bash
# Show available queries
python demo_client.py

# Test with real Datadog connection (requires credentials)
DATADOG_API_KEY=your_key DATADOG_APP_KEY=your_app_key python real_client.py
```
