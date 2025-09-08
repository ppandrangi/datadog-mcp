#!/usr/bin/env python3
"""
Final coverage push
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server
import json
import os

class TestFinalCoveragePush:
    """Final tests to maximize coverage"""
    
    @pytest.mark.asyncio
    async def test_analyze_data_all_types(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=json.dumps(test_data))
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                mock_open.return_value.__aexit__ = AsyncMock(return_value=None)
                
                # Test summary
                result = await server.analyze_data("/test.json", mock_ctx, "summary")
                assert "analysis_type" in result
                
                # Test stats
                result = await server.analyze_data("/test.json", mock_ctx, "stats")
                assert "analysis_type" in result
                
                # Test trends
                result = await server.analyze_data("/test.json", mock_ctx, "trends")
                assert "analysis_type" in result

    def test_all_generate_summary_branches(self):
        # Test monitors with no alerts
        monitors_data = [{"overall_state": "OK"}, {"overall_state": "OK"}]
        result = server._generate_summary(monitors_data)
        assert result["alerting_monitors"] == 0
        
        # Test events with empty list
        events_data = {"events": []}
        result = server._generate_summary(events_data)
        assert result["record_count"] == 0
        
        # Test series with empty pointlist
        series_data = {"series": [{"pointlist": []}]}
        result = server._generate_summary(series_data)
        assert result["total_data_points"] == 0

    def test_all_calculate_stats_branches(self):
        # Test with all None values
        data = {"series": [{"pointlist": [[1, None], [2, None]]}]}
        result = server._calculate_stats(data)
        assert "calculated_at" in result
        
        # Test with single value
        data = {"series": [{"pointlist": [[1, 42]]}]}
        result = server._calculate_stats(data)
        assert result["min_value"] == 42
        assert result["max_value"] == 42

    def test_all_analyze_trends_branches(self):
        # Test with exactly 10% change (boundary)
        data = {"series": [{"pointlist": [[1, 100], [2, 110]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"
        
        # Test with exactly -10% change (boundary)
        data = {"series": [{"pointlist": [[1, 100], [2, 90]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"

    @pytest.mark.asyncio
    async def test_all_error_paths(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Test all API error paths that we can easily trigger
        apis_and_funcs = [
            ('server.DowntimesApi', server.get_downtimes, []),
            ('server.TagsApi', server.get_tags, []),
            ('server.TeamsApi', server.get_teams, []),
            ('server.UsersApi', server.get_users, []),
        ]
        
        for api_patch, func, args in apis_and_funcs:
            with patch(api_patch) as mock_api:
                mock_api.side_effect = Exception("API Error")
                result = await func(mock_ctx, *args)
                assert "error" in result

    def test_edge_case_data_structures(self):
        # Test _generate_summary with various data structures
        
        # Test with nested structure
        nested_data = {"data": {"nested": {"events": [{"id": 1}]}}}
        result = server._generate_summary(nested_data)
        assert result["data_type"] == "unknown"
        
        # Test with list at root
        list_data = [{"item": 1}, {"item": 2}]
        result = server._generate_summary(list_data)
        assert result["data_type"] == "monitors"  # Assumes list is monitors

    def test_config_edge_cases(self):
        # Test config with minimal params
        config = server.DatadogConfig(api_key="k", app_key="a")
        assert config.site == "datadoghq.com"
        
        # Test config with all params
        config = server.DatadogConfig(api_key="key", app_key="app", site="custom.site")
        assert config.site == "custom.site"

    @pytest.mark.asyncio
    async def test_store_data_edge_cases(self):
        # Test with empty data
        with patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
            mock_open.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await server._store_data({}, "empty")
            assert "empty_" in result
            
            # Test with complex nested data
            complex_data = {
                "level1": {
                    "level2": {
                        "level3": ["item1", "item2"]
                    }
                }
            }
            result = await server._store_data(complex_data, "complex")
            assert "complex_" in result

    def test_main_function_coverage(self):
        # Ensure main function is covered
        with patch.object(server.mcp, 'run') as mock_run:
            server.main()
            mock_run.assert_called_once()

    def test_app_context_properties(self):
        # Test AppContext with different configurations
        config1 = server.DatadogConfig(api_key="test1", app_key="app1")
        config2 = server.DatadogConfig(api_key="test2", app_key="app2", site="eu")
        
        client1 = MagicMock()
        client2 = MagicMock()
        
        ctx1 = server.AppContext(api_client=client1, config=config1)
        ctx2 = server.AppContext(api_client=client2, config=config2)
        
        assert ctx1.config.api_key == "test1"
        assert ctx2.config.site == "eu"
        assert ctx1.api_client != ctx2.api_client

    def test_load_config_error_cases(self):
        # Test missing API key
        with patch.dict(os.environ, {'DATADOG_APP_KEY': 'app'}, clear=True):
            with pytest.raises(ValueError, match="DATADOG_API_KEY"):
                server._load_config()
        
        # Test missing APP key
        with patch.dict(os.environ, {'DATADOG_API_KEY': 'key'}, clear=True):
            with pytest.raises(ValueError, match="DATADOG_APP_KEY"):
                server._load_config()

    def test_setup_api_client_comprehensive(self):
        config = server.DatadogConfig(api_key='test', app_key='app', site='datadoghq.com')
        
        with patch('server.Configuration') as mock_config_class:
            with patch('server.AsyncApiClient') as mock_client_class:
                mock_config = MagicMock()
                mock_config_class.return_value = mock_config
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                
                # Test that all configuration is set
                result = server._setup_api_client(config)
                
                # Verify all the configuration calls were made
                assert mock_config.enable_retry == True
                assert mock_config.max_retries == 3
                mock_client_class.assert_called_once_with(mock_config)
                assert result == mock_client
