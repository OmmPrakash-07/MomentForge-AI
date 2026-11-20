
import { useRef, useState } from "react";
import "./App.css";
import {
  uploadVideo,
  getVideoMetadata,
  generateThumbnail,
  getThumbnailUrl,
  type VideoUploadResponse,
  type VideoMetadata,
} from "./services/videoService";

type InputMode = "youtube" | "upload";

function App() {
  const [mode, setMode] = useState<InputMode>("youtube");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [clipDuration, setClipDuration] = useState("30");

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] =
    useState<VideoUploadResponse | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file?: File) => {
    if (!file) return;

    const allowedExtensions = [".mp4", ".mkv", ".mov", ".avi", ".webm"];
    const extension = file.name
      .slice(file.name.lastIndexOf("."))
      .toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setError("Please select MP4, MKV, MOV, AVI or WEBM video.");
      return;
    }

    setSelectedFile(file);
    setUploadResult(null);
    setMetadata(null);
    setThumbnailUrl("");
    setUploadProgress(0);
    setError("");
    setSuccess("");
  };

  const handleStart = async () => {
    setError("");
    setSuccess("");

    if (mode === "youtube") {
      if (!youtubeUrl.trim()) {
        setError("Please enter a YouTube URL.");
        return;
      }

      setError("YouTube URL processing will be added in a later milestone.");
      return;
    }

    if (!selectedFile) {
      setError("Please select a video first.");
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress(0);
      setUploadResult(null);
      setMetadata(null);
      setThumbnailUrl("");

      // 1. Upload video to FastAPI backend
      const uploaded = await uploadVideo(
        selectedFile,
        (progress) => setUploadProgress(progress)
      );

      setUploadResult(uploaded);
      setUploadProgress(100);

      // 2. Extract metadata and generate thumbnail
      const [metadataResult, thumbnailResult] = await Promise.all([
        getVideoMetadata(uploaded.video_id),
        generateThumbnail(uploaded.video_id),
      ]);

      setMetadata(metadataResult);
      setThumbnailUrl(getThumbnailUrl(thumbnailResult.thumbnail));
      setSuccess("Video uploaded and analyzed successfully!");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">M</div>
          <div>
            <h2>MomentForge</h2>
            <span>AI CLIPPING STUDIO</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <nav>
          <a className="nav-item active">◈ &nbsp; Dashboard</a>
          <a className="nav-item">▣ &nbsp; My Projects</a>
          <a className="nav-item">✂ &nbsp; Generated Clips</a>
          <a className="nav-item">◷ &nbsp; Processing History</a>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-card">
            <div className="system-title">
              <span className="online-dot" />
              Local AI Engine
            </div>
            <p>Ollama connection</p>
            <strong>Ready to connect</strong>
            <span className="system-note">Live status integration coming next</span>
          </div>
          <div className="profile">
            <div className="avatar">O</div>
            <div>
              <strong>My Workspace</strong>
              <span>Local environment</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace /</span> Dashboard
          </div>
          <div className="top-status">
            <span className="online-dot" />
            Local processing environment
          </div>
        </header>

        <section className="content">
          <div className="welcome">
            <div>
              <div className="eyebrow">YOUR AI VIDEO WORKSPACE</div>
              <h1>Turn hours into <span>moments.</span></h1>
              <p>
                Transform long videos into engaging short-form content
                using your local AI engine.
              </p>
            </div>
            <div className="welcome-icon">✂</div>
          </div>

          <div className="section-heading">
            <div>
              <h2>Create a new project</h2>
              <p>Choose how you want to import your video.</p>
            </div>
            <span className="step-label">STEP 01 / INPUT</span>
          </div>

          <div className="workspace-card">
            <div className="tabs">
              <button
                className={mode === "youtube" ? "tab active-tab" : "tab"}
                onClick={() => setMode("youtube")}
                disabled={isUploading}
              >
                ▶ &nbsp; YouTube URL
              </button>
              <button
                className={mode === "upload" ? "tab active-tab" : "tab"}
                onClick={() => setMode("upload")}
                disabled={isUploading}
              >
                ↑ &nbsp; Local Upload
              </button>
            </div>

            {mode === "youtube" ? (
              <div className="input-section">
                <label htmlFor="youtube-url">YouTube video link</label>
                <div className="url-input">
                  <span>▶</span>
                  <input
                    id="youtube-url"
                    type="url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                  />
                </div>
                <p className="helper">
                  Paste a video URL you own or are authorized to process.
                </p>
              </div>
            ) : (
              <div className="input-section">
                <label>Upload your video</label>
                <div
                  className="dropzone"
                  onClick={() => !isUploading && fileInputRef.current?.click()}
                >
                  <div className="upload-icon">↑</div>
                  <h3>
                    {selectedFile
                      ? selectedFile.name
                      : "Drop your video here"}
                  </h3>
                  <p>Or click to browse files from your computer</p>
                  <span>MP4 · MKV · MOV · AVI · WEBM</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp4,.mkv,.mov,.avi,.webm"
                    hidden
                    disabled={isUploading}
                    onChange={(e) => handleFile(e.target.files?.[0])}
                  />
                </div>

                {selectedFile && (
                  <div className="selected-file">
                    <span>{selectedFile.name}</span>
                    <span>{formatFileSize(selectedFile.size)}</span>
                    {!isUploading && (
                      <button
                        className="remove-file"
                        onClick={() => {
                          setSelectedFile(null);
                          setUploadResult(null);
                          setMetadata(null);
                          setThumbnailUrl("");
                          setError("");
                          setSuccess("");
                          if (fileInputRef.current) {
                            fileInputRef.current.value = "";
                          }
                        }}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="divider" />

            <div className="settings-heading">
              <div>
                <h3>Clip preferences</h3>
                <p>Choose your initial output settings.</p>
              </div>
              <span className="auto-badge">✦ AI ASSISTED</span>
            </div>

            <div className="settings-grid">
              <div className="setting">
                <label htmlFor="duration">Clip duration</label>
                <select
                  id="duration"
                  value={clipDuration}
                  onChange={(e) => setClipDuration(e.target.value)}
                >
                  <option value="15">15 seconds</option>
                  <option value="30">30 seconds</option>
                  <option value="45">45 seconds</option>
                  <option value="60">60 seconds</option>
                </select>
              </div>

              <div className="setting">
                <label>Output format</label>
                <div className="format-value">9:16 &nbsp; Vertical Shorts</div>
              </div>
            </div>

            {isUploading && (
              <div className="upload-progress">
                <div className="progress-label">
                  <span>Uploading video...</span>
                  <strong>{uploadProgress}%</strong>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {error && <div className="status-message error-message">{error}</div>}
            {success && (
              <div className="status-message success-message">{success}</div>
            )}

            <button
              className="start-button"
              onClick={handleStart}
              disabled={isUploading}
            >
              {isUploading
                ? "Processing video..."
                : "✦  Start AI Clipping  →"}
            </button>

            <p className="privacy-note">
              Your local video files stay on your computer.
            </p>
          </div>

          {uploadResult && (
            <div className="result-card">
              <div className="result-heading">
                <div>
                  <span className="eyebrow">UPLOAD COMPLETE</span>
                  <h2>Video analysis</h2>
                </div>
                <span className="result-status">✓ Uploaded</span>
              </div>

              {thumbnailUrl && (
                <img
                  className="video-thumbnail"
                  src={thumbnailUrl}
                  alt="Uploaded video thumbnail"
                />
              )}

              <h3>{uploadResult.filename}</h3>
              <p className="helper">
                Video ID: {uploadResult.video_id}
              </p>

              {metadata && (
                <div className="metadata-grid">
                  <div className="metadata-item">
                    <span>Duration</span>
                    <strong>{metadata.duration_formatted}</strong>
                  </div>
                  <div className="metadata-item">
                    <span>Resolution</span>
                    <strong>
                      {metadata.resolution.width} × {metadata.resolution.height}
                    </strong>
                  </div>
                  <div className="metadata-item">
                    <span>Frame rate</span>
                    <strong>{metadata.fps} FPS</strong>
                  </div>
                  <div className="metadata-item">
                    <span>Video codec</span>
                    <strong>{metadata.video_codec.toUpperCase()}</strong>
                  </div>
                  <div className="metadata-item">
                    <span>Audio codec</span>
                    <strong>{metadata.audio_codec ?? "No audio stream"}</strong>
                  </div>
                  <div className="metadata-item">
                    <span>File size</span>
                    <strong>{formatFileSize(metadata.size_bytes)}</strong>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="bottom-grid">
            <div className="info-card">
              <div className="info-icon purple">✦</div>
              <div>
                <h3>Local AI processing</h3>
                <p>Use your own hardware and locally running AI models.</p>
              </div>
            </div>
            <div className="info-card">
              <div className="info-icon blue">◷</div>
              <div>
                <h3>Long video support</h3>
                <p>Designed to process lengthy recordings in manageable chunks.</p>
              </div>
            </div>
          </div>

          <footer>
            MomentForge AI <span>·</span> Built for creators, powered locally.
          </footer>
        </section>
      </main>
    </div>
  );
}

export default App;
