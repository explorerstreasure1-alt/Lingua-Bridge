# 🌐 LinguaBridge — Groq Edition

**Firefox ✅ Safari ✅ Chrome ✅ Edge ✅ Mobil ✅**
Model indirme yok · RAM sorunu yok · Groq Whisper API ile anında çalışır

---

## Klasör Yapısı
```
linguabridge/
├── frontend/        ← Vercel deploy eder
│   └── index.html
├── backend/         ← Railway deploy eder
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
├── vercel.json      ← root'ta durur
└── README.md
```

---

## ADIM 1 — Groq API Key Al (Ücretsiz, 1 dakika)

1. **console.groq.com** → Google ile giriş yap
2. Sol menü → **API Keys → Create API Key**
3. Key'i kopyala: `gsk_xxxxxxxxxxxxxxxxxxxx`

**Limit:** Günlük 28.800 dakika ses tanıma — ücretsiz, sınırsız gibi.

---

## ADIM 2 — GitHub'a Yükle
```bash
git init
git add .
git commit -m "LinguaBridge Groq Edition"
git remote add origin https://github.com/KULLANICI/linguabridge.git
git push -u origin main
```

---

## ADIM 3 — Railway Deploy (Backend)

1. **railway.app** → New Project → Deploy from GitHub → `linguabridge`
2. **Settings → Root Directory → `backend`**
3. **Variables** sekmesi → **+ New Variable**:
   ```
   GROQ_API_KEY = gsk_xxxxxxxxxxxxxxxxxxxx
   ```
4. Deploy et → **~60 saniyede** hazır (model indirme yok!)
5. **Settings → Domains → Generate Domain** → URL al

---

## ADIM 4 — Vercel Deploy (Frontend)

1. **vercel.com** → New Project → GitHub → `linguabridge`
2. **Root Directory → `frontend`**
3. Deploy et → URL al

---

## ADIM 5 — Bağla

Vercel siteni aç → sarı kutucuğa Railway URL'ini yaz → **Kaydet & Test Et** → ✅

---

## Neden Groq?

| | Eski (Faster-Whisper) | Yeni (Groq API) |
|---|---|---|
| RAM | 500MB+ | ~80MB |
| İlk yükleme | 3-5 dakika | 60 saniye |
| Healthcheck | Başarısız | ✅ Anında geçer |
| Hız | Yavaş (CPU) | ⚡ 10x hızlı |
| Ücret | Ücretsiz | Ücretsiz |
