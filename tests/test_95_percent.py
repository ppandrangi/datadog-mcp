#!/usr/bin/env python3
"""
Targeted tests to reach 95% coverage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import server
import json
import os
from pathlib import Path

class Test95Percent:
    """Tests targeting specific uncovered lines"""
    
    @pytest.mark.asyncio
    async def test_search_metrics_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MetricsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"metrics": ["test.metric1", "test.metric2"]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_metrics = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.search_metrics("test", mock_ctx)
                assert "metric_count" in result
                assert result["metric_count"] == 2

    @pytest.mark.asyncio
    async def test_get_metric_metadata_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MetricsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"description": "test metric", "unit": "count", "type": "gauge"}
            mock_api_instance = MagicMock()
            mock_api_instance.get_metric_metadata = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_metric_metadata("test.metric", mock_ctx)
                assert "metric_name" in result
                assert result["metric_name"] == "test.metric"

    @pytest.mark.asyncio
    async def test_get_metrics_with_await(self):
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
            mock_api_instance = MagicMock()
            mock_api_instance.query_metrics = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_metrics("test.metric", 1000, 2000, mock_ctx)
                assert "series_count" in result
                assert result["series_count"] == 2

    @pytest.mark.asyncio
    async def test_get_monitors_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_monitor1 = MagicMock()
            mock_monitor1.to_dict.return_value = {"overall_state": "OK"}
            mock_monitor2 = MagicMock()
            mock_monitor2.to_dict.return_value = {"overall_state": "Alert"}
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_monitors = AsyncMock(return_value=[mock_monitor1, mock_monitor2])
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_monitors(mock_ctx)
                assert "total_monitors" in result
                assert result["total_monitors"] == 2

    @pytest.mark.asyncio
    async def test_get_monitor_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": 123, "name": "Test Monitor", "overall_state": "OK"}
            mock_api_instance = MagicMock()
            mock_api_instance.get_monitor = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_monitor("123", mock_ctx)
                assert "monitor_id" in result
                assert result["monitor_id"] == 123

    @pytest.mark.asyncio
    async def test_create_monitor_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.MonitorsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": 456, "name": "New Monitor"}
            mock_api_instance = MagicMock()
            mock_api_instance.create_monitor = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.create_monitor("New Monitor", "metric alert", "query", "message", mock_ctx)
                assert "monitor_id" in result
                assert result["monitor_id"] == 456

    @pytest.mark.asyncio
    async def test_get_dashboards_with_await(self):
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
            mock_api_instance = MagicMock()
            mock_api_instance.list_dashboards = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_dashboards(mock_ctx)
                assert "total_dashboards" in result
                assert result["total_dashboards"] == 2

    @pytest.mark.asyncio
    async def test_get_dashboard_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.DashboardsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"id": "abc", "title": "Test Dashboard", "widgets": []}
            mock_api_instance = MagicMock()
            mock_api_instance.get_dashboard = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_dashboard("abc", mock_ctx)
                assert "dashboard_id" in result
                assert result["dashboard_id"] == "abc"

    @pytest.mark.asyncio
    async def test_search_logs_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.LogsApiV2') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": [{"id": "log1"}, {"id": "log2"}]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_logs = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.search_logs("ERROR", "2024-01-01", "2024-01-02", mock_ctx)
                assert "log_count" in result
                assert result["log_count"] == 2

    @pytest.mark.asyncio
    async def test_get_events_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.EventsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"events": [{"id": "event1"}]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_events = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_events(1000, 2000, mock_ctx)
                assert "event_count" in result
                assert result["event_count"] == 1

    @pytest.mark.asyncio
    async def test_get_infrastructure_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.HostsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"host_list": [{"up": True}, {"up": False}]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_hosts = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_infrastructure(mock_ctx)
                assert "total_hosts" in result
                assert result["total_hosts"] == 2

    @pytest.mark.asyncio
    async def test_get_synthetics_tests_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.SyntheticsApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"tests": [{"type": "api"}, {"type": "browser"}]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_tests = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_synthetics_tests(mock_ctx)
                assert "test_count" in result
                assert result["test_count"] == 2

    @pytest.mark.asyncio
    async def test_get_rum_applications_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.RUMApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": [{"id": "app1"}]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_rum_applications = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_rum_applications(mock_ctx)
                assert "application_count" in result
                assert result["application_count"] == 1

    @pytest.mark.asyncio
    async def test_get_security_rules_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.SecurityMonitoringApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"data": [{"attributes": {"isEnabled": True}}]}
            mock_api_instance = MagicMock()
            mock_api_instance.list_security_monitoring_rules = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_security_rules(mock_ctx)
                assert "total_rules" in result
                assert result["total_rules"] == 1

    @pytest.mark.asyncio
    async def test_get_service_map_with_await(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.ServiceMapApi') as mock_api:
            mock_response = MagicMock()
            mock_response.to_dict.return_value = {"services": [{"name": "service1"}]}
            mock_api_instance = MagicMock()
            mock_api_instance.get_service_map = AsyncMock(return_value=mock_response)
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_service_map(mock_ctx)
                assert "service_count" in result
                assert result["service_count"] == 1

    @pytest.mark.asyncio
    async def test_get_incidents_with_pagination(self):
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()
        mock_ctx.request_context.lifespan_context.api_client = MagicMock()
        
        with patch('server.IncidentsApi') as mock_api:
            mock_incident = MagicMock()
            mock_incident.to_dict.return_value = {"attributes": {"state": "active"}}
            
            async def mock_pagination(**kwargs):
                yield mock_incident
                yield mock_incident
            
            mock_api_instance = MagicMock()
            mock_api_instance.list_incidents_with_pagination = mock_pagination
            mock_api.return_value = mock_api_instance
            
            with patch('server._store_data', return_value="/test.json"):
                result = await server.get_incidents(mock_ctx, page_size=10)
                assert "total_incidents" in result
                assert result["total_incidents"] == 2

    @pytest.mark.asyncio
    async def test_store_data_with_complex_serialization(self):
        from datetime import datetime, timezone
        
        test_data = {
            "timestamp": datetime.now(timezone.utc),
            "nested": {"key": "value"},
            "list": [1, 2, 3]
        }
        
        with patch('aiofiles.open', mock_open()) as mock_file:
            mock_file.return_value.__aenter__ = AsyncMock()
            mock_file.return_value.__aexit__ = AsyncMock()
            mock_file.return_value.write = AsyncMock()
            
            result = await server._store_data(test_data, "complex")
            assert "complex_" in result
            assert result.endswith(".json")

    def test_generate_summary_comprehensive(self):
        # Test all branches of _generate_summary
        
        # Test monitors data
        monitors_data = [
            {"overall_state": "OK"},
            {"overall_state": "Alert"},
            {"overall_state": "No Data"}
        ]
        result = server._generate_summary(monitors_data)
        assert result["data_type"] == "monitors"
        assert result["alerting_monitors"] == 1
        
        # Test events data
        events_data = {"events": [{"id": 1}, {"id": 2}]}
        result = server._generate_summary(events_data)
        assert result["data_type"] == "events"
        assert result["record_count"] == 2
        
        # Test series data with large dataset
        large_series = {"series": [{"pointlist": [[i, i] for i in range(1500)]}]}
        result = server._generate_summary(large_series)
        assert "Large dataset" in result["key_insights"][0]

    def test_calculate_stats_comprehensive(self):
        # Test all branches of _calculate_stats
        
        # Test with mixed data types
        data = {
            "series": [
                {"pointlist": [[1, 10], [2, None], [3, 30]]},
                {"pointlist": [[1, 5], [2, 15]]}
            ]
        }
        result = server._calculate_stats(data)
        assert result["min_value"] == 5
        assert result["max_value"] == 30
        assert result["total_points"] == 4
        
        # Test with no series
        data = {"no_series": True}
        result = server._calculate_stats(data)
        assert len(result) == 1  # Only timestamp

    def test_analyze_trends_comprehensive(self):
        # Test all branches of _analyze_trends
        
        # Test increasing trend
        data = {"series": [{"pointlist": [[1, 10], [2, 20]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "increasing"
        assert result["change_percentage"] == 100.0
        
        # Test decreasing trend
        data = {"series": [{"pointlist": [[1, 20], [2, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "decreasing"
        assert result["change_percentage"] == -50.0
        
        # Test stable trend (small change)
        data = {"series": [{"pointlist": [[1, 100], [2, 102]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
        
        # Test with zero first value
        data = {"series": [{"pointlist": [[1, 0], [2, 10]]}]}
        result = server._analyze_trends(data)
        assert result["trend_direction"] == "stable"
