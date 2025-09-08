# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by:

1. **Do NOT** create a public GitHub issue
2. Send an email to the maintainers with details of the vulnerability
3. Include steps to reproduce the issue
4. Provide any relevant logs or screenshots

## Security Best Practices

When using this MCP server:

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files or secure environment variable management
3. **Network Security**: Run the server in a secure network environment
4. **Access Control**: Limit access to the MCP server to authorized users only
5. **Regular Updates**: Keep dependencies updated to patch security vulnerabilities

## Datadog API Security

This server requires Datadog API and Application keys:
- Store these securely using environment variables
- Use the principle of least privilege for API key permissions
- Regularly rotate your API keys
- Monitor API key usage in Datadog's security logs

## Dependencies

This project uses the official Datadog API client library. Security updates for dependencies are monitored and applied promptly.
