"""
LinguaBridge Backend - Railway Optimized
"""
import asyncio
import io
import json
import logging
import os
import tempfile
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("linguabridge")

app = FastAPI(title="LinguaBridge API")

# CORS ayarları - Frontend'in bağlanabilmesi için şart
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Whisper model yükleme ─────────────────────
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
DEVICE             = os.getenv("DEVICE", "cpu")
COMPUTE_TYPE       = "int8" if DEVICE == "cpu" else "float16"

whisper_model: WhisperModel = None

@app.on_event("startup")
async def startup():
    global whisper_model
    log.info(f"🎙 Whisper '{WHISPER_MODEL_SIZE}' yükleniyor...")
    whisper_model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        download_root="/app/models"
    )
    log.info("✅ Whisper hazır!")

# ── SAĞLIK KONTROLÜ (Railway bu rotayı bekliyor) ──
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "LinguaBridge Backend is running"}

# ── Ana ses işleme endpoint'i ───────────────────
@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    source_lang: str  = Form("tr"),
    target_lang: str  = Form("en"),
):
    if not whisper_model:
        return JSONResponse({"error": "Model yükleniyor"}, status_code=503)

    start = time.time()
    audio_bytes = await audio.read()

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = whisper_model.transcribe(tmp_path, beam_size=3)
        transcript = " ".join(seg.text.strip() for seg in segments).strip()
        translated = await do_translate(transcript, source_lang, target_lang)

        return {
            "transcript": transcript,
            "translated": translated,
            "ms": int((time.time() - start) * 1000)
        }
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ── Çeviri motoru ─────────────────────────────
async def do_translate(text: str, from_lang: str, to_lang: str) -> str:
    if from_lang == to_lang or not text:
        return text

    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": f"{from_lang}|{to_lang}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(url, params=params)
            return r.json()["responseData"]["translatedText"]
        except:
            return text

# ── SUNUCU BAŞLATMA (En kritik kısım) ──────────
if __name__ == "__main__":
    import uvicorn

    # Railway'in verdiği dinamik portu yakala
    port = int(os.environ.get("PORT", 8080))

    # 0.0.0.0 hostu dış dünyaya açılmak için zorunludur
    uvicorn.run(app, host="0.0.0.0", port=port)
