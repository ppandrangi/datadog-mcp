#!/usr/bin/env python3
"""
Real MCP client to query actual Datadog data
"""
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock
from server import validate_api_key, search_metrics, get_monitors

async def create_real_context():
    """Create a real context with actual API client"""
    from server import _load_config, _setup_api_client, AppContext
    
    config = _load_config()
    api_client = _setup_api_client(config)
    app_context = AppContext(api_client=api_client, config=config)
    
    mock_ctx = MagicMock()
    mock_ctx.info = AsyncMock()
    mock_ctx.error = AsyncMock()
    mock_ctx.request_context.lifespan_context = app_context
    
    return mock_ctx

async def run_real_queries():
    """Run actual queries against Datadog"""
    print("🔗 Connecting to Datadog with your credentials...")
    print("=" * 60)
    
    try:
        ctx = await create_real_context()
        
        # Query 1: Validate credentials
        print("\n1️⃣ Validating API credentials...")
        result = await validate_api_key(ctx)
        if result.get('valid'):
            print(f"✅ {result['summary']}")
            print(f"   Site: {result['site']}")
        else:
            print(f"❌ {result.get('error', 'Validation failed')}")
            return
        
        # Query 2: Search for common metrics
        print("\n2️⃣ Searching for system metrics...")
        result = await search_metrics("system", ctx)
        if 'error' not in result:
            print(f"✅ Found {result['metric_count']} system metrics")
            if result['sample_metrics']:
                print("   Sample metrics:")
                for metric in result['sample_metrics'][:3]:
                    print(f"   - {metric}")
        else:
            print(f"❌ {result['error']}")
        
        # Query 3: Get monitors
        print("\n3️⃣ Retrieving monitors...")
        result = await get_monitors(ctx)
        if 'error' not in result:
            print(f"✅ Found {result['total_monitors']} monitors")
            if result['monitor_states']:
                print(f"   States: {result['monitor_states']}")
            if result['alerting_count'] > 0:
                print(f"   ⚠️  {result['alerting_count']} monitors currently alerting")
        else:
            print(f"❌ {result['error']}")
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("   This might be due to network/SSL issues in the test environment")
    
    print("\n" + "=" * 60)
    print("🎯 Sample queries completed!")

if __name__ == "__main__":
    asyncio.run(run_real_queries())
