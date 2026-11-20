
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

from app.services.processing_config import (
    CHUNK_DURATION_SECONDS,
    CHUNKS_DIR,
    JOBS_DIR,
    SCENE_THRESHOLD,
    MIN_SCENE_LENGTH,
)


def run_command(command: list[str]):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        timeout=3600,
    )


def get_video_duration(video_path: Path) -> float:
    ffprobe = shutil.which("ffprobe")

    if not ffprobe:
        raise RuntimeError("FFprobe not found")

    result = run_command([
        ffprobe,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ])

    return float(result.stdout.strip())


def save_checkpoint(path: Path, data: dict):
    temporary_path = path.with_suffix(".tmp")

    temporary_path.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8",
    )

    temporary_path.replace(path)


def detect_chunk_scenes(chunk_path: Path, offset: float):
    video = open_video(str(chunk_path))

    manager = SceneManager()
    manager.add_detector(
        ContentDetector(
            threshold=SCENE_THRESHOLD,
            min_scene_len=MIN_SCENE_LENGTH,
        )
    )

    manager.detect_scenes(video=video, show_progress=False)

    scene_list = manager.get_scene_list(start_in_scene=True)

    scenes = []

    for start, end in scene_list:
        start_seconds = offset + start.get_seconds()
        end_seconds = offset + end.get_seconds()

        scenes.append({
            "start_seconds": round(start_seconds, 3),
            "end_seconds": round(end_seconds, 3),
            "duration_seconds": round(
                end_seconds - start_seconds, 3
            ),
        })

    return scenes


def process_video_chunks(video_id: str, video_path: Path):
    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError("FFmpeg not found")

    duration = get_video_duration(video_path)

    job_dir = JOBS_DIR / video_id
    job_dir.mkdir(parents=True, exist_ok=True)

    chunk_dir = CHUNKS_DIR / video_id
    chunk_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = job_dir / "checkpoint.json"

    if checkpoint_path.exists():
        checkpoint = json.loads(
            checkpoint_path.read_text(encoding="utf-8")
        )
    else:
        checkpoint = {
            "video_id": video_id,
            "duration_seconds": duration,
            "chunk_duration_seconds": CHUNK_DURATION_SECONDS,
            "completed_chunks": [],
            "scenes": [],
            "status": "processing",
        }

    total_chunks = int(
        (duration + CHUNK_DURATION_SECONDS - 1)
        // CHUNK_DURATION_SECONDS
    )

    completed = set(checkpoint["completed_chunks"])

    for chunk_number in range(total_chunks):
        if chunk_number in completed:
            continue

        start = chunk_number * CHUNK_DURATION_SECONDS
        chunk_duration = min(
            CHUNK_DURATION_SECONDS,
            duration - start,
        )

        chunk_path = chunk_dir / f"chunk_{chunk_number:05d}.mp4"

        # Extract one chunk. Stream copy avoids full video re-encoding.
        if not chunk_path.exists():
            run_command([
                ffmpeg,
                "-y",
                "-ss", str(start),
                "-i", str(video_path),
                "-t", str(chunk_duration),
                "-map", "0",
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(chunk_path),
            ])

        scenes = detect_chunk_scenes(chunk_path, start)

        for index, scene in enumerate(scenes, start=1):
            scene["scene_number"] = (
                chunk_number * 100000 + index
            )
            scene["chunk_number"] = chunk_number

        checkpoint["scenes"].extend(scenes)
        checkpoint["total_chunks"] = total_chunks

        checkpoint["progress_percent"] = round(
            len(checkpoint["completed_chunks"]) / total_chunks * 100,
            2,
        )

        save_checkpoint(checkpoint_path, checkpoint)

    checkpoint["scenes"].sort(
        key=lambda scene: scene["start_seconds"]
    )

    for index, scene in enumerate(checkpoint["scenes"], start=1):
        scene["scene_number"] = index

    checkpoint["total_chunks"] = total_chunks
    checkpoint["total_scenes"] = len(checkpoint["scenes"])
    checkpoint["progress_percent"] = 100
    checkpoint["status"] = "completed"

    save_checkpoint(checkpoint_path, checkpoint)

    return checkpoint


async def process_video_chunks_async(
    video_id: str,
    video_path: Path,
):
    return await asyncio.to_thread(
        process_video_chunks,
        video_id,
        video_path,
    )
