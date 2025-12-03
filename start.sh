#!/bin/bash

# BYOM Chat - Start Script
# Starts Open WebUI connected to LM Studio (foreground mode)

export PATH="$HOME/.local/bin:$PATH"

# Handle Ctrl+C gracefully
trap 'echo ""; echo "👋 Shutting down..."; exit 0' INT TERM

echo "🚀 Starting Open WebUI..."
echo "📡 Connecting to LM Studio at http://127.0.0.1:1234"
echo ""
echo "Access the chat at: http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""

exec env \
  DATA_DIR=~/.open-webui \
  OPENAI_API_BASE_URL=http://127.0.0.1:1234/v1 \
  OPENAI_API_KEY=lm-studio \
  ENABLE_OLLAMA_API=false \
  uvx --python 3.11 open-webui@latest serve
