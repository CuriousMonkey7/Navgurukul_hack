# AI Interview System

An automated technical interviewer that watches your screen and listens to your voice to conduct real-time project interviews.

## What it does

The system captures your screen and voice during a presentation, then uses OCR to read visible content and Whisper to transcribe speech. It generates contextual questions based on what you show and say, maintaining conversation flow throughout the interview. At the end, it evaluates your performance across technical depth, clarity, originality, and implementation understanding.

## Requirements

You need Python 3.8 or later, Tesseract OCR, FFmpeg, and Ollama installed on your system.

Install Tesseract:
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

Install Ollama from https://ollama.ai and pull the model:
```bash
ollama pull qwen2.5:3b
```

## Setup

Install the Python dependencies:
```bash
pip install -r requirements.txt
```

## Running

Start the server:
```bash
python server.py
```

Open http://localhost:8000 in your browser. Click "Start Interview" and grant permissions for screen sharing and microphone. Present your project normally, speaking about what you're showing. The AI will ask questions every few seconds. When done, click "End Interview & Get Feedback" to see your scores.

## How it works

The frontend captures screen frames and audio chunks via WebSocket. The server uses Silero VAD to filter silence, Whisper to transcribe speech, Tesseract to extract text from screens, and a local LLM through Ollama to generate questions and evaluate responses. The interview maintains conversational context by referencing previous exchanges.

## Files

- `server.py` - FastAPI server handling WebSocket connections
- `interview_manager.py` - Interview logic and scoring system
- `vad.py` - Voice activity detection
- `index.html` - Web interface
- `requirements.txt` - Dependencies

---

## How It Works

```
┌─────────────┐
│   Browser   │ Screen + Audio Capture (every 4s)
└──────┬──────┘
       │ WebSocket
       ▼
┌─────────────────────────────────────────────┐
│              Server (server.py)              │
│                                              │
│  1. Save image (JPG) & audio (WebM→WAV)     │
│  2. Voice Activity Detection (VAD)          │
│  3. Speech-to-Text (Whisper)                │
│  4. OCR (Tesseract)                         │
│  5. Send to Interview Manager               │
└──────┬───────────────────────────────┬──────┘
       │                               │
       ▼                               ▼
┌─────────────────┐         ┌──────────────────┐
│ interview_      │         │   Ollama LLM     │
│ manager.py      │◄────────┤  (qwen2.5:3b)    │
│                 │         │                  │
│ • Maintain      │         │ • Generate       │
│   conversation  │         │   questions      │
│ • Generate      │         │ • Evaluate       │
│   questions     │         │   responses      │
│ • Score         │         └──────────────────┘
│   candidate     │
└─────────────────┘
```

---

