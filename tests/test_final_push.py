#!/usr/bin/env python3
"""
Final push to 80% coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server

class TestFinalPush:
    """Final tests to reach 80%"""
    
    @pytest.mark.asyncio
    async def test_get_service_map_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        # Test when ServiceMapApi is available
        with patch('server.ServiceMapApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"services": []}
            mock_api.return_value.get_service_map = AsyncMock(return_value=mock_response)
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_service_map(mock_ctx)
                assert "service_count" in result

    @pytest.mark.asyncio
    async def test_get_service_map_no_api(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Test when ServiceMapApi is None
        with patch('server.ServiceMapApi', None):
            result = await server.get_service_map(mock_ctx)
            assert "error" in result

    def test_datadog_config_defaults(self):
        config = server.DatadogConfig(api_key="test", app_key="app")
        assert config.site == "datadoghq.com"

    def test_datadog_config_custom_site(self):
        config = server.DatadogConfig(api_key="test", app_key="app", site="datadoghq.eu")
        assert config.site == "datadoghq.eu"

    def test_generate_summary_unknown_type(self):
        data = {"unknown": "data"}
        result = server._generate_summary(data)
        assert result["data_type"] == "unknown"
        assert result["record_count"] == 0

    def test_calculate_stats_no_series(self):
        data = {"no_series": "data"}
        result = server._calculate_stats(data)
        assert "calculated_at" in result
        assert len(result) == 1  # Only timestamp

    def test_analyze_trends_no_series(self):
        data = {"no_series": "data"}
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

    def test_analyze_trends_zero_first_value(self):
        data = {"series": [{"pointlist": [[1, 0], [2, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"  # Can't calculate percentage from 0

    @pytest.mark.asyncio
    async def test_analyze_data_file_not_exists(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('pathlib.Path.exists', return_value=False):
            result = await server.analyze_data("/nonexistent.json", mock_ctx)
            assert "error" in result
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_data_unknown_type(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value='{"test": "data"}')
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "unknown_type")
                assert "error" in result
                assert "Unknown analysis type" in result["error"]
