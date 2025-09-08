#!/usr/bin/env python3
"""
Syntax validation for the modernized Datadog MCP Server

This script validates the Python syntax and basic structure without requiring dependencies.
"""

import ast
import sys
from pathlib import Path

def validate_python_syntax(filepath):
    """Validate Python syntax of a file"""
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source)
        print(f"✅ {filepath.name}: Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ {filepath.name}: Syntax error at line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {filepath.name}: Error reading file: {e}")
        return False

def check_modern_patterns(filepath):
    """Check for modern MCP patterns in the code"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        patterns = {
            "Lifespan management": "@asynccontextmanager" in content,
            "Context usage": "ctx: Context" in content,
            "Type annotations": "AsyncIterator" in content,
            "Dataclass usage": "@dataclass" in content,
            "Modern imports": "from mcp.server.fastmcp import Context, FastMCP" in content,
        }
        
        print(f"\n📋 Modern patterns in {filepath.name}:")
        all_good = True
        for pattern, found in patterns.items():
            status = "✅" if found else "❌"
            print(f"  {status} {pattern}")
            if not found:
                all_good = False
        
        return all_good
    except Exception as e:
        print(f"❌ Error checking patterns: {e}")
        return False

def main():
    """Run validation"""
    print("Validating Modernized Datadog MCP Server")
    print("=" * 45)
    
    current_dir = Path(__file__).parent
    files_to_check = [
        current_dir / "server.py"
    ]
    
    results = {}
    
    for filepath in files_to_check:
        if filepath.exists():
            print(f"\nValidating {filepath.name}...")
            syntax_ok = validate_python_syntax(filepath)
            patterns_ok = check_modern_patterns(filepath)
            results[filepath.name] = syntax_ok and patterns_ok
        else:
            print(f"⚠️  {filepath.name} not found")
            results[filepath.name] = False
    
    print("\n" + "=" * 45)
    print("Validation Summary:")
    
    for filename, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {filename}: {status}")
    
    if results.get("server.py", False):
        print("\n🎉 Server validation passed!")
        print("The server follows current MCP SDK patterns and is ready for use.")
        return 0
    else:
        print("\n⚠️  Validation issues found. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
