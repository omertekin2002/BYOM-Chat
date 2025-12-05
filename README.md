# BYOM Chat - Bring Your Own Model

A self-hosted AI chat interface using Open WebUI. Works **standalone with cloud APIs** or connected to **local models via LM Studio**. Includes **custom Sora video generation support**.

## Quick Start

### One-Time Setup

Install `uv` (Python runtime manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Start the Chat Interface

```bash
./start.sh
```

Access the web interface at: **http://localhost:8080**

The script auto-detects if LM Studio is running and configures accordingly.

### Launch Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Auto** | `./start.sh` | Auto-detects LM Studio, falls back to standalone |
| **Standalone** | `./start.sh --standalone` | Cloud APIs only (OpenAI, Anthropic, etc.) |
| **Local** | `./start.sh --local` | Requires LM Studio running |

### First-Time Setup

1. Open **http://localhost:8080**
2. Create an admin account (first user becomes admin)
3. Go to **Settings** → **Admin Settings** → **Connections**
4. Add your API keys (OpenAI, Anthropic, Google AI, etc.)

## Features

- ☁️ **Standalone mode** - Works without local models, just add API keys
- 💻 **Local models** - Connect to LM Studio for offline/private AI
- 🔑 **Bring your own API keys** - OpenAI, Anthropic, Google AI, Azure, and more
- 📁 **RAG** - Upload documents for context-aware conversations
- 👥 **Multi-user** - Admin controls and user management
- 💾 **Persistent** - Chat history saved in `~/.open-webui`
- 🎨 **Beautiful UI** - Modern, ChatGPT-like interface
- 🖼️ **Image generation** - DALL-E, gpt-image-1, Stable Diffusion
- 🎬 **Video generation** - Sora support (custom feature!)

## Configuration

### Adding Cloud APIs

After logging in as admin:
**Settings** → **Admin Settings** → **Connections**

Supported providers:
- OpenAI (GPT-4, GPT-4o, o1, etc.)
- Anthropic (Claude)
- Google AI (Gemini)
- Azure OpenAI
- Any OpenAI-compatible API

### Using with LM Studio

1. Start LM Studio and enable the local server (default: `http://127.0.0.1:1234`)
2. Load a model in LM Studio
3. Run `./start.sh` (auto-detects) or `./start.sh --local`

### Changing LM Studio Port

```bash
OPENAI_API_BASE_URL=http://127.0.0.1:YOUR_PORT/v1 ./start.sh --local
```

## Data Location

All data is stored in `~/.open-webui/`:
- Chat history
- User accounts
- Uploaded files
- Settings

To reset: `rm -rf ~/.open-webui`

---

## 🎬 Sora Video Generation (Custom Feature)

This fork includes **full Sora video generation support** via OpenAI's Video API, including both backend API and frontend UI.

### Features

- ✅ Admin settings panel for video configuration
- ✅ Video generation modal in chat interface
- ✅ Support for all Sora models (sora-2, sora-2-pro)
- ✅ Configurable duration (4, 8, 12 seconds)
- ✅ Multiple video sizes/resolutions
- ✅ Quality settings (standard, HD)
- ✅ Async video generation with progress tracking
- ✅ Video list management (view, download, delete)

### Setup

1. Go to **Admin Settings** → **Videos**
2. Enable Video Generation
3. Enter your OpenAI API key (must have Sora access)
4. Configure default settings (model, duration, size, quality)
5. Save settings

### Using Video Generation

1. In any chat, click the **Integrations** button (component icon)
2. Click **Video** to open the Video Generation modal
3. Enter your prompt describing the video
4. Adjust settings as needed
5. Click **Generate Video**
6. Wait for generation to complete (1-5 minutes)
7. Download your video!

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/videos/config` | GET | Get video generation config |
| `/api/v1/videos/config/update` | POST | Update video generation config |
| `/api/v1/videos/models` | GET | List available video models |
| `/api/v1/videos/generations` | POST | Create a video (async) |
| `/api/v1/videos/generations/sync` | POST | Create a video and wait for completion |
| `/api/v1/videos/list` | GET | List all video generation jobs |
| `/api/v1/videos/{video_id}` | GET | Get video status |
| `/api/v1/videos/{video_id}/content` | GET | Download completed video |
| `/api/v1/videos/{video_id}` | DELETE | Delete a video |

### Example: Generate a Video via API

```bash
curl -X POST http://localhost:8080/api/v1/videos/generations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A calico cat playing piano in a jazz club",
    "model": "sora-2",
    "seconds": "8",
    "size": "1920x1080"
  }'
```

### Environment Variables

```bash
ENABLE_VIDEO_GENERATION=true
VIDEO_GENERATION_ENGINE=openai
VIDEO_GENERATION_MODEL=sora-2
VIDEO_DURATION=4
VIDEO_SIZE=1920x1080
VIDEO_QUALITY=standard
VIDEOS_OPENAI_API_BASE_URL=https://api.openai.com/v1
VIDEOS_OPENAI_API_KEY=your-api-key
```

---

## Running from Modified Source

To use the Sora features, run from the modified source:

```bash
cd open-webui-source

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run the backend
python -m open_webui.main
```

For the frontend (development mode):
```bash
cd open-webui-source
npm install
npm run dev
```

---

## Modified Files Summary

### Backend (Python)

| File | Change |
|------|--------|
| `backend/open_webui/routers/videos.py` | **NEW** - Complete video generation API |
| `backend/open_webui/config.py` | Added video configuration options |
| `backend/open_webui/main.py` | Registered video router |

### Frontend (Svelte/TypeScript)

| File | Change |
|------|--------|
| `src/lib/constants.ts` | Added `VIDEOS_API_BASE_URL` |
| `src/lib/apis/videos/index.ts` | **NEW** - Video API client functions |
| `src/lib/components/admin/Settings/Videos.svelte` | **NEW** - Admin settings panel |
| `src/lib/components/admin/Settings.svelte` | Added Videos tab |
| `src/lib/components/chat/VideoGenerationModal.svelte` | **NEW** - Video generation UI |
| `src/lib/components/chat/MessageInput.svelte` | Added video generation button support |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | Added Video button |
| `src/lib/components/chat/Chat.svelte` | Integrated VideoGenerationModal |

---

## Troubleshooting

### No models showing?
1. **Standalone mode**: Add API keys in **Settings** → **Admin Settings** → **Connections**
2. **Local mode**: Make sure LM Studio is running with a model loaded

### Video generation not working?
1. Make sure you have an OpenAI API key with Sora access
2. Check the API key is configured in **Admin Settings** → **Videos**
3. Verify `ENABLE_VIDEO_GENERATION` is enabled
4. Check browser console for errors

---

## Alternative: Docker Setup

If you prefer Docker (uses more RAM but isolated):

```bash
docker compose up -d
```

Access at: **http://localhost:3000**

Stop with: `docker compose down`

**Note:** By default, Docker runs in standalone mode. To connect to LM Studio, edit `docker-compose.yml` and uncomment the LM Studio environment variables.
