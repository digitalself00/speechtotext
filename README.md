# 🎙️ OpenAI Speech-to-Text (Vercel Ready)

A modern, fast, serverless Speech-to-Text web application powered by **OpenAI Audio Transcriptions API** (Whisper) and configured for **1-click deployment on Vercel**.

---

## ⚡ Why This Architecture for Vercel?

The original application was built with **Streamlit** (`speechToText.py`). However, **Streamlit cannot run natively on Vercel** because:
- Streamlit requires a persistent, long-running Python server with continuous WebSocket connections.
- Vercel is a **Serverless** platform designed for stateless request-response functions.

### ✨ What We Built for Vercel:
- **Backend (`api/index.py`)**: A lightweight, fast Python Serverless Function using **FastAPI** that interacts with the OpenAI Audio API.
- **Frontend (`public/index.html`)**: A responsive UI built with Tailwind CSS that supports:
  - 📁 File upload with drag & drop (MP3, WAV, M4A, WEBM, FLAC, OGG, MP4).
  - 🎙️ Live microphone recording directly in the browser.
  - 🎧 Audio playback & preview before transcription.
  - ⚙️ Model selection (`whisper-1`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`).
  - 📋 One-click copy & `.txt` download of transcriptions.
  - 🔑 Flexible API key support (configured via Vercel Environment Variables or directly in the UI).
- **Streamlit Version Preserved**: The original `speechToText.py` is preserved if you still want to run it locally or deploy to Streamlit Community Cloud.

---

## 🚀 How to Deploy on Vercel

### Method 1: Deploy via GitHub (Recommended)

1. **Commit and Push your changes to GitHub**:
   ```bash
   git add .
   git commit -m "Configure project for Vercel deployment"
   git push origin main
   ```

2. **Import into Vercel**:
   - Go to [vercel.com](https://vercel.com) and log in.
   - Click **"Add New..."** > **"Project"**.
   - Select your repository: `digitalself00/speechtotext`.
   - Vercel will automatically detect `vercel.json` and `api/index.py`.

3. **Configure Environment Variable**:
   - In the **Environment Variables** section before deploying:
     - **Name**: `OPENAI_API_KEY`
     - **Value**: `sk-...` (your OpenAI API key)
   - Click **Add**.

4. **Deploy**:
   - Click **Deploy**.
   - Your speech-to-text app will be live on `https://your-project.vercel.app` in under 1 minute!

---

### Method 2: Deploy via Vercel CLI

If you have Node.js installed, you can deploy directly from your terminal:

1. Install the Vercel CLI globally:
   ```bash
   npm install -g vercel
   ```

2. Link and deploy your project:
   ```bash
   vercel
   ```
   Follow the prompts to connect your Vercel account.

3. Add your OpenAI API key:
   ```bash
   vercel env add OPENAI_API_KEY
   ```
   Paste your secret key when prompted.

4. Deploy to production:
   ```bash
   vercel --prod
   ```

---

## 💻 Running Locally

### Option A: Run the Vercel Web App (FastAPI + HTML)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set your OpenAI API key in your environment:
   ```powershell
   # Windows PowerShell:
   $env:OPENAI_API_KEY="sk-..."
   ```

3. Start the local server:
   ```bash
   uvicorn api.index:app --reload
   ```

4. Open your browser at `http://localhost:8000`.

---

### Option B: Run the Original Streamlit App

If you prefer the original Streamlit interface locally:

```bash
pip install streamlit openai
$env:OPENAI_API_KEY="sk-..."
streamlit run speechToText.py
```

---

## 📁 Project Structure

```text
speechtotext/
├── api/
│   └── index.py             # Vercel Python Serverless Function (FastAPI)
├── public/
│   └── index.html           # Modern responsive web frontend
├── speechToText.py          # Original Streamlit application
├── vercel.json              # Vercel routing configuration
├── requirements.txt         # Python dependencies for Vercel
├── .env.example             # Template for environment variables
├── .gitignore               # Git ignore rules
└── README.md                # Deployment and setup guide
```

---

## 🛡️ Audio File Limits on Vercel

- **Vercel Serverless Function payload limit**: 4.5 MB on Hobby (free) plan, 25 MB on Pro plan.
- **OpenAI Audio API limit**: Up to 25 MB.
- Audio recordings and common formats (MP3, WAV, M4A, WEBM) are supported.
