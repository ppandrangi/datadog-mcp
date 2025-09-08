#!/usr/bin/env python3
"""
Final tests to reach 80% coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server

class TestRemainingCoverage:
    """Cover remaining functions"""
    
    @pytest.mark.asyncio
    async def test_get_incidents_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.IncidentsApi') as mock_api:
            mock_incident = MagicMock()
            mock_incident.to_dict.return_value = {"attributes": {"state": "active"}}
            
            async def mock_pagination():
                yield mock_incident
            
            mock_api.return_value.list_incidents_with_pagination = mock_pagination
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_incidents(mock_ctx)
                assert "total_incidents" in result

    @pytest.mark.asyncio
    async def test_get_slos_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.ServiceLevelObjectivesApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": []}
            mock_api.return_value.list_slos = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_slos(mock_ctx)
                assert "total_slos" in result

    @pytest.mark.asyncio
    async def test_get_notebooks_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.NotebooksApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": []}
            mock_api.return_value.list_notebooks = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_notebooks(mock_ctx)
                assert "total_notebooks" in result

    def test_load_config_success(self):
        with patch.dict('os.environ', {'DATADOG_API_KEY': 'test', 'DATADOG_APP_KEY': 'app'}):
            config = server._load_config()
            assert config.api_key == 'test'
            assert config.app_key == 'app'

    def test_load_config_missing_keys(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError):
                server._load_config()

    def test_setup_api_client(self):
        config = server.DatadogConfig(api_key='test', app_key='app')
        client = server._setup_api_client(config)
        assert client is not None

    @pytest.mark.asyncio
    async def test_store_data(self):
        test_data = {"test": "data"}
        with patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
            
            result = await server._store_data(test_data, "test")
            assert "test_" in result
            assert result.endswith(".json")

    def test_generate_summary_large_dataset(self):
        data = {"series": [{"pointlist": [[i, i*10] for i in range(2000)]}]}
        result = server._generate_summary(data)
        assert "Large dataset" in result["key_insights"]

    def test_calculate_stats_empty(self):
        data = {"series": []}
        result = server._calculate_stats(data)
        assert "calculated_at" in result

    def test_analyze_trends_stable(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_analyze_trends_increasing(self):
        data = {"series": [{"pointlist": [[1, 10], [2, 50]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"

    def test_analyze_trends_decreasing(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"

    def test_analyze_trends_no_data(self):
        data = {"series": [{"pointlist": []}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_main_function(self):
        with patch.object(server.mcp, 'run') as mock_run:
            server.main()
            mock_run.assert_called_once()

class TestErrorHandling:
    """Test more error paths"""
    
    @pytest.mark.asyncio
    async def test_all_api_error_paths(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        # Test multiple API error paths
        apis_to_test = [
            ('server.TagsApi', server.get_tags),
            ('server.TeamsApi', server.get_teams),
            ('server.UsersApi', server.get_users),
            ('server.ServiceLevelObjectivesApi', server.get_slos),
            ('server.NotebooksApi', server.get_notebooks),
        ]
        
        for api_patch, func in apis_to_test:
            with patch(api_patch) as mock_api:
                mock_api.return_value.list_teams = AsyncMock(side_effect=Exception("API Error"))
                mock_api.return_value.list_users = AsyncMock(side_effect=Exception("API Error"))
                mock_api.return_value.list_host_tags = AsyncMock(side_effect=Exception("API Error"))
                mock_api.return_value.list_slos = AsyncMock(side_effect=Exception("API Error"))
                mock_api.return_value.list_notebooks = AsyncMock(side_effect=Exception("API Error"))
                
                result = await func(mock_ctx)
                assert "error" in result
