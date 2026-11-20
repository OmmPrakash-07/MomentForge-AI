
from pathlib import Path

# Each chunk will cover 10 minutes.
CHUNK_DURATION_SECONDS = 600

# Processing directories
BASE_DIR = Path(__file__).resolve().parents[2]

STORAGE_DIR = BASE_DIR / "storage"

UPLOAD_DIR = STORAGE_DIR / "uploads"
CHUNKS_DIR = STORAGE_DIR / "chunks"
JOBS_DIR = STORAGE_DIR / "jobs"
ANALYSIS_DIR = STORAGE_DIR / "analysis"

# Scene detection settings
SCENE_THRESHOLD = 27.0
MIN_SCENE_LENGTH = 15

# Create directories automatically
for directory in [
    UPLOAD_DIR,
    CHUNKS_DIR,
    JOBS_DIR,
    ANALYSIS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
