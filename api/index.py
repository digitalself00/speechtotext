import os
import json
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, AuthenticationError, RateLimitError, BadRequestError, APIError

app = FastAPI(
    title="OpenAI Speech-to-Text & Task Extraction API",
    description="Vercel Serverless API for audio transcription and structured task extraction using OpenAI GPT-5 Mini",
    version="1.1.0"
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

SYSTEM_TASK_PROMPT = """You are an expert AI task extractor.
Analyze the transcribed speech and extract a structured task item.
Respond ONLY with a valid JSON object matching the following structure:
{
  "title": "<Concise, clear task title>",
  "description": "<Detailed description of what needs to be done, including context and key details>",
  "start_time": "<Scheduled start time or date if mentioned (e.g. 'Tomorrow at 10:00 AM', '2026-10-28 09:00'), otherwise 'Not specified'>",
  "end_time": "<Deadline or completion time if mentioned (e.g. 'Friday 5:00 PM', '2026-10-31'), otherwise 'Not specified'>",
  "priority": "<Priority level based on urgency cues: 'Low', 'Medium', 'High', or 'Urgent'>"
}

Do not include any explanation or markdown backticks outside the JSON. Return strictly a raw JSON object."""

def resolve_api_key(
    form_key: Optional[str] = None,
    authorization: Optional[str] = None,
    x_api_key: Optional[str] = None,
    x_openai_key: Optional[str] = None
) -> str:
    """Helper to resolve OpenAI API key from form field, headers, or environment."""
    key = None
    if form_key and form_key.strip():
        key = form_key.strip()
    elif x_api_key and x_api_key.strip():
        key = x_api_key.strip()
    elif x_openai_key and x_openai_key.strip():
        key = x_openai_key.strip()
    elif authorization and authorization.strip():
        auth = authorization.strip()
        if auth.lower().startswith("bearer "):
            key = auth[7:].strip()
        else:
            key = auth
    else:
        key = os.environ.get("OPENAI_API_KEY")

    if not key:
        raise HTTPException(
            status_code=400,
            detail=(
                "OpenAI API key is missing. Please provide it via 'api_key' form field, "
                "'Authorization: Bearer <key>' header, or set OPENAI_API_KEY in Vercel environment variables."
            )
        )
    return key


async def validate_and_read_audio(file: UploadFile) -> tuple[str, bytes, str]:
    """Validates audio file extension and size, returning (filename, bytes, content_type)."""
    filename = file.filename or "audio.mp3"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    try:
        audio_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds OpenAI's 25 MB limit. Please provide a smaller audio file."
        )

    content_type = file.content_type or f"audio/{ext if ext else 'mpeg'}"
    return filename, audio_bytes, content_type


@app.get("/api/health")
async def health_check():
    """Health check endpoint to test connection and check if server key is configured."""
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "status": "healthy",
        "has_server_api_key": has_key,
        "endpoints": [
            "/api/speech-to-task",
            "/api/extract-task",
            "/api/transcribe"
        ],
        "default_llm_model": "gpt-5-mini",
        "transcription_model": "whisper-1"
    }


@app.post("/api/speech-to-task")
@app.post("/api/extract-task")
async def speech_to_task(
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
    model: str = Form("gpt-5-mini"),
    transcription_model: str = Form("whisper-1"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    x_openai_key: Optional[str] = Header(None)
):
    """
    Exposed API:
    Input: OpenAI Key and Speech file (plus optional model selection)
    Process: Speech-to-Text transcription -> OpenAI GPT-5 Mini task extraction
    Output: JSON with title, description, strat_time (start_time), end_time, priority
    """
    resolved_key = resolve_api_key(api_key, authorization, x_api_key, x_openai_key)
    filename, audio_bytes, content_type = await validate_and_read_audio(file)

    try:
        client = OpenAI(api_key=resolved_key)

        # Step 1: Transcribe Speech to Text
        stt_response = client.audio.transcriptions.create(
            model=transcription_model,
            file=(filename, audio_bytes, content_type)
        )
        transcribed_text = stt_response.text

        if not transcribed_text or not transcribed_text.strip():
            return {
                "title": "No speech detected",
                "description": "Audio file contained no recognizable speech.",
                "start_time": "Not specified",
                "strat_time": "Not specified",
                "end_time": "Not specified",
                "priority": "Low",
                "raw_transcription": ""
            }

        # Step 2: Extract Task with OpenAI GPT model (default: gpt-5-mini)
        llm_model = model.strip() if model and model.strip() else "gpt-5-mini"
        messages = [
            {"role": "system", "content": SYSTEM_TASK_PROMPT},
            {"role": "user", "content": f"Transcribed speech text:\n\"\"\"{transcribed_text}\"\"\""}
        ]

        try:
            completion = client.chat.completions.create(
                model=llm_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2
            )
        except Exception as e:
            err_str = str(e).lower()
            # If gpt-5-mini is not yet accessible on user account, gracefully fall back to gpt-4o-mini
            if "not found" in err_str or "does not exist" in err_str or "model" in err_str:
                llm_model = "gpt-4o-mini"
                completion = client.chat.completions.create(
                    model=llm_model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
            else:
                raise

        # Step 3: Parse and validate JSON output
        raw_json_str = completion.choices[0].message.content or "{}"
        try:
            task_data = json.loads(raw_json_str)
        except Exception:
            task_data = {}

        title = task_data.get("title") or "Untitled Task"
        description = task_data.get("description") or transcribed_text
        start_time = task_data.get("start_time") or task_data.get("strat_time") or "Not specified"
        end_time = task_data.get("end_time") or "Not specified"
        priority = task_data.get("priority") or "Medium"

        # Return exact JSON requested by user:
        # task title, description, strat time, end time, priority
        return {
            "title": title,
            "description": description,
            "start_time": start_time,
            "strat_time": start_time,  # included for exact matching with user's prompt key
            "end_time": end_time,
            "priority": priority,
            "raw_transcription": transcribed_text,
            "model_used": llm_model
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
            detail=f"OpenAI bad request: {getattr(e, 'message', str(e))}"
        )
    except APIError as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API error: {getattr(e, 'message', str(e))}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Task extraction failed: {str(e)}"
        )


@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    api_key: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """Simple audio-to-text transcription endpoint."""
    resolved_key = resolve_api_key(api_key, authorization, x_api_key)
    filename, audio_bytes, content_type = await validate_and_read_audio(file)

    try:
        client = OpenAI(api_key=resolved_key)
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
        raise HTTPException(status_code=401, detail="Authentication failed: Invalid OpenAI API key.")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit or quota exceeded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# Mount public directory for local testing
public_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
if os.path.isdir(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="static")
