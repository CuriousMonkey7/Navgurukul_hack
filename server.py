import base64
import uuid
import os
import json
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from interview_manager import InterviewManager

import pytesseract
from PIL import Image

import soundfile as sf
import torch
import numpy as np

from faster_whisper import WhisperModel

from silero_vad import load_silero_vad, get_speech_timestamps

import subprocess

def convert_to_wav(input_path):
    # Always output a .wav file in temp dir with a new uuid
    output_path = f"{TEMP_DIR}/{uuid.uuid4()}.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        output_path
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return output_path
# -----------------------------
# CONFIG
# -----------------------------

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

MIN_SPEECH_DURATION = 0.5  # seconds (reduced from 0.8 for better sensitivity)
WHISPER_MODEL_SIZE = "base"

# -----------------------------
# INIT MODELS
# -----------------------------

print("Loading Whisper...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE)

print("Loading Silero VAD...")
vad_model = load_silero_vad()

print("Loading Interview Manager...")
interviewer = InterviewManager()

print("System ready.")


# -----------------------------
# FASTAPI
# -----------------------------

app = FastAPI()


# -----------------------------
# OCR FUNCTION
# -----------------------------

def extract_text(image_path):

    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()

    except Exception as e:
        print("OCR error:", e)
        return ""


# -----------------------------
# VAD FUNCTION
# -----------------------------

def has_valid_speech(audio_path):

    try:

        wav, sr = sf.read(audio_path)

        if len(wav.shape) > 1:
            wav = wav.mean(axis=1)

        wav = wav.astype("float32")
        print("VAD numpy dtype:", wav.dtype)
        wav = torch.from_numpy(wav).contiguous()
        print("VAD torch dtype:", wav.dtype)

        speech_segments = get_speech_timestamps(
            wav,
            vad_model,
            sampling_rate=sr
        )

        total_duration = 0

        for seg in speech_segments:

            duration = (seg["end"] - seg["start"]) / sr
            total_duration += duration

        return total_duration >= MIN_SPEECH_DURATION

    except Exception as e:

        print("VAD error:", e)
        return False


# -----------------------------
# STT FUNCTION
# -----------------------------

def transcribe(audio_path):

    try:

        segments, _ = whisper_model.transcribe(
            audio_path,
            beam_size=1
        )

        text = ""

        for seg in segments:
            text += seg.text.strip() + " "

        return text.strip()

    except Exception as e:

        print("STT error:", e)
        return ""


# -----------------------------
# SAVE BASE64 FILE
# -----------------------------

def save_base64_file(data_b64, extension):

    try:

        if "," in data_b64:
            data_b64 = data_b64.split(",")[1]

        file_path = f"{TEMP_DIR}/{uuid.uuid4()}.{extension}"

        with open(file_path, "wb") as f:
            f.write(base64.b64decode(data_b64))

        return file_path

    except Exception as e:

        print("Save error:", e)
        return None


# -----------------------------
# WEBSOCKET INTERVIEW LOOP
# -----------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()

    print("\n" + "="*50)
    print("🎯 Client connected - Interview session started")
    print("="*50 + "\n")

    is_processing = False  # Lock to prevent overlapping processing

    try:

        while True:

            data = await ws.receive_json()

            # Check if we're already processing
            if is_processing:
                print("⏳ Still processing previous response, skipping this audio chunk...")
                await ws.send_json({
                    "status": "processing",
                    "message": "AI is thinking, please wait..."
                })
                continue

            is_processing = True  # Set lock

            image_b64 = data.get("image")
            audio_b64 = data.get("audio")

            if not image_b64 or not audio_b64:
                print("⚠️  Incomplete data received")
                is_processing = False
                continue


            # Save files

            image_path = save_base64_file(image_b64, "jpg")
            audio_webm_path = save_base64_file(audio_b64, "webm")
            if not image_path or not audio_webm_path:
                print("❌ Failed to save files")
                is_processing = False
                continue

            # Convert webm to wav
            audio_wav_path = convert_to_wav(audio_webm_path)
            if not audio_wav_path:
                print("❌ Failed to convert audio")
                is_processing = False
                continue



            # VAD CHECK
            if not has_valid_speech(audio_wav_path):
                print("🔇 No valid speech detected (below threshold)")
                # Send ready status so client doesn't stay locked
                await ws.send_json({
                    "status": "ready_no_speech",
                    "message": "No speech detected, continue when ready"
                })
                is_processing = False
                continue

            print("✓ Speech detected - processing...")

            # STT
            transcript = transcribe(audio_wav_path)

            if len(transcript) < 3:
                print("⚠️  Transcript too short:", transcript)
                # Send ready status so client doesn't stay locked
                await ws.send_json({
                    "status": "ready_no_speech",
                    "message": "Transcript too short, continue when ready"
                })
                is_processing = False
                continue


            print(f"📝 Transcript: {transcript}")


            # OCR
            ocr_text = extract_text(image_path)

            if ocr_text:
                print(f"🖼️  OCR extracted: {ocr_text[:100]}{'...' if len(ocr_text) > 100 else ''}")
            else:
                print("🖼️  No text detected on screen")


            # Ask LLM
            question = interviewer.ask_question(
                transcript,
                ocr_text
            )


            print(f"🤖 AI Question: {question}\n")


            # Send response
            await ws.send_json({
                "status": "ready",
                "transcript": transcript,
                "question": question
            })

            is_processing = False  # Release lock


    except WebSocketDisconnect:

        print("\n" + "="*50)
        print("👋 Client disconnected - Interview session ended")
        print("="*50 + "\n")

    except Exception as e:

        print(f"\n❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()

        await ws.close()


# -----------------------------
# SCORECARD ENDPOINT
# -----------------------------

@app.get("/evaluate")
async def evaluate():

    try:

        scorecard = interviewer.generate_scorecard()

        return scorecard

    except Exception as e:

        print("Evaluation error:", e)
        return {"error": str(e)}


# -----------------------------
# RESET INTERVIEW
# -----------------------------

@app.post("/reset")
async def reset_interview():
    """Reset the interviewer for a new session"""
    global interviewer
    
    try:
        interviewer = InterviewManager()
        return {"status": "Interview reset successfully"}
    
    except Exception as e:
        return {"error": str(e)}


# -----------------------------
# SERVE FRONTEND
# -----------------------------

@app.get("/")
async def serve_frontend():

    with open("index.html", "r") as f:

        return HTMLResponse(f.read())


# -----------------------------
# START SERVER
# -----------------------------

if __name__ == "__main__":

    import uvicorn

    print("Starting server at http://localhost:8000")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
