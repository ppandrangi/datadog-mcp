#!/usr/bin/env python3
"""
Simple MCP client to test Datadog server with read-only queries
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from server import (
    validate_api_key, get_monitors, get_dashboards, 
    get_infrastructure, get_synthetics_tests
)

async def create_mock_context():
    """Create a mock context for testing"""
    mock_ctx = MagicMock()
    mock_ctx.info = AsyncMock()
    mock_ctx.error = AsyncMock()
    mock_ctx.request_context.lifespan_context.config.site = 'datadoghq.com'
    return mock_ctx

async def test_read_only_queries():
    """Test various read-only Datadog queries"""
    print("🚀 Testing Datadog MCP Server - Read-Only Queries")
    print("=" * 60)
    
    ctx = await create_mock_context()
    
    # Test 1: Validate API credentials
    print("\n1️⃣ Testing API Validation...")
    try:
        result = await validate_api_key(ctx)
        print(f"✅ API Validation: {result.get('summary', 'Success')}")
    except Exception as e:
        print(f"❌ API Validation failed: {str(e)}")
    
    # Test 2: Get monitors (mocked for demo)
    print("\n2️⃣ Testing Monitor Retrieval...")
    try:
        # Mock the API response to avoid actual API calls
        from unittest.mock import patch
        with patch('server.MonitorsApi') as mock_api:
            mock_monitor = MagicMock()
            mock_monitor.to_dict.return_value = {
                "id": 12345,
                "name": "CPU Usage Alert", 
                "overall_state": "OK",
                "type": "metric alert"
            }
            mock_api.return_value.list_monitors = AsyncMock(return_value=[mock_monitor])
            
            with patch('server._store_data', return_value="/tmp/monitors.json"):
                result = await get_monitors(ctx)
                print(f"✅ Monitors: Found {result.get('total_monitors', 0)} monitors")
                print(f"   States: {result.get('monitor_states', {})}")
    except Exception as e:
        print(f"❌ Monitor query failed: {str(e)}")
    
    # Test 3: Get dashboards (mocked)
    print("\n3️⃣ Testing Dashboard Retrieval...")
    try:
        with patch('server.DashboardsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "dashboards": [
                    {"id": "abc-123", "title": "System Overview"},
                    {"id": "def-456", "title": "Application Metrics"}
                ]
            }
            mock_api.return_value.list_dashboards = AsyncMock(return_value=mock_response)
            
            with patch('server._store_data', return_value="/tmp/dashboards.json"):
                result = await get_dashboards(ctx)
                print(f"✅ Dashboards: Found {result.get('total_dashboards', 0)} dashboards")
                print(f"   Sample: {result.get('sample_dashboards', [])}")
    except Exception as e:
        print(f"❌ Dashboard query failed: {str(e)}")
    
    # Test 4: Get infrastructure (mocked)
    print("\n4️⃣ Testing Infrastructure Query...")
    try:
        with patch('server.HostsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "host_list": [
                    {"name": "web-server-01", "up": True},
                    {"name": "db-server-01", "up": True},
                    {"name": "cache-server-01", "up": False}
                ]
            }
            mock_api.return_value.list_hosts = AsyncMock(return_value=mock_response)
            
            with patch('server._store_data', return_value="/tmp/infrastructure.json"):
                result = await get_infrastructure(ctx)
                print(f"✅ Infrastructure: {result.get('total_hosts', 0)} hosts")
                print(f"   Active: {result.get('active_hosts', 0)}, Inactive: {result.get('inactive_hosts', 0)}")
    except Exception as e:
        print(f"❌ Infrastructure query failed: {str(e)}")
    
    # Test 5: Get synthetics tests (mocked)
    print("\n5️⃣ Testing Synthetics Tests...")
    try:
        with patch('server.SyntheticsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "tests": [
                    {"name": "API Health Check", "type": "api"},
                    {"name": "Website Load Test", "type": "browser"}
                ]
            }
            mock_api.return_value.list_tests = AsyncMock(return_value=mock_response)
            
            with patch('server._store_data', return_value="/tmp/synthetics.json"):
                result = await get_synthetics_tests(ctx)
                print(f"✅ Synthetics: Found {result.get('test_count', 0)} tests")
                print(f"   Types: {result.get('test_types', {})}")
    except Exception as e:
        print(f"❌ Synthetics query failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Read-only query testing completed!")
    print("💾 All data would be cached to local JSON files")
    print("🔒 No write operations performed - safe read-only access")

if __name__ == "__main__":
    asyncio.run(test_read_only_queries())
