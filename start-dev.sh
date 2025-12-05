#!/bin/bash

# BYOM Chat - Development Start Script
# Runs from modified source with Sora video generation support

set -e

export PATH="$HOME/.local/bin:$PATH"

# Handle Ctrl+C gracefully
trap 'echo ""; echo "👋 Shutting down..."; exit 0' INT TERM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/open-webui-source"
BACKEND_DIR="$SOURCE_DIR/backend"

echo "🚀 BYOM Chat - Development Mode (with Sora)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Error: open-webui-source directory not found"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required"
    exit 1
fi

# Check if dependencies are installed
if [ ! -f "$BACKEND_DIR/.deps_installed" ]; then
    echo "📦 Installing backend dependencies (first time only)..."
    echo "   This may take a few minutes..."
    cd "$BACKEND_DIR"
    python3 -m pip install -r requirements.txt -q
    touch .deps_installed
    echo "   ✅ Dependencies installed"
    echo ""
fi

cd "$BACKEND_DIR"

# Check if LM Studio is running
check_lm_studio() {
    curl -s --connect-timeout 2 http://127.0.0.1:1234/v1/models > /dev/null 2>&1
    return $?
}

if check_lm_studio; then
    echo "📡 LM Studio detected at http://127.0.0.1:1234"
    export OPENAI_API_BASE_URL="http://127.0.0.1:1234/v1"
    export OPENAI_API_KEY="lm-studio"
else
    echo "☁️  Running in standalone mode (add API keys in Settings)"
fi

echo ""
echo "🎬 Sora video generation: ENABLED"
echo "🌐 Access the chat at: http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set data directory
export DATA_DIR="$HOME/.open-webui"
export ENABLE_OLLAMA_API="false"

# Run the backend
exec python -m open_webui.main

