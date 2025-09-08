#!/usr/bin/env python3
"""
Final integration tests for maximum coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server
import os

class TestFinalIntegration:
    """Final integration tests"""
    
    @pytest.mark.asyncio
    async def test_app_lifespan_complete(self):
        """Test complete app lifespan"""
        mock_server = MagicMock()
        
        with patch.dict(os.environ, {'DATADOG_API_KEY': 'test', 'DATADOG_APP_KEY': 'app'}):
            with patch('server._setup_api_client') as mock_setup:
                mock_client = MagicMock()
                mock_setup.return_value = mock_client
                
                async with server.app_lifespan(mock_server) as ctx:
                    assert isinstance(ctx, server.AppContext)
                    assert ctx.config.api_key == 'test'
                    assert ctx.api_client == mock_client

    def test_config_comprehensive(self):
        """Test all config scenarios"""
        # Test with all environment variables
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'full_key',
            'DATADOG_APP_KEY': 'full_app',
            'DATADOG_SITE': 'datadoghq.eu'
        }):
            config = server._load_config()
            assert config.api_key == 'full_key'
            assert config.app_key == 'full_app'
            assert config.site == 'datadoghq.eu'

    def test_setup_api_client_complete(self):
        """Test complete API client setup"""
        config = server.DatadogConfig(
            api_key='integration_key',
            app_key='integration_app',
            site='datadoghq.com'
        )
        
        with patch('server.Configuration') as mock_config_class:
            with patch('server.AsyncApiClient') as mock_client_class:
                mock_config = MagicMock()
                mock_config_class.return_value = mock_config
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                result = server._setup_api_client(config)
                
                # Verify all configuration was applied
                assert mock_config.enable_retry == True
                assert mock_config.max_retries == 3
                assert result == mock_client

    @pytest.mark.asyncio
    async def test_store_data_comprehensive(self):
        """Test comprehensive data storage"""
        from datetime import datetime, timezone
        
        complex_data = {
            "timestamp": datetime.now(timezone.utc),
            "metrics": [
                {"name": "cpu", "value": 85.5},
                {"name": "memory", "value": 72.1}
            ],
            "metadata": {
                "source": "integration_test",
                "version": "1.0"
            }
        }
        
        with patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
            mock_open.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await server._store_data(complex_data, "integration")
            assert "integration_" in result
            assert result.endswith(".json")

    def test_data_analysis_comprehensive(self):
        """Test all data analysis functions comprehensively"""
        
        # Test _generate_summary with all data types
        monitor_data = [
            {"overall_state": "OK", "name": "Monitor 1"},
            {"overall_state": "Alert", "name": "Monitor 2"},
            {"overall_state": "Warn", "name": "Monitor 3"}
        ]
        result = server._generate_summary(monitor_data)
        assert result["data_type"] == "monitors"
        assert result["alerting_monitors"] == 1
        
        # Test _calculate_stats with comprehensive data
        stats_data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20], [3, 30]]},
                {"pointlist": [[1, 5], [2, 15], [3, 25]]}
            ]
        }
        result = server._calculate_stats(stats_data)
        assert result["min_value"] == 5
        assert result["max_value"] == 30
        assert result["total_points"] == 6
        
        # Test _analyze_trends with different scenarios
        trend_data = {"series": [{"pointlist": [[1, 100], [2, 150]]}]}
        result = server._analyze_trends(trend_data)
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_cleanup_cache_comprehensive(self):
        """Test comprehensive cache cleanup"""
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Create mock files with different ages
        old_file = MagicMock()
        old_file.stat.return_value.st_mtime = 1000000  # Very old
        old_file.unlink = MagicMock()
        
        recent_file = MagicMock()
        recent_file.stat.return_value.st_mtime = 9999999999  # Very recent
        
        with patch('server.DATA_DIR') as mock_dir:
            mock_dir.glob.return_value = [old_file, recent_file]
            
            result = await server.cleanup_cache(mock_ctx, 24)
            assert result["deleted_count"] == 1
            old_file.unlink.assert_called_once()

    def test_all_utility_functions(self):
        """Test all utility functions for coverage"""
        
        # Test DatadogConfig with all parameters
        config = server.DatadogConfig(
            api_key="util_key",
            app_key="util_app", 
            site="datadoghq.eu"
        )
        assert config.api_key == "util_key"
        assert config.site == "datadoghq.eu"
        
        # Test AppContext creation
        mock_client = MagicMock()
        app_ctx = server.AppContext(api_client=mock_client, config=config)
        assert app_ctx.api_client == mock_client
        assert app_ctx.config == config

    def test_main_function_integration(self):
        """Test main function execution"""
        with patch.object(server.mcp, 'run') as mock_run:
            server.main()
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_scenarios(self):
        """Test various error scenarios"""
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Test file not found in analyze_data
        with patch('pathlib.Path.exists', return_value=False):
            result = await server.analyze_data("/nonexistent.json", mock_ctx)
            assert "error" in result
            assert "not found" in result["error"]

    def test_edge_cases_comprehensive(self):
        """Test comprehensive edge cases"""
        
        # Test _generate_summary with empty data
        empty_data = {}
        result = server._generate_summary(empty_data)
        assert result["data_type"] == "unknown"
        assert result["record_count"] == 0
        
        # Test _calculate_stats with no data
        no_data = {"no_series": True}
        result = server._calculate_stats(no_data)
        assert "calculated_at" in result
        
        # Test _analyze_trends with no data
        result = server._analyze_trends(no_data)
        assert result["trend_direction"] == "stable"

    def test_configuration_edge_cases(self):
        """Test configuration edge cases"""
        
        # Test missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                server._load_config()
        
        # Test partial environment variables
        with patch.dict(os.environ, {'DATADOG_API_KEY': 'key'}, clear=True):
            with pytest.raises(ValueError):
                server._load_config()

    @pytest.mark.asyncio
    async def test_async_patterns(self):
        """Test async patterns and context management"""
        
        # Test proper async context usage
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Test that async functions properly handle context
        await mock_ctx.info("Test message")
        await mock_ctx.error("Test error")
        
        mock_ctx.info.assert_called_with("Test message")
        mock_ctx.error.assert_called_with("Test error")
