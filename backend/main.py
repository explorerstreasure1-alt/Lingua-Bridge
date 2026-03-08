"""
LinguaBridge Backend
- Faster-Whisper ile tarayıcı bağımsız ses tanıma
- MyMemory + Lingva ile çeviri
- WebSocket ile gerçek zamanlı iletişim
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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("linguabridge")

app = FastAPI(title="LinguaBridge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Whisper model (startup'ta yükle) ─────────────────────
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")
DEVICE             = os.getenv("DEVICE", "cpu")
COMPUTE_TYPE       = "int8" if DEVICE == "cpu" else "float16"

whisper_model: WhisperModel = None

@app.on_event("startup")
async def startup():
    global whisper_model
    log.info(f"🎙 Whisper '{WHISPER_MODEL_SIZE}' yükleniyor ({DEVICE})...")
    whisper_model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        download_root="/app/models"
    )
    log.info("✅ Whisper hazır!")

# ── Sağlık kontrolü ──────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "whisper": WHISPER_MODEL_SIZE, "device": DEVICE}

# ── Ana endpoint: ses → metin → çeviri ───────────────────
@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    source_lang: str  = Form("tr"),
    target_lang: str  = Form("en"),
):
    if not whisper_model:
        return JSONResponse({"error": "Model yükleniyor, bekle"}, status_code=503)

    start = time.time()
    audio_bytes = await audio.read()
    if len(audio_bytes) < 1000:
        return JSONResponse({"error": "Ses çok kısa"}, status_code=400)

    suffix = ".webm"
    ext = audio.filename.split(".")[-1] if audio.filename else "webm"
    if ext in ("ogg", "mp4", "wav", "mp3", "webm"):
        suffix = f".{ext}"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        whisper_lang = source_lang if source_lang != "auto" else None
        segments, info = whisper_model.transcribe(
            tmp_path,
            language=whisper_lang,
            beam_size=3,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300}
        )

        transcript = " ".join(seg.text.strip() for seg in segments).strip()
        detected_lang = info.language

        if not transcript:
            return JSONResponse({
                "transcript": "",
                "translated": "",
                "detected_lang": detected_lang,
                "ms": int((time.time() - start) * 1000)
            })

        translated = await do_translate(transcript, source_lang, target_lang)
        ms = int((time.time() - start) * 1000)
        log.info(f"[{source_lang}→{target_lang}] '{transcript[:40]}' → '{translated[:40]}' ({ms}ms)")

        return {
            "transcript":    transcript,
            "translated":    translated,
            "detected_lang": detected_lang,
            "ms":            ms
        }
    finally:
        try: os.unlink(tmp_path)
        except: pass

@app.post("/translate")
async def translate_endpoint(body: dict):
    text        = body.get("text", "")
    source_lang = body.get("source_lang", "tr")
    target_lang = body.get("target_lang", "en")
    if not text:
        return {"translated": ""}
    translated = await do_translate(text, source_lang, target_lang)
    return {"translated": translated, "original": text}

async def do_translate(text: str, from_lang: str, to_lang: str) -> str:
    if from_lang == to_lang:
        return text
    try:
        result = await mymemory_translate(text, from_lang, to_lang)
        if result and result != text:
            return result
    except Exception as e:
        log.warning(f"MyMemory başarısız: {e}")
    try:
        result = await lingva_translate(text, from_lang, to_lang)
        if result:
            return result
    except Exception as e:
        log.warning(f"Lingva başarısız: {e}")
    return text

async def mymemory_translate(text: str, from_lang: str, to_lang: str) -> str:
    url = "https://api.mymemory.translated.net/get"
    params = {"q": text, "langpair": f"{from_lang}|{to_lang}", "de": "translate@linguabridge.app"}
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(url, params=params)
        j = r.json()
        if j.get("responseStatus") == 200:
            return j["responseData"]["translatedText"]
        raise Exception(f"Status: {j.get('responseStatus')}")

async def lingva_translate(text: str, from_lang: str, to_lang: str) -> str:
    instances = ["https://lingva.ml", "https://translate.plausibility.cloud", "https://lingva.lunar.icu"]
    import urllib.parse
    encoded = urllib.parse.quote(text)
    async with httpx.AsyncClient(timeout=6.0) as client:
        for base in instances:
            try:
                url = f"{base}/api/v1/{from_lang}/{to_lang}/{encoded}"
                r = await client.get(url)
                if r.status_code == 200:
                    j = r.json()
                    if j.get("translation"): return j["translation"]
            except: continue
    raise Exception("Tüm Lingva instance'ları başarısız")

@app.websocket("/ws/transcribe")
async def ws_transcribe(ws: WebSocket):
    await ws.accept()
    log.info("WebSocket bağlandı")
    try:
        while True:
            data = await ws.receive_json()
            import base64
            audio_bytes = base64.b64decode(data.get("audio_b64", ""))
            source_lang = data.get("source_lang", "tr")
            target_lang = data.get("target_lang", "en")

            if len(audio_bytes) < 1000: continue

            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                segments, info = whisper_model.transcribe(
                    tmp_path,
                    language=source_lang if source_lang != "auto" else None,
                    beam_size=3,
                    vad_filter=True
                )
                transcript = " ".join(s.text.strip() for s in segments).strip()
                if transcript:
                    translated = await do_translate(transcript, source_lang, target_lang)
                    await ws.send_json({"transcript": transcript, "translated": translated, "detected": info.language})
            finally:
                try: os.unlink(tmp_path)
                except: pass
    except WebSocketDisconnect:
        log.info("WebSocket kapandı")
    except Exception as e:
        log.error(f"WebSocket hata: {e}")
        try: await ws.close()
        except: pass

# --- SUNUCU ÇALIŞTIRMA AYARI (DUVARIN DİBİNDE OLMALI) ---
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
