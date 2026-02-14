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

## Configuration

You can adjust settings in the source files:

Speech detection threshold in [server.py](server.py):
```python
MIN_SPEECH_DURATION = 0.5
```

LLM model in [interview_manager.py](interview_manager.py):
```python
MODEL = "qwen2.5:3b"
```

Capture frequency in [index.html](index.html):
```javascript
}, 4000);  // milliseconds
```

---

## 🐛 Troubleshooting

### "No valid speech detected"
- Speak louder or closer to microphone
- Check microphone permissions
- Adjust `MIN_SPEECH_DURATION` in server.py

### OCR not extracting text
- Ensure text is clearly visible on screen
- Use higher resolution screen share
- Check if Tesseract is installed correctly

### Ollama connection error
- Verify Ollama is running: `ollama list`
- Ensure model is downloaded: `ollama pull qwen2.5:3b`
- Restart Ollama service

### WebSocket connection failed
- Check if server is running on port 8000
- Ensure no firewall blocking localhost
- Try restarting the server

### Audio conversion fails
- Install FFmpeg: `brew install ffmpeg` (macOS)
- Check FFmpeg is in PATH: `ffmpeg -version`

---

## 📊 How It Works

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

## 🎯 Assignment Compliance Checklist

- [x] **OCR**: Extracts content from screens ✅
- [x] **STT**: Transcribes student speech ✅
- [x] **Content Analysis**: Analyzes UI, code, slides, diagrams ✅
- [x] **Context-Aware Questions**: Generated from extracted content ✅
- [x] **Follow-up Questions**: Based on responses and screen content ✅
- [x] **Technical Depth Scoring**: 1-10 scale ✅
- [x] **Clarity Scoring**: 1-10 scale ✅
- [x] **Originality Scoring**: 1-10 scale ✅
- [x] **Implementation Understanding Scoring**: 1-10 scale ✅
- [x] **Live Demo**: Real-time interview capability ✅
- [x] **Feedback Report**: Comprehensive score + feedback ✅

---

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Video recording of interview sessions
- [ ] Export scorecard as PDF
- [ ] Support for multiple simultaneous interviews
- [ ] Integration with GitHub for code analysis
- [ ] Sentiment analysis of responses
- [ ] Real-time hints for nervous students

---

## 📝 License

This project is created for NavGurukul Challenge 1.

---

## 👤 Author

Built for NavGurukul AI-Driven Automated Interviewer Challenge

---

## 🙏 Acknowledgments

- **Whisper AI** by OpenAI for speech recognition
- **Silero VAD** for voice activity detection
- **Tesseract OCR** for text extraction
- **Ollama** for local LLM inference
- **FastAPI** for WebSocket server
