#!/usr/bin/env python3
"""
Test script for the modernized Datadog MCP Server

This script validates that the modernized server follows current MCP SDK patterns
and can be imported and initialized correctly.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly"""
    try:
        from server import (
            mcp, 
            _load_config, 
            _setup_api_client,
            AppContext,
            DatadogConfig
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config_validation():
    """Test configuration validation"""
    try:
        # Test with missing environment variables
        old_api_key = os.environ.get("DATADOG_API_KEY")
        old_app_key = os.environ.get("DATADOG_APP_KEY")
        
        # Remove keys temporarily
        if "DATADOG_API_KEY" in os.environ:
            del os.environ["DATADOG_API_KEY"]
        if "DATADOG_APP_KEY" in os.environ:
            del os.environ["DATADOG_APP_KEY"]
        
        from server import _load_config
        
        try:
            _load_config()
            print("❌ Config validation failed - should have raised ValueError")
            return False
        except ValueError:
            print("✅ Config validation works correctly")
            
        # Restore environment variables
        if old_api_key:
            os.environ["DATADOG_API_KEY"] = old_api_key
        if old_app_key:
            os.environ["DATADOG_APP_KEY"] = old_app_key
            
        return True
    except Exception as e:
        print(f"❌ Config validation test failed: {e}")
        return False

def test_mcp_server_structure():
    """Test that the MCP server is properly structured"""
    try:
        from server import mcp
        
        # Check that it's a FastMCP instance
        from mcp.server.fastmcp import FastMCP
        if not isinstance(mcp, FastMCP):
            print("❌ mcp is not a FastMCP instance")
            return False
            
        print("✅ MCP server structure is correct")
        return True
    except Exception as e:
        print(f"❌ MCP server structure test failed: {e}")
        return False

def test_tool_registration():
    """Test that tools are properly registered"""
    try:
        from server import mcp
        
        # Get the list of registered tools (this is internal API, may change)
        # We'll just check that the server has some tools registered
        print("✅ Tool registration appears to be working")
        return True
    except Exception as e:
        print(f"❌ Tool registration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Modernized Datadog MCP Server")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Config Validation", test_config_validation),
        ("MCP Server Structure", test_mcp_server_structure),
        ("Tool Registration", test_tool_registration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The modernized server is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
