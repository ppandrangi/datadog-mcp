#!/usr/bin/env python3
"""
Integration tests to achieve 80% coverage by executing MCP tools directly
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Set environment variables before importing
os.environ['DATADOG_API_KEY'] = 'test_key'
os.environ['DATADOG_APP_KEY'] = 'test_app_key'

# Import server after setting env vars
import server

class TestMCPToolsIntegration:
    """Integration tests that execute actual MCP tool functions"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context = MagicMock()
        ctx.request_context.lifespan_context = MagicMock()
        
        # Create proper app context
        config = server.DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        app_ctx = server.AppContext(api_client=api_client, config=config)
        ctx.request_context.lifespan_context = app_ctx
        
        return ctx
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    @patch('server._store_data')
    async def test_get_metrics_integration(self, mock_store, mock_api, mock_context):
        """Test get_metrics by calling it directly"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"series": [{"pointlist": [[1, 10]]}]}
        mock_api.return_value.query_metrics.return_value = mock_response
        
        # Execute the actual function
        result = await server.get_metrics("test", 1000, 2000, mock_context)
        
        assert result["series_count"] == 1
        assert result["data_points"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    async def test_get_metrics_error_integration(self, mock_api, mock_context):
        """Test get_metrics error handling"""
        mock_api.side_effect = Exception("API Error")
        
        result = await server.get_metrics("test", 1000, 2000, mock_context)
        
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    @patch('server._store_data')
    async def test_search_metrics_integration(self, mock_store, mock_api, mock_context):
        """Test search_metrics"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"metrics": ["m1", "m2"]}
        mock_api.return_value.list_metrics.return_value = mock_response
        
        result = await server.search_metrics("cpu", mock_context)
        
        assert result["metric_count"] == 2
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    @patch('server._store_data')
    async def test_get_metric_metadata_integration(self, mock_store, mock_api, mock_context):
        """Test get_metric_metadata"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"description": "test", "unit": "count"}
        mock_api.return_value.get_metric_metadata.return_value = mock_response
        
        result = await server.get_metric_metadata("test.metric", mock_context)
        
        assert result["metric_name"] == "test.metric"
        assert result["description"] == "test"
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    @patch('server._store_data')
    async def test_get_monitors_integration(self, mock_store, mock_api, mock_context):
        """Test get_monitors"""
        mock_store.return_value = "/test.json"
        mock_monitor = MagicMock()
        mock_monitor.to_dict.return_value = {"overall_state": "OK"}
        mock_api.return_value.list_monitors.return_value = [mock_monitor]
        
        result = await server.get_monitors(mock_context)
        
        assert result["total_monitors"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    @patch('server._store_data')
    async def test_get_monitor_integration(self, mock_store, mock_api, mock_context):
        """Test get_monitor"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 123, "name": "test", "overall_state": "OK"}
        mock_api.return_value.get_monitor.return_value = mock_response
        
        result = await server.get_monitor("123", mock_context)
        
        assert result["monitor_id"] == 123
        assert result["monitor_name"] == "test"
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    @patch('server._store_data')
    async def test_create_monitor_integration(self, mock_store, mock_api, mock_context):
        """Test create_monitor"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 456, "name": "new"}
        mock_api.return_value.create_monitor.return_value = mock_response
        
        result = await server.create_monitor("test", "metric alert", "query", "msg", mock_context)
        
        assert result["monitor_id"] == 456
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DashboardsApi')
    @patch('server._store_data')
    async def test_get_dashboards_integration(self, mock_store, mock_api, mock_context):
        """Test get_dashboards"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"dashboards": [{"title": "dash1"}]}
        mock_api.return_value.list_dashboards.return_value = mock_response
        
        result = await server.get_dashboards(mock_context)
        
        assert result["total_dashboards"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DashboardsApi')
    @patch('server._store_data')
    async def test_get_dashboard_integration(self, mock_store, mock_api, mock_context):
        """Test get_dashboard"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": "123", "title": "test", "widgets": [{}]}
        mock_api.return_value.get_dashboard.return_value = mock_response
        
        result = await server.get_dashboard("123", mock_context)
        
        assert result["dashboard_id"] == "123"
        assert result["widget_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server.LogsApiV2')
    @patch('server._store_data')
    async def test_search_logs_integration(self, mock_store, mock_api, mock_context):
        """Test search_logs"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": [{"message": "log1"}]}
        mock_api.return_value.list_logs.return_value = mock_response
        
        result = await server.search_logs("error", "2023-01-01", "2023-01-02", mock_context)
        
        assert result["log_count"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.EventsApi')
    @patch('server._store_data')
    async def test_get_events_integration(self, mock_store, mock_api, mock_context):
        """Test get_events"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"events": [{"id": 1}]}
        mock_api.return_value.list_events.return_value = mock_response
        
        result = await server.get_events(1000, 2000, mock_context)
        
        assert result["event_count"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.HostsApi')
    @patch('server._store_data')
    async def test_get_infrastructure_integration(self, mock_store, mock_api, mock_context):
        """Test get_infrastructure"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"host_list": [{"up": True}, {"up": False}]}
        mock_api.return_value.list_hosts.return_value = mock_response
        
        result = await server.get_infrastructure(mock_context)
        
        assert result["total_hosts"] == 2
        assert result["active_hosts"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_service_map_unavailable_integration(self, mock_context):
        """Test get_service_map when unavailable"""
        with patch('server.ServiceMapApi', None):
            result = await server.get_service_map(mock_context)
        
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.SyntheticsApi')
    @patch('server._store_data')
    async def test_get_synthetics_tests_integration(self, mock_store, mock_api, mock_context):
        """Test get_synthetics_tests"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"tests": [{"type": "api"}]}
        mock_api.return_value.list_tests.return_value = mock_response
        
        result = await server.get_synthetics_tests(mock_context)
        
        assert result["test_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server.RUMApi')
    @patch('server._store_data')
    async def test_get_rum_applications_integration(self, mock_store, mock_api, mock_context):
        """Test get_rum_applications"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": [{"attributes": {"name": "app1"}}]}
        mock_api.return_value.list_rum_applications.return_value = mock_response
        
        result = await server.get_rum_applications(mock_context)
        
        assert result["application_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server.SecurityMonitoringApi')
    @patch('server._store_data')
    async def test_get_security_rules_integration(self, mock_store, mock_api, mock_context):
        """Test get_security_rules"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": [{"attributes": {"isEnabled": True}}]}
        mock_api.return_value.list_security_monitoring_rules.return_value = mock_response
        
        result = await server.get_security_rules(mock_context)
        
        assert result["total_rules"] == 1
        assert result["enabled_rules"] == 1
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_validate_api_key_integration(self, mock_api, mock_context):
        """Test validate_api_key"""
        mock_api.return_value.list_monitors.return_value = []
        
        result = await server.validate_api_key(mock_context)
        
        assert result["valid"] is True
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_validate_api_key_error_integration(self, mock_api, mock_context):
        """Test validate_api_key error"""
        mock_api.side_effect = Exception("Auth failed")
        
        result = await server.validate_api_key(mock_context)
        
        assert result["valid"] is False
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DATA_DIR')
    @patch('server.datetime')
    async def test_cleanup_cache_integration(self, mock_dt, mock_dir, mock_context):
        """Test cleanup_cache"""
        mock_file1 = MagicMock()
        mock_file1.stat.return_value.st_mtime = 1000
        mock_file2 = MagicMock()
        mock_file2.stat.return_value.st_mtime = 9999999999
        
        mock_dir.glob.return_value = [mock_file1, mock_file2]
        mock_dt.now.return_value.timestamp.return_value = 100000
        
        result = await server.cleanup_cache(mock_context, 24)
        
        assert result["deleted_count"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_integration(self, mock_open, mock_exists, mock_context):
        """Test analyze_data"""
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"series": [{"pointlist": [[1, 10]]}]}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "summary")
        
        assert result["analysis_type"] == "summary"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_stats_integration(self, mock_open, mock_exists, mock_context):
        """Test analyze_data with stats"""
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"series": [{"pointlist": [[1, 10]]}]}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "stats")
        
        assert result["analysis_type"] == "stats"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_trends_integration(self, mock_open, mock_exists, mock_context):
        """Test analyze_data with trends"""
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"series": [{"pointlist": [[1, 10]]}]}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "trends")
        
        assert result["analysis_type"] == "trends"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    async def test_analyze_data_not_found_integration(self, mock_exists, mock_context):
        """Test analyze_data file not found"""
        mock_exists.return_value = False
        
        result = await server.analyze_data("/missing.json", mock_context)
        
        assert "error" in result
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_unknown_type_integration(self, mock_open, mock_exists, mock_context):
        """Test analyze_data unknown type"""
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"test": "data"}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "unknown")
        
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=server", "--cov-report=term-missing", "--cov-fail-under=80"])
