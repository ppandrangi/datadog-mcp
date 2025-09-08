#!/usr/bin/env python3
"""
Minimal tests to boost coverage to 80%
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server

class TestNewAPIs:
    """Test new API endpoints for coverage"""
    
    @pytest.mark.asyncio
    async def test_get_downtimes(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DowntimesApi') as mock_api:
            mock_api.return_value.list_downtimes = AsyncMock(return_value=[])
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_downtimes(mock_ctx)
                assert "total_downtimes" in result

    @pytest.mark.asyncio
    async def test_create_downtime(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DowntimesApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": 123}
            mock_api.return_value.create_downtime = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.create_downtime(["host:test"], ctx=mock_ctx)
                assert "downtime_id" in result

    @pytest.mark.asyncio
    async def test_get_tags(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.TagsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"tags": {}}
            mock_api.return_value.list_host_tags = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_tags(mock_ctx)
                assert "host_count" in result

    @pytest.mark.asyncio
    async def test_get_teams(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.TeamsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": []}
            mock_api.return_value.list_teams = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_teams(mock_ctx)
                assert "total_teams" in result

    @pytest.mark.asyncio
    async def test_get_users(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.UsersApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"users": []}
            mock_api.return_value.list_users = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_users(mock_ctx)
                assert "total_users" in result

    @pytest.mark.asyncio
    async def test_create_dashboard(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DashboardsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": "abc", "title": "test"}
            mock_api.return_value.create_dashboard = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.create_dashboard("test", "ordered", [], mock_ctx)
                assert "dashboard_id" in result

    @pytest.mark.asyncio
    async def test_update_dashboard(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DashboardsApi') as mock_api:
            mock_existing = MagicMock()
            mock_existing.to_dict.return_value = {"title": "old", "widgets": []}
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": "abc", "title": "new"}
            mock_api.return_value.get_dashboard = AsyncMock(return_value=mock_existing)
            mock_api.return_value.update_dashboard = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.update_dashboard("abc", title="new", ctx=mock_ctx)
                assert "dashboard_id" in result

    @pytest.mark.asyncio
    async def test_delete_dashboard(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DashboardsApi') as mock_api:
            mock_api.return_value.delete_dashboard = AsyncMock()
            result = await server.delete_dashboard("abc", mock_ctx)
            assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_update_monitor(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_existing = MagicMock()
            mock_existing.to_dict.return_value = {"name": "old", "query": "old"}
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": 123, "name": "new"}
            mock_api.return_value.get_monitor = AsyncMock(return_value=mock_existing)
            mock_api.return_value.update_monitor = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.update_monitor("123", name="new", ctx=mock_ctx)
                assert "monitor_id" in result

    @pytest.mark.asyncio
    async def test_delete_monitor(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_api.return_value.delete_monitor = AsyncMock()
            result = await server.delete_monitor("123", mock_ctx)
            assert result["status"] == "deleted"

class TestDataAnalysis:
    """Test data analysis functions"""
    
    @pytest.mark.asyncio
    async def test_analyze_data_stats(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value='{"series": [{"pointlist": [[1, 10], [2, 20]]}]}')
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "stats")
                assert "analysis_type" in result

    @pytest.mark.asyncio
    async def test_analyze_data_trends(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value='{"series": [{"pointlist": [[1, 10], [2, 20]]}]}')
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "trends")
                assert "analysis_type" in result

    def test_generate_summary_monitors(self):
        data = [{"overall_state": "OK"}, {"overall_state": "Alert"}]
        result = server._generate_summary(data)
        assert result["data_type"] == "monitors"
        assert result["alerting_monitors"] == 1

    def test_generate_summary_events(self):
        data = {"events": [{"id": 1}, {"id": 2}]}
        result = server._generate_summary(data)
        assert result["data_type"] == "events"

    def test_calculate_stats(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        result = server._calculate_stats(data)
        assert "min_value" in result
        assert result["min_value"] == 10

    def test_analyze_trends(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 30]]}]}
        result = server._analyze_trends(data)
        assert "trend_direction" in result
        assert result["change_percentage"] == 200.0

class TestErrorPaths:
    """Test error handling paths"""
    
    @pytest.mark.asyncio
    async def test_api_errors(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DowntimesApi') as mock_api:
            mock_api.return_value.list_downtimes = AsyncMock(side_effect=Exception("API Error"))
            result = await server.get_downtimes(mock_ctx)
            assert "error" in result

    @pytest.mark.asyncio
    async def test_analyze_data_file_not_found(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('pathlib.Path.exists', return_value=False):
            result = await server.analyze_data("/nonexistent.json", mock_ctx)
            assert "error" in result
