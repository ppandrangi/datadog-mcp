#!/usr/bin/env python3
"""
Final test to reach 80%
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server
import tempfile
from pathlib import Path

class TestFinal80:
    """Final tests to reach 80%"""
    
    @pytest.mark.asyncio
    async def test_cleanup_cache_with_files(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        # Create mock files
        mock_file1 = MagicMock()
        mock_file1.stat.return_value.st_mtime = 0  # Very old
        mock_file1.unlink = MagicMock()
        
        mock_file2 = MagicMock()
        mock_file2.stat.return_value.st_mtime = 999999999999  # Very new
        
        with patch('server.DATA_DIR') as mock_dir:
            mock_dir.glob.return_value = [mock_file1, mock_file2]
            
            result = await server.cleanup_cache(mock_ctx, 24)
            assert result["deleted_count"] == 1
            mock_file1.unlink.assert_called_once()

    def test_generate_summary_events_data(self):
        data = {"events": [{"id": 1}, {"id": 2}, {"id": 3}]}
        result = server._generate_summary(data)
        assert result["data_type"] == "events"
        assert result["record_count"] == 3

    def test_generate_summary_monitors_with_alerts(self):
        data = [
            {"overall_state": "OK"},
            {"overall_state": "Alert"},
            {"overall_state": "Alert"},
            {"overall_state": "No Data"}
        ]
        result = server._generate_summary(data)
        assert result["data_type"] == "monitors"
        assert result["alerting_monitors"] == 2
        assert "2 monitors currently alerting" in result["key_insights"]

    def test_calculate_stats_with_data(self):
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, 20]]},
                {"pointlist": [[1, 30], [2, None], [3, 40]]}  # Include None values
            ]
        }
        result = server._calculate_stats(data)
        assert result["min_value"] == 10
        assert result["max_value"] == 40
        assert result["total_points"] == 4  # None values excluded

    def test_analyze_trends_with_change(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 150]]}]}  # 50% increase
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 50.0

    def test_analyze_trends_decreasing_trend(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 50]]}]}  # 50% decrease
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"
        assert result["change_percentage"] == -50.0

    def test_analyze_trends_stable_trend(self):
        data = {"series": [{"pointlist": [[1, 100], [2, 105]]}]}  # 5% increase (stable)
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"

    def test_analyze_trends_with_none_values(self):
        data = {"series": [{"pointlist": [[1, None], [2, 10], [3, None]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"  # Only one valid value

    @pytest.mark.asyncio
    async def test_analyze_data_json_parse_error(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value='invalid json')
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "summary")
                assert "error" in result

    def test_app_context_creation(self):
        from datadog_api_client import AsyncApiClient
        config = server.DatadogConfig(api_key="test", app_key="app")
        
        # Mock the AsyncApiClient
        mock_client = MagicMock()
        
        app_ctx = server.AppContext(api_client=mock_client, config=config)
        assert app_ctx.config.api_key == "test"
        assert app_ctx.api_client == mock_client
