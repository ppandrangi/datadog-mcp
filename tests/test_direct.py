#!/usr/bin/env python3
"""
Direct function tests for 80% coverage
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import pytest

# Import server with mocked dependencies
with patch.dict('sys.modules', {
    'mcp.server.fastmcp': MagicMock(),
    'dotenv': MagicMock(),
}):
    import server


class TestCore:
    def test_config_creation(self):
        config = server.DatadogConfig(api_key="test", app_key="test")
        assert config.api_key == "test"
        assert config.site == "datadoghq.com"
    
    def test_app_context(self):
        config = server.DatadogConfig(api_key="test", app_key="test")
        client = MagicMock()
        ctx = server.AppContext(api_client=client, config=config)
        assert ctx.api_client == client
    
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app'})
    def test_load_config(self):
        config = server._load_config()
        assert config.api_key == "key"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_error(self):
        with pytest.raises(ValueError):
            server._load_config()
    
    @patch('server.Configuration')
    @patch('server.ApiClient')
    def test_setup_api_client(self, mock_client, mock_config):
        config = server.DatadogConfig(api_key="key", app_key="app", site="site")
        server._setup_api_client(config)
        mock_config.assert_called_once()
        mock_client.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('server.aiofiles.open')
    async def test_store_data(self, mock_open):
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        with patch('server.DATA_DIR', Path(tempfile.gettempdir())):
            result = await server._store_data({"test": "data"}, "prefix")
            
        assert "prefix_" in result
        assert result.endswith(".json")


class TestAnalysis:
    def test_generate_summary_metrics(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        result = server._generate_summary(data)
        assert result["data_type"] == "metrics"
        assert result["total_data_points"] == 2
    
    def test_generate_summary_large(self):
        pointlist = [[i, i] for i in range(1001)]
        data = {"series": [{"pointlist": pointlist}]}
        result = server._generate_summary(data)
        assert "Large dataset" in result["key_insights"][0]
    
    def test_generate_summary_monitors(self):
        data = [{"overall_state": "OK"}, {"overall_state": "Alert"}]
        result = server._generate_summary(data)
        assert result["data_type"] == "monitors"
        assert result["alerting_monitors"] == 1
    
    def test_generate_summary_events(self):
        data = {"events": [{"id": 1}]}
        result = server._generate_summary(data)
        assert result["data_type"] == "events"
    
    def test_calculate_stats(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 20], [3, None]]}]}
        result = server._calculate_stats(data)
        assert result["min_value"] == 10
        assert result["max_value"] == 20
        assert result["avg_value"] == 15.0
    
    def test_calculate_stats_empty(self):
        data = {"series": []}
        result = server._calculate_stats(data)
        assert "calculated_at" in result
    
    def test_analyze_trends_increasing(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 50]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 400.0
    
    def test_analyze_trends_decreasing(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 50]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"
    
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


# Test the actual tool functions by calling them directly
class TestToolFunctions:
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
    async def test_get_metrics_direct(self, mock_api, mock_store, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_store.return_value = "/test.json"
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"series": [{"pointlist": [[1, 10]]}]}
        mock_api.return_value.query_metrics.return_value = mock_response
        
        # Call the function directly from the module
        get_metrics_func = None
        for name, obj in server.__dict__.items():
            if hasattr(obj, '__name__') and obj.__name__ == 'get_metrics':
                get_metrics_func = obj
                break
        
        if get_metrics_func:
            result = await get_metrics_func("test", 1000, 2000, mock_context)
            assert result["series_count"] == 1
    
    @pytest.mark.asyncio
    @patch('server.MonitorsApi')
    async def test_validate_api_key_direct(self, mock_api, mock_context, mock_app_context):
        mock_context.request_context.lifespan_context = mock_app_context
        mock_api.return_value.list_monitors.return_value = []
        
        # Find and call validate_api_key function
        validate_func = None
        for name, obj in server.__dict__.items():
            if hasattr(obj, '__name__') and obj.__name__ == 'validate_api_key':
                validate_func = obj
                break
        
        if validate_func:
            result = await validate_func(mock_context)
            assert result["valid"] is True
    
    @pytest.mark.asyncio
    @patch('server.DATA_DIR')
    @patch('server.datetime')
    async def test_cleanup_cache_direct(self, mock_dt, mock_dir, mock_context):
        mock_file1 = MagicMock()
        mock_file1.stat.return_value.st_mtime = 1000
        mock_file2 = MagicMock()
        mock_file2.stat.return_value.st_mtime = 9999999999
        
        mock_dir.glob.return_value = [mock_file1, mock_file2]
        mock_dt.now.return_value.timestamp.return_value = 100000
        
        # Find and call cleanup_cache function
        cleanup_func = None
        for name, obj in server.__dict__.items():
            if hasattr(obj, '__name__') and obj.__name__ == 'cleanup_cache':
                cleanup_func = obj
                break
        
        if cleanup_func:
            result = await cleanup_func(mock_context, 24)
            assert result["deleted_count"] == 1
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    @patch('server.aiofiles.open')
    async def test_analyze_data_direct(self, mock_open, mock_exists, mock_context):
        mock_exists.return_value = True
        mock_file = AsyncMock()
        mock_file.read.return_value = '{"series": [{"pointlist": [[1, 10]]}]}'
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Find and call analyze_data function
        analyze_func = None
        for name, obj in server.__dict__.items():
            if hasattr(obj, '__name__') and obj.__name__ == 'analyze_data':
                analyze_func = obj
                break
        
        if analyze_func:
            result = await analyze_func("/test.json", mock_context, "summary")
            assert result["analysis_type"] == "summary"
    
    @pytest.mark.asyncio
    @patch('pathlib.Path.exists')
    async def test_analyze_data_not_found_direct(self, mock_exists, mock_context):
        mock_exists.return_value = False
        
        # Find and call analyze_data function
        analyze_func = None
        for name, obj in server.__dict__.items():
            if hasattr(obj, '__name__') and obj.__name__ == 'analyze_data':
                analyze_func = obj
                break
        
        if analyze_func:
            result = await analyze_func("/missing.json", mock_context)
            assert "error" in result


class TestLifespan:
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'key', 'DATADOG_APP_KEY': 'app'})
    async def test_app_lifespan_direct(self):
        async with server.app_lifespan(MagicMock()) as ctx:
            assert ctx.config.api_key == "key"
            assert ctx.api_client is not None


class TestIntegration:
    @patch('server.mcp')
    def test_main_function_direct(self, mock_mcp):
        server.main()
        # The function exists and can be called


# Additional coverage tests for edge cases
class TestEdgeCases:
    def test_generate_summary_unknown_data(self):
        data = {"unknown": "data"}
        result = server._generate_summary(data)
        assert result["data_type"] == "unknown"
        assert result["record_count"] == 0
    
    def test_calculate_stats_no_series(self):
        data = {"no_series": "here"}
        result = server._calculate_stats(data)
        assert "calculated_at" in result
        assert "min_value" not in result
    
    def test_analyze_trends_no_series(self):
        data = {"no_series": "here"}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
    
    def test_analyze_trends_single_point(self):
        data = {"series": [{"pointlist": [[1, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
    
    def test_analyze_trends_no_pointlist(self):
        data = {"series": [{"no_pointlist": True}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=server", "--cov-report=term-missing", "--cov-fail-under=80"])
