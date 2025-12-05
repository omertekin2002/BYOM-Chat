#!/bin/bash

# BYOM Chat - Start Script
# Starts Open WebUI in standalone mode or connected to LM Studio

export PATH="$HOME/.local/bin:$PATH"

# Handle Ctrl+C gracefully
trap 'echo ""; echo "👋 Shutting down..."; exit 0' INT TERM

# Check if LM Studio is running
check_lm_studio() {
    curl -s --connect-timeout 2 http://127.0.0.1:1234/v1/models > /dev/null 2>&1
    return $?
}

# Parse arguments
MODE="auto"
while [[ $# -gt 0 ]]; do
    case $1 in
        --local|--lm-studio)
            MODE="local"
            shift
            ;;
        --standalone|--cloud)
            MODE="standalone"
            shift
            ;;
        --help|-h)
            echo "BYOM Chat - Bring Your Own Model"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --local, --lm-studio    Force connection to LM Studio (requires LM Studio running)"
            echo "  --standalone, --cloud   Run without local models (add API keys in Settings)"
            echo "  --help, -h              Show this help message"
            echo ""
            echo "Without options, auto-detects if LM Studio is running."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 BYOM Chat - Bring Your Own Model"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Determine which mode to use
if [ "$MODE" = "auto" ]; then
    echo "🔍 Auto-detecting LM Studio..."
    if check_lm_studio; then
        MODE="local"
        echo "   ✅ LM Studio detected at http://127.0.0.1:1234"
    else
        MODE="standalone"
        echo "   ℹ️  LM Studio not detected, running standalone"
    fi
    echo ""
fi

# Build environment based on mode
if [ "$MODE" = "local" ]; then
    if ! check_lm_studio; then
        echo "❌ Error: LM Studio is not running at http://127.0.0.1:1234"
        echo ""
        echo "Please either:"
        echo "  1. Start LM Studio and enable the local server"
        echo "  2. Run with --standalone flag to use cloud APIs only"
        exit 1
    fi
    
    echo "📡 Mode: Local + Cloud"
    echo "   • LM Studio: http://127.0.0.1:1234"
    echo "   • Add cloud APIs in Settings → Admin Settings → Connections"
    echo ""
    
    EXTRA_ENV="OPENAI_API_BASE_URL=http://127.0.0.1:1234/v1 OPENAI_API_KEY=lm-studio"
else
    echo "☁️  Mode: Standalone (Cloud APIs only)"
    echo "   • Add your API keys in Settings → Admin Settings → Connections"
    echo "   • Supports: OpenAI, Anthropic, Google AI, Azure, and more"
    echo ""
    
    EXTRA_ENV=""
fi

echo "🌐 Access the chat at: http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start Open WebUI
exec env \
    DATA_DIR=~/.open-webui \
    ENABLE_OLLAMA_API=false \
    $EXTRA_ENV \
    uvx --python 3.11 open-webui@latest serve
