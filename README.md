# BYOM Chat - Bring Your Own Model

A self-hosted AI chat interface using Open WebUI connected to LM Studio.

## Quick Start (Native - No Docker)

### Prerequisites
- LM Studio running with local server enabled at `http://127.0.0.1:1234`

### One-Time Setup

Install `uv` (Python runtime manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Start the Chat Interface

```bash
DATA_DIR=~/.open-webui \
OPENAI_API_BASE_URL=http://127.0.0.1:1234/v1 \
OPENAI_API_KEY=lm-studio \
ENABLE_OLLAMA_API=false \
uvx --python 3.11 open-webui@latest serve
```

Access the web interface at: **http://localhost:8080**

### Using the Start Script

For convenience, run:

```bash
./start.sh
```

## Configuration

### Connecting to Other APIs

After logging in, add cloud API providers through:
**Settings** → **Admin Settings** → **Connections**

Supported providers:
- OpenAI
- Anthropic
- Google AI
- Azure OpenAI
- Any OpenAI-compatible API

### Changing LM Studio Port

If LM Studio runs on a different port, update the `OPENAI_API_BASE_URL`:

```bash
OPENAI_API_BASE_URL=http://127.0.0.1:YOUR_PORT/v1
```

## Features

- 💬 Chat with local LLMs via LM Studio
- 🔑 Bring your own API keys for cloud providers
- 📁 Upload documents for RAG (Retrieval-Augmented Generation)
- 👥 Multi-user support with admin controls
- 💾 Persistent chat history (stored in `~/.open-webui`)
- 🎨 Beautiful, ChatGPT-like interface

## Data Location

All data is stored in `~/.open-webui/`:
- Chat history
- User accounts
- Uploaded files
- Settings

## Troubleshooting

### Models not showing up?
1. Make sure LM Studio's local server is running
2. Check that a model is loaded in LM Studio
3. In Open WebUI, go to **Settings** → **Admin Settings** → **Connections**

### Reset everything
```bash
rm -rf ~/.open-webui
```

---

## Alternative: Docker Setup

If you prefer Docker (uses more RAM but isolated):

```bash
docker compose up -d
```

Access at: **http://localhost:3000**

Stop with: `docker compose down`
