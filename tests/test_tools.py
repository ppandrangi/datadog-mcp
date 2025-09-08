#!/usr/bin/env python3
"""
Additional tests for MCP tools to achieve 80% coverage
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


class TestMetricsTools:
    """Test metrics-related tools"""
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        """Create mock app context"""
        from server import AppContext, DatadogConfig
        
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_search_metrics_success(self, mock_context, mock_app_context):
        """Test search_metrics tool success"""
        from server import search_metrics
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "metrics": ["metric1", "metric2", "metric3"]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_metrics.return_value = mock_response
        
        with patch('server.MetricsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await search_metrics("cpu", mock_context)
        
        assert result["metric_count"] == 3
        assert result["sample_metrics"] == ["metric1", "metric2", "metric3"]
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_metric_metadata_success(self, mock_context, mock_app_context):
        """Test get_metric_metadata tool success"""
        from server import get_metric_metadata
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "description": "CPU usage metric",
            "unit": "percent",
            "type": "gauge"
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.get_metric_metadata.return_value = mock_response
        
        with patch('server.MetricsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_metric_metadata("system.cpu.user", mock_context)
        
        assert result["metric_name"] == "system.cpu.user"
        assert result["description"] == "CPU usage metric"
        assert result["unit"] == "percent"
        assert result["type"] == "gauge"


class TestMonitorTools:
    """Test monitor-related tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_get_monitors_success(self, mock_context, mock_app_context):
        """Test get_monitors tool success"""
        from server import get_monitors
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_monitor1 = MagicMock()
        mock_monitor1.to_dict.return_value = {"overall_state": "OK", "name": "Monitor 1"}
        mock_monitor2 = MagicMock()
        mock_monitor2.to_dict.return_value = {"overall_state": "Alert", "name": "Monitor 2"}
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_monitors.return_value = [mock_monitor1, mock_monitor2]
        
        with patch('server.MonitorsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_monitors(mock_context)
        
        assert result["total_monitors"] == 2
        assert result["alerting_count"] == 1
        assert result["monitor_states"]["OK"] == 1
        assert result["monitor_states"]["Alert"] == 1
    
    @pytest.mark.asyncio
    async def test_get_monitor_success(self, mock_context, mock_app_context):
        """Test get_monitor tool success"""
        from server import get_monitor
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "id": 123,
            "name": "Test Monitor",
            "overall_state": "OK",
            "type": "metric alert"
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.get_monitor.return_value = mock_response
        
        with patch('server.MonitorsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_monitor("123", mock_context)
        
        assert result["monitor_id"] == 123
        assert result["monitor_name"] == "Test Monitor"
        assert result["status"] == "OK"
        assert result["monitor_type"] == "metric alert"
    
    @pytest.mark.asyncio
    async def test_create_monitor_success(self, mock_context, mock_app_context):
        """Test create_monitor tool success"""
        from server import create_monitor
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "id": 456,
            "name": "New Monitor"
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.create_monitor.return_value = mock_response
        
        with patch('server.MonitorsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await create_monitor(
                    "New Monitor",
                    "metric alert",
                    "avg(last_5m):avg:system.cpu.user{*} > 0.8",
                    "CPU is high",
                    mock_context
                )
        
        assert result["monitor_id"] == 456
        assert result["monitor_name"] == "New Monitor"
        assert result["status"] == "created"
        mock_context.info.assert_called_once()


class TestDashboardTools:
    """Test dashboard-related tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_get_dashboards_success(self, mock_context, mock_app_context):
        """Test get_dashboards tool success"""
        from server import get_dashboards
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "dashboards": [
                {"title": "Dashboard 1"},
                {"title": "Dashboard 2"},
                {"title": "Dashboard 3"}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_dashboards.return_value = mock_response
        
        with patch('server.DashboardsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_dashboards(mock_context)
        
        assert result["total_dashboards"] == 3
        assert result["sample_dashboards"] == ["Dashboard 1", "Dashboard 2", "Dashboard 3"]
    
    @pytest.mark.asyncio
    async def test_get_dashboard_success(self, mock_context, mock_app_context):
        """Test get_dashboard tool success"""
        from server import get_dashboard
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "id": "abc-123",
            "title": "Test Dashboard",
            "widgets": [{"type": "timeseries"}, {"type": "query_value"}],
            "layout_type": "ordered"
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.get_dashboard.return_value = mock_response
        
        with patch('server.DashboardsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_dashboard("abc-123", mock_context)
        
        assert result["dashboard_id"] == "abc-123"
        assert result["dashboard_title"] == "Test Dashboard"
        assert result["widget_count"] == 2
        assert result["layout_type"] == "ordered"


class TestLogsAndEventsTools:
    """Test logs and events tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_search_logs_success(self, mock_context, mock_app_context):
        """Test search_logs tool success"""
        from server import search_logs
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "data": [
                {"message": "Log entry 1"},
                {"message": "Log entry 2"}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_logs.return_value = mock_response
        
        with patch('server.LogsApiV2', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await search_logs("error", "2023-01-01", "2023-01-02", mock_context, 50)
        
        assert result["log_count"] == 2
        assert result["query"] == "error"
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_success(self, mock_context, mock_app_context):
        """Test get_events tool success"""
        from server import get_events
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "events": [
                {"id": 1, "title": "Event 1"},
                {"id": 2, "title": "Event 2"}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_events.return_value = mock_response
        
        with patch('server.EventsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_events(1000, 2000, mock_context, "normal", "datadog")
        
        assert result["event_count"] == 2
        assert result["priority_filter"] == "normal"
        assert result["sources_filter"] == "datadog"
        mock_context.info.assert_called_once()


class TestInfrastructureTools:
    """Test infrastructure-related tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_get_infrastructure_success(self, mock_context, mock_app_context):
        """Test get_infrastructure tool success"""
        from server import get_infrastructure
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "host_list": [
                {"up": True, "name": "host1"},
                {"up": False, "name": "host2"},
                {"up": True, "name": "host3"}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_hosts.return_value = mock_response
        
        with patch('server.HostsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_infrastructure(mock_context)
        
        assert result["total_hosts"] == 3
        assert result["active_hosts"] == 2
        assert result["inactive_hosts"] == 1
        mock_context.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_service_map_success(self, mock_context, mock_app_context):
        """Test get_service_map tool success"""
        from server import get_service_map
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "services": [
                {"name": "service1"},
                {"name": "service2"}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.get_service_map.return_value = mock_response
        
        with patch('server.ServiceMapApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_service_map(mock_context, "production")
        
        assert result["service_count"] == 2
        assert result["environment"] == "production"


class TestSyntheticsAndRUMTools:
    """Test Synthetics and RUM tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_get_synthetics_tests_success(self, mock_context, mock_app_context):
        """Test get_synthetics_tests tool success"""
        from server import get_synthetics_tests
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "tests": [
                {"type": "api", "name": "API Test"},
                {"type": "browser", "name": "Browser Test"},
                {"type": "api", "name": "Another API Test"}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_tests.return_value = mock_response
        
        with patch('server.SyntheticsApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_synthetics_tests(mock_context)
        
        assert result["test_count"] == 3
        assert result["test_types"]["api"] == 2
        assert result["test_types"]["browser"] == 1
    
    @pytest.mark.asyncio
    async def test_get_rum_applications_success(self, mock_context, mock_app_context):
        """Test get_rum_applications tool success"""
        from server import get_rum_applications
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "data": [
                {"attributes": {"name": "Web App"}},
                {"attributes": {"name": "Mobile App"}},
                {"attributes": {}}  # Test missing name
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_rum_applications.return_value = mock_response
        
        with patch('server.RUMApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_rum_applications(mock_context)
        
        assert result["application_count"] == 3
        assert "Web App" in result["sample_applications"]
        assert "Mobile App" in result["sample_applications"]


class TestSecurityTools:
    """Test security monitoring tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_get_security_rules_success(self, mock_context, mock_app_context):
        """Test get_security_rules tool success"""
        from server import get_security_rules
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "data": [
                {"attributes": {"isEnabled": True}},
                {"attributes": {"isEnabled": False}},
                {"attributes": {"isEnabled": True}}
            ]
        }
        
        mock_api_instance = MagicMock()
        mock_api_instance.list_security_monitoring_rules.return_value = mock_response
        
        with patch('server.SecurityMonitoringApi', return_value=mock_api_instance):
            with patch('server._store_data', return_value="/test/path.json"):
                result = await get_security_rules(mock_context)
        
        assert result["total_rules"] == 3
        assert result["enabled_rules"] == 2
        assert result["disabled_rules"] == 1


class TestErrorHandling:
    """Test error handling across all tools"""
    
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock()
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()
        ctx.request_context.lifespan_context = MagicMock()
        return ctx
    
    @pytest.fixture
    def mock_app_context(self):
        from server import AppContext, DatadogConfig
        config = DatadogConfig(api_key="test", app_key="test")
        api_client = MagicMock()
        return AppContext(api_client=api_client, config=config)
    
    @pytest.mark.asyncio
    async def test_search_metrics_error(self, mock_context, mock_app_context):
        """Test search_metrics error handling"""
        from server import search_metrics
        
        mock_context.request_context.lifespan_context = mock_app_context
        
        with patch('server.MetricsApi', side_effect=Exception("Network error")):
            result = await search_metrics("cpu", mock_context)
        
        assert "error" in result
        assert "Network error" in result["error"]
        mock_context.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_cache_error(self, mock_context):
        """Test cleanup_cache error handling"""
        from server import cleanup_cache
        
        with patch('server.DATA_DIR.glob', side_effect=Exception("Permission denied")):
            result = await cleanup_cache(mock_context, 24)
        
        assert "error" in result
        assert "Permission denied" in result["error"]
        mock_context.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
