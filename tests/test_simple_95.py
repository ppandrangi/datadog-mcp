#!/usr/bin/env python3
"""
Simple tests to reach 95% coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server
import json
import os
import tempfile
from pathlib import Path

class TestSimple95:
    """Simple tests for 95% coverage"""
    
    def test_datadog_config_all_params(self):
        config = server.DatadogConfig(
            api_key="test_key",
            app_key="test_app", 
            site="datadoghq.eu"
        )
        assert config.api_key == "test_key"
        assert config.app_key == "test_app"
        assert config.site == "datadoghq.eu"

    def test_app_context_creation(self):
        config = server.DatadogConfig(api_key="test", app_key="app")
        mock_client = MagicMock()
        
        app_ctx = server.AppContext(api_client=mock_client, config=config)
        assert app_ctx.api_client == mock_client
        assert app_ctx.config == config

    def test_load_config_with_all_env_vars(self):
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'env_key',
            'DATADOG_APP_KEY': 'env_app',
            'DATADOG_SITE': 'datadoghq.eu'
        }):
            config = server._load_config()
            assert config.api_key == 'env_key'
            assert config.app_key == 'env_app'
            assert config.site == 'datadoghq.eu'

    def test_load_config_default_site(self):
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'key',
            'DATADOG_APP_KEY': 'app'
        }, clear=True):
            config = server._load_config()
            assert config.site == 'datadoghq.com'

    def test_setup_api_client_config(self):
        config = server.DatadogConfig(api_key='test', app_key='app', site='datadoghq.eu')
        
        with patch('server.Configuration') as mock_config_class:
            with patch('server.AsyncApiClient') as mock_client_class:
                mock_config = MagicMock()
                mock_config_class.return_value = mock_config
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result = server._setup_api_client(config)
                
                # Verify configuration setup
                assert mock_config.enable_retry == True
                assert mock_config.max_retries == 3
                assert result == mock_client

    @pytest.mark.asyncio
    async def test_store_data_simple(self):
        test_data = {"simple": "data"}
        
        with patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
            mock_open.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await server._store_data(test_data, "simple")
            assert "simple_" in result
            assert result.endswith(".json")

    def test_generate_summary_monitors_detailed(self):
        monitors_data = [
            {"overall_state": "OK", "name": "Monitor 1"},
            {"overall_state": "Alert", "name": "Monitor 2"},
            {"overall_state": "Alert", "name": "Monitor 3"},
            {"overall_state": "No Data", "name": "Monitor 4"},
            {"overall_state": "Warn", "name": "Monitor 5"}
        ]
        
        result = server._generate_summary(monitors_data)
        assert result["data_type"] == "monitors"
        assert result["record_count"] == 5
        assert result["alerting_monitors"] == 2
        assert "2 monitors currently alerting" in result["key_insights"]

    def test_generate_summary_events_detailed(self):
        events_data = {
            "events": [
                {"id": 1, "title": "Event 1"},
                {"id": 2, "title": "Event 2"},
                {"id": 3, "title": "Event 3"}
            ]
        }
        
        result = server._generate_summary(events_data)
        assert result["data_type"] == "events"
        assert result["record_count"] == 3

    def test_generate_summary_series_small(self):
        series_data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20]]},
                {"pointlist": [[1, 30]]}
            ]
        }
        
        result = server._generate_summary(series_data)
        assert result["data_type"] == "metrics"
        assert result["series_count"] == 2
        assert result["total_data_points"] == 3

    def test_generate_summary_series_large(self):
        # Create large dataset > 1000 points
        large_pointlist = [[i, i*10] for i in range(1200)]
        series_data = {"series": [{"pointlist": large_pointlist}]}
        
        result = server._generate_summary(series_data)
        assert result["data_type"] == "metrics"
        assert "Large dataset" in result["key_insights"][0]

    def test_generate_summary_unknown_data(self):
        unknown_data = {"unknown_field": "value", "another": [1, 2, 3]}
        
        result = server._generate_summary(unknown_data)
        assert result["data_type"] == "unknown"
        assert result["record_count"] == 0

    def test_calculate_stats_comprehensive(self):
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20], [3, None]]},  # None value
                {"pointlist": [[1, 5], [2, 15], [3, 25]]},
                {"pointlist": [[1, None], [2, 30]]}  # None at start
            ]
        }
        
        result = server._calculate_stats(data)
        assert result["min_value"] == 5
        assert result["max_value"] == 30
        assert result["total_points"] == 5  # Excluding None values
        assert "calculated_at" in result

    def test_calculate_stats_no_series(self):
        data = {"no_series": True}
        
        result = server._calculate_stats(data)
        assert len(result) == 1  # Only timestamp
        assert "calculated_at" in result

    def test_calculate_stats_empty_series(self):
        data = {"series": []}
        
        result = server._calculate_stats(data)
        assert len(result) == 1  # Only timestamp
        assert "calculated_at" in result

    def test_analyze_trends_increasing(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 100.0
        assert result["first_value"] == 10
        assert result["last_value"] == 20

    def test_analyze_trends_decreasing(self):
        data = {"series": [{"pointlist": [[1, 50], [2, 25]]}]}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"
        assert result["change_percentage"] == -50.0

    def test_analyze_trends_stable_small_change(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 103]]}]}  # 3% change
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_analyze_trends_stable_zero_start(self):
        data = {"series": [{"pointlist": [[1, 0], [2, 10]]}]}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"  # Can't calculate % from 0

    def test_analyze_trends_no_series(self):
        data = {"no_series": True}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_analyze_trends_empty_pointlist(self):
        data = {"series": [{"pointlist": []}]}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_analyze_trends_single_point(self):
        data = {"series": [{"pointlist": [[1, 10]]}]}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_analyze_trends_with_none_values(self):
        data = {"series": [{"pointlist": [[1, None], [2, 10], [3, None]]}]}
        
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"  # Only one valid value

    def test_analyze_trends_multiple_series(self):
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20]]},  # 100% increase
                {"pointlist": [[1, 50], [2, 25]]}   # 50% decrease
            ]
        }
        
        result = server._analyze_trends(data)
        # Should use first series for trend calculation
        assert result["trend_direction"] == "increasing"

    @pytest.mark.asyncio
    async def test_analyze_data_file_operations(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Test file not found
        with patch('pathlib.Path.exists', return_value=False):
            result = await server.analyze_data("/nonexistent.json", mock_ctx)
            assert "error" in result
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_data_json_error(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value='invalid json')
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                mock_open.return_value.__aexit__ = AsyncMock(return_value=None)
                
                result = await server.analyze_data("/test.json", mock_ctx)
                assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_data_unknown_type(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {"test": "data"}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=json.dumps(test_data))
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                mock_open.return_value.__aexit__ = AsyncMock(return_value=None)
                
                result = await server.analyze_data("/test.json", mock_ctx, "unknown_type")
                assert "error" in result
                assert "Unknown analysis type" in result["error"]

    @pytest.mark.asyncio
    async def test_cleanup_cache_with_old_files(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Create mock old file
        mock_old_file = MagicMock()
        mock_old_file.stat.return_value.st_mtime = 0  # Very old timestamp
        mock_old_file.unlink = MagicMock()
        
        # Create mock new file
        mock_new_file = MagicMock()
        mock_new_file.stat.return_value.st_mtime = 999999999999  # Very new timestamp
        
        with patch('server.DATA_DIR') as mock_dir:
            mock_dir.glob.return_value = [mock_old_file, mock_new_file]
            
            result = await server.cleanup_cache(mock_ctx, 24)
            assert result["deleted_count"] == 1
            assert result["total_files"] == 2
            mock_old_file.unlink.assert_called_once()

    def test_main_function_execution(self):
        with patch.object(server.mcp, 'run') as mock_run:
            server.main()
            mock_run.assert_called_once()
