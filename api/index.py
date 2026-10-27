import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, AuthenticationError, RateLimitError, BadRequestError, APIError

app = FastAPI(
    title="OpenAI Speech-to-Text API",
    description="Vercel Serverless Function for OpenAI Speech-to-Text transcription",
    version="1.0.0"
)

# Enable CORS for external callers or local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {
    "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "flac"
}

@app.get("/api/health")
async def health_check():
    """Health check endpoint to test connection and check if server key is configured."""
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "status": "healthy",
        "has_server_api_key": has_key,
        "supported_models": [
            "whisper-1",
            "gpt-4o-mini-transcribe",
            "gpt-4o-transcribe"
        ]
    }

@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    api_key: Optional[str] = Form(None)
):
    """
    Transcribes uploaded audio file using OpenAI Audio API.
    """
    # 1. Resolve API key
    resolved_key = (api_key.strip() if api_key and api_key.strip() else None) or os.environ.get("OPENAI_API_KEY")
    if not resolved_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "OpenAI API key is missing. Please set OPENAI_API_KEY in your "
                "Vercel project environment variables or enter it in the UI."
            )
        )

    # 2. Validate filename / extension
    filename = file.filename or "audio.mp3"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 3. Read audio bytes
    try:
        audio_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Vercel Hobby serverless max request body is ~4.5 MB; warn if file is unexpectedly large
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds OpenAI's 25 MB limit. Please upload a smaller audio file."
        )

    # 4. Initialize client and call OpenAI
    try:
        client = OpenAI(api_key=resolved_key)
        content_type = file.content_type or f"audio/{ext if ext else 'mpeg'}"
        
        response = client.audio.transcriptions.create(
            model=model,
            file=(filename, audio_bytes, content_type)
        )

        return {
            "success": True,
            "text": response.text,
            "model": model,
            "filename": filename
        }

    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed. The provided OpenAI API key is invalid or expired."
        )
    except RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="OpenAI Rate limit reached or quota exceeded. Please check your OpenAI billing/quota."
        )
    except BadRequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"OpenAI bad request error: {getattr(e, 'message', str(e))}"
        )
    except APIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API error: {getattr(e, 'message', str(e))}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

# Mount public directory for local testing
public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.isdir(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="static")
