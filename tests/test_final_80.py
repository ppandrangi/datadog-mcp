#!/usr/bin/env python3
"""
Final test to reach 80%
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server
import json
import os

class TestFinal80Coverage:
    """Final comprehensive tests"""
    
    @pytest.mark.asyncio
    async def test_get_metrics_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MetricsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "series": [
                    {"pointlist": [[1, 10], [2, 20]]},
                    {"pointlist": [[1, 30]]}
                ]
            }
            mock_api.return_value.query_metrics.return_value = mock_response
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_metrics("test.metric", 1000, 2000, mock_ctx)
                assert "series_count" in result
                assert result["series_count"] == 2

    @pytest.mark.asyncio
    async def test_get_monitors_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_monitor1 = MagicMock()
            mock_monitor1.to_dict.return_value = {"overall_state": "OK"}
            mock_monitor2 = MagicMock()
            mock_monitor2.to_dict.return_value = {"overall_state": "Alert"}
            
            mock_api.return_value.list_monitors.return_value = [mock_monitor1, mock_monitor2]
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_monitors(mock_ctx)
                assert "total_monitors" in result
                assert result["total_monitors"] == 2

    @pytest.mark.asyncio
    async def test_get_monitor_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "id": 123,
                "name": "Test Monitor",
                "overall_state": "OK"
            }
            mock_api.return_value.get_monitor.return_value = mock_response
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_monitor("123", mock_ctx)
                assert "monitor_id" in result
                assert result["monitor_id"] == 123

    @pytest.mark.asyncio
    async def test_create_monitor_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "id": 456,
                "name": "New Monitor"
            }
            mock_api.return_value.create_monitor.return_value = mock_response
            with patch('server._store_data', return_value="/test.json"):
                result = await server.create_monitor("New Monitor", "metric alert", "query", "message", mock_ctx)
                assert "monitor_id" in result
                assert result["monitor_id"] == 456

    @pytest.mark.asyncio
    async def test_get_dashboards_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DashboardsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {
                "dashboards": [
                    {"id": "abc", "title": "Dashboard 1"},
                    {"id": "def", "title": "Dashboard 2"}
                ]
            }
            mock_api.return_value.list_dashboards.return_value = mock_response
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_dashboards(mock_ctx)
                assert "total_dashboards" in result
                assert result["total_dashboards"] == 2

    def test_load_config_with_env_vars(self):
        with patch.dict(os.environ, {
            'DATADOG_API_KEY': 'test_key',
            'DATADOG_APP_KEY': 'test_app',
            'DATADOG_SITE': 'datadoghq.eu'
        }):
            config = server._load_config()
            assert config.api_key == 'test_key'
            assert config.app_key == 'test_app'
            assert config.site == 'datadoghq.eu'

    def test_load_config_missing_api_key(self):
        with patch.dict(os.environ, {'DATADOG_APP_KEY': 'test_app'}, clear=True):
            with pytest.raises(ValueError, match="DATADOG_API_KEY"):
                server._load_config()

    def test_load_config_missing_app_key(self):
        with patch.dict(os.environ, {'DATADOG_API_KEY': 'test_key'}, clear=True):
            with pytest.raises(ValueError, match="DATADOG_APP_KEY"):
                server._load_config()

    def test_setup_api_client_configuration(self):
        config = server.DatadogConfig(api_key='test', app_key='app', site='datadoghq.com')
        
        with patch('server.AsyncApiClient') as mock_client:
            with patch('server.Configuration') as mock_config:
                mock_config_instance = MagicMock()
                mock_config.return_value = mock_config_instance
                
                client = server._setup_api_client(config)
                
                # Verify configuration was set up correctly
                assert mock_config_instance.api_key['apiKeyAuth'] == 'test'
                assert mock_config_instance.api_key['appKeyAuth'] == 'app'
                assert mock_config_instance.server_variables['site'] == 'datadoghq.com'
                assert mock_config_instance.enable_retry == True
                assert mock_config_instance.max_retries == 3
