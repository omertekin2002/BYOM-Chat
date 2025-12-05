#!/bin/bash

# BYOM Chat - Development Start Script
# Runs from modified source with Sora video generation support

set -e

# Use Node 22 (required for frontend build)
export PATH="/opt/homebrew/opt/node@22/bin:$HOME/.local/bin:$PATH"

# Handle Ctrl+C gracefully
trap 'echo ""; echo "👋 Shutting down..."; exit 0' INT TERM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/open-webui-source"
BACKEND_DIR="$SOURCE_DIR/backend"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "🚀 BYOM Chat - Development Mode (with Sora)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if source exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Error: open-webui-source directory not found"
    exit 1
fi

# Check for Python 3.11 (required for compatibility)
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Error: Python 3.11 is required"
    echo "   Install with: brew install python@3.11"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment with Python 3.11 (first time only)..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "   ✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if backend dependencies are installed
if [ ! -f "$VENV_DIR/.deps_installed" ]; then
    echo "📦 Installing backend dependencies (first time only)..."
    echo "   This may take a few minutes..."
    cd "$BACKEND_DIR"
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    touch "$VENV_DIR/.deps_installed"
    echo "   ✅ Backend dependencies installed"
    echo ""
fi

# Check if frontend is built
if [ ! -d "$SOURCE_DIR/build" ]; then
    echo "📦 Building frontend (first time only)..."
    echo "   This may take a few minutes..."
    cd "$SOURCE_DIR"
    npm install --legacy-peer-deps
    npm run build
    echo "   ✅ Frontend built"
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

# Generate secret key if not exists
KEY_FILE="$DATA_DIR/.webui_secret_key"
if [ ! -f "$KEY_FILE" ]; then
    head -c 12 /dev/random | base64 > "$KEY_FILE"
fi
export WEBUI_SECRET_KEY=$(cat "$KEY_FILE")

# Run the backend with uvicorn
exec python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080
