#!/usr/bin/env python3
"""
Complete coverage tests to reach 100% for MCP tools, data storage, and lifespan management
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Set environment variables
os.environ['DATADOG_API_KEY'] = 'test_key'
os.environ['DATADOG_APP_KEY'] = 'test_app_key'

import server

class TestMCPToolsComplete:
    """Complete MCP tools coverage"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context = MagicMock()
        config = server.DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        app_ctx = server.AppContext(api_client=api_client, config=config)
        ctx.request_context.lifespan_context = app_ctx
        return ctx
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    async def test_search_metrics_error(self, mock_api, mock_context):
        """Test search_metrics error path"""
        mock_api.side_effect = Exception("Search error")
        result = await server.search_metrics("cpu", mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    async def test_get_metric_metadata_error(self, mock_api, mock_context):
        """Test get_metric_metadata error path"""
        mock_api.side_effect = Exception("Metadata error")
        result = await server.get_metric_metadata("test.metric", mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_get_monitors_error(self, mock_api, mock_context):
        """Test get_monitors error path"""
        mock_api.side_effect = Exception("Monitors error")
        result = await server.get_monitors(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_get_monitor_error(self, mock_api, mock_context):
        """Test get_monitor error path"""
        mock_api.side_effect = Exception("Monitor error")
        result = await server.get_monitor("123", mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_create_monitor_error(self, mock_api, mock_context):
        """Test create_monitor error path"""
        mock_api.side_effect = Exception("Create error")
        result = await server.create_monitor("test", "alert", "query", "msg", mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DashboardsApi')
    async def test_get_dashboards_error(self, mock_api, mock_context):
        """Test get_dashboards error path"""
        mock_api.side_effect = Exception("Dashboards error")
        result = await server.get_dashboards(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DashboardsApi')
    async def test_get_dashboard_error(self, mock_api, mock_context):
        """Test get_dashboard error path"""
        mock_api.side_effect = Exception("Dashboard error")
        result = await server.get_dashboard("123", mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.LogsApiV2')
    async def test_search_logs_error(self, mock_api, mock_context):
        """Test search_logs error path"""
        mock_api.side_effect = Exception("Logs error")
        result = await server.search_logs("error", "2023-01-01", "2023-01-02", mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.EventsApi')
    async def test_get_events_error(self, mock_api, mock_context):
        """Test get_events error path"""
        mock_api.side_effect = Exception("Events error")
        result = await server.get_events(1000, 2000, mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.HostsApi')
    async def test_get_infrastructure_error(self, mock_api, mock_context):
        """Test get_infrastructure error path"""
        mock_api.side_effect = Exception("Infrastructure error")
        result = await server.get_infrastructure(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.SyntheticsApi')
    async def test_get_synthetics_tests_error(self, mock_api, mock_context):
        """Test get_synthetics_tests error path"""
        mock_api.side_effect = Exception("Synthetics error")
        result = await server.get_synthetics_tests(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.RUMApi')
    async def test_get_rum_applications_error(self, mock_api, mock_context):
        """Test get_rum_applications error path"""
        mock_api.side_effect = Exception("RUM error")
        result = await server.get_rum_applications(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.SecurityMonitoringApi')
    async def test_get_security_rules_error(self, mock_api, mock_context):
        """Test get_security_rules error path"""
        mock_api.side_effect = Exception("Security error")
        result = await server.get_security_rules(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DATA_DIR')
    async def test_cleanup_cache_error(self, mock_dir, mock_context):
        """Test cleanup_cache error path"""
        mock_dir.glob.side_effect = Exception("Cleanup error")
        result = await server.cleanup_cache(mock_context, 24)
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_json_error(self, mock_open, mock_exists, mock_context):
        """Test analyze_data JSON parsing error"""
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = 'invalid json'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "summary")
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.ServiceMapApi')
    @patch('server._store_data')
    async def test_get_service_map_with_api(self, mock_store, mock_api, mock_context):
        """Test get_service_map with available API"""
        mock_store.return_value = "/test.json"
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"services": [{"name": "svc1"}]}
        mock_api.return_value.get_service_map.return_value = mock_response
        
        result = await server.get_service_map(mock_context, "prod")
        assert result["service_count"] == 1
        assert result["environment"] == "prod"
    
    @pytest.mark.asyncio
    @patch('server.ServiceMapApi')
    async def test_get_service_map_error(self, mock_api, mock_context):
        """Test get_service_map error path"""
        mock_api.side_effect = Exception("Service map error")
        result = await server.get_service_map(mock_context)
        assert "error" in result
        mock_context.error.assert_called_once()


class TestDataStorageComplete:
    """Complete data storage coverage"""
    
    @pytest.mark.asyncio
    @patch('server.aiofiles.open')
    async def test_store_data_write_error(self, mock_open):
        """Test _store_data write error"""
        mock_file = AsyncMock()
        mock_file.write.side_effect = Exception("Write error")
        mock_open.return_value.__aenter__.return_value = mock_file
        
        with patch('server.DATA_DIR', Path(tempfile.gettempdir())):
            with pytest.raises(Exception):
                await server._store_data({"test": "data"}, "prefix")
    
    @pytest.mark.asyncio
    @patch('server.aiofiles.open')
    async def test_store_data_complex_serialization(self, mock_open):
        """Test _store_data with complex objects"""
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Test with datetime and other complex objects
        from datetime import datetime, timezone
        complex_data = {
            "timestamp": datetime.now(timezone.utc),
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "none_value": None
        }
        
        with patch('server.DATA_DIR', Path(tempfile.gettempdir())):
            result = await server._store_data(complex_data, "complex")
            
        assert "complex_" in result
        mock_file.write.assert_called_once()


class TestLifespanComplete:
    """Complete lifespan management coverage"""
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app'})
    async def test_app_lifespan_cleanup(self):
        """Test app_lifespan cleanup path"""
        mock_server = MagicMock()
        
        # Test that cleanup happens even if exception occurs
        with patch('server._setup_api_client') as mock_setup:
            mock_client = AsyncMock()
            mock_setup.return_value = mock_client
            
            async with server.app_lifespan(mock_server) as ctx:
                assert ctx.config.api_key == "key"
                # Simulate some work that could raise exception
                pass
            
            # Setup should have been called
            mock_setup.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app'})
    async def test_app_lifespan_exception_handling(self):
        """Test app_lifespan exception in setup"""
        mock_server = MagicMock()
        
        with patch('server._setup_api_client') as mock_setup:
            mock_setup.side_effect = Exception("Setup error")
            
            with pytest.raises(Exception):
                async with server.app_lifespan(mock_server) as ctx:
                    pass


class TestMainFunction:
    """Test main function coverage"""
    
    @patch('server.mcp')
    def test_main_function_execution(self, mock_mcp):
        """Test main function actually calls mcp.run()"""
        server.main()
        mock_mcp.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=server", "--cov-report=term-missing"])
