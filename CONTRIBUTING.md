# Contributing

Thank you for your interest in contributing to the Datadog MCP Server!

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Run tests: `cd tests && python -m pytest`

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for public functions
- Keep functions focused and small

## Testing

- Write tests for new features
- Maintain test coverage above 90%
- Test both success and error cases
- Use async/await patterns consistently

## Pull Requests

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## Safety

- Only add read-only operations
- No mutation/write operations allowed
- Validate all inputs
- Handle errors gracefully
