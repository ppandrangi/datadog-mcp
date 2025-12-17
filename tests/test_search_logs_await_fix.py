#!/usr/bin/env python3
"""
Test suite for search_logs async/await fix (PR #2)

Tests that the search_logs function properly awaits the async list_logs call,
fixing the "'coroutine' object has no attribute 'to_dict'" error.
"""

import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datadog_api_client import AsyncApiClient


class TestSearchLogsAwaitFix:
    """Test search_logs async/await fix"""

    @pytest.mark.asyncio
    async def test_search_logs_awaits_async_call(self):
        """Test that search_logs properly awaits the async list_logs call"""
        from server import search_logs, AppContext, DatadogConfig

        # Create mock context
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()

        # Create mock API client
        mock_api_client = MagicMock(spec=AsyncApiClient)
        mock_api_client.__enter__ = MagicMock(return_value=mock_api_client)
        mock_api_client.__exit__ = MagicMock(return_value=None)

        # Create mock config
        mock_config = DatadogConfig(
            api_key="test_key",
            app_key="test_app_key",
            site="datadoghq.com"
        )

        # Create app context
        app_ctx = AppContext(api_client=mock_api_client, config=mock_config)
        mock_ctx.request_context.lifespan_context = app_ctx

        # Create mock response that would be returned by await
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "data": [
                {"message": "Test log entry 1"},
                {"message": "Test log entry 2"}
            ]
        }

        # Mock the LogsApiV2 instance and its list_logs method
        mock_logs_api = MagicMock()
        # The key fix: list_logs should return a coroutine that resolves to mock_response
        mock_logs_api.list_logs = AsyncMock(return_value=mock_response)

        with patch('server.LogsApiV2', return_value=mock_logs_api):
            with patch('server._store_data', new_callable=AsyncMock, return_value="/test/logs.json"):
                result = await search_logs(
                    query="error",
                    from_time="now-1h",
                    to_time="now",
                    ctx=mock_ctx,
                    limit=10
                )

        # Verify the response was properly awaited and processed
        assert result["log_count"] == 2
        assert result["filepath"] == "/test/logs.json"
        assert "Retrieved 2 log entries" in result["summary"]

        # Verify list_logs was called (and awaited)
        mock_logs_api.list_logs.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_logs_returns_coroutine_not_dict_without_await(self):
        """
        Test that demonstrates the bug: without await, list_logs returns a coroutine
        This test verifies our fix by showing what would happen without await
        """
        # Create mock logs API
        mock_logs_api = MagicMock()

        # Simulate the bug: list_logs returns a coroutine (async function not awaited)
        async def fake_list_logs(body):
            return MagicMock(to_dict=lambda: {"data": []})

        mock_logs_api.list_logs = fake_list_logs

        # Call list_logs without await (the bug)
        response_without_await = mock_logs_api.list_logs(body={})

        # This should be a coroutine, not the actual response
        assert inspect.iscoroutine(response_without_await)

        # Trying to call .to_dict() on a coroutine would fail
        with pytest.raises(AttributeError, match="'coroutine' object has no attribute 'to_dict'"):
            response_without_await.to_dict()

        # Clean up the coroutine
        response_without_await.close()

        # Now with await (the fix)
        response_with_await = await mock_logs_api.list_logs(body={})

        # This should work fine
        result = response_with_await.to_dict()
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_search_logs_handles_empty_results(self):
        """Test search_logs with empty results"""
        from server import search_logs, AppContext, DatadogConfig

        # Create mock context
        mock_ctx = MagicMock()
        mock_ctx.info = AsyncMock()
        mock_ctx.error = AsyncMock()

        # Create mock API client
        mock_api_client = MagicMock(spec=AsyncApiClient)
        mock_api_client.__enter__ = MagicMock(return_value=mock_api_client)
        mock_api_client.__exit__ = MagicMock(return_value=None)

        # Create mock config
        mock_config = DatadogConfig(
            api_key="test_key",
            app_key="test_app_key",
            site="datadoghq.com"
        )

        # Create app context
        app_ctx = AppContext(api_client=mock_api_client, config=mock_config)
        mock_ctx.request_context.lifespan_context = app_ctx

        # Create mock response with no logs
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {"data": []}

        # Mock the LogsApiV2 instance
        mock_logs_api = MagicMock()
        mock_logs_api.list_logs = AsyncMock(return_value=mock_response)

        with patch('server.LogsApiV2', return_value=mock_logs_api):
            with patch('server._store_data', new_callable=AsyncMock, return_value="/test/logs.json"):
                result = await search_logs(
                    query="nonexistent",
                    from_time="now-1h",
                    to_time="now",
                    ctx=mock_ctx,
                    limit=10
                )

        # Verify empty results are handled correctly
        assert result["log_count"] == 0
        assert "Retrieved 0 log entries" in result["summary"]

        # Verify list_logs was properly awaited
        mock_logs_api.list_logs.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
