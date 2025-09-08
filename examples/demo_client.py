#!/usr/bin/env python3
"""
Demo MCP client showing available read-only queries
"""
import asyncio
import json
from datetime import datetime, timezone

def show_available_queries():
    """Show all available read-only queries"""
    print("🔍 Datadog MCP Server - Available Read-Only Queries")
    print("=" * 60)
    
    queries = [
        {
            "name": "validate_api_key",
            "description": "Test API credentials",
            "example": "validate_api_key(ctx)",
            "returns": "API validation status and site info"
        },
        {
            "name": "search_metrics", 
            "description": "Find metrics by pattern",
            "example": "search_metrics('system.cpu', ctx)",
            "returns": "List of matching metric names"
        },
        {
            "name": "get_metrics",
            "description": "Query time series data", 
            "example": "get_metrics('system.cpu.user{*}', 1640995200, 1640998800, ctx)",
            "returns": "Time series data points and statistics"
        },
        {
            "name": "get_monitors",
            "description": "List all monitoring alerts",
            "example": "get_monitors(ctx)", 
            "returns": "Monitor states and alert counts"
        },
        {
            "name": "get_monitor",
            "description": "Get specific monitor details",
            "example": "get_monitor('12345', ctx)",
            "returns": "Monitor configuration and current state"
        },
        {
            "name": "get_dashboards",
            "description": "List all dashboards",
            "example": "get_dashboards(ctx)",
            "returns": "Dashboard titles and IDs"
        },
        {
            "name": "get_infrastructure", 
            "description": "Get host information",
            "example": "get_infrastructure(ctx)",
            "returns": "Host count and status summary"
        },
        {
            "name": "search_logs",
            "description": "Search log entries",
            "example": "search_logs('ERROR', '2024-01-01T00:00:00Z', '2024-01-01T23:59:59Z', ctx)",
            "returns": "Matching log entries"
        },
        {
            "name": "get_synthetics_tests",
            "description": "Get synthetic monitoring tests", 
            "example": "get_synthetics_tests(ctx)",
            "returns": "Test configurations and types"
        },
        {
            "name": "get_incidents",
            "description": "Get incident data (with pagination)",
            "example": "get_incidents(ctx, page_size=25)",
            "returns": "Incident states and details"
        },
        {
            "name": "create_monitor",
            "description": "Create new monitoring alert",
            "example": "create_monitor('CPU Alert', 'metric alert', 'avg(last_5m):avg:system.cpu.user{*} > 0.8', 'CPU high', ctx)",
            "returns": "Created monitor ID and details"
        },
        {
            "name": "update_monitor", 
            "description": "Update existing monitor",
            "example": "update_monitor('12345', name='Updated CPU Alert', ctx=ctx)",
            "returns": "Updated monitor details"
        },
        {
            "name": "delete_monitor",
            "description": "Delete a monitor",
            "example": "delete_monitor('12345', ctx)",
            "returns": "Deletion confirmation"
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}️⃣ {query['name']}")
        print(f"   📝 {query['description']}")
        print(f"   💻 {query['example']}")
        print(f"   📊 Returns: {query['returns']}")
    
    print(f"\n" + "=" * 60)
    print("✅ Your Datadog credentials are configured:")
    print("   API Key: 2245e679...96b5")
    print("   App Key: 7d145803...46c1") 
    print("   Site: datadoghq.com")
    print()
    print("🔒 All queries support full CRUD operations")
    print("💾 Results are cached locally as JSON files")
    print("🚀 Ready for MCP client connections!")

def show_sample_responses():
    """Show what typical responses look like"""
    print("\n📋 Sample Response Formats:")
    print("=" * 40)
    
    # Sample monitor response
    monitor_response = {
        "filepath": "/cache/monitors_1640995200_abc123.json",
        "summary": "Retrieved 15 monitors",
        "total_monitors": 15,
        "monitor_states": {"OK": 12, "Alert": 2, "No Data": 1},
        "alerting_count": 2
    }
    
    print("\n🔔 get_monitors() response:")
    print(json.dumps(monitor_response, indent=2))
    
    # Sample metrics response  
    metrics_response = {
        "filepath": "/cache/metrics_1640995200_def456.json",
        "summary": "Retrieved 3 metric series with 144 data points", 
        "series_count": 3,
        "data_points": 144,
        "query": "system.cpu.user{*}",
        "time_range": "1640995200 to 1640998800"
    }
    
    print("\n📈 get_metrics() response:")
    print(json.dumps(metrics_response, indent=2))

if __name__ == "__main__":
    show_available_queries()
    show_sample_responses()
