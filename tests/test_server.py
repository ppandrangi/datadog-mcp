#!/usr/bin/env python3
"""
Comprehensive test suite for Datadog MCP Server
Target: 80% code coverage
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from datetime import datetime, timezone

import pytest
import asyncio


class TestDatadogConfig:
    """Test DatadogConfig model"""
    
    def test_config_creation(self):
        """Test config creation with valid data"""
        from server import DatadogConfig
        
        config = DatadogConfig(
            api_key="test_api_key",
            app_key="test_app_key",
            site="datadoghq.com"
        )
        
        assert config.api_key == "test_api_key"
        assert config.app_key == "test_app_key"
        assert config.site == "datadoghq.com"
    
    def test_config_default_site(self):
        """Test config with default site"""
        from server import DatadogConfig
        
        config = DatadogConfig(
            api_key="test_api_key",
            app_key="test_app_key"
        )
        
        assert config.site == "datadoghq.com"


class TestAppContext:
    """Test AppContext dataclass"""
    
    def test_app_context_creation(self):
        """Test AppContext creation"""
        from server import AppContext, DatadogConfig
        
        config = DatadogConfig(api_key="test", app_key="test")
        mock_client = MagicMock()
        
        ctx = AppContext(api_client=mock_client, config=config)
        
        assert ctx.api_client == mock_client
        assert ctx.config == config


class TestConfigurationFunctions:
    """Test configuration loading functions"""
    
    @patch.dict(os.environ, {
        'DATADOG_API_KEY': 'test_api_key',
        'DATADOG_APP_KEY': 'test_app_key',
        'DATADOG_SITE': 'datadoghq.eu'
    })
    def test_load_config_success(self):
        """Test successful config loading"""
        from server import _load_config
        
        config = _load_config()
        
        assert config.api_key == "test_api_key"
        assert config.app_key == "test_app_key"
        assert config.site == "datadoghq.eu"
    
    @patch.dict(os.environ, {
        'DATADOG_API_KEY': 'test_api_key',
        'DATADOG_APP_KEY': 'test_app_key'
    })
    def test_load_config_default_site(self):
        """Test config loading with default site"""
        from server import _load_config
        
        config = _load_config()
        
        assert config.site == "datadoghq.com"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_missing_api_key(self):
        """Test config loading with missing API key"""
        from server import _load_config
        
        with pytest.raises(ValueError, match="DATADOG_API_KEY and DATADOG_APP_KEY must be set"):
            _load_config()
    
    @patch.dict(os.environ, {'DATADOG_API_KEY': 'test_key'}, clear=True)
    def test_load_config_missing_app_key(self):
        """Test config loading with missing app key"""
        from server import _load_config
        
        with pytest.raises(ValueError, match="DATADOG_API_KEY and DATADOG_APP_KEY must be set"):
            _load_config()
    
    @patch('server.Configuration')
    @patch('server.ApiClient')
    def test_setup_api_client(self, mock_api_client, mock_configuration):
        """Test API client setup"""
        from server import _setup_api_client, DatadogConfig
        
        config = DatadogConfig(
            api_key="test_api_key",
            app_key="test_app_key",
            site="datadoghq.com"
        )
        
        mock_config_instance = MagicMock()
        mock_configuration.return_value = mock_config_instance
        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance
        
        result = _setup_api_client(config)
        
        assert mock_config_instance.api_key["apiKeyAuth"] == "test_api_key"
        assert mock_config_instance.api_key["appKeyAuth"] == "test_app_key"
        assert mock_config_instance.server_variables["site"] == "datadoghq.com"
        assert result == mock_client_instance


class TestDataStorage:
    """Test data storage functionality"""
    
    @pytest.mark.asyncio
    async def test_store_data(self):
        """Test data storage"""
        from server import _store_data
        
        test_data = {"test": "data", "timestamp": 1234567890}
        
        with patch('server.DATA_DIR', Path(tempfile.gettempdir())):
            with patch('aiofiles.open', mock_open()) as mock_file:
                mock_file.return_value.__aenter__.return_value.write = AsyncMock()
                
                filepath = await _store_data(test_data, "test")
                
                assert "test_" in filepath
                assert filepath.endswith(".json")
                mock_file.return_value.__aenter__.return_value.write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_data_with_complex_object(self):
        """Test storing complex data with datetime objects"""
        from server import _store_data
        
        test_data = {
            "timestamp": datetime.now(timezone.utc),
            "nested": {"key": "value"}
        }
        
        with patch('server.DATA_DIR', Path(tempfile.gettempdir())):
            with patch('aiofiles.open', mock_open()) as mock_file:
                mock_file.return_value.__aenter__.return_value.write = AsyncMock()
                
                filepath = await _store_data(test_data, "complex")
                
                assert "complex_" in filepath
                mock_file.return_value.__aenter__.return_value.write.assert_called_once()


class TestAnalysisFunctions:
    """Test data analysis functions"""
    
    def test_generate_summary_metrics(self):
        """Test summary generation for metrics data"""
        from server import _generate_summary
        
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20]]},
                {"pointlist": [[1, 30], [2, 40], [3, 50]]}
            ]
        }
        
        result = _generate_summary(data)
        
        assert result["data_type"] == "metrics"
        assert result["record_count"] == 2
        assert result["total_data_points"] == 5
    
    def test_generate_summary_large_dataset(self):
        """Test summary with large dataset"""
        from server import _generate_summary
        
        # Create data with >1000 points
        pointlist = [[i, i*10] for i in range(1001)]
        data = {"series": [{"pointlist": pointlist}]}
        
        result = _generate_summary(data)
        
        assert "Large dataset - consider aggregation" in result["key_insights"]
    
    def test_generate_summary_monitors(self):
        """Test summary generation for monitors data"""
        from server import _generate_summary
        
        data = [
            {"overall_state": "OK"},
            {"overall_state": "Alert"},
            {"overall_state": "Alert"}
        ]
        
        result = _generate_summary(data)
        
        assert result["data_type"] == "monitors"
        assert result["record_count"] == 3
        assert result["alerting_monitors"] == 2
        assert "2 monitors currently alerting" in result["key_insights"]
    
    def test_generate_summary_events(self):
        """Test summary generation for events data"""
        from server import _generate_summary
        
        data = {"events": [{"id": 1}, {"id": 2}]}
        
        result = _generate_summary(data)
        
        assert result["data_type"] == "events"
        assert result["record_count"] == 2
    
    def test_calculate_stats_metrics(self):
        """Test statistics calculation for metrics"""
        from server import _calculate_stats
        
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20]]},
                {"pointlist": [[1, 30], [2, None], [3, 50]]}  # Test None handling
            ]
        }
        
        result = _calculate_stats(data)
        
        assert result["min_value"] == 10
        assert result["max_value"] == 50
        assert result["avg_value"] == 27.5  # (10+20+30+50)/4
        assert result["total_points"] == 4
        assert "calculated_at" in result
    
    def test_calculate_stats_empty_data(self):
        """Test statistics with empty data"""
        from server import _calculate_stats
        
        data = {"series": []}
        
        result = _calculate_stats(data)
        
        assert "calculated_at" in result
        assert "min_value" not in result
    
    def test_analyze_trends_increasing(self):
        """Test trend analysis - increasing"""
        from server import _analyze_trends
        
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, 50]]}  # 400% increase
            ]
        }
        
        result = _analyze_trends(data)
        
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 400.0
    
    def test_analyze_trends_decreasing(self):
        """Test trend analysis - decreasing"""
        from server import _analyze_trends
        
        data = {
            "series": [
                {"pointlist": [[1, 100], [2, 50]]}  # 50% decrease
            ]
        }
        
        result = _analyze_trends(data)
        
        assert result["trend_direction"] == "decreasing"
        assert result["change_percentage"] == -50.0
    
    def test_analyze_trends_stable(self):
        """Test trend analysis - stable"""
        from server import _analyze_trends
        
        data = {
            "series": [
                {"pointlist": [[1, 100], [2, 105]]}  # 5% increase (stable)
            ]
        }
        
        result = _analyze_trends(data)
        
        assert result["trend_direction"] == "stable"
        assert result["change_percentage"] == 5.0
    
    def test_analyze_trends_empty_series(self):
        """Test trend analysis with empty series"""
        from server import _analyze_trends
        
        data = {"series": []}
        
        result = _analyze_trends(data)
        
        assert result["trend_direction"] == "stable"
        assert "analyzed_at" in result


class TestMCPTools:
    """Test MCP tool functions"""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        """Create mock app context"""
        from server import AppContext, DatadogConfig
        
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_get_metrics_success(self, mock_context, mock_app_context):
        """Test get_metrics tool success"""
        from server import get_metrics
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "series": [
                {"pointlist": [[1, 10], [2, 20]]},
                {"pointlist": [[1, 30]]}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.query_metrics.return_value = mock_response
        
        with patch('server.MetricsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_metrics("test.metric", 1000, 2000, mock_context)
        
        assert result["series_count"] == 2
        assert result["data_points"] == 3
        assert result["filepath"] == "/test/path.json"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_metrics_error(self, mock_context, mock_app_context):
        """Test get_metrics tool error handling"""
        from server import get_metrics
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        with patch('server.MetricsApi', side_effect=Exception("API Error")):
            result = await get_metrics("test.metric", 1000, 2000, mock_context)
        
        assert "error" in result
        assert "API Error" in result["error"]
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, mock_context, mock_app_context):
        """Test validate_api_key tool success"""
        from server import validate_api_key
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_monitors.return_value = []
        
        with patch('server.MonitorsApi', return_value=mock_api_instance):
            result = await validate_api_key(mock_context)
        
        assert result["valid"] is True
        assert result["test_successful"] is True
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_error(self, mock_context, mock_app_context):
        """Test validate_api_key tool error"""
        from server import validate_api_key
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        with patch('server.MonitorsApi', side_effect=Exception("Auth failed")):
            result = await validate_api_key(mock_context)
        
        assert result["valid"] is False
        assert "Auth failed" in result["error"]
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_cache_success(self, mock_context):
        """Test cleanup_cache tool success"""
        from server import cleanup_cache
        
        with patch('server.DATA_DIR') as mock_dir:
            mock_file1 = MagicMock()
            mock_file1.stat.return_value.st_mtime = 1000  # Old file
            mock_file2 = MagicMock()
            mock_file2.stat.return_value.st_mtime = 9999999999  # New file
            
            mock_dir.glob.return_value = [mock_file1, mock_file2]
            
            with patch('server.datetime') as mock_dt:
                mock_dt.now.return_value.timestamp.return_value = 100000
                
                result = await cleanup_cache(mock_context, 24)
        
        assert result["deleted_count"] == 1
        mock_file1.unlink.assert_called_once()
        mock_file2.unlink.assert_not_called()
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_data_success(self, mock_context):
        """Test analyze_data tool success"""
        from server import analyze_data
        
        test_data = {"series": [{"pointlist": [[1, 10]]}]}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open', mock_open(read_data=json.dumps(test_data))):
                result = await analyze_data("/test/path.json", mock_context, "summary")
        
        assert result["analysis_type"] == "summary"
        assert result["filepath"] == "/test/path.json"
        assert "result" in result
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_data_file_not_found(self, mock_context):
        """Test analyze_data with missing file"""
        from server import analyze_data
        
        with patch('pathlib.Path.exists', return_value=False):
            result = await analyze_data("/missing/file.json", mock_context)
        
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_data_unknown_type(self, mock_context):
        """Test analyze_data with unknown analysis type"""
        from server import analyze_data
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open', mock_open(read_data='{"test": "data"}')):
                result = await analyze_data("/test/path.json", mock_context, "unknown")
        
        assert "error" in result
        assert "Unknown analysis type" in result["error"]


class TestLifespanManagement:
    """Test lifespan management"""
    
    @pytest.mark.asyncio
    async def test_app_lifespan(self):
        """Test app lifespan context manager"""
        from server import app_lifespan
        
        mock_server = MagicMock()
        
        with patch('server._load_config') as mock_load:
            with patch('server._setup_api_client') as mock_setup:
                mock_config = MagicMock()
                mock_client = MagicMock()
                mock_load.return_value = mock_config
                mock_setup.return_value = mock_client
                
                async with app_lifespan(mock_server) as ctx:
                    assert ctx.config == mock_config
                    assert ctx.api_client == mock_client
                
                mock_load.assert_called_once()
                mock_setup.assert_called_once_with(mock_config)


class TestIntegration:
    """Integration tests"""
    
    def test_mcp_server_creation(self):
        """Test MCP server is created correctly"""
        from server import mcp
        from mcp.server.fastmcp import FastMCP
        
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "datadog-mcp"
        assert mcp.version == "1.0.0"
    
    def test_main_function(self):
        """Test main function"""
        from server import main
        
        with patch('server.mcp') as mock_mcp:
            main()
            mock_mcp.run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=server", "--cov-report=term-missing", "--cov-report=html"])
