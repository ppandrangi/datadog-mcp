#!/usr/bin/env python3
"""
Simple tests to reach 80% coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server

class TestSimpleCoverage:
    """Simple tests for remaining coverage"""
    
    @pytest.mark.asyncio
    async def test_search_metrics_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MetricsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"metrics": ["test.metric"]}
            mock_api.return_value.list_metrics = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.search_metrics("test", mock_ctx)
                assert "metric_count" in result

    @pytest.mark.asyncio
    async def test_get_metric_metadata_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MetricsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"description": "test", "unit": "count"}
            mock_api.return_value.get_metric_metadata = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_metric_metadata("test.metric", mock_ctx)
                assert "metric_name" in result

    @pytest.mark.asyncio
    async def test_get_dashboard_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DashboardsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": "abc", "title": "test", "widgets": []}
            mock_api.return_value.get_dashboard = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_dashboard("abc", mock_ctx)
                assert "dashboard_id" in result

    @pytest.mark.asyncio
    async def test_search_logs_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.LogsApiV2') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": []}
            mock_api.return_value.list_logs = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.search_logs("ERROR", "2024-01-01", "2024-01-02", mock_ctx)
                assert "log_count" in result

    @pytest.mark.asyncio
    async def test_get_events_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.EventsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"events": []}
            mock_api.return_value.list_events = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_events(1000, 2000, mock_ctx)
                assert "event_count" in result

    @pytest.mark.asyncio
    async def test_get_infrastructure_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.HostsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"host_list": [{"up": True}]}
            mock_api.return_value.list_hosts = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_infrastructure(mock_ctx)
                assert "total_hosts" in result

    @pytest.mark.asyncio
    async def test_get_synthetics_tests_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.SyntheticsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"tests": [{"type": "api"}]}
            mock_api.return_value.list_tests = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_synthetics_tests(mock_ctx)
                assert "test_count" in result

    @pytest.mark.asyncio
    async def test_get_rum_applications_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.RUMApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": []}
            mock_api.return_value.list_rum_applications = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_rum_applications(mock_ctx)
                assert "application_count" in result

    @pytest.mark.asyncio
    async def test_get_security_rules_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.SecurityMonitoringApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": [{"attributes": {"isEnabled": True}}]}
            mock_api.return_value.list_security_monitoring_rules = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_security_rules(mock_ctx)
                assert "total_rules" in result

    @pytest.mark.asyncio
    async def test_cleanup_cache_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('server.DATA_DIR') as mock_dir:
            mock_file = MagicMock()
            mock_file.stat.return_value.st_mtime = 0  # Very old file
            mock_file.unlink = MagicMock()
            mock_dir.glob.return_value = [mock_file]
            
            result = await server.cleanup_cache(mock_ctx, 1)
            assert "deleted_count" in result
