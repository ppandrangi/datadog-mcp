# Datadog MCP Server

A comprehensive Model Context Protocol (MCP) server for Datadog integration, providing full CRUD access to Datadog APIs with modern async patterns. Built with the official Datadog Python SDK and MCP Python SDK.

## 🚀 Features

- 🔧 **Full CRUD operations** - Create, read, update, delete across all supported APIs
- ⚡ **Async operations** - Built with AsyncApiClient for optimal performance
- 🔄 **Automatic retries** - Rate limiting and error handling with exponential backoff
- 📊 **Comprehensive coverage** - 31 tools across all major Datadog APIs
- 💾 **Local caching** - Results stored as timestamped JSON files
- 🔒 **Type-safe** - Full type hints and Pydantic models
- 📈 **Built-in analysis** - Statistical analysis, trend detection, and data summarization
- 🛡️ **Security-first** - Environment-based credential management

## 📋 Prerequisites

- Python 3.8+
- Valid Datadog API and Application keys
- MCP-compatible client (VS Code, Cursor, Claude Desktop, etc.)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATADOG_API_KEY="your_api_key"
export DATADOG_APP_KEY="your_app_key"
export DATADOG_SITE="datadoghq.com"  # Optional

# Run the server
python server.py
```

## MCP Client Integration

### VS Code with Continue

1. Install the Continue extension in VS Code
2. Add to your Continue config (`~/.continue/config.json`):

```json
{
  "mcpServers": {
    "datadog": {
      "command": "python",
      "args": ["/path/to/datadog-mcp-python/server.py"],
      "env": {
        "DATADOG_API_KEY": "your_api_key",
        "DATADOG_APP_KEY": "your_app_key"
      }
    }
  }
}
```

### Cursor

1. Open Cursor settings
2. Add MCP server configuration:

```json
{
  "mcp.servers": {
    "datadog": {
      "command": "python",
      "args": ["/path/to/datadog-mcp-python/server.py"],
      "env": {
        "DATADOG_API_KEY": "your_api_key",
        "DATADOG_APP_KEY": "your_app_key"
      }
    }
  }
}
```

### Amazon Q Developer

1. Configure in your Q Developer settings:

```json
{
  "mcpServers": {
    "datadog-mcp": {
      "command": "python3",
      "args": ["/path/to/datadog-mcp-python/server.py"],
      "env": {
        "DATADOG_API_KEY": "your_api_key",
        "DATADOG_APP_KEY": "your_app_key",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "datadog": {
      "command": "python",
      "args": ["/path/to/datadog-mcp-python/server.py"],
      "env": {
        "DATADOG_API_KEY": "your_api_key",
        "DATADOG_APP_KEY": "your_app_key"
      }
    }
  }
}
```

### Gemini CLI

1. Install Gemini CLI with MCP support
2. Configure the server:

```bash
gemini mcp add datadog python /path/to/datadog-mcp-python/server.py \
  --env DATADOG_API_KEY=your_api_key \
  --env DATADOG_APP_KEY=your_app_key
```

### Generic MCP Client

For any MCP-compatible client, use these connection details:

- **Transport**: stdio
- **Command**: `python server.py`
- **Working Directory**: `/path/to/datadog-mcp-python/`
- **Environment Variables**: `DATADOG_API_KEY`, `DATADOG_APP_KEY`

## Available Tools (31 Total)

### Metrics & Monitoring (9 tools)
- `validate_api_key` - Test API credentials
- `get_metrics` - Query time series data
- `search_metrics` - Find metrics by pattern
- `get_metric_metadata` - Get metric metadata
- `get_monitors` - List monitoring alerts
- `get_monitor` - Get specific monitor details
- `create_monitor` - Create new monitoring alerts
- `update_monitor` - Update existing monitors
- `delete_monitor` - Delete monitors

### Dashboards & Visualization (5 tools)
- `get_dashboards` - List all dashboards
- `get_dashboard` - Get dashboard details
- `create_dashboard` - Create new dashboards
- `update_dashboard` - Update existing dashboards
- `delete_dashboard` - Delete dashboards

### Logs & Events (2 tools)
- `search_logs` - Search log entries
- `get_events` - Get system events

### Infrastructure & Tags (5 tools)
- `get_infrastructure` - Get host information
- `get_service_map` - Get service dependencies
- `get_tags` - Get host tags
- `get_downtimes` - Get scheduled downtimes
- `create_downtime` - Create scheduled downtimes

### Testing & Applications (2 tools)
- `get_synthetics_tests` - Get synthetic tests
- `get_rum_applications` - Get RUM applications

### Security & Incidents (4 tools)
- `get_security_rules` - Get security monitoring rules
- `get_incidents` - Get incident data (with pagination)
- `get_slos` - Get Service Level Objectives
- `get_notebooks` - Get Datadog notebooks

### Teams & Users (2 tools)
- `get_teams` - Get teams
- `get_users` - Get users

### Utilities (2 tools)
- `analyze_data` - Analyze cached data
- `cleanup_cache` - Clean old cache files

## Usage Examples

Once connected to an MCP client, you can use natural language to interact with Datadog:

### Monitoring Examples
- "Show me all monitors that are currently alerting"
- "Create a monitor for high CPU usage above 80%"
- "Get metrics for system.cpu.user over the last hour"
- "Search for all memory-related metrics"

### Dashboard Examples
- "List all my dashboards"
- "Create a new dashboard for system monitoring"
- "Show me the widgets in my main dashboard"

### Infrastructure Examples
- "Show me all hosts and their status"
- "Get the service map for my application"
- "List all tags for production hosts"

### Incident Management
- "Show me all active incidents"
- "Get the latest security monitoring rules"
- "List all SLOs and their current status"

## Configuration

The server uses the latest Datadog API client with:
- AsyncApiClient for non-blocking operations
- Automatic retry on rate limits (429 errors)
- 3 retry attempts with exponential backoff
- Unstable operations enabled for pagination

## 🏗️ Architecture

### Core Components
- **DatadogMCPServer**: Main server class with API client management
- **DatadogConfig**: Pydantic model for configuration validation
- **Tool Handlers**: Individual async functions for each API endpoint
- **Data Storage**: Automatic JSON file caching with timestamps
- **Analysis Engine**: Built-in data analysis capabilities

### Data Flow
1. **Request**: MCP client calls tool with parameters
2. **API Call**: Server makes authenticated request to Datadog API
3. **Storage**: Response data is cached to local JSON file
4. **Analysis**: Optional built-in analysis of the data
5. **Response**: Summary and file path returned to client

## 📈 Performance

### Async Implementation
- All API calls are asynchronous
- Non-blocking file I/O operations
- Efficient memory usage for large datasets

### Rate Limiting
- Respects Datadog API rate limits
- Automatic retry logic with exponential backoff
- Efficient batching for bulk operations

## Example Code Usage

```python
# Create a monitor
create_monitor(
    name="High CPU Usage",
    monitor_type="metric alert", 
    query="avg(last_5m):avg:system.cpu.user{*} > 0.8",
    message="CPU usage is high @slack-alerts"
)

# Create a dashboard
create_dashboard(
    title="System Overview",
    layout_type="ordered",
    widgets=[{
        "definition": {
            "type": "timeseries",
            "requests": [{"q": "avg:system.cpu.user{*}"}]
        }
    }]
)

# Schedule downtime
create_downtime(
    scope=["host:web-server-01"],
    start=1640995200,
    end=1640998800,
    message="Scheduled maintenance"
)
```

## Security & Features

- **Full CRUD operations** - Complete create, read, update, delete support
- **Write operations enabled** - All mutation tools available
- **Local data caching** - All results stored locally as JSON files
- **Error handling** - Comprehensive exception management
- **Pagination support** - Handle large datasets efficiently
- **Type safety** - Full type hints throughout
- **Rate limiting** - Automatic retry on API limits

## Development

### Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Format code
black server.py
flake8 server.py --max-line-length=88

# Run tests
cd tests && python -m pytest --cov=../server
```

### Adding New Tools
1. Add new method to `DatadogMCPServer` class
2. Decorate with `@self.mcp.tool()`
3. Implement proper error handling and data storage
4. Add tests and update documentation

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your `DATADOG_API_KEY` and `DATADOG_APP_KEY` are correct
2. **Connection Issues**: Ensure the server is running and accessible
3. **Permission Errors**: Check that your API keys have the necessary permissions
4. **Rate Limiting**: The server automatically handles rate limits with retries

### Debug Mode

Enable debug logging by setting:
```bash
export DATADOG_DEBUG=true
```

## License

MIT License - see LICENSE file for details.
