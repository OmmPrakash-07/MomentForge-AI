
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(
    title="MomentForge AI",
    description="AI-powered automatic video clipping platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to MomentForge AI",
        "status": "running"
    }


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "application": "MomentForge AI",
        "version": "0.1.0"
    }


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
