# MomentForge AI

### Turn Hours into Viral Moments.

**MomentForge AI** is an intelligent, local-first video clipping platform designed to transform long-form videos into engaging short-form content such as YouTube Shorts and Instagram Reels.

The platform is being developed to analyze long videos, detect scenes, identify interesting moments, and automatically generate short clips using locally running AI models and video-processing tools.

---

## Project Overview

MomentForge AI aims to simplify video editing by automating the process of finding interesting moments in long recordings.

It is designed to support multiple types of content:

- Gaming and gameplay recordings
- Podcasts and interviews
- Livestreams
- Educational videos
- Tutorials and presentations
- Other long-form video content

The application supports local video uploads and is being designed for YouTube URL processing.

## Key Features

### Implemented Features

- **Video Upload:** Upload local video files through the application.
- **Video Metadata Extraction:** Extract duration, resolution, FPS, codecs, and file size using FFprobe.
- **Thumbnail Generation:** Generate video thumbnails using FFmpeg.
- **Scene Detection:** Detect visual scene boundaries using PySceneDetect.
- **Chunk-Based Processing:** Divide long videos into manageable 10-minute chunks.
- **Checkpoint System:** Save completed chunks and scene analysis results in JSON files.
- **Background Processing:** Execute video processing through FastAPI background tasks.
- **Processing Status API:** Retrieve job status, completed chunks, total chunks, and progress percentage.
- **Duplicate Processing Protection:** Avoid reprocessing videos that already have a completed checkpoint.

### Planned Features

- AI-powered interesting moment detection
- Audio transcription using Faster-Whisper
- AI moment ranking and scoring
- Automatic 9:16 vertical video generation
- Animated captions and subtitles
- Automatic clip titles and descriptions
- Hashtag generation
- Thumbnail generation for individual clips
- Pause and resume processing
- Live frontend processing progress
- YouTube URL processing
- Video project and clip management

---

## Tech Stack

| Category | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Video Processing | FFmpeg, FFprobe |
| Scene Detection | PySceneDetect, OpenCV |
| Background Processing | FastAPI BackgroundTasks, asyncio |
| Local AI Runtime | Ollama |
| AI Model | GPT-OSS 20B (installed for local text reasoning) |
| Data Storage | JSON-based processing checkpoints |
| Development Tools | VS Code, Git, GitHub |

## System Architecture

```text
MomentForge-AI/
│
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   │   └── videoService.ts
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── index.css
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── processing_config.py
│   │   │   └── chunk_processor.py
│   │   ├── __init__.py
│   │   └── main.py
│   │
│   ├── storage/
│   │   ├── uploads/
│   │   ├── thumbnails/
│   │   ├── analysis/
│   │   ├── chunks/
│   │   └── jobs/
│   │
│   └── .venv/
│
├── docs/
├── scripts/
├── .gitignore
└── README.md
```

Generated video files, chunks, thumbnails, and processing data are stored locally and should not be committed to GitHub.

---

## Installation and Setup

### Prerequisites

Install the following software:

- Python 3.11+
- Node.js and npm
- FFmpeg and FFprobe
- Git
- Ollama (for local AI model integration)

### 1. Clone the repository

```bash
git clone https://github.com/OmmPrakash-07/MomentForge-AI.git

cd MomentForge-AI
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
py -3.11 -m venv .venv
```

Activate the environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install fastapi "uvicorn[standard]" httpx python-multipart
pip install "scenedetect[opencv]"
```

Start the backend server:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

## API Endpoints

The backend currently provides the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Backend welcome message |
| GET | `/api/health` | Backend health check |
| GET | `/api/ollama/status` | Check Ollama connection |
| POST | `/api/videos/upload` | Upload a local video |
| GET | `/api/videos/{video_id}/metadata` | Extract video metadata |
| POST | `/api/videos/{video_id}/thumbnail` | Generate thumbnail |
| GET | `/api/videos/{video_id}/thumbnail/file` | Retrieve generated thumbnail |
| POST | `/api/videos/{video_id}/scenes` | Detect video scenes |
| POST | `/api/videos/{video_id}/process-chunks` | Start background chunk processing |
| GET | `/api/videos/{video_id}/processing-status` | Retrieve processing progress |

All API endpoints can be tested through the FastAPI Swagger interface.

---

## Long Video Processing

MomentForge AI uses a chunk-based architecture to handle lengthy video recordings without loading the entire video into memory.

### Processing Workflow

```text
Original Video
      |
      v
Video Metadata Extraction
      |
      v
Video Duration Calculation
      |
      v
Divide Video into 10-Minute Chunks
      |
      v
Extract Video Chunks using FFmpeg
      |
      v
Detect Scenes using PySceneDetect
      |
      v
Save Scene Data and Checkpoints
      |
      v
Update Processing Progress
      |
      v
Combine Scene Results
      |
      v
Completed Processing Job
```

### Checkpoint Storage

Processing information is stored locally:

```text
backend/storage/jobs/
    └── VIDEO_ID/
        └── checkpoint.json
```

The checkpoint stores:

- Video ID
- Total video duration
- Chunk duration
- Completed chunk numbers
- Detected scenes
- Processing progress
- Job status

Completed chunks can be skipped when processing is run again.

**Current limitation:** Checkpoint-based recovery is implemented at completed-chunk boundaries. An interrupted active chunk may need to be processed again. Durable job queues and full pause/resume controls are planned improvements.

---

## Current Development Progress

| Milestone | Description | Status |
|---|---|---|
| 1 | Project structure and initial setup | Completed |
| 2 | FastAPI backend and video upload | Completed |
| 3 | Video metadata and thumbnail generation | Completed |
| 4 | Frontend and backend integration | Completed |
| 5 | Video scene detection | Completed |
| 6 | Long video chunk processing | Completed |
| 7 | Background jobs and processing status | Completed |
| 8 | Frontend live progress integration | Planned |
| 9 | Audio transcription | Planned |
| 10 | AI-powered moment detection | Planned |
| 11 | Automatic Shorts generation | Planned |
| 12 | Captions and metadata generation | Planned |

---

## Local AI Philosophy

MomentForge AI is being developed with a local-first approach.

The goal is to use locally available hardware and open-source tools for video processing and AI inference, reducing dependence on paid cloud APIs.

The installed Ollama model is available for local text reasoning. Vision-based analysis and transcription integration are still under development.

---

## Future Goals

- Fully automated video clipping
- Support for 10–20 hour recordings
- Intelligent scene and moment analysis
- Automatic short-form video creation
- GPU-accelerated video processing
- Local AI-powered content generation
- Background job recovery and monitoring
- A complete creator-focused dashboard

---

## Repository

GitHub: https://github.com/OmmPrakash-07/MomentForge-AI

## License

License to be determined.

---

**MomentForge AI — Turn Hours into Viral Moments.**

*Built for creators, powered locally.*