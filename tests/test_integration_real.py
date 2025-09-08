#!/usr/bin/env python3
"""
Integration tests for Datadog MCP server
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
import server

class TestIntegrationReal:
    """Integration tests with real async patterns"""
    
    @pytest.fixture
    def mock_context(self):
        """Create a properly configured mock context"""
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Create proper app context
        config = server.DatadogConfig(api_key="test", app_key="test")
        mock_client = MagicMock()
        app_ctx = server.AppContext(api_client=mock_client, config=config)
        mock_ctx.request_context.lifespan_context = app_ctx
        
        return mock_ctx

    @pytest.mark.asyncio
    async def test_get_metrics_integration(self, mock_context):
        """Test get_metrics with proper async mocking"""
        with patch('server.MetricsApi') as mock_api_class:
            # Create mock response
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "series": [
                    {"pointlist": [[1640995200, 10.5], [1640995260, 12.3]]},
                    {"pointlist": [[1640995200, 8.7]]}
                ]
            }
            
            # Create mock API instance
            mock_api_instance = MagicMock()
            mock_api_instance.query_metrics = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/metrics.json"):
                result = await server.get_metrics(
                    "system.cpu.user{*}", 1640995200, 1640995800, mock_context
                )
                
                assert "series_count" in result
                assert result["series_count"] == 2
                assert result["data_points"] == 3
                mock_api_instance.query_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_metrics_integration(self, mock_context):
        """Test search_metrics with proper async mocking"""
        with patch('server.MetricsApi') as mock_api_class:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "metrics": ["system.cpu.user", "system.cpu.system", "system.memory.used"]
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_metrics = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/search.json"):
                result = await server.search_metrics("system", mock_context)
                
                assert "metric_count" in result
                assert result["metric_count"] == 3
                assert "system.cpu.user" in result["sample_metrics"]

    @pytest.mark.asyncio
    async def test_get_monitors_integration(self, mock_context):
        """Test get_monitors with proper async mocking"""
        with patch('server.MonitorsApi') as mock_api_class:
            # Create mock monitors
            mock_monitor1 = MagicMock()
            mock_monitor1.to_dict.return_value = {
                "id": 123,
                "name": "CPU Alert",
                "overall_state": "OK"
            }
            
            mock_monitor2 = MagicMock()
            mock_monitor2.to_dict.return_value = {
                "id": 456,
                "name": "Memory Alert", 
                "overall_state": "Alert"
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_monitors = AsyncMock(return_value=[mock_monitor1, mock_monitor2])
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/monitors.json"):
                result = await server.get_monitors(mock_context)
                
                assert "total_monitors" in result
                assert result["total_monitors"] == 2
                assert result["monitor_states"]["OK"] == 1
                assert result["monitor_states"]["Alert"] == 1
                assert result["alerting_count"] == 1

    @pytest.mark.asyncio
    async def test_create_monitor_integration(self, mock_context):
        """Test create_monitor with proper async mocking"""
        with patch('server.MonitorsApi') as mock_api_class:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "id": 789,
                "name": "New CPU Alert",
                "type": "metric alert",
                "query": "avg(last_5m):avg:system.cpu.user{*} > 0.8"
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.create_monitor = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/monitor_created.json"):
                result = await server.create_monitor(
                    "New CPU Alert",
                    "metric alert", 
                    "avg(last_5m):avg:system.cpu.user{*} > 0.8",
                    "CPU usage is high @slack-alerts",
                    mock_context
                )
                
                assert "monitor_id" in result
                assert result["monitor_id"] == 789
                assert result["monitor_name"] == "New CPU Alert"

    @pytest.mark.asyncio
    async def test_get_dashboards_integration(self, mock_context):
        """Test get_dashboards with proper async mocking"""
        with patch('server.DashboardsApi') as mock_api_class:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "dashboards": [
                    {"id": "abc-123", "title": "System Overview", "is_favorite": True},
                    {"id": "def-456", "title": "Application Metrics", "is_favorite": False}
                ]
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_dashboards = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/dashboards.json"):
                result = await server.get_dashboards(mock_context)
                
                assert "total_dashboards" in result
                assert result["total_dashboards"] == 2
                assert len(result["sample_dashboards"]) == 2

    @pytest.mark.asyncio
    async def test_search_logs_integration(self, mock_context):
        """Test search_logs with proper async mocking"""
        with patch('server.LogsApiV2') as mock_api_class:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "data": [
                    {"id": "log1", "attributes": {"message": "Error occurred"}},
                    {"id": "log2", "attributes": {"message": "Another error"}}
                ]
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_logs = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/logs.json"):
                result = await server.search_logs(
                    "ERROR", "2024-01-01T00:00:00Z", "2024-01-01T23:59:59Z", mock_context
                )
                
                assert "log_count" in result
                assert result["log_count"] == 2

    @pytest.mark.asyncio
    async def test_get_infrastructure_integration(self, mock_context):
        """Test get_infrastructure with proper async mocking"""
        with patch('server.HostsApi') as mock_api_class:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "host_list": [
                    {"name": "web-01", "up": True, "last_reported_time": 1640995200},
                    {"name": "web-02", "up": True, "last_reported_time": 1640995200},
                    {"name": "db-01", "up": False, "last_reported_time": 1640995000}
                ]
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_hosts = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/infrastructure.json"):
                result = await server.get_infrastructure(mock_context)
                
                assert "total_hosts" in result
                assert result["total_hosts"] == 3
                assert result["active_hosts"] == 2
                assert result["inactive_hosts"] == 1

    @pytest.mark.asyncio
    async def test_get_synthetics_tests_integration(self, mock_context):
        """Test get_synthetics_tests with proper async mocking"""
        with patch('server.SyntheticsApi') as mock_api_class:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "tests": [
                    {"name": "API Health Check", "type": "api", "status": "live"},
                    {"name": "Website Load Test", "type": "browser", "status": "paused"}
                ]
            }
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_tests = AsyncMock(return_value=mock_response)
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/synthetics.json"):
                result = await server.get_synthetics_tests(mock_context)
                
                assert "test_count" in result
                assert result["test_count"] == 2
                assert "api" in result["test_types"]
                assert "browser" in result["test_types"]

    @pytest.mark.asyncio
    async def test_get_incidents_integration(self, mock_context):
        """Test get_incidents with pagination"""
        with patch('server.IncidentsApi') as mock_api_class:
            # Create mock incidents
            mock_incident1 = MagicMock()
            mock_incident1.to_dict.return_value = {
                "id": "incident-1",
                "attributes": {"state": "active", "title": "Database Down"}
            }
            
            mock_incident2 = MagicMock()
            mock_incident2.to_dict.return_value = {
                "id": "incident-2", 
                "attributes": {"state": "resolved", "title": "API Slow"}
            }
            
            # Mock pagination
            async def mock_pagination(**kwargs):
                yield mock_incident1
                yield mock_incident2
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_incidents_with_pagination = mock_pagination
            mock_api_class.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test/incidents.json"):
                result = await server.get_incidents(mock_context, page_size=10)
                
                assert "total_incidents" in result
                assert result["total_incidents"] == 2
                assert result["incident_states"]["active"] == 1
                assert result["incident_states"]["resolved"] == 1

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_context):
        """Test error handling in API calls"""
        with patch('server.MetricsApi') as mock_api_class:
            mock_api_instance = MagicMock()
            mock_api_instance.query_metrics = AsyncMock(side_effect=Exception("API Error"))
            mock_api_class.return_value = mock_api_instance
            
            result = await server.get_metrics("test", 1000, 2000, mock_context)
            
            assert "error" in result
            assert "API Error" in result["error"]
            mock_context.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_integration(self):
        """Test app lifespan context manager"""
        mock_server = MagicMock()
        
        with patch('server._load_config') as mock_load:
            with patch('server._setup_api_client') as mock_setup:
                mock_config = server.DatadogConfig(api_key="test", app_key="test")
                mock_client = MagicMock()
                mock_load.return_value = mock_config
                mock_setup.return_value = mock_client
                
                async with server.app_lifespan(mock_server) as ctx:
                    assert isinstance(ctx, server.AppContext)
                    assert ctx.config == mock_config
                    assert ctx.api_client == mock_client
                
                mock_load.assert_called_once()
                mock_setup.assert_called_once_with(mock_config)
