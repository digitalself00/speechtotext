# 🎙️ OpenAI Speech-to-Task & Speech-to-Text (Vercel Serverless)

A modern, serverless AI application and REST API powered by **OpenAI Whisper (Speech-to-Text)** and **OpenAI GPT-5 Mini**, configured for **1-click deployment on Vercel**.

---

## 🌟 Features & API Capabilities

1. **Speech-to-Task API (`POST /api/speech-to-task` or `/api/extract-task`)**:
   - **Input**: Audio speech file + OpenAI API Key (via form field, headers, or environment variable).
   - **Process**: Transcribes speech using Whisper, then uses **OpenAI GPT-5 Mini** (with auto-fallback to `gpt-4o-mini`) to extract structured task information.
   - **Output**: Pure JSON containing:
     - `title`: Task title
     - `description`: Detailed description
     - `start_time` / `strat_time`: Scheduled start time
     - `end_time`: Deadline or end time
     - `priority`: Task priority (`Low`, `Medium`, `High`, `Urgent`)
     - `raw_transcription`: Full speech-to-text transcript
     - `model_used`: LLM model used for extraction

2. **Web Interface (`public/index.html`)**:
   - Modern, responsive Tailwind CSS UI.
   - Live microphone recording directly in browser.
   - Audio drag-and-drop upload (MP3, WAV, M4A, WEBM, FLAC, OGG, MP4).
   - Interactive task cards, priority badges, JSON viewer, and copy buttons.

3. **Simple Transcription API (`POST /api/transcribe`)**:
   - Audio-to-text transcription endpoint.

---

## 📡 API Reference: Speech-to-Task

### Endpoint:
`POST /api/speech-to-task` (or `POST /api/extract-task`)

### Headers:
- `Content-Type: multipart/form-data`
- `Authorization: Bearer <OPENAI_API_KEY>` *(optional if passed in form or configured in Vercel)*

### Form-Data Parameters:
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | Binary File | **Yes** | Audio recording (`.mp3`, `.wav`, `.m4a`, `.webm`, `.ogg`, etc.) |
| `api_key` | String | Optional | OpenAI API key (if not set in `Authorization` header or Vercel env) |
| `model` | String | Optional | Model for extraction (Default: `gpt-5-mini` with auto-fallback to `gpt-4o-mini`) |
| `transcription_model` | String | Optional | Transcription model (Default: `whisper-1`) |

### Example cURL Request:
```bash
curl -X POST "https://<your-project>.vercel.app/api/speech-to-task" \
  -F "file=@meeting_task.mp3" \
  -F "api_key=sk-your-openai-api-key"
```

### Example JSON Response:
```json
{
  "title": "Prepare Q3 Financial Review",
  "description": "Finalize revenue slides and sync with accounting before the team meeting",
  "start_time": "Tomorrow at 9:00 AM",
  "strat_time": "Tomorrow at 9:00 AM",
  "end_time": "Tomorrow at 1:00 PM",
  "priority": "High",
  "raw_transcription": "Hey please make sure to prepare the Q3 financial review slides tomorrow starting at 9 AM and get it done by 1 PM before the team meeting this is high priority.",
  "model_used": "gpt-5-mini"
}
```

### Example Python Request:
```python
import requests

url = "https://<your-project>.vercel.app/api/speech-to-task"

with open("voice_memo.mp3", "rb") as f:
    files = {"file": f}
    data = {"api_key": "sk-your-key"}
    response = requests.post(url, files=files, data=data)
    task = response.json()

print("Title:", task["title"])
print("Description:", task["description"])
print("Start Time:", task["start_time"])
print("End Time:", task["end_time"])
print("Priority:", task["priority"])
```

### Example JavaScript / TypeScript (Fetch):
```javascript
const formData = new FormData();
formData.append('file', audioBlob, 'task.mp3');
formData.append('api_key', 'sk-your-key');

const res = await fetch('/api/speech-to-task', {
  method: 'POST',
  body: formData
});

const task = await res.json();
console.log(task.title, task.priority, task.start_time, task.end_time);
```

---

## 🚀 How to Deploy on Vercel

### Step 1: Push changes to GitHub
```powershell
git add .
git commit -m "Add speech-to-task API with GPT-5 Mini extraction"
git push origin main
```

### Step 2: Deploy in Vercel
1. Log in to [vercel.com](https://vercel.com).
2. Click **"Add New..."** > **"Project"** and select repository `digitalself00/speechtotext`.
3. Under **Environment Variables**, add:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: your OpenAI API key
4. Click **Deploy**.

Your API and web interface will be live immediately!

---

## 💻 Running Locally

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set your API key in environment
$env:OPENAI_API_KEY="sk-..."

# 3. Start local development server
uvicorn api.index:app --reload
```

Visit `http://localhost:8000` to use the interactive app.
