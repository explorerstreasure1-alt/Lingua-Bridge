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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("linguabridge")

app = FastAPI(title="LinguaBridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
DEVICE             = os.getenv("DEVICE", "cpu")

whisper_model: WhisperModel = None
model_lock = asyncio.Lock()


def _load_model() -> WhisperModel:
    log.info(f"🎙 Whisper '{WHISPER_MODEL_SIZE}' yükleniyor...")
    model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device=DEVICE,
        compute_type="int8",
        download_root="/app/models",
    )
    log.info("✅ Whisper hazır!")
    return model


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "LinguaBridge Backend is running"}


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    source_lang: str  = Form("tr"),
    target_lang: str  = Form("en"),
):
    global whisper_model

    # İlk istekte lazy load
    if whisper_model is None:
        async with model_lock:
            if whisper_model is None:
                loop = asyncio.get_event_loop()
                whisper_model = await loop.run_in_executor(None, _load_model)

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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
