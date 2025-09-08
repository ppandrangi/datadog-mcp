#!/usr/bin/env python3
"""
Datadog MCP Server

A comprehensive Model Context Protocol server for Datadog integration
built with the official Python SDK and Datadog API client.
"""

import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from datadog_api_client import AsyncApiClient, Configuration
from datadog_api_client.v1.api.dashboards_api import DashboardsApi
from datadog_api_client.v1.api.events_api import EventsApi
from datadog_api_client.v1.api.hosts_api import HostsApi
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi
# Add missing imports for additional APIs
from datadog_api_client.v1.api.notebooks_api import NotebooksApi
from datadog_api_client.v1.api.service_level_objectives_api import ServiceLevelObjectivesApi
from datadog_api_client.v2.api.incidents_api import IncidentsApi
from datadog_api_client.v1.api.downtimes_api import DowntimesApi
from datadog_api_client.v1.api.tags_api import TagsApi
from datadog_api_client.v1.api.users_api import UsersApi
from datadog_api_client.v2.api.teams_api import TeamsApi
# ServiceMapApi might not be available in all versions, handle gracefully
try:
    from datadog_api_client.v1.api.service_map_api import ServiceMapApi
except ImportError:
    ServiceMapApi = None
from datadog_api_client.v1.api.synthetics_api import SyntheticsApi
from datadog_api_client.v2.api.logs_api import LogsApi as LogsApiV2
from datadog_api_client.v2.api.rum_api import RUMApi
from datadog_api_client.v2.api.security_monitoring_api import SecurityMonitoringApi
from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = Path("datadog_cache")
DATA_DIR.mkdir(exist_ok=True)


class DatadogConfig(BaseModel):
    """Datadog configuration model"""
    api_key: str
    app_key: str
    site: str = "datadoghq.com"


@dataclass
class AppContext:
    """Application context with typed dependencies"""
    api_client: AsyncApiClient
    config: DatadogConfig


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    config = _load_config()
    api_client = _setup_api_client(config)
    
    try:
        yield AppContext(api_client=api_client, config=config)
    finally:
        # Cleanup on shutdown - AsyncApiClient handles its own cleanup
        pass


def _load_config() -> DatadogConfig:
    """Load Datadog configuration from environment"""
    api_key = os.getenv("DATADOG_API_KEY")
    app_key = os.getenv("DATADOG_APP_KEY")
    site = os.getenv("DATADOG_SITE", "datadoghq.com")
    
    if not api_key or not app_key:
        raise ValueError("DATADOG_API_KEY and DATADOG_APP_KEY must be set")
        
    return DatadogConfig(api_key=api_key, app_key=app_key, site=site)


def _setup_api_client(config: DatadogConfig) -> AsyncApiClient:
    """Setup Datadog API client"""
    configuration = Configuration()
    configuration.api_key["apiKeyAuth"] = config.api_key
    configuration.api_key["appKeyAuth"] = config.app_key
    configuration.server_variables["site"] = config.site
    
    # Enable retry for rate limits and configure retries
    configuration.enable_retry = True
    configuration.max_retries = 3
    
    # Disable SSL verification for development (fix SSL certificate issues)
    configuration.verify_ssl = False
    
    # Enable unstable operations for pagination and newer features
    configuration.unstable_operations["list_incidents"] = True
    # Note: list_downtimes and list_teams may not be available as unstable operations
    
    return AsyncApiClient(configuration)


async def _store_data(data: Any, prefix: str) -> str:
    """Store data to filesystem and return file path"""
    timestamp = int(datetime.now(timezone.utc).timestamp())
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}_{timestamp}_{unique_id}.json"
    filepath = DATA_DIR / filename
    
    async with aiofiles.open(filepath, 'w') as f:
        await f.write(json.dumps(data, indent=2, default=str))
        
    return str(filepath)


# Create FastMCP instance with lifespan management
mcp = FastMCP("datadog-mcp", lifespan=app_lifespan)


# Core Metrics Tools
@mcp.tool()
async def get_metrics(
    query: str,
    from_timestamp: int,
    to_timestamp: int,
    ctx: Context
) -> Dict[str, Any]:
    """Query Datadog metrics and store results"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = MetricsApi(app_ctx.api_client)
        response = await api_instance.query_metrics(
            _from=from_timestamp,
            to=to_timestamp,
            query=query
        )
            
        data = response.to_dict()
        filepath = await _store_data(data, "metrics")
        
        series_count = len(data.get("series", []))
        total_points = sum(len(s.get("pointlist", [])) for s in data.get("series", []))
        
        await ctx.info(f"Retrieved {series_count} metric series with {total_points} data points")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {series_count} metric series with {total_points} data points",
            "series_count": series_count,
            "data_points": total_points,
            "query": query,
            "time_range": f"{from_timestamp} to {to_timestamp}"
        }
    except Exception as e:
        await ctx.error(f"Failed to get metrics: {str(e)}")
        return {"error": f"Failed to get metrics: {str(e)}"}


@mcp.tool()
async def search_metrics(query: str, ctx: Context) -> Dict[str, Any]:
    """Search for metrics by name pattern"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        async with app_ctx.api_client as api_client:
            api_instance = MetricsApi(api_client)
            # Use list_metrics with query parameter
            response = await api_instance.list_metrics(q=query)
            
        data = response.to_dict()
        filepath = await _store_data(data, "metrics_search")
        
        metrics = data.get("metrics", [])
        await ctx.info(f"Found {len(metrics)} metrics matching '{query}'")
        
        return {
            "filepath": filepath,
            "summary": f"Found {len(metrics)} metrics matching '{query}'",
            "metric_count": len(metrics),
            "sample_metrics": metrics[:10] if metrics else []
        }
    except Exception as e:
        await ctx.error(f"Failed to search metrics: {str(e)}")
        return {"error": f"Failed to search metrics: {str(e)}"}


@mcp.tool()
async def get_metric_metadata(metric_name: str, ctx: Context) -> Dict[str, Any]:
    """Get metadata for a specific metric"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        with app_ctx.api_client as api_client:
            api_instance = MetricsApi(api_client)
            response = api_instance.get_metric_metadata(metric_name=metric_name)
            
        data = response.to_dict()
        filepath = await _store_data(data, "metric_metadata")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved metadata for metric: {metric_name}",
            "metric_name": metric_name,
            "description": data.get("description", "No description"),
            "unit": data.get("unit", "No unit"),
            "type": data.get("type", "Unknown")
        }
    except Exception as e:
        await ctx.error(f"Failed to get metric metadata: {str(e)}")
        return {"error": f"Failed to get metric metadata: {str(e)}"}


# Monitor Management Tools
@mcp.tool()
async def get_monitors(ctx: Context) -> Dict[str, Any]:
    """Get all Datadog monitors"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = MonitorsApi(app_ctx.api_client)
        response = await api_instance.list_monitors()
            
        data = [monitor.to_dict() for monitor in response]
        filepath = await _store_data(data, "monitors")
        
        # Analyze monitor states
        states = {}
        for monitor in data:
            state = monitor.get("overall_state", "Unknown")
            states[state] = states.get(state, 0) + 1
        
        await ctx.info(f"Retrieved {len(data)} monitors")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(data)} monitors",
            "total_monitors": len(data),
            "monitor_states": states,
            "alerting_count": states.get("Alert", 0)
        }
    except Exception as e:
        await ctx.error(f"Failed to get monitors: {str(e)}")
        return {"error": f"Failed to get monitors: {str(e)}"}


@mcp.tool()
async def get_monitor(monitor_id: str, ctx: Context) -> Dict[str, Any]:
    """Get specific monitor by ID"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = MonitorsApi(app_ctx.api_client)
        response = await api_instance.get_monitor(int(monitor_id))
            
        data = response.to_dict()
        filepath = await _store_data(data, "monitor")
        
        return {
            "filepath": filepath,
            "summary": f"Monitor: {data.get('name')} - Status: {data.get('overall_state')}",
            "monitor_id": data.get("id"),
            "monitor_name": data.get("name"),
            "status": data.get("overall_state"),
            "monitor_type": data.get("type")
        }
    except Exception as e:
        await ctx.error(f"Failed to get monitor {monitor_id}: {str(e)}")
        return {"error": f"Failed to get monitor {monitor_id}: {str(e)}"}


@mcp.tool()
async def create_monitor(
    name: str,
    monitor_type: str,
    query: str,
    message: str,
    ctx: Context,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new Datadog monitor"""
    try:
        from datadog_api_client.v1.model.monitor import Monitor
        
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        monitor_config = {
            "name": name,
            "type": monitor_type,
            "query": query,
            "message": message
        }
        
        if options:
            monitor_config.update(options)
        
        api_instance = MonitorsApi(app_ctx.api_client)
        monitor = Monitor(**monitor_config)
        response = await api_instance.create_monitor(body=monitor)
            
        data = response.to_dict()
        filepath = await _store_data(data, "monitor_created")
        
        await ctx.info(f"Created monitor: {data.get('name')} (ID: {data.get('id')})")
        
        return {
            "filepath": filepath,
            "summary": f"Created monitor: {data.get('name')} (ID: {data.get('id')})",
            "monitor_id": data.get("id"),
            "monitor_name": data.get("name"),
            "status": "created"
        }
    except Exception as e:
        await ctx.error(f"Failed to create monitor: {str(e)}")
        return {"error": f"Failed to create monitor: {str(e)}"}


# Dashboard Tools
@mcp.tool()
async def get_dashboards(ctx: Context) -> Dict[str, Any]:
    """Get all Datadog dashboards"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        async with app_ctx.api_client as api_client:
            api_instance = DashboardsApi(api_client)
            response = await api_instance.list_dashboards()
            
        data = response.to_dict()
        filepath = await _store_data(data, "dashboards")
        
        dashboards = data.get("dashboards", [])
        await ctx.info(f"Retrieved {len(dashboards)} dashboards")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(dashboards)} dashboards",
            "total_dashboards": len(dashboards),
            "sample_dashboards": [d.get("title", "Untitled") for d in dashboards[:5]]
        }
    except Exception as e:
        await ctx.error(f"Failed to get dashboards: {str(e)}")
        return {"error": f"Failed to get dashboards: {str(e)}"}


@mcp.tool()
async def get_dashboard(dashboard_id: str, ctx: Context) -> Dict[str, Any]:
    """Get specific dashboard by ID"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        with app_ctx.api_client as api_client:
            api_instance = DashboardsApi(api_client)
            response = api_instance.get_dashboard(dashboard_id)
            
        data = response.to_dict()
        filepath = await _store_data(data, "dashboard")
        
        widgets = data.get("widgets", [])
        return {
            "filepath": filepath,
            "summary": f"Dashboard: {data.get('title')} with {len(widgets)} widgets",
            "dashboard_id": data.get("id"),
            "dashboard_title": data.get("title"),
            "widget_count": len(widgets),
            "layout_type": data.get("layout_type")
        }
    except Exception as e:
        await ctx.error(f"Failed to get dashboard {dashboard_id}: {str(e)}")
        return {"error": f"Failed to get dashboard {dashboard_id}: {str(e)}"}


@mcp.tool()
async def create_dashboard(
    title: str,
    layout_type: str,
    widgets: List[Dict[str, Any]],
    ctx: Context,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new dashboard"""
    try:
        from datadog_api_client.v1.model.dashboard import Dashboard
        
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        dashboard_data = {
            "title": title,
            "layout_type": layout_type,
            "widgets": widgets
        }
        if description:
            dashboard_data["description"] = description
        
        api_instance = DashboardsApi(app_ctx.api_client)
        dashboard = Dashboard(**dashboard_data)
        response = await api_instance.create_dashboard(body=dashboard)
        
        data = response.to_dict()
        filepath = await _store_data(data, "dashboard_created")
        
        return {
            "filepath": filepath,
            "summary": f"Created dashboard: {data.get('title')} (ID: {data.get('id')})",
            "dashboard_id": data.get("id"),
            "dashboard_title": data.get("title"),
            "status": "created"
        }
    except Exception as e:
        await ctx.error(f"Failed to create dashboard: {str(e)}")
        return {"error": f"Failed to create dashboard: {str(e)}"}


@mcp.tool()
async def update_dashboard(
    dashboard_id: str,
    title: Optional[str] = None,
    widgets: Optional[List[Dict[str, Any]]] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """Update an existing dashboard"""
    try:
        from datadog_api_client.v1.model.dashboard import Dashboard
        
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = DashboardsApi(app_ctx.api_client)
        
        # Get existing dashboard
        existing = await api_instance.get_dashboard(dashboard_id)
        update_data = existing.to_dict()
        
        # Update fields
        if title:
            update_data["title"] = title
        if widgets:
            update_data["widgets"] = widgets
        
        dashboard = Dashboard(**update_data)
        response = await api_instance.update_dashboard(dashboard_id, body=dashboard)
        
        data = response.to_dict()
        filepath = await _store_data(data, "dashboard_updated")
        
        return {
            "filepath": filepath,
            "summary": f"Updated dashboard: {data.get('title')} (ID: {data.get('id')})",
            "dashboard_id": data.get("id"),
            "dashboard_title": data.get("title"),
            "status": "updated"
        }
    except Exception as e:
        await ctx.error(f"Failed to update dashboard: {str(e)}")
        return {"error": f"Failed to update dashboard: {str(e)}"}


@mcp.tool()
async def delete_dashboard(dashboard_id: str, ctx: Context) -> Dict[str, Any]:
    """Delete a dashboard"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = DashboardsApi(app_ctx.api_client)
        await api_instance.delete_dashboard(dashboard_id)
        
        return {
            "summary": f"Successfully deleted dashboard ID: {dashboard_id}",
            "dashboard_id": dashboard_id,
            "status": "deleted"
        }
    except Exception as e:
        await ctx.error(f"Failed to delete dashboard: {str(e)}")
        return {"error": f"Failed to delete dashboard: {str(e)}"}


# Logs Tools
@mcp.tool()
async def search_logs(
    query: str,
    from_time: str,
    to_time: str,
    ctx: Context,
    limit: int = 100
) -> Dict[str, Any]:
    """Search Datadog logs"""
    try:
        from datadog_api_client.v2.model.logs_list_request import LogsListRequest
        from datadog_api_client.v2.model.logs_query_filter import LogsQueryFilter
        from datadog_api_client.v2.model.logs_sort import LogsSort
        
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        body = LogsListRequest(
            filter=LogsQueryFilter(
                query=query,
                _from=from_time,
                to=to_time
            ),
            page={"limit": limit},
            sort=LogsSort.TIMESTAMP_ASCENDING
        )
        
        with app_ctx.api_client as api_client:
            api_instance = LogsApiV2(api_client)
            response = api_instance.list_logs(body=body)
            
        data = response.to_dict()
        filepath = await _store_data(data, "logs")
        
        logs = data.get("data", [])
        await ctx.info(f"Retrieved {len(logs)} log entries")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(logs)} log entries",
            "log_count": len(logs),
            "query": query,
            "time_range": f"{from_time} to {to_time}"
        }
    except Exception as e:
        await ctx.error(f"Failed to search logs: {str(e)}")
        return {"error": f"Failed to search logs: {str(e)}"}


# Events Tools
@mcp.tool()
async def get_events(
    start: int,
    end: int,
    ctx: Context,
    priority: Optional[str] = None,
    sources: Optional[str] = None
) -> Dict[str, Any]:
    """Get Datadog events"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        async with app_ctx.api_client as api_client:
            api_instance = EventsApi(api_client)
            
            kwargs = {"start": start, "end": end}
            if priority:
                kwargs["priority"] = priority
            if sources:
                kwargs["sources"] = sources
            
            response = await api_instance.list_events(**kwargs)
            
        data = response.to_dict()
        filepath = await _store_data(data, "events")
        
        events = data.get("events", [])
        await ctx.info(f"Retrieved {len(events)} events")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(events)} events",
            "event_count": len(events),
            "time_range": f"{start} to {end}",
            "priority_filter": priority,
            "sources_filter": sources
        }
    except Exception as e:
        await ctx.error(f"Failed to get events: {str(e)}")
        return {"error": f"Failed to get events: {str(e)}"}


# Infrastructure Tools
@mcp.tool()
async def get_infrastructure(ctx: Context) -> Dict[str, Any]:
    """Get infrastructure and hosts information"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        async with app_ctx.api_client as api_client:
            api_instance = HostsApi(api_client)
            response = await api_instance.list_hosts()
            
        # Handle response structure properly
        if hasattr(response, 'host_list'):
            hosts = [host.to_dict() for host in response.host_list]
        else:
            hosts = []
            
        data = {"host_list": hosts}
        filepath = await _store_data(data, "infrastructure")
        
        active_hosts = sum(1 for h in hosts if h.get("up", False))
        
        await ctx.info(f"Found {len(hosts)} hosts ({active_hosts} active)")
        
        return {
            "filepath": filepath,
            "summary": f"Found {len(hosts)} hosts ({active_hosts} active)",
            "total_hosts": len(hosts),
            "active_hosts": active_hosts,
            "inactive_hosts": len(hosts) - active_hosts
        }
    except Exception as e:
        await ctx.error(f"Failed to get infrastructure: {str(e)}")
        return {"error": f"Failed to get infrastructure: {str(e)}"}


# Service Map Tools - Commented out due to API availability issues
# @mcp.tool()
# async def get_service_map(ctx: Context, env: Optional[str] = None) -> Dict[str, Any]:
#     """Get Datadog service map - API not available in current client version"""
#     return {"error": "ServiceMapApi not available in this Datadog client version"}


# Synthetics Tools
@mcp.tool()
async def get_synthetics_tests(ctx: Context) -> Dict[str, Any]:
    """Get all Synthetics tests"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        async with app_ctx.api_client as api_client:
            api_instance = SyntheticsApi(api_client)
            response = await api_instance.list_tests()
            
        # Handle the correct response structure - response has .tests attribute
        data = {
            "tests": [test.to_dict() for test in response.tests] if hasattr(response, 'tests') else []
        }
        filepath = await _store_data(data, "synthetics_tests")
        
        tests = data.get("tests", [])
        test_types = {}
        for test in tests:
            test_type = test.get("type", "unknown")
            test_types[test_type] = test_types.get(test_type, 0) + 1
        
        return {
            "filepath": filepath,
            "summary": f"Found {len(tests)} Synthetics tests",
            "test_count": len(tests),
            "test_types": test_types
        }
    except Exception as e:
        await ctx.error(f"Failed to get Synthetics tests: {str(e)}")
        return {"error": f"Failed to get Synthetics tests: {str(e)}"}


# RUM Tools - Commented out due to API availability issues
# @mcp.tool()
# async def get_rum_applications(ctx: Context) -> Dict[str, Any]:
#     """Get RUM applications"""
#     # API not available in current client version


# Security Monitoring Tools
@mcp.tool()
async def get_security_rules(ctx: Context) -> Dict[str, Any]:
    """Get security monitoring rules"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        with app_ctx.api_client as api_client:
            api_instance = SecurityMonitoringApi(api_client)
            response = api_instance.list_security_monitoring_rules()
            
        data = response.to_dict()
        filepath = await _store_data(data, "security_rules")
        
        rules = data.get("data", [])
        enabled_rules = sum(1 for r in rules if r.get("attributes", {}).get("isEnabled"))
        
        return {
            "filepath": filepath,
            "summary": f"Found {len(rules)} security rules ({enabled_rules} enabled)",
            "total_rules": len(rules),
            "enabled_rules": enabled_rules,
            "disabled_rules": len(rules) - enabled_rules
        }
    except Exception as e:
        await ctx.error(f"Failed to get security rules: {str(e)}")
        return {"error": f"Failed to get security rules: {str(e)}"}


# Utility Tools
@mcp.tool()
async def validate_api_key(ctx: Context) -> Dict[str, Any]:
    """Validate Datadog API credentials"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        with app_ctx.api_client as api_client:
            api_instance = MonitorsApi(api_client)
            response = api_instance.list_monitors(page_size=1)
            
        await ctx.info("API credentials validated successfully")
        
        return {
            "valid": True,
            "summary": "API credentials are valid and working",
            "site": app_ctx.config.site,
            "test_successful": True
        }
    except Exception as e:
        await ctx.error(f"API validation failed: {str(e)}")
        return {
            "valid": False,
            "error": f"API validation failed: {str(e)}",
            "site": "unknown"
        }


@mcp.tool()
async def cleanup_cache(ctx: Context, older_than_hours: int = 24) -> Dict[str, Any]:
    """Clean up old cached data files"""
    try:
        cutoff_time = datetime.now(timezone.utc).timestamp() - (older_than_hours * 3600)
        deleted_count = 0
        
        for file_path in DATA_DIR.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
        
        await ctx.info(f"Cleaned up {deleted_count} files older than {older_than_hours} hours")
        
        return {
            "summary": f"Cleaned up {deleted_count} files older than {older_than_hours} hours",
            "deleted_count": deleted_count,
            "cache_directory": str(DATA_DIR)
        }
    except Exception as e:
        await ctx.error(f"Failed to cleanup cache: {str(e)}")
        return {"error": f"Failed to cleanup cache: {str(e)}"}


# Add missing write operations
@mcp.tool()
async def update_monitor(
    monitor_id: str,
    name: Optional[str] = None,
    query: Optional[str] = None,
    message: Optional[str] = None,
    ctx: Context = None,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update an existing Datadog monitor"""
    try:
        from datadog_api_client.v1.model.monitor import Monitor
        
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        # Get existing monitor first
        api_instance = MonitorsApi(app_ctx.api_client)
        existing = await api_instance.get_monitor(int(monitor_id))
        
        # Update only provided fields
        update_data = existing.to_dict()
        if name:
            update_data["name"] = name
        if query:
            update_data["query"] = query
        if message:
            update_data["message"] = message
        if options:
            update_data.update(options)
        
        monitor = Monitor(**update_data)
        response = await api_instance.update_monitor(int(monitor_id), body=monitor)
        
        data = response.to_dict()
        filepath = await _store_data(data, "monitor_updated")
        
        await ctx.info(f"Updated monitor: {data.get('name')} (ID: {data.get('id')})")
        
        return {
            "filepath": filepath,
            "summary": f"Updated monitor: {data.get('name')} (ID: {data.get('id')})",
            "monitor_id": data.get("id"),
            "monitor_name": data.get("name"),
            "status": "updated"
        }
    except Exception as e:
        await ctx.error(f"Failed to update monitor: {str(e)}")
        return {"error": f"Failed to update monitor: {str(e)}"}


@mcp.tool()
async def delete_monitor(monitor_id: str, ctx: Context) -> Dict[str, Any]:
    """Delete a Datadog monitor"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = MonitorsApi(app_ctx.api_client)
        await api_instance.delete_monitor(int(monitor_id))
        
        await ctx.info(f"Deleted monitor ID: {monitor_id}")
        
        return {
            "summary": f"Successfully deleted monitor ID: {monitor_id}",
            "monitor_id": monitor_id,
            "status": "deleted"
        }
    except Exception as e:
        await ctx.error(f"Failed to delete monitor: {str(e)}")
        return {"error": f"Failed to delete monitor: {str(e)}"}


# Incidents API (with pagination support)
@mcp.tool()
async def get_incidents(ctx: Context, page_size: int = 25) -> Dict[str, Any]:
    """Get incidents with pagination support"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = IncidentsApi(app_ctx.api_client)
        incidents = []
        
        # Use pagination to get all incidents
        async for incident in api_instance.list_incidents_with_pagination(page_size=page_size):
            incidents.append(incident.to_dict())
        
        filepath = await _store_data(incidents, "incidents")
        
        # Analyze incident states
        states = {}
        for incident in incidents:
            state = incident.get("attributes", {}).get("state", "unknown")
            states[state] = states.get(state, 0) + 1
        
        await ctx.info(f"Retrieved {len(incidents)} incidents")
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(incidents)} incidents",
            "total_incidents": len(incidents),
            "incident_states": states,
            "active_incidents": states.get("active", 0)
        }
    except Exception as e:
        await ctx.error(f"Failed to get incidents: {str(e)}")
        return {"error": f"Failed to get incidents: {str(e)}"}


# SLOs API
@mcp.tool()
async def get_slos(ctx: Context) -> Dict[str, Any]:
    """Get Service Level Objectives"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = ServiceLevelObjectivesApi(app_ctx.api_client)
        response = await api_instance.list_slos()
        
        data = response.to_dict()
        filepath = await _store_data(data, "slos")
        
        slos = data.get("data", [])
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(slos)} SLOs",
            "total_slos": len(slos)
        }
    except Exception as e:
        await ctx.error(f"Failed to get SLOs: {str(e)}")
        return {"error": f"Failed to get SLOs: {str(e)}"}


# Notebooks API
@mcp.tool()
async def get_notebooks(ctx: Context) -> Dict[str, Any]:
    """Get Datadog notebooks"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = NotebooksApi(app_ctx.api_client)
        response = await api_instance.list_notebooks()
        
        data = response.to_dict()
        filepath = await _store_data(data, "notebooks")
        
        notebooks = data.get("data", [])
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(notebooks)} notebooks",
            "total_notebooks": len(notebooks)
        }
    except Exception as e:
        await ctx.error(f"Failed to get notebooks: {str(e)}")
        return {"error": f"Failed to get notebooks: {str(e)}"}


# Downtimes API
@mcp.tool()
async def get_downtimes(ctx: Context) -> Dict[str, Any]:
    """Get scheduled downtimes"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = DowntimesApi(app_ctx.api_client)
        response = await api_instance.list_downtimes()
        
        data = [downtime.to_dict() for downtime in response]
        filepath = await _store_data(data, "downtimes")
        
        active_count = sum(1 for d in data if d.get("active", False))
        
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(data)} downtimes ({active_count} active)",
            "total_downtimes": len(data),
            "active_downtimes": active_count
        }
    except Exception as e:
        await ctx.error(f"Failed to get downtimes: {str(e)}")
        return {"error": f"Failed to get downtimes: {str(e)}"}


@mcp.tool()
async def create_downtime(
    scope: List[str],
    start: Optional[int] = None,
    end: Optional[int] = None,
    message: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """Create a scheduled downtime"""
    try:
        from datadog_api_client.v1.model.downtime import Downtime
        
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        downtime_data = {"scope": scope}
        if start:
            downtime_data["start"] = start
        if end:
            downtime_data["end"] = end
        if message:
            downtime_data["message"] = message
        
        api_instance = DowntimesApi(app_ctx.api_client)
        downtime = Downtime(**downtime_data)
        response = await api_instance.create_downtime(body=downtime)
        
        data = response.to_dict()
        filepath = await _store_data(data, "downtime_created")
        
        return {
            "filepath": filepath,
            "summary": f"Created downtime (ID: {data.get('id')})",
            "downtime_id": data.get("id"),
            "scope": data.get("scope"),
            "status": "created"
        }
    except Exception as e:
        await ctx.error(f"Failed to create downtime: {str(e)}")
        return {"error": f"Failed to create downtime: {str(e)}"}


# Tags API
@mcp.tool()
async def get_tags(ctx: Context, source: Optional[str] = None) -> Dict[str, Any]:
    """Get host tags"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = TagsApi(app_ctx.api_client)
        kwargs = {}
        if source:
            kwargs["source"] = source
        
        response = await api_instance.list_host_tags(**kwargs)
        
        data = response.to_dict()
        filepath = await _store_data(data, "tags")
        
        tags = data.get("tags", {})
        return {
            "filepath": filepath,
            "summary": f"Retrieved tags for {len(tags)} hosts",
            "host_count": len(tags),
            "source": source or "all"
        }
    except Exception as e:
        await ctx.error(f"Failed to get tags: {str(e)}")
        return {"error": f"Failed to get tags: {str(e)}"}


# Teams API
@mcp.tool()
async def get_teams(ctx: Context) -> Dict[str, Any]:
    """Get teams"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = TeamsApi(app_ctx.api_client)
        response = await api_instance.list_teams()
        
        data = response.to_dict()
        filepath = await _store_data(data, "teams")
        
        teams = data.get("data", [])
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(teams)} teams",
            "total_teams": len(teams)
        }
    except Exception as e:
        await ctx.error(f"Failed to get teams: {str(e)}")
        return {"error": f"Failed to get teams: {str(e)}"}


# Users API
@mcp.tool()
async def get_users(ctx: Context) -> Dict[str, Any]:
    """Get users"""
    try:
        app_ctx: AppContext = ctx.request_context.lifespan_context
        
        api_instance = UsersApi(app_ctx.api_client)
        response = await api_instance.list_users()
        
        data = response.to_dict()
        filepath = await _store_data(data, "users")
        
        users = data.get("users", [])
        return {
            "filepath": filepath,
            "summary": f"Retrieved {len(users)} users",
            "total_users": len(users)
        }
    except Exception as e:
        await ctx.error(f"Failed to get users: {str(e)}")
        return {"error": f"Failed to get users: {str(e)}"}


# Data Analysis Tools
@mcp.tool()
async def analyze_data(
    filepath: str,
    ctx: Context,
    analysis_type: str = "summary"
) -> Dict[str, Any]:
    """Analyze stored Datadog data"""
    try:
        if not Path(filepath).exists():
            return {"error": f"Data file not found: {filepath}"}
        
        async with aiofiles.open(filepath, 'r') as f:
            content = await f.read()
            data = json.loads(content)
        
        if analysis_type == "summary":
            result = _generate_summary(data)
        elif analysis_type == "stats":
            result = _calculate_stats(data)
        elif analysis_type == "trends":
            result = _analyze_trends(data)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
        
        await ctx.info(f"Completed {analysis_type} analysis of {filepath}")
        
        return {
            "analysis_type": analysis_type,
            "filepath": filepath,
            "result": result
        }
    except Exception as e:
        await ctx.error(f"Analysis failed: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}


def _generate_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of data"""
    summary = {
        "data_type": "unknown",
        "record_count": 0,
        "key_insights": []
    }
    
    if "series" in data:
        # Metrics data
        summary["data_type"] = "metrics"
        summary["record_count"] = len(data["series"])
        total_points = sum(len(s.get("pointlist", [])) for s in data["series"])
        summary["total_data_points"] = total_points
        
        if total_points > 1000:
            summary["key_insights"].append("Large dataset - consider aggregation")
            
    elif isinstance(data, list) and data:
        if "overall_state" in data[0]:
            # Monitors
            summary["data_type"] = "monitors"
            summary["record_count"] = len(data)
            alerting = sum(1 for m in data if m.get("overall_state") == "Alert")
            summary["alerting_monitors"] = alerting
            
            if alerting > 0:
                summary["key_insights"].append(f"{alerting} monitors currently alerting")
                
    elif "events" in data:
        # Events
        summary["data_type"] = "events"
        events = data["events"]
        summary["record_count"] = len(events)
        
    return summary


def _calculate_stats(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate basic statistics"""
    stats = {"calculated_at": datetime.now(timezone.utc).isoformat()}
    
    if "series" in data:
        # Metrics statistics
        all_values = []
        for series in data["series"]:
            if "pointlist" in series:
                values = [p[1] for p in series["pointlist"] if p[1] is not None]
                all_values.extend(values)
        
        if all_values:
            stats.update({
                "min_value": min(all_values),
                "max_value": max(all_values),
                "avg_value": sum(all_values) / len(all_values),
                "total_points": len(all_values)
            })
    
    return stats


def _analyze_trends(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze trends in time series data"""
    trends = {
        "trend_direction": "stable",
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }
    
    if "series" in data and data["series"]:
        series = data["series"][0]  # Analyze first series
        if "pointlist" in series and len(series["pointlist"]) > 1:
            values = [p[1] for p in series["pointlist"] if p[1] is not None]
            
            if len(values) >= 2:
                first_val = values[0]
                last_val = values[-1]
                
                if first_val != 0:
                    change_pct = ((last_val - first_val) / first_val) * 100
                    trends["change_percentage"] = round(change_pct, 2)
                    
                    if change_pct > 10:
                        trends["trend_direction"] = "increasing"
                    elif change_pct < -10:
                        trends["trend_direction"] = "decreasing"
    
    return trends


def main():
    """Main entry point"""
    mcp.run()


if __name__ == "__main__":
    main()
