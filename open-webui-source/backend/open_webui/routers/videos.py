import asyncio
import base64
import io
import json
import logging
import mimetypes
import re
import time
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENABLE_FORWARD_USER_INFO_HEADERS, SRC_LOG_LEVELS
from open_webui.routers.files import upload_file_handler
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.headers import include_user_info_headers
from pydantic import BaseModel

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("VIDEOS", logging.INFO))

VIDEO_CACHE_DIR = CACHE_DIR / "video" / "generations"
VIDEO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()


class VideosConfig(BaseModel):
    ENABLE_VIDEO_GENERATION: bool
    VIDEO_GENERATION_ENGINE: str
    VIDEO_GENERATION_MODEL: str
    VIDEO_DURATION: Optional[str]
    VIDEO_SIZE: Optional[str]
    VIDEO_QUALITY: Optional[str]
    VIDEOS_OPENAI_API_BASE_URL: str
    VIDEOS_OPENAI_API_KEY: str


@router.get("/config", response_model=VideosConfig)
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_VIDEO_GENERATION": getattr(
            request.app.state.config, "ENABLE_VIDEO_GENERATION", False
        ),
        "VIDEO_GENERATION_ENGINE": getattr(
            request.app.state.config, "VIDEO_GENERATION_ENGINE", "openai"
        ),
        "VIDEO_GENERATION_MODEL": getattr(
            request.app.state.config, "VIDEO_GENERATION_MODEL", "sora-2"
        ),
        "VIDEO_DURATION": getattr(
            request.app.state.config, "VIDEO_DURATION", "4"
        ),
        "VIDEO_SIZE": getattr(
            request.app.state.config, "VIDEO_SIZE", "1920x1080"
        ),
        "VIDEO_QUALITY": getattr(
            request.app.state.config, "VIDEO_QUALITY", "standard"
        ),
        "VIDEOS_OPENAI_API_BASE_URL": getattr(
            request.app.state.config, "VIDEOS_OPENAI_API_BASE_URL", "https://api.openai.com/v1"
        ),
        "VIDEOS_OPENAI_API_KEY": getattr(
            request.app.state.config, "VIDEOS_OPENAI_API_KEY", ""
        ),
    }


@router.post("/config/update")
async def update_config(
    request: Request, form_data: VideosConfig, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_VIDEO_GENERATION = form_data.ENABLE_VIDEO_GENERATION
    request.app.state.config.VIDEO_GENERATION_ENGINE = form_data.VIDEO_GENERATION_ENGINE
    request.app.state.config.VIDEO_GENERATION_MODEL = form_data.VIDEO_GENERATION_MODEL
    request.app.state.config.VIDEO_DURATION = form_data.VIDEO_DURATION
    request.app.state.config.VIDEO_SIZE = form_data.VIDEO_SIZE
    request.app.state.config.VIDEO_QUALITY = form_data.VIDEO_QUALITY
    request.app.state.config.VIDEOS_OPENAI_API_BASE_URL = form_data.VIDEOS_OPENAI_API_BASE_URL
    request.app.state.config.VIDEOS_OPENAI_API_KEY = form_data.VIDEOS_OPENAI_API_KEY

    return await get_config(request, user)


@router.get("/models")
def get_models(request: Request, user=Depends(get_verified_user)):
    """Get available video generation models."""
    engine = getattr(request.app.state.config, "VIDEO_GENERATION_ENGINE", "openai")
    
    if engine == "openai":
        return [
            {"id": "sora-2", "name": "Sora 2"},
            {"id": "sora-2-pro", "name": "Sora 2 Pro"},
        ]
    
    return []


class CreateVideoForm(BaseModel):
    model: Optional[str] = None
    prompt: str
    input_reference: Optional[str] = None  # base64-encoded image or URL
    seconds: Optional[str] = None  # "4", "8", or "12"
    size: Optional[str] = None
    quality: Optional[str] = None
    n: int = 1


class VideoStatus(BaseModel):
    id: str
    object: str
    model: str
    status: str
    progress: int
    created_at: int
    size: Optional[str] = None
    seconds: Optional[str] = None
    quality: Optional[str] = None


@router.post("/generations")
async def video_generations(
    request: Request,
    form_data: CreateVideoForm,
    user=Depends(get_verified_user),
):
    """
    Create a video generation request.
    
    This endpoint initiates video generation and returns the video job info.
    Since video generation is async, you'll need to poll /videos/{id} for status
    and use /videos/{id}/content to retrieve the final video.
    """
    engine = getattr(request.app.state.config, "VIDEO_GENERATION_ENGINE", "openai")
    
    if engine != "openai":
        raise HTTPException(
            status_code=400,
            detail="Only OpenAI (Sora) video generation is currently supported."
        )
    
    api_key = getattr(request.app.state.config, "VIDEOS_OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Video generation API key is not configured. Please set it in Admin Settings > Videos."
        )
    
    base_url = getattr(
        request.app.state.config, 
        "VIDEOS_OPENAI_API_BASE_URL", 
        "https://api.openai.com/v1"
    )
    
    model = form_data.model or getattr(
        request.app.state.config, "VIDEO_GENERATION_MODEL", "sora-2"
    )
    
    seconds = form_data.seconds or getattr(
        request.app.state.config, "VIDEO_DURATION", "4"
    )
    
    size = form_data.size or getattr(
        request.app.state.config, "VIDEO_SIZE", "1920x1080"
    )
    
    quality = form_data.quality or getattr(
        request.app.state.config, "VIDEO_QUALITY", "standard"
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    if ENABLE_FORWARD_USER_INFO_HEADERS:
        headers = include_user_info_headers(headers, user)
    
    # Build request data
    data = {
        "model": model,
        "prompt": form_data.prompt,
        "seconds": seconds,
        "size": size,
        "quality": quality,
    }
    
    # Handle input_reference (image-to-video)
    files = None
    if form_data.input_reference:
        # If it's a base64 image, we need to send as multipart form
        if form_data.input_reference.startswith("data:"):
            header, encoded = form_data.input_reference.split(",", 1)
            mime_type = header.split(";")[0].lstrip("data:")
            image_data = base64.b64decode(encoded)
            
            files = {
                "input_reference": ("reference.png", io.BytesIO(image_data), mime_type)
            }
            # Remove Content-Type header for multipart
            del headers["Content-Type"]
        elif form_data.input_reference.startswith("http"):
            # URL reference - include in JSON
            data["input_reference"] = form_data.input_reference
    
    try:
        if files:
            # Multipart form request
            r = await asyncio.to_thread(
                requests.post,
                url=f"{base_url}/videos",
                headers=headers,
                data=data,
                files=files,
            )
        else:
            # JSON request
            r = await asyncio.to_thread(
                requests.post,
                url=f"{base_url}/videos",
                headers=headers,
                json=data,
            )
        
        r.raise_for_status()
        result = r.json()
        
        log.info(f"Video generation initiated: {result}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_detail = error_data["error"].get("message", str(e))
        except:
            pass
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        log.exception(f"Video generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_videos(
    request: Request,
    user=Depends(get_verified_user),
    limit: int = 20,
    after: Optional[str] = None,
):
    """List all video generation jobs."""
    api_key = getattr(request.app.state.config, "VIDEOS_OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Video API key not configured.")
    
    base_url = getattr(
        request.app.state.config,
        "VIDEOS_OPENAI_API_BASE_URL",
        "https://api.openai.com/v1"
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    params = {"limit": limit}
    if after:
        params["after"] = after
    
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{base_url}/videos",
            headers=headers,
            params=params,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.exception(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}")
async def get_video(
    request: Request,
    video_id: str,
    user=Depends(get_verified_user),
):
    """Get the status of a video generation job."""
    api_key = getattr(request.app.state.config, "VIDEOS_OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Video API key not configured.")
    
    base_url = getattr(
        request.app.state.config,
        "VIDEOS_OPENAI_API_BASE_URL",
        "https://api.openai.com/v1"
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{base_url}/videos/{video_id}",
            headers=headers,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.exception(f"Error getting video status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/content")
async def get_video_content(
    request: Request,
    video_id: str,
    user=Depends(get_verified_user),
):
    """
    Retrieve the content of a completed video.
    Returns the video file as a streaming response.
    """
    api_key = getattr(request.app.state.config, "VIDEOS_OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Video API key not configured.")
    
    base_url = getattr(
        request.app.state.config,
        "VIDEOS_OPENAI_API_BASE_URL",
        "https://api.openai.com/v1"
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        r = await asyncio.to_thread(
            requests.get,
            url=f"{base_url}/videos/{video_id}/content",
            headers=headers,
            stream=True,
        )
        r.raise_for_status()
        
        content_type = r.headers.get("content-type", "video/mp4")
        
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk
        
        return StreamingResponse(
            generate(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{video_id}.mp4"'
            }
        )
    except Exception as e:
        log.exception(f"Error getting video content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{video_id}")
async def delete_video(
    request: Request,
    video_id: str,
    user=Depends(get_verified_user),
):
    """Delete a video."""
    api_key = getattr(request.app.state.config, "VIDEOS_OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="Video API key not configured.")
    
    base_url = getattr(
        request.app.state.config,
        "VIDEOS_OPENAI_API_BASE_URL",
        "https://api.openai.com/v1"
    )
    
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        r = await asyncio.to_thread(
            requests.delete,
            url=f"{base_url}/videos/{video_id}",
            headers=headers,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.exception(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generations/sync")
async def video_generations_sync(
    request: Request,
    form_data: CreateVideoForm,
    user=Depends(get_verified_user),
    timeout: int = 300,  # 5 minute default timeout
    poll_interval: int = 5,  # Poll every 5 seconds
):
    """
    Create a video and wait for completion (synchronous).
    
    This endpoint initiates video generation and polls until complete,
    then returns the video URL. Use this for a simpler integration
    when you don't want to handle polling yourself.
    
    WARNING: Video generation can take several minutes. This endpoint
    will hold the connection open until the video is ready or timeout.
    """
    # First, create the video generation job
    result = await video_generations(request, form_data, user)
    
    video_id = result.get("id")
    if not video_id:
        raise HTTPException(status_code=500, detail="Failed to get video ID from response")
    
    # Poll for completion
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = await get_video(request, video_id, user)
        
        if status.get("status") == "completed":
            # Video is ready - return the content URL
            return {
                "id": video_id,
                "status": "completed",
                "url": f"/api/v1/videos/{video_id}/content",
                "model": status.get("model"),
                "size": status.get("size"),
                "seconds": status.get("seconds"),
            }
        elif status.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Video generation failed: {status.get('error', 'Unknown error')}"
            )
        
        # Still processing, wait and poll again
        await asyncio.sleep(poll_interval)
    
    # Timeout reached
    raise HTTPException(
        status_code=408,
        detail=f"Video generation timed out after {timeout} seconds. Video ID: {video_id}. You can check status at /api/v1/videos/{video_id}"
    )

