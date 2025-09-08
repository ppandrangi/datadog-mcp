#!/bin/bash

# Datadog MCP Server Setup Script

set -e

echo "🚀 Setting up Datadog MCP Server..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Create cache directory
echo "📁 Creating cache directory..."
mkdir -p datadog_cache

# Setup environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Datadog API credentials"
else
    echo "✅ Environment file already exists"
fi

# Test installation
echo "🧪 Testing installation..."
python3 -c "
import sys
try:
    from server import DatadogMCPServer
    print('✅ Server import successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Datadog API credentials"
echo "2. Run: python3 server.py"
echo "3. Or add to Q CLI configuration"
echo ""
echo "For help, see README.md"
