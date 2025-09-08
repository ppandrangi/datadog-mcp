#!/usr/bin/env python3
"""
Final test suite for 80% code coverage
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime, timezone

import pytest

# Mock MCP and external dependencies
mock_fastmcp = MagicMock()
mock_context_class = MagicMock()
mock_fastmcp.Context = mock_context_class

with patch.dict('sys.modules', {
    'mcp.server.fastmcp': mock_fastmcp,
    'dotenv': MagicMock(),
}):
    import server


class TestDatadogConfig:
    def test_config_creation(self):
        config = server.DatadogConfig(api_key="test", app_key="test", site="test.com")
        assert config.api_key == "test"
        assert config.app_key == "test"
        assert config.site == "test.com"
    
    def test_config_default_site(self):
        config = server.DatadogConfig(api_key="test", app_key="test")
        assert config.site == "datadoghq.com"


class TestAppContext:
    def test_app_context_creation(self):
        config = server.DatadogConfig(api_key="test", app_key="test")
        client = MagicMock()
        ctx = server.AppContext(api_client=client, config=config)
        assert ctx.api_client == client
        assert ctx.config == config


class TestConfigurationFunctions:
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app', 'DATADOG_SITE': 'eu'})
    def test_load_config_success(self):
        config = server._load_config()
        assert config.api_key == "key"
        assert config.app_key == "app"
        assert config.site == "eu"
    
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app'})
    def test_load_config_default_site(self):
        config = server._load_config()
        assert config.site == "datadoghq.com"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_missing_keys(self):
        with pytest.raises(ValueError):
            server._load_config()
    
    @patch('server.Configuration')
    @patch('server.ApiClient')
    def test_setup_api_client(self, mock_client, mock_config):
        config = server.DatadogConfig(api_key="key", app_key="app", site="site")
        mock_config_inst = MagicMock()
        mock_config.return_value = mock_config_inst
        mock_client_inst = MagicMock()
        mock_client.return_value = mock_client_inst
        
        result = server._setup_api_client(config)
        
        assert result == mock_client_inst
        mock_config.assert_called_once()
        mock_client.assert_called_once()


class TestDataStorage:
    @pytest.mark.asyncio
    @patch('server.aiofiles.open')
    async def test_store_data(self, mock_open):
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        with patch('server.DATA_DIR', Path(tempfile.gettempdir())):
            result = await server._store_data({"test": "data"}, "prefix")
            
        assert "prefix_" in result
        assert result.endswith(".json")
        mock_file.write.assert_called_once()


class TestAnalysisFunctions:
    def test_generate_summary_metrics(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        result = server._generate_summary(data)
        assert result["data_type"] == "metrics"
        assert result["record_count"] == 1
        assert result["total_data_points"] == 2
    
    def test_generate_summary_large_dataset(self):
        pointlist = [[i, i] for i in range(1001)]
        data = {"series": [{"pointlist": pointlist}]}
        result = server._generate_summary(data)
        assert "Large dataset - consider aggregation" in result["key_insights"]
    
    def test_generate_summary_monitors(self):
        data = [{"overall_state": "OK"}, {"overall_state": "Alert"}]
        result = server._generate_summary(data)
        assert result["data_type"] == "monitors"
        assert result["alerting_monitors"] == 1
    
    def test_generate_summary_events(self):
        data = {"events": [{"id": 1}]}
        result = server._generate_summary(data)
        assert result["data_type"] == "events"
        assert result["record_count"] == 1
    
    def test_calculate_stats_metrics(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 20], [3, None]]}]}
        result = server._calculate_stats(data)
        assert result["min_value"] == 10
        assert result["max_value"] == 20
        assert result["avg_value"] == 15.0
        assert result["total_points"] == 2
    
    def test_calculate_stats_empty(self):
        data = {"series": []}
        result = server._calculate_stats(data)
        assert "calculated_at" in result
        assert "min_value" not in result
    
    def test_analyze_trends_increasing(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 50]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 400.0
    
    def test_analyze_trends_decreasing(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 50]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"
        assert result["change_percentage"] == -50.0
    
    def test_analyze_trends_stable(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 105]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
    
    def test_analyze_trends_empty(self):
        data = {"series": []}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
    
    def test_analyze_trends_zero_division(self):
        data = {"series": [{"pointlist": [[1, 0], [2, 50]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"


class TestMCPTools:
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        config = server.DatadogConfig(api_key="test", app_key="test")
        client = MagicMock()
        return server.AppContext(api_client=client, config=config)
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.MetricsApi')
    async def test_get_metrics_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"series": [{"pointlist": [[1, 10]]}]}
        mock_api.return_value.query_metrics.return_value = mock_response
        
        result = await server.get_metrics("test", 1000, 2000, mock_context)
        
        assert result["series_count"] == 1
        assert result["data_points"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MetricsApi')
    async def test_get_metrics_error(self, mock_api, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_api.side_effect = Exception("API Error")
        
        result = await server.get_metrics("test", 1000, 2000, mock_context)
        
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.MetricsApi')
    async def test_search_metrics_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"metrics": ["m1", "m2"]}
        mock_api.return_value.list_metrics.return_value = mock_response
        
        result = await server.search_metrics("cpu", mock_context)
        
        assert result["metric_count"] == 2
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.MetricsApi')
    async def test_get_metric_metadata_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"description": "test", "unit": "count", "type": "gauge"}
        mock_api.return_value.get_metric_metadata.return_value = mock_response
        
        result = await server.get_metric_metadata("test.metric", mock_context)
        
        assert result["metric_name"] == "test.metric"
        assert result["description"] == "test"
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.MonitorsApi')
    async def test_get_monitors_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_monitor = MagicMock()
        mock_monitor.to_dict.return_value = {"overall_state": "OK"}
        mock_api.return_value.list_monitors.return_value = [mock_monitor]
        
        result = await server.get_monitors(mock_context)
        
        assert result["total_monitors"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.MonitorsApi')
    async def test_get_monitor_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 123, "name": "test", "overall_state": "OK"}
        mock_api.return_value.get_monitor.return_value = mock_response
        
        result = await server.get_monitor("123", mock_context)
        
        assert result["monitor_id"] == 123
        assert result["monitor_name"] == "test"
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.MonitorsApi')
    async def test_create_monitor_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": 456, "name": "new monitor"}
        mock_api.return_value.create_monitor.return_value = mock_response
        
        result = await server.create_monitor("test", "metric alert", "query", "message", mock_context)
        
        assert result["monitor_id"] == 456
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.DashboardsApi')
    async def test_get_dashboards_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"dashboards": [{"title": "dash1"}]}
        mock_api.return_value.list_dashboards.return_value = mock_response
        
        result = await server.get_dashboards(mock_context)
        
        assert result["total_dashboards"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.DashboardsApi')
    async def test_get_dashboard_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"id": "123", "title": "test", "widgets": [{}]}
        mock_api.return_value.get_dashboard.return_value = mock_response
        
        result = await server.get_dashboard("123", mock_context)
        
        assert result["dashboard_id"] == "123"
        assert result["widget_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.LogsApiV2')
    async def test_search_logs_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": [{"message": "log1"}]}
        mock_api.return_value.list_logs.return_value = mock_response
        
        result = await server.search_logs("error", "2023-01-01", "2023-01-02", mock_context)
        
        assert result["log_count"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.EventsApi')
    async def test_get_events_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"events": [{"id": 1}]}
        mock_api.return_value.list_events.return_value = mock_response
        
        result = await server.get_events(1000, 2000, mock_context)
        
        assert result["event_count"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.HostsApi')
    async def test_get_infrastructure_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"host_list": [{"up": True}, {"up": False}]}
        mock_api.return_value.list_hosts.return_value = mock_response
        
        result = await server.get_infrastructure(mock_context)
        
        assert result["total_hosts"] == 2
        assert result["active_hosts"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_service_map_unavailable(self, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        
        with patch('server.ServiceMapApi', None):
            result = await server.get_service_map(mock_context)
        
        assert "error" in result
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.SyntheticsApi')
    async def test_get_synthetics_tests_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"tests": [{"type": "api"}]}
        mock_api.return_value.list_tests.return_value = mock_response
        
        result = await server.get_synthetics_tests(mock_context)
        
        assert result["test_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.RUMApi')
    async def test_get_rum_applications_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": [{"attributes": {"name": "app1"}}]}
        mock_api.return_value.list_rum_applications.return_value = mock_response
        
        result = await server.get_rum_applications(mock_context)
        
        assert result["application_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server._store_data')
    @patch('server.SecurityMonitoringApi')
    async def test_get_security_rules_success(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": [{"attributes": {"isEnabled": True}}]}
        mock_api.return_value.list_security_monitoring_rules.return_value = mock_response
        
        result = await server.get_security_rules(mock_context)
        
        assert result["total_rules"] == 1
        assert result["enabled_rules"] == 1
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_validate_api_key_success(self, mock_api, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_api.return_value.list_monitors.return_value = []
        
        result = await server.validate_api_key(mock_context)
        
        assert result["valid"] is True
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_validate_api_key_error(self, mock_api, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_api.side_effect = Exception("Auth failed")
        
        result = await server.validate_api_key(mock_context)
        
        assert result["valid"] is False
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.DATA_DIR')
    @patch('server.datetime')
    async def test_cleanup_cache_success(self, mock_dt, mock_dir, mock_context):
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
    async def test_analyze_data_success(self, mock_open, mock_exists, mock_context):
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"series": [{"pointlist": [[1, 10]]}]}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "summary")
        
        assert result["analysis_type"] == "summary"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    async def test_analyze_data_file_not_found(self, mock_exists, mock_context):
        mock_exists.return_value = False
        
        result = await server.analyze_data("/missing.json", mock_context)
        
        assert "error" in result
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_stats(self, mock_open, mock_exists, mock_context):
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
    async def test_analyze_data_trends(self, mock_open, mock_exists, mock_context):
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"series": [{"pointlist": [[1, 10]]}]}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "trends")
        
        assert result["analysis_type"] == "trends"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_unknown_type(self, mock_open, mock_exists, mock_context):
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"test": "data"}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        result = await server.analyze_data("/test.json", mock_context, "unknown")
        
        assert "error" in result


class TestLifespanManagement:
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app'})
    @patch('server._setup_api_client')
    async def test_app_lifespan(self, mock_setup):
        mock_client = MagicMock()
        mock_setup.return_value = mock_client
        
        async with server.app_lifespan(MagicMock()) as ctx:
            assert ctx.api_client == mock_client
            assert ctx.config.api_key == "key"


class TestIntegration:
    @patch('server.mcp')
    def test_main_function(self, mock_mcp):
        server.main()
        mock_mcp.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=server", "--cov-report=term-missing", "--cov-fail-under=80"])
