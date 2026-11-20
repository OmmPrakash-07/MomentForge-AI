
const API_BASE_URL = "http://127.0.0.1:8000";

export interface VideoUploadResponse {
  message: string;
  video_id: string;
  filename: string;
  stored_filename: string;
  size_bytes: number;
  size_mb: number;
  status: string;
}

export interface VideoMetadata {
  video_id: string;
  filename: string;
  duration_seconds: number;
  duration_formatted: string;
  resolution: {
    width: number;
    height: number;
  };
  video_codec: string;
  audio_codec: string | null;
  fps: string;
  bitrate: string;
  size_bytes: number;
  status: string;
}

export interface ThumbnailResponse {
  video_id: string;
  thumbnail: string;
  status: string;
}

export async function uploadVideo(
  file: File,
  onProgress?: (progress: number) => void
): Promise<VideoUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // XMLHttpRequest provides upload progress events.
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open("POST", `${API_BASE_URL}/api/videos/upload`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed: ${xhr.responseText}`));
      }
    };

    xhr.onerror = () => reject(new Error("Could not connect to backend"));

    xhr.send(formData);
  });
}

export async function getVideoMetadata(
  videoId: string
): Promise<VideoMetadata> {
  const response = await fetch(
    `${API_BASE_URL}/api/videos/${videoId}/metadata`
  );

  if (!response.ok) {
    throw new Error("Could not extract video metadata");
  }

  return response.json();
}

export async function generateThumbnail(
  videoId: string
): Promise<ThumbnailResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/videos/${videoId}/thumbnail`,
    { method: "POST" }
  );

  if (!response.ok) {
    throw new Error("Thumbnail generation failed");
  }

  return response.json();
}

export function getThumbnailUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
