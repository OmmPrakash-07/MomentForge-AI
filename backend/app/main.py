
import asyncio
import json
import uuid
import subprocess
import shutil

from uuid import UUID
from pathlib import Path

import httpx

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

from app.services.chunk_processor import process_video_chunks


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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# STORAGE CONFIGURATION
# ==========================================

UPLOAD_DIR = Path("storage/uploads")
THUMBNAIL_DIR = Path("storage/thumbnails")
ANALYSIS_DIR = Path("storage/analysis")
JOBS_DIR = Path("storage/jobs")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm"
}

CHUNK_SIZE = 1024 * 1024


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


# ==========================================
# VIDEO SCENE DETECTION
# ==========================================

def detect_video_scenes(video_path: Path):

    video = open_video(str(video_path))

    scene_manager = SceneManager()

    scene_manager.add_detector(
        ContentDetector(
            threshold=27.0,
            min_scene_len=15
        )
    )

    scene_manager.detect_scenes(
        video=video,
        show_progress=False
    )

    scene_list = scene_manager.get_scene_list()

    scenes = []

    for index, (start_time, end_time) in enumerate(
        scene_list,
        start=1
    ):

        start_seconds = start_time.get_seconds()
        end_seconds = end_time.get_seconds()

        scenes.append({
            "scene_number": index,
            "start_seconds": round(start_seconds, 3),
            "end_seconds": round(end_seconds, 3),
            "duration_seconds": round(
                end_seconds - start_seconds,
                3
            )
        })

    return scenes


# ==========================================
# ANALYZE VIDEO SCENES API
# ==========================================

@app.post("/api/videos/{video_id}/scenes")
async def analyze_video_scenes(video_id: str):

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

    try:
        scenes = await asyncio.to_thread(
            detect_video_scenes,
            video_path
        )

        result = {
            "video_id": safe_id,
            "total_scenes": len(scenes),
            "scenes": scenes,
            "status": "scene_detection_completed"
        }

        result_path = ANALYSIS_DIR / f"{safe_id}_scenes.json"

        with open(result_path, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4)

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Scene detection failed: {str(error)}"
        )


# ==========================================
# BACKGROUND VIDEO CHUNK PROCESSING
# ==========================================

@app.post("/api/videos/{video_id}/process-chunks")
async def process_video_in_chunks(
    video_id: str,
    background_tasks: BackgroundTasks
):

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

    job_dir = JOBS_DIR / safe_id
    job_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = job_dir / "checkpoint.json"

    if checkpoint_path.exists():

        try:
            checkpoint = json.loads(
                checkpoint_path.read_text(encoding="utf-8")
            )

        except (json.JSONDecodeError, OSError):
            raise HTTPException(
                status_code=500,
                detail="Processing checkpoint is corrupted or unreadable"
            )

        if checkpoint.get("status") == "processing":
            raise HTTPException(
                status_code=409,
                detail="This video is already processing"
            )

        if checkpoint.get("status") == "completed":
            return {
                "video_id": safe_id,
                "status": "completed",
                "message": "Video has already been processed"
            }

    else:
        checkpoint = {
            "video_id": safe_id,
            "completed_chunks": [],
            "scenes": [],
            "progress_percent": 0,
            "status": "queued"
        }

    checkpoint["status"] = "processing"

    checkpoint_path.write_text(
        json.dumps(checkpoint, indent=4),
        encoding="utf-8"
    )

    background_tasks.add_task(
        process_video_chunks,
        safe_id,
        matches[0]
    )

    return {
        "video_id": safe_id,
        "status": "processing",
        "message": "Video processing started in background"
    }


# ==========================================
# VIDEO PROCESSING STATUS
# ==========================================

@app.get("/api/videos/{video_id}/processing-status")
async def get_processing_status(video_id: str):

    try:
        safe_id = str(UUID(video_id))

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid video ID"
        )

    checkpoint_path = (
        JOBS_DIR / safe_id / "checkpoint.json"
    )

    if not checkpoint_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processing job not found"
        )

    try:
        checkpoint = json.loads(
            checkpoint_path.read_text(encoding="utf-8")
        )

    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Processing checkpoint is corrupted or unreadable"
        )

    completed_chunks = checkpoint.get("completed_chunks", [])
    total_chunks = checkpoint.get("total_chunks", 0)

    progress = (
        round(len(completed_chunks) / total_chunks * 100, 2)
        if total_chunks > 0
        else checkpoint.get("progress_percent", 0)
    )

    return {
        "video_id": safe_id,
        "status": checkpoint.get("status", "unknown"),
        "completed_chunks": len(completed_chunks),
        "total_chunks": total_chunks,
        "progress_percent": progress,
        "total_scenes": len(checkpoint.get("scenes", []))
    }
