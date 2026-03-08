"""
LinguaBridge Backend - Railway Optimized
"""
import asyncio
import logging
import os
import tempfile
import time

import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("linguabridge")

app = FastAPI(title="LinguaBridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Whisper config ─────────────────────────────
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
DEVICE             = os.getenv("DEVICE", "cpu")
COMPUTE_TYPE       = "int8" if DEVICE == "cpu" else "float16"

whisper_model: WhisperModel = None
model_ready = False          # ← yeni flag

@app.on_event("startup")
async def startup():
    """Modeli arka planda yükle — healthcheck bloklanmasın."""
    asyncio.create_task(_load_model_background())

async def _load_model_background():
    global whisper_model, model_ready
    log.info(f"🎙 Whisper '{WHISPER_MODEL_SIZE}' arka planda yükleniyor...")
    try:
        # CPU-bound işi thread pool'a at, event loop'u bloklamasın
        loop = asyncio.get_event_loop()
        whisper_model = await loop.run_in_executor(
            None,
            lambda: WhisperModel(
                WHISPER_MODEL_SIZE,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                download_root="/app/models",
            )
        )
        model_ready = True
        log.info("✅ Whisper hazır!")
    except Exception as e:
        log.error(f"❌ Whisper yüklenemedi: {e}")

# ── SAĞLIK KONTROLÜ ────────────────────────────
@app.get("/health")
async def health():
    # Railway sadece 200 bekliyor; model durumunu da ekledik (opsiyonel)
    return {"status": "ok", "model_ready": model_ready}

@app.get("/")
async def root():
    return {"message": "LinguaBridge Backend is running"}

# ── Transkripsiyon ──────────────────────────────
@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    source_lang: str  = Form("tr"),
    target_lang: str  = Form("en"),
):
    if not model_ready:
        return JSONResponse(
            {"error": "Model henüz hazır değil, lütfen bekleyin"},
            status_code=503
        )

    start = time.time()
    audio_bytes = await audio.read()

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        loop = asyncio.get_event_loop()
        segments, _ = await loop.run_in_executor(
            None,
            lambda: whisper_model.transcribe(tmp_path, beam_size=3)
        )
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

# ── Çeviri motoru ───────────────────────────────
async def do_translate(text: str, from_lang: str, to_lang: str) -> str:
    if from_lang == to_lang or not text:
        return text

    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": f"{from_lang}|{to_lang}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(url, params=params)
            return r.json()["responseData"]["translatedText"]
        except Exception:
            return text

# ── SUNUCU BAŞLATMA ─────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
