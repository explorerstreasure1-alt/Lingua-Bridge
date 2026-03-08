"""
LinguaBridge Backend — Groq Whisper API
Model indirme yok, RAM sorunu yok, Railway free tier'da sorunsuz çalışır.
"""

import gc
import logging
import os
import tempfile
import time
import urllib.parse

import httpx
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("linguabridge")

app = FastAPI(title="LinguaBridge API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL   = "whisper-large-v3-turbo"  # En hızlı, ücretsiz

# ── Healthcheck — anında 200 döner ──────────────────────
@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "engine": "groq-whisper", "ready": bool(GROQ_API_KEY)}

# ── Ana endpoint: ses → metin → çeviri ──────────────────
@app.post("/transcribe")
async def transcribe(
    audio:       UploadFile = File(...),
    source_lang: str        = Form("tr"),
    target_lang: str        = Form("en"),
):
    if not GROQ_API_KEY:
        return JSONResponse({"error": "GROQ_API_KEY eksik"}, status_code=500)

    start       = time.time()
    audio_bytes = await audio.read()

    if len(audio_bytes) < 1500:
        return JSONResponse({"error": "Ses çok kısa"}, status_code=400)

    # Uzantıyı belirle
    ext = "webm"
    if audio.filename:
        e = audio.filename.rsplit(".", 1)[-1].lower()
        if e in ("ogg", "mp4", "wav", "mp3", "webm", "m4a"):
            ext = e

    # Geçici dosyaya yaz
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # ── 1. Groq Whisper STT ──────────────────────────
        transcript = await groq_transcribe(tmp_path, ext, source_lang)
        if not transcript:
            return {"transcript": "", "translated": "", "ms": int((time.time()-start)*1000)}

        # ── 2. Çeviri ────────────────────────────────────
        translated = await do_translate(transcript, source_lang, target_lang)

        ms = int((time.time() - start) * 1000)
        log.info(f"[{source_lang}→{target_lang}] «{transcript[:40]}» → «{translated[:40]}» ({ms}ms)")

        return {
            "transcript": transcript,
            "translated": translated or transcript,
            "ms":         ms,
        }
    finally:
        try:    os.unlink(tmp_path)
        except: pass
        gc.collect()

async def groq_transcribe(path: str, ext: str, lang: str) -> str:
    """Ses dosyasını Groq Whisper API'ye gönderir, metni döndürür."""
    mime_map = {
        "webm": "audio/webm", "ogg": "audio/ogg",
        "mp4":  "audio/mp4",  "m4a": "audio/mp4",
        "wav":  "audio/wav",  "mp3": "audio/mpeg",
    }
    mime = mime_map.get(ext, "audio/webm")

    with open(path, "rb") as f:
        audio_data = f.read()

    # Groq desteklenen diller (ISO-639-1)
    supported = {
        "tr","en","ru","uk","de","fr","es","it","pt","ar",
        "zh","ja","ko","hi","nl","pl","vi","id","sv","fi","da","no","cs","sk","hu"
    }
    whisper_lang = lang if lang in supported else None

    async with httpx.AsyncClient(timeout=30.0) as client:
        files   = {"file": (f"audio.{ext}", audio_data, mime)}
        data    = {"model": GROQ_MODEL, "response_format": "text"}
        if whisper_lang:
            data["language"] = whisper_lang

        r = await client.post(
            GROQ_STT_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files=files,
            data=data,
        )

    if r.status_code == 200:
        return r.text.strip()

    log.error(f"Groq STT hata {r.status_code}: {r.text[:200]}")
    raise Exception(f"Groq STT başarısız: {r.status_code}")

# ── Çeviri: MyMemory → Lingva fallback ──────────────────
async def do_translate(text: str, from_lang: str, to_lang: str) -> str:
    if not text or from_lang == to_lang:
        return text
    try:
        return await mymemory(text, from_lang, to_lang)
    except Exception as e:
        log.warning(f"MyMemory başarısız: {e}")
    try:
        return await lingva(text, from_lang, to_lang)
    except Exception as e:
        log.warning(f"Lingva başarısız: {e}")
    return text

async def mymemory(text: str, frm: str, to: str) -> str:
    url = (
        f"https://api.mymemory.translated.net/get"
        f"?q={urllib.parse.quote(text)}&langpair={frm}|{to}&de=user@linguabridge.io"
    )
    async with httpx.AsyncClient(timeout=8.0) as c:
        r = await c.get(url)
        j = r.json()
    if j.get("responseStatus") == 200:
        raw = j["responseData"]["translatedText"]
        # HTML entity decode
        import html
        return html.unescape(raw)
    raise Exception(f"status {j.get('responseStatus')}")

async def lingva(text: str, frm: str, to: str) -> str:
    encoded = urllib.parse.quote(text)
    instances = [
        "https://lingva.ml",
        "https://translate.plausibility.cloud",
        "https://lingva.lunar.icu",
    ]
    async with httpx.AsyncClient(timeout=7.0) as c:
        for base in instances:
            try:
                r = await c.get(f"{base}/api/v1/{frm}/{to}/{encoded}")
                if r.status_code == 200:
                    j = r.json()
                    if j.get("translation"):
                        return j["translation"]
            except:
                continue
    raise Exception("Tüm Lingva instance'ları başarısız")

# ── Sadece çeviri endpoint'i ─────────────────────────────
@app.post("/translate")
async def translate_only(body: dict):
    text        = body.get("text", "")
    source_lang = body.get("source_lang", "tr")
    target_lang = body.get("target_lang", "en")
    if not text:
        return {"translated": ""}
    translated = await do_translate(text, source_lang, target_lang)
    return {"translated": translated, "original": text}
