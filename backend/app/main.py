
import asyncio
import json
import uuid
import subprocess
import shutil

from uuid import UUID
from pathlib import Path

import httpx

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

app = FastAPI(
    title="MomentForge AI",
    description="AI-powered automatic video clipping platform",
    version="0.1.0"
)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# STORAGE CONFIGURATION
# ==========================================

UPLOAD_DIR = Path("storage/uploads")
THUMBNAIL_DIR = Path("storage/thumbnails")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm"
}

CHUNK_SIZE = 1024 * 1024  # 1 MB


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
async def root():
    return {
        "message": "Welcome to MomentForge AI",
        "status": "running"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "application": "MomentForge AI",
        "version": "0.1.0"
    }


# ==========================================
# OLLAMA STATUS
# ==========================================

@app.get("/api/ollama/status")
async def ollama_status():

    ollama_url = "http://127.0.0.1:11434/api/tags"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(ollama_url)
            response.raise_for_status()

            data = response.json()

            models = [
                model["name"]
                for model in data.get("models", [])
            ]

            return {
                "connected": True,
                "models": models
            }

    except (httpx.HTTPError, ValueError):
        return {
            "connected": False,
            "models": [],
            "message": "Ollama is unavailable"
        }


# ==========================================
# VIDEO UPLOAD
# ==========================================

@app.post("/api/videos/upload")
async def upload_video(file: UploadFile = File(...)):

    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format"
        )

    video_id = str(uuid.uuid4())

    safe_filename = f"{video_id}{extension}"
    file_path = UPLOAD_DIR / safe_filename

    total_size = 0

    try:
        with open(file_path, "wb") as output_file:

            while True:
                chunk = await file.read(CHUNK_SIZE)

                if not chunk:
                    break

                output_file.write(chunk)
                total_size += len(chunk)

        return {
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "filename": file.filename,
            "stored_filename": safe_filename,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "status": "uploaded"
        }

    except Exception:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Video upload failed"
        )

    finally:
        await file.close()


# ==========================================
# VIDEO METADATA EXTRACTION
# ==========================================

@app.get("/api/videos/{video_id}/metadata")
async def get_video_metadata(video_id: str):

    try:
        safe_id = str(UUID(video_id))

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid video ID"
        )

    matching_files = list(UPLOAD_DIR.glob(f"{safe_id}.*"))

    if not matching_files:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    video_path = matching_files[0]

    ffprobe_path = shutil.which("ffprobe")

    if not ffprobe_path:
        raise HTTPException(
            status_code=500,
            detail="FFprobe executable not found in PATH"
        )

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            [
                ffprobe_path,
                "-v", "error",
                "-show_entries",
                "format=duration,size,bit_rate:"
                "stream=codec_type,codec_name,width,height,"
                "r_frame_rate,avg_frame_rate,sample_rate,channels",
                "-of", "json",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        data = json.loads(result.stdout)

        format_data = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"),
            {}
        )

        audio_stream = next(
            (s for s in streams if s.get("codec_type") == "audio"),
            {}
        )

        if not video_stream:
            raise HTTPException(
                status_code=422,
                detail="Uploaded file does not contain a video stream"
            )

        duration = float(format_data.get("duration", 0))

        return {
            "video_id": safe_id,
            "filename": video_path.name,

            "duration_seconds": round(duration, 2),

            "duration_formatted": (
                f"{int(duration // 3600):02d}:"
                f"{int((duration % 3600) // 60):02d}:"
                f"{int(duration % 60):02d}"
            ),

            "resolution": {
                "width": video_stream.get("width"),
                "height": video_stream.get("height")
            },

            "video_codec": video_stream.get("codec_name"),
            "audio_codec": audio_stream.get("codec_name"),

            "fps": video_stream.get("avg_frame_rate"),
            "bitrate": format_data.get("bit_rate"),
            "size_bytes": int(format_data.get("size", 0)),

            "status": "metadata_extracted"
        }

    except HTTPException:
        raise

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Video metadata extraction timed out"
        )

    except subprocess.CalledProcessError:
        raise HTTPException(
            status_code=422,
            detail="FFprobe could not process this video"
        )

    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Metadata extraction failed: {str(error)}"
        )


# ==========================================
# GENERATE VIDEO THUMBNAIL
# ==========================================

@app.post("/api/videos/{video_id}/thumbnail")
async def generate_thumbnail(video_id: str):

    try:
        safe_id = str(UUID(video_id))

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid video ID"
        )

    matches = list(UPLOAD_DIR.glob(f"{safe_id}.*"))

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Video not found"
        )

    video_path = matches[0]

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise HTTPException(
            status_code=500,
            detail="FFmpeg executable not found in PATH"
        )

    thumbnail_path = THUMBNAIL_DIR / f"{safe_id}.jpg"

    try:
        await asyncio.to_thread(
            subprocess.run,
            [
                ffmpeg_path,
                "-y",
                "-ss", "1",
                "-i", str(video_path),
                "-frames:v", "1",
                "-q:v", "2",
                str(thumbnail_path)
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )

        if not thumbnail_path.exists() or thumbnail_path.stat().st_size == 0:
            raise HTTPException(
                status_code=500,
                detail="Thumbnail file was not generated"
            )

        return {
            "video_id": safe_id,
            "thumbnail": f"/api/videos/{safe_id}/thumbnail/file",
            "status": "thumbnail_generated"
        }

    except HTTPException:
        raise

    except subprocess.CalledProcessError:
        thumbnail_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Thumbnail generation failed"
        )

    except subprocess.TimeoutExpired:
        thumbnail_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=504,
            detail="Thumbnail generation timed out"
        )

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=f"Thumbnail generation failed: {str(error)}"
        )


# ==========================================
# SERVE VIDEO THUMBNAIL
# ==========================================

@app.get("/api/videos/{video_id}/thumbnail/file")
async def get_thumbnail(video_id: str):

    try:
        safe_id = str(UUID(video_id))

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid video ID"
        )

    thumbnail_path = THUMBNAIL_DIR / f"{safe_id}.jpg"

    if not thumbnail_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Thumbnail not found"
        )

    return FileResponse(
        thumbnail_path,
        media_type="image/jpeg",
        filename=f"{safe_id}.jpg"
    )
