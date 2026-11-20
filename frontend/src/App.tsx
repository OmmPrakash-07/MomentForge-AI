
import { useRef, useState } from "react";
import "./App.css";

type InputMode = "youtube" | "upload";

function App() {
  const [mode, setMode] = useState<InputMode>("youtube");
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [clipDuration, setClipDuration] = useState("30");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file?: File) => {
    if (!file) return;

    const allowed = ["video/mp4", "video/x-matroska", "video/quicktime"];

    if (!allowed.includes(file.type)) {
      alert("Please select an MP4, MKV or MOV video.");
      return;
    }

    setSelectedFile(file);
  };

  const handleStart = () => {
    if (mode === "youtube" && !youtubeUrl.trim()) {
      alert("Please enter a YouTube URL.");
      return;
    }

    if (mode === "upload" && !selectedFile) {
      alert("Please select a video first.");
      return;
    }

    alert("Dashboard is ready! Backend processing will be connected next.");
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
              >
                ▶ &nbsp; YouTube URL
              </button>
              <button
                className={mode === "upload" ? "tab active-tab" : "tab"}
                onClick={() => setMode("upload")}
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
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="upload-icon">↑</div>
                  <h3>
                    {selectedFile
                      ? selectedFile.name
                      : "Drop your video here"}
                  </h3>
                  <p>Or click to browse files from your computer</p>
                  <span>MP4 · MKV · MOV</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp4,.mkv,.mov,video/mp4,video/x-matroska,video/quicktime"
                    hidden
                    onChange={(e) => handleFile(e.target.files?.[0])}
                  />
                </div>
                {selectedFile && (
                  <button
                    className="remove-file"
                    onClick={() => setSelectedFile(null)}
                  >
                    Remove selected video
                  </button>
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

            <button className="start-button" onClick={handleStart}>
              ✦ &nbsp; Start AI Clipping &nbsp; →
            </button>
            <p className="privacy-note">
              Your local video files stay on your computer.
            </p>
          </div>

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
