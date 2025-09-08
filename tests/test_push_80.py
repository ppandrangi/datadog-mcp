#!/usr/bin/env python3
"""
Push to 80% coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import server
import json

class TestPush80:
    """Tests to push coverage to 80%"""
    
    @pytest.mark.asyncio
    async def test_analyze_data_summary_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {
            "series": [{"pointlist": [[1, 10], [2, 20]]}],
            "events": [{"id": 1}]
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=json.dumps(test_data))
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "summary")
                assert "analysis_type" in result
                assert result["analysis_type"] == "summary"

    @pytest.mark.asyncio
    async def test_analyze_data_stats_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {"series": [{"pointlist": [[1, 10], [2, 20], [3, 30]]}]}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=json.dumps(test_data))
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "stats")
                assert "analysis_type" in result
                assert result["analysis_type"] == "stats"

    @pytest.mark.asyncio
    async def test_analyze_data_trends_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {"series": [{"pointlist": [[1, 10], [2, 20], [3, 30]]}]}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=json.dumps(test_data))
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "trends")
                assert "analysis_type" in result
                assert result["analysis_type"] == "trends"

    @pytest.mark.asyncio
    async def test_analyze_data_anomalies_success(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        
        test_data = {"series": [{"pointlist": [[1, 10], [2, 100], [3, 15]]}]}  # Anomaly at point 2
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('aiofiles.open') as mock_open:
                mock_file = AsyncMock()
                mock_file.read = AsyncMock(return_value=json.dumps(test_data))
                mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
                
                result = await server.analyze_data("/test.json", mock_ctx, "anomalies")
                assert "analysis_type" in result
                assert result["analysis_type"] == "anomalies"

    def test_generate_summary_with_large_dataset(self):
        # Create a dataset with > 1000 points
        large_pointlist = [[i, i*10] for i in range(1500)]
        data = {"series": [{"pointlist": large_pointlist}]}
        
        result = server._generate_summary(data)
        assert "Large dataset" in result["key_insights"][0]

    def test_calculate_stats_edge_cases(self):
        # Test with mixed valid and None values
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, None], [3, 30]]},
                {"pointlist": [[1, None], [2, 20]]}
            ]
        }
        result = server._calculate_stats(data)
        assert result["min_value"] == 10
        assert result["max_value"] == 30
        assert result["total_points"] == 3  # Only valid points

    def test_analyze_trends_edge_cases(self):
        # Test with all None values
        data = {"series": [{"pointlist": [[1, None], [2, None]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
        
        # Test with zero division
        data = {"series": [{"pointlist": [[1, 0], [2, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"  # Can't calculate % from 0

    @pytest.mark.asyncio
    async def test_store_data_with_datetime(self):
        from datetime import datetime, timezone
        
        test_data = {
            "timestamp": datetime.now(timezone.utc),
            "value": 42
        }
        
        with patch('aiofiles.open') as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
            
            result = await server._store_data(test_data, "test")
            assert result.endswith(".json")
            mock_file.write.assert_called_once()

    def test_config_validation(self):
        # Test valid config
        config = server.DatadogConfig(api_key="test", app_key="app")
        assert config.api_key == "test"
        
        # Test with custom site
        config = server.DatadogConfig(api_key="test", app_key="app", site="datadoghq.eu")
        assert config.site == "datadoghq.eu"
